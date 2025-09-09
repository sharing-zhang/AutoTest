#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动时间配置检查脚本
检查TIMER_MAIN.data文件中的活动时间配置是否符合标准
支持多种文件格式和编码方式
"""

import os
import re
import datetime
from typing import Dict, Any, List, Tuple, Optional
from script_base import create_simple_script


# ==================== 辅助函数区域 ====================

def get_timer_file_path(script, directory: str) -> str:
    """
    在指定目录中查找TIMER_MAIN.data相关文件
    支持多种文件名格式

    Args:
        script: ScriptBase实例
        directory: 搜索目录

    Returns:
        str: 找到的文件路径
    """
    possible_files = [
        'TIMER_MAIN.data',
        'TIMER_MAIN.data.txt',
        'timer_main.data',
        'timer_main.data.txt'
    ]

    script.debug(f"在目录 {directory} 中搜索定时器文件")

    for filename in possible_files:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            script.info(f"找到文件: {filename}")
            return file_path

    # 如果没有找到，返回默认的文件路径
    default_path = os.path.join(directory, 'TIMER_MAIN.data')
    script.warning(f"未找到已知文件名，使用默认路径: {default_path}")
    return default_path


def read_file_with_encoding(script, file_path: str, preferred_encoding: str) -> Tuple[str, str]:
    """
    使用合适的编码读取文件内容

    Args:
        script: ScriptBase实例
        file_path: 文件路径
        preferred_encoding: 首选编码

    Returns:
        Tuple[str, str]: (文件内容, 实际使用的编码)

    Raises:
        Exception: 读取文件失败
    """
    encodings_to_try = [preferred_encoding, 'utf-8', 'utf-16', 'gbk', 'ascii']

    for encoding in encodings_to_try:
        try:
            script.debug(f"尝试使用 {encoding} 编码读取文件")
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            script.info(f"成功使用 {encoding} 编码读取文件")
            return content, encoding
        except UnicodeDecodeError:
            script.debug(f"{encoding} 编码失败，尝试下一个")
            continue
        except Exception as e:
            script.error(f"使用 {encoding} 编码读取文件时发生错误: {e}")
            continue

    raise Exception("所有编码方式都无法读取文件")


def parse_activity_block(script, block: str, block_index: int) -> Optional[Dict[str, str]]:
    """
    解析单个活动配置块

    Args:
        script: ScriptBase实例
        block: 配置块文本
        block_index: 配置块索引

    Returns:
        Optional[Dict]: 解析后的活动信息，解析失败返回None
    """
    if not block.strip():
        return None

    # 提取信息
    id_match = re.search(r'id="(.*?)"', block)
    name_match = re.search(r'name="(.*?)"', block)
    open_time_match = re.search(r'openTime="(.*?)"', block)
    end_time_match = re.search(r'endTime="(.*?)"', block)

    if not all([id_match, name_match, open_time_match, end_time_match]):
        script.warning(f"配置块 {block_index + 1} 信息不完整，跳过")
        return None

    return {
        'id': id_match.group(1),
        'name': name_match.group(1),
        'open_time': open_time_match.group(1),
        'end_time': end_time_match.group(1)
    }


def calculate_duration(script, open_time: str, end_time: str) -> Optional[Dict[str, Any]]:
    """
    计算活动持续时间

    Args:
        script: ScriptBase实例
        open_time: 开始时间字符串
        end_time: 结束时间字符串

    Returns:
        Optional[Dict]: 时间计算结果，计算失败返回None
    """
    time_format = "%Y-%m-%d %H:%M:%S"

    try:
        open_date = datetime.datetime.strptime(open_time, time_format)
        end_date = datetime.datetime.strptime(end_time, time_format)
        delta = end_date - open_date

        if delta.total_seconds() <= 0:
            script.warning(f"结束时间早于或等于开始时间: {open_time} -> {end_time}")
            return None

        return {
            'delta': delta,
            'days': delta.days,
            'hours': delta.seconds // 3600,
            'minutes': (delta.seconds // 60) % 60,
            'total_hours': round(delta.total_seconds() / 3600, 2)
        }

    except ValueError as e:
        script.error(f"时间格式错误: {open_time} -> {end_time}, 错误: {e}")
        return None


def is_standard_duration(script, duration_info: Dict[str, Any]) -> bool:
    """
    检查活动持续时间是否符合标准配置

    Args:
        script: ScriptBase实例
        duration_info: 持续时间信息

    Returns:
        bool: 是否符合标准
    """
    days = duration_info['days']
    hours = duration_info['hours']
    minutes = duration_info['minutes']

    # 标准配置检查
    standard_configs = [
        # 精确的天数配置
        (days == 3 and minutes < 1),
        (days == 7 and minutes < 1),
        (days == 14 and minutes < 1),
        # 接近整天的配置 (23小时59分以上)
        (days == 2 and hours == 23 and minutes >= 59),
        (days == 6 and hours == 23 and minutes >= 59),
        (days == 13 and hours == 23 and minutes >= 59)
    ]

    is_standard = any(standard_configs)
    script.debug(f"持续时间检查: {days}天{hours}小时{minutes}分钟 - {'标准' if is_standard else '非标准'}")

    return is_standard


def print_colored_message(script, message: str, color: str):
    """
    输出带颜色的消息

    Args:
        script: ScriptBase实例
        message: 消息内容
        color: 颜色 ('red', 'green', 'yellow')
    """
    colors = {
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'reset': '\033[0m'
    }

    color_code = colors.get(color, '')
    reset_code = colors['reset']

    print(f"{color_code}{message}{reset_code}")


def validate_parameters(script, directory: str, encoding: str) -> Tuple[bool, str]:
    """
    验证输入参数

    Args:
        script: ScriptBase实例
        directory: 目录路径
        encoding: 文件编码

    Returns:
        Tuple[bool, str]: (验证是否通过, 错误信息)
    """
    script.debug("开始验证输入参数")
    script.info(f"接收到参数 - directory: '{directory}', encoding: '{encoding}'")

    # 验证目录参数
    if not directory:
        error_msg = "目录参数不能为空"
        script.error(error_msg)
        return False, error_msg

    # 验证目录路径格式（支持Windows和Linux路径）
    directory = str(directory).strip()
    if not directory:
        error_msg = "目录参数去除空格后为空"
        script.error(error_msg)
        return False, error_msg

    script.info(f"验证目录路径: {directory}")

    # 检查目录是否存在
    if not os.path.exists(directory):
        error_msg = f"目录不存在: {directory}"
        script.error(error_msg)
        script.info(f"当前工作目录: {os.getcwd()}")

        # 尝试列出父目录内容（如果存在）
        parent_dir = os.path.dirname(directory)
        if os.path.exists(parent_dir):
            try:
                contents = os.listdir(parent_dir)
                script.info(f"父目录 {parent_dir} 的内容: {contents[:10]}")  # 只显示前10个
            except Exception as e:
                script.warning(f"无法读取父目录内容: {e}")

        return False, error_msg

    # 检查是否为目录
    if not os.path.isdir(directory):
        error_msg = f"路径不是目录: {directory}"
        script.error(error_msg)
        return False, error_msg

    # 验证编码参数
    valid_encodings = ['UTF-16', 'UTF-8', 'GBK', 'ASCII']
    if encoding not in valid_encodings:
        script.warning(f"编码 '{encoding}' 不在推荐列表中，但将尝试使用")

    script.info("参数验证通过")
    return True, ""


def get_and_validate_parameters(script) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    获取并验证脚本参数

    Args:
        script: ScriptBase实例

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: (目录路径, 编码, 错误信息)
    """
    try:
        script.info("开始获取脚本参数")

        # 获取参数，使用配置文件中定义的默认值
        directory = script.get_parameter('directory', 'C:\\temp')
        encoding = script.get_parameter('encoding', 'UTF-16')

        script.info(f"原始参数 - directory: '{directory}' (类型: {type(directory)})")
        script.info(f"原始参数 - encoding: '{encoding}' (类型: {type(encoding)})")

        # 参数类型和格式处理
        if directory is None:
            directory = 'C:\\temp'
            script.warning("directory参数为None，使用默认值")

        if encoding is None:
            encoding = 'UTF-16'
            script.warning("encoding参数为None，使用默认值")

        # 确保参数为字符串类型
        directory = str(directory).strip()
        encoding = str(encoding).strip()

        script.info(f"处理后参数 - directory: '{directory}', encoding: '{encoding}'")

        # 验证参数
        is_valid, error_msg = validate_parameters(script, directory, encoding)

        if not is_valid:
            return None, None, error_msg

        return directory, encoding, None

    except Exception as e:
        error_msg = f"获取参数时发生异常: {str(e)}"
        script.error(error_msg)
        import traceback
        script.debug(f"异常堆栈: {traceback.format_exc()}")
        return None, None, error_msg


# ==================== 主逻辑函数 ====================

def main_logic(script):
    """
    活动时间配置检查主逻辑

    Args:
        script: ScriptBase实例
    """

    script.info("=== 开始执行活动时间配置检查 ===")

    # 1. 获取并验证参数
    directory, encoding, param_error = get_and_validate_parameters(script)

    if param_error:
        return script.error_result(param_error, "ParameterError")

    script.info(f"使用参数 - 检查目录: {directory}, 文件编码: {encoding}")

    # 2. 查找并读取文件
    try:
        file_path = get_timer_file_path(script, directory)

        if not os.path.exists(file_path):
            error_msg = f"未找到TIMER_MAIN.data文件在目录: {directory}"
            script.error(error_msg)

            # 列出目录中的文件以帮助调试
            try:
                files_in_dir = os.listdir(directory)
                script.info(f"目录 {directory} 中的文件: {files_in_dir}")
            except Exception as list_error:
                script.warning(f"无法列出目录内容: {list_error}")

            return script.error_result(error_msg, 'FileNotFound')

        script.info(f"准备读取文件: {file_path}")
        content, actual_encoding = read_file_with_encoding(script, file_path, encoding)
        blocks = content.split('\n\n')

        script.info(f"成功读取文件，使用编码: {actual_encoding}，共找到 {len(blocks)} 个配置块")

    except Exception as e:
        error_msg = f"读取文件失败: {str(e)}"
        script.error(error_msg)
        import traceback
        script.debug(f"文件读取异常堆栈: {traceback.format_exc()}")
        return script.error_result(error_msg, 'FileReadError')

    # 3. 处理配置块
    total_activities = 0
    invalid_time_activities = 0
    abnormal_duration_activities = []

    script.info("开始解析活动配置块...")

    for i, block in enumerate(blocks):
        # 解析活动信息
        activity_info = parse_activity_block(script, block, i)
        if not activity_info:
            continue

        total_activities += 1
        script.debug(f"处理活动 {total_activities}: {activity_info['name']} (ID: {activity_info['id']})")

        # 计算持续时间
        duration_info = calculate_duration(
            script,
            activity_info['open_time'],
            activity_info['end_time']
        )

        if not duration_info:
            invalid_time_activities += 1
            print_colored_message(
                script,
                f"⚠️  无效的活动时间配置: ID: {activity_info['id']}, Name: {activity_info['name']}, "
                f"openTime={activity_info['open_time']}, endTime={activity_info['end_time']}",
                'yellow'
            )
            continue

        # 检查是否符合标准
        if not is_standard_duration(script, duration_info):
            abnormal_activity = {
                'id': activity_info['id'],
                'name': activity_info['name'],
                'open_time': activity_info['open_time'],
                'end_time': activity_info['end_time'],
                'duration_days': duration_info['days'],
                'duration_hours': duration_info['hours'],
                'duration_minutes': duration_info['minutes'],
                'duration_text': f"{duration_info['days']}天 {duration_info['hours']}小时 {duration_info['minutes']}分钟",
                'total_duration_hours': duration_info['total_hours']
            }
            abnormal_duration_activities.append(abnormal_activity)

            print_colored_message(
                script,
                f"🔴 需要注意的活动时间配置:\n"
                f"   ID: {activity_info['id']}\n"
                f"   Name: {activity_info['name']}\n"
                f"   开始时间: {activity_info['open_time']}\n"
                f"   结束时间: {activity_info['end_time']}\n"
                f"   持续时间: {abnormal_activity['duration_text']}",
                'red'
            )

    # 4. 生成检查结果摘要
    script.info("=== 活动时间配置检查完成 ===")
    script.info(f"📊 检查统计:")
    script.info(f"   - 总活动数: {total_activities}")
    script.info(f"   - 时间格式无效的活动数: {invalid_time_activities}")
    script.info(f"   - 持续时间异常的活动数: {len(abnormal_duration_activities)}")

    # 5. 构建结果数据
    has_issues = len(abnormal_duration_activities) > 0 or invalid_time_activities > 0
    issues_count = len(abnormal_duration_activities) + invalid_time_activities

    result_data = {
        'input_parameters': {
            'directory': directory,
            'encoding_requested': encoding
        },
        'file_info': {
            'file_path': file_path,
            'encoding_used': actual_encoding,
            'file_exists': True
        },
        'analysis_results': {
            'total_activities': total_activities,
            'invalid_time_activities': invalid_time_activities,
            'abnormal_duration_count': len(abnormal_duration_activities),
            'abnormal_duration_activities': abnormal_duration_activities
        },
        'check_summary': {
            'has_issues': has_issues,
            'issues_count': issues_count,
            'check_passed': not has_issues
        }
    }

    # 6. 生成最终消息并返回结果
    if has_issues:
        message = f"🔍 检查完成：发现 {issues_count} 个活动时间配置问题，需要关注"
        print_colored_message(script, message, 'yellow')
        script.warning(message)
    else:
        message = "✅ 检查完成：所有活动时间配置都符合标准"
        print_colored_message(script, message, 'green')
        script.info(message)

    return script.success_result(message, result_data)


if __name__ == '__main__':
    create_simple_script('check_ConfigTime', main_logic)