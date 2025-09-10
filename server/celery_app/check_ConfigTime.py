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

def find_target_files(script, directory: str, file_names: List[str], recursive: bool) -> List[str]:
    """
    在指定目录中查找目标文件名，支持是否递归

    Args:
        script: ScriptBase实例
        directory: 搜索目录
        file_names: 文件名列表
        recursive: 是否递归

    Returns:
        List[str]: 找到的文件路径列表
    """
    normalized = {str(n).strip() for n in (file_names or []) if str(n).strip()}
    if not normalized:
        normalized = {
            'TIMER_MAIN.data',
            'TIMER_MAIN.data.txt',
            'timer_main.data',
            'timer_main.data.txt'
        }

    matched: List[str] = []
    script.debug(f"在目录 {directory} 中搜索文件: {sorted(list(normalized))} (递归: {recursive})")

    try:
        if recursive:
            for root, _, files in os.walk(directory):
                for fname in files:
                    if fname in normalized:
                        matched.append(os.path.join(root, fname))
        else:
            for fname in os.listdir(directory):
                path = os.path.join(directory, fname)
                if os.path.isfile(path) and fname in normalized:
                    matched.append(path)
    except Exception as e:
        script.error(f"搜索文件时发生错误: {e}")

    if not matched:
        script.warning("未找到匹配的配置文件")

    return matched


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
    特殊处理：当持续时间为x天23:59:59时，直接处理为x+1天

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

        # 计算基本时间信息
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds // 60) % 60
        seconds = delta.seconds % 60

        # 特殊处理：当持续时间为23:59:59时，直接处理为1天
        if hours == 23 and minutes == 59 and seconds == 59:
            days += 1
            hours = 0
            minutes = 0
            seconds = 0
            script.debug(f"检测到{days-1}天23:59:59格式，调整为{days-1}天 -> {days}天")
        
        # 计算调整后的总小时数
        total_hours = days * 24 + hours + minutes / 60 + seconds / 3600

        return {
            'delta': delta,
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'total_hours': round(total_hours, 2),
            'original_days': delta.days,  # 保留原始天数用于调试
            'adjusted': hours == 0 and minutes == 0 and seconds == 0 and days > delta.days  # 标记是否被调整
        }

    except ValueError as e:
        script.error(f"时间格式错误: {open_time} -> {end_time}, 错误: {e}")
        return None


def is_days_in_expected(script, duration_info: Dict[str, Any], expected_days: List[int]) -> bool:
    """
    检查持续天数是否在允许范围内

    Args:
        script: ScriptBase实例
        duration_info: 持续时间信息
        expected_days: 期望天数列表

    Returns:
        bool: 是否在期望范围内
    """
    days = duration_info['days']
    ok = days in set(expected_days or [])
    script.debug(f"持续时间天数检查: {days} 天 - {'在范围内' if ok else '不在范围'}，允许: {expected_days}")
    return ok


def print_message(message):
    """
    简单打印消息（无颜色）
    """
    import sys
    import re

    try:
        # 确保message是字符串
        if not isinstance(message, str):
            message = str(message)

        # 在Windows环境下移除emoji
        if sys.platform == "win32":
            emoji_pattern = re.compile("["
                                       u"\U0001F600-\U0001F64F"  # emoticons
                                       u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                       u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                       u"\U0001F1E0-\U0001F1FF"  # flags
                                       "]+", flags=re.UNICODE)
            message = emoji_pattern.sub('', message)

        print(message)

    except UnicodeEncodeError:
        clean_message = message.encode('ascii', errors='ignore').decode('ascii')
        print(clean_message)
    except Exception as e:
        print(f"打印消息时出错: {e}")
        try:
            print(str(message))
        except:
            print("无法显示消息内容")


def validate_parameters(script, directory: str, encoding: str, expected_days: List[int] = None) -> Tuple[bool, str]:
    """
    验证输入参数

    Args:
        script: ScriptBase实例
        directory: 目录路径
        encoding: 文件编码
        expected_days: 期望天数列表

    Returns:
        Tuple[bool, str]: (验证是否通过, 错误信息)
    """
    script.debug("开始验证输入参数")
    script.info(f"接收到参数 - directory: '{directory}', encoding: '{encoding}', expected_days: {expected_days}")

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

    # 验证期望天数参数
    if expected_days is not None:
        if not isinstance(expected_days, (list, tuple)):
            error_msg = "期望天数参数必须是列表或元组"
            script.error(error_msg)
            return False, error_msg
        
        if not expected_days:
            error_msg = "期望天数列表不能为空"
            script.error(error_msg)
            return False, error_msg
        
        # 检查天数是否都是正整数
        for day in expected_days:
            if not isinstance(day, int) or day <= 0:
                error_msg = f"期望天数必须是正整数，发现无效值: {day}"
                script.error(error_msg)
                return False, error_msg
        
        # 检查天数范围是否合理（1-365天）
        max_day = max(expected_days)
        if max_day > 365:
            script.warning(f"发现较大的天数值: {max_day}，请确认是否合理")
        
        script.info(f"期望天数验证通过: {expected_days}")

    script.info("参数验证通过")
    return True, ""


def get_and_validate_parameters(script) -> Tuple[Optional[str], Optional[str], Optional[List[str]], Optional[bool], Optional[List[int]], Optional[str]]:
    """
    获取并验证脚本参数

    Args:
        script: ScriptBase实例

    Returns:
        Tuple[Optional[str], Optional[str], Optional[List[str]], Optional[bool], Optional[List[int]], Optional[str]]:
            (目录路径, 编码, 文件名集合, 是否递归, 期望天数集合, 错误信息)
    """
    try:
        script.info("开始获取脚本参数")

        # 获取参数，使用配置文件中定义的默认值
        directory = script.get_parameter('directory', 'C:\\temp')
        encoding = script.get_parameter('encoding', 'UTF-16')
        file_names = script.get_parameter('file_names', [
            'TIMER_MAIN.data', 'TIMER_MAIN.data.txt', 'timer_main.data', 'timer_main.data.txt'
        ])
        recursive = script.get_parameter('recursive', False)
        expected_days_param = script.get_parameter('expected_days', [3, 7, 14])

        script.info(f"原始参数 - directory: '{directory}' (类型: {type(directory)})")
        script.info(f"原始参数 - encoding: '{encoding}' (类型: {type(encoding)})")

        # 参数类型和格式处理
        if directory is None:
            directory = 'C:\\temp'
            script.warning("directory参数为None，使用默认值")

        if encoding is None:
            encoding = 'UTF-16'
            script.warning("encoding参数为None，使用默认值")

        # file_names 处理为列表[str]
        if file_names is None:
            file_names = ['TIMER_MAIN.data', 'TIMER_MAIN.data.txt', 'timer_main.data', 'timer_main.data.txt']
            script.warning("file_names参数为None，使用默认值")
        elif isinstance(file_names, str):
            file_names = [seg.strip() for seg in file_names.split(',') if seg.strip()]
        elif isinstance(file_names, (list, tuple)):
            file_names = [str(x).strip() for x in file_names if str(x).strip()]
        else:
            file_names = [str(file_names)]

        # recursive 转为布尔
        recursive = bool(recursive)

        # expected_days 转为列表[int] - 支持多种输入格式
        if expected_days_param is None:
            expected_days = [3, 7, 14]
            script.warning("expected_days参数为None，使用默认值")
        elif isinstance(expected_days_param, (list, tuple)):
            expected_days = []
            for x in expected_days_param:
                try:
                    # 支持字符串和数字类型
                    if isinstance(x, str):
                        # 处理逗号分隔的字符串
                        if ',' in x:
                            for item in x.split(','):
                                item = item.strip()
                                if item.isdigit():
                                    expected_days.append(int(item))
                        else:
                            if x.strip().isdigit():
                                expected_days.append(int(x.strip()))
                    else:
                        expected_days.append(int(x))
                except (ValueError, TypeError) as e:
                    script.warning(f"跳过无效的天数值: {x}, 错误: {e}")
                    continue
        elif isinstance(expected_days_param, str):
            # 处理字符串格式，支持逗号分隔
            expected_days = []
            for item in expected_days_param.split(','):
                item = item.strip()
                if item.isdigit():
                    expected_days.append(int(item))
                else:
                    script.warning(f"跳过无效的天数值: {item}")
        else:
            try:
                expected_days = [int(expected_days_param)]
            except (ValueError, TypeError):
                expected_days = [3, 7, 14]
                script.warning(f"expected_days参数格式无效: {expected_days_param}，使用默认值")
        
        # 确保至少有一个有效值
        if not expected_days:
            expected_days = [3, 7, 14]
            script.warning("没有有效的天数参数，使用默认值")
        
        # 去重并排序
        expected_days = sorted(list(set(expected_days)))
        script.info(f"处理后的期望天数: {expected_days}")

        # 确保参数为字符串类型
        directory = str(directory).strip()
        encoding = str(encoding).strip()

        script.info(f"处理后参数 - directory: '{directory}', encoding: '{encoding}'")

        # 验证参数
        is_valid, error_msg = validate_parameters(script, directory, encoding, expected_days)

        if not is_valid:
            return None, None, None, None, None, error_msg

        return directory, encoding, file_names, recursive, expected_days, None

    except Exception as e:
        error_msg = f"获取参数时发生异常: {str(e)}"
        script.error(error_msg)
        import traceback
        script.debug(f"异常堆栈: {traceback.format_exc()}")
        return None, None, None, None, None, error_msg


# ==================== 主逻辑函数 ====================

def main_logic(script):
    """
    活动时间配置检查主逻辑

    Args:
        script: ScriptBase实例
    """

    script.info("=== 开始执行活动时间配置检查 ===")

    # 1. 获取并验证参数
    directory, encoding, file_names, recursive, expected_days, param_error = get_and_validate_parameters(script)

    if param_error:
        return script.error_result(param_error, "ParameterError")

    script.info(f"使用参数 - 检查目录: {directory}, 文件编码: {encoding}, 递归: {recursive}, 期望天数: {expected_days}, 目标文件: {file_names}")

    # 2. 查找目标文件
    target_files = find_target_files(script, directory, file_names or [], bool(recursive))
    if not target_files:
        error_msg = f"未在目录 {directory} 找到目标配置文件"
        script.error(error_msg)
        try:
            files_in_dir = os.listdir(directory)
            script.info(f"目录 {directory} 中的文件: {files_in_dir[:50]}")
        except Exception as list_error:
            script.warning(f"无法列出目录内容: {list_error}")
        return script.error_result(error_msg, 'FileNotFound')

    # 3. 处理配置块
    total_activities = 0
    invalid_time_activities = 0
    abnormal_duration_activities = []
    processed_files_info: List[Dict[str, Any]] = []

    script.info("开始解析活动配置块...")

    # 逐文件读取并检查
    for file_path in target_files:
        script.info(f"准备读取文件: {file_path}")
        try:
            content, actual_encoding = read_file_with_encoding(script, file_path, encoding)
            blocks = content.split('\n\n')
            script.info(f"成功读取文件，使用编码: {actual_encoding}，共找到 {len(blocks)} 个配置块")
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            script.error(error_msg)
            import traceback
            script.debug(f"文件读取异常堆栈: {traceback.format_exc()}")
            return script.error_result(error_msg, 'FileReadError')

        file_total = 0
        file_invalid = 0
        file_abnormal = 0

        for i, block in enumerate(blocks):
            # 解析活动信息
            activity_info = parse_activity_block(script, block, i)
            if not activity_info:
                continue

            total_activities += 1
            file_total += 1
            script.debug(f"处理活动 {total_activities}: {activity_info['name']} (ID: {activity_info['id']})")

            # 计算持续时间
            duration_info = calculate_duration(
                script,
                activity_info['open_time'],
                activity_info['end_time']
            )

            if not duration_info:
                invalid_time_activities += 1
                file_invalid += 1
                print_message(
                    f"无效的活动时间配置: 文件={os.path.basename(file_path)}, ID={activity_info['id']}, Name={activity_info['name']}, 开始时间={activity_info['open_time']}, 结束时间={activity_info['end_time']}"
                )
                continue

            # 检查天数是否在配置范围
            if not is_days_in_expected(script, duration_info, expected_days or []):
                abnormal_activity = {
                    'file_path': file_path,
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

                file_abnormal += 1

                print_message(
                    f"持续天数不在允许范围 ({expected_days}): 文件={os.path.basename(file_path)}, ID={activity_info['id']}, Name={activity_info['name']}, 开始时间={activity_info['open_time']}, 结束时间={activity_info['end_time']}, 持续时间={abnormal_activity['duration_text']}"
                )

        processed_files_info.append({
            'file_path': file_path,
            'encoding_used': actual_encoding if 'actual_encoding' in locals() else None,
            'total_activities': file_total,
            'invalid_time_activities': file_invalid,
            'abnormal_duration_activities': file_abnormal
        })

    # 4. 生成检查结果摘要
    script.info("=== 活动时间配置检查完成 ===")
    script.info(f"检查统计:")
    script.info(f"   - 总活动数: {total_activities}")
    script.info(f"   - 时间格式无效的活动数: {invalid_time_activities}")
    script.info(f"   - 持续时间异常的活动数: {len(abnormal_duration_activities)}")

    # 5. 构建结果数据
    has_issues = len(abnormal_duration_activities) > 0 or invalid_time_activities > 0
    issues_count = len(abnormal_duration_activities) + invalid_time_activities

    result_data = {
        'input_parameters': {
            'directory': directory,
            'encoding_requested': encoding,
            'recursive': bool(recursive),
            'file_names': file_names,
            'expected_days': expected_days
        },
        'file_info': {
            'searched_directory': directory,
            'target_files': target_files,
            'files_processed': processed_files_info
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
        message = f"检查完成：发现 {issues_count} 个活动时间配置问题，需要关注"
        print_message(message)
        script.warning(message)
    else:
        message = "检查完成：所有活动时间配置都符合标准"
        print_message(message)
        script.info(message)

    return script.success_result(message, result_data)


if __name__ == '__main__':
    create_simple_script('check_ConfigTime', main_logic)