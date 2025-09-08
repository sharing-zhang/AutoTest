#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动时间配置检查脚本
检查TIMER_MAIN.data文件中的活动时间配置是否符合标准
"""

import os
import re
import datetime
from typing import Dict, Any
from script_base import ScriptBase, create_simple_script


def get_timer_file_path(directory: str) -> str:
    """
    在指定目录中查找TIMER_MAIN.data相关文件
    支持多种文件名格式
    """
    possible_files = [
        'TIMER_MAIN.data',
        'TIMER_MAIN.data.txt',
        'timer_main.data',
        'timer_main.data.txt'
    ]

    for filename in possible_files:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            return file_path

    # 如果没有找到，返回默认的文件路径
    return os.path.join(directory, 'TIMER_MAIN.data')


def check_activity_time_config(script: ScriptBase) -> Dict[str, Any]:
    """检查活动时间配置的主要逻辑"""

    # 分别定义红色、绿色和黄色的ANSI escape code
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RESET = '\033[0m'  # 用于重置颜色

    # 从参数获取目录路径
    directory = script.get_parameter('directory', 'C:\\temp')
    encoding = script.get_parameter('encoding', 'UTF-16')

    script.info(f"开始检查目录: {directory}")

    # 检查目录是否存在
    if not os.path.exists(directory):
        error_msg = f"目录不存在: {directory}"
        script.error(error_msg)
        return script.error_result(error_msg, 'DirectoryNotFound')

    if not os.path.isdir(directory):
        error_msg = f"路径不是目录: {directory}"
        script.error(error_msg)
        return script.error_result(error_msg, 'NotADirectory')

    # 查找TIMER_MAIN.data文件
    file_path = get_timer_file_path(directory)
    script.info(f"查找到文件路径: {file_path}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        error_msg = f"未找到TIMER_MAIN.data文件在目录: {directory}"
        script.error(error_msg)
        return script.error_result(error_msg, 'FileNotFound')

    # 读取文件内容
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
            blocks = content.split('\n\n')
        script.info(f"成功读取文件，共找到 {len(blocks)} 个配置块")
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            script.warning(f"使用{encoding}编码失败，尝试UTF-8编码")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                blocks = content.split('\n\n')
            encoding = 'utf-8'  # 更新实际使用的编码
            script.info(f"使用UTF-8编码成功读取文件")
        except Exception as e2:
            error_msg = f"读取文件失败(多种编码尝试): {str(e2)}"
            script.error(error_msg)
            return script.error_result(error_msg, 'EncodingError')
    except Exception as e:
        error_msg = f"读取文件失败: {str(e)}"
        script.error(error_msg)
        return script.error_result(error_msg, 'FileReadError')

    time_format = "%Y-%m-%d %H:%M:%S"

    # 统计信息
    total_activities = 0
    invalid_time_activities = 0
    abnormal_duration_activities = []

    # 处理每个配置块
    for i, block in enumerate(blocks):
        if not block.strip():  # 跳过空块
            continue

        total_activities += 1

        # 提取信息
        id_match = re.search(r'id="(.*?)"', block)
        name_match = re.search(r'name="(.*?)"', block)
        open_time_match = re.search(r'openTime="(.*?)"', block)
        end_time_match = re.search(r'endTime="(.*?)"', block)

        if not all([id_match, name_match, open_time_match, end_time_match]):
            script.warning(f"配置块 {i + 1} 信息不完整，跳过")
            continue

        activity_id = id_match.group(1)
        name = name_match.group(1)
        open_time = open_time_match.group(1)
        end_time = end_time_match.group(1)

        try:
            # 计算时间间隔
            open_date = datetime.datetime.strptime(open_time, time_format)
            end_date = datetime.datetime.strptime(end_time, time_format)
            delta = end_date - open_date

            # 检查时间逻辑是否合理
            if delta.total_seconds() <= 0:
                script.warning(f"活动 {activity_id} 结束时间早于或等于开始时间")
                invalid_time_activities += 1
                continue

            interval_days = delta.days
            interval_hours = delta.seconds // 3600
            interval_minutes = (delta.seconds // 60) % 60

            # 检查是否符合标准配置
            is_standard_config = (
                    (interval_days == 3 and interval_minutes < 1) or
                    (interval_days == 7 and interval_minutes < 1) or
                    (interval_days == 14 and interval_minutes < 1) or
                    (interval_days == 2 and interval_hours == 23 and interval_minutes >= 59) or
                    (interval_days == 6 and interval_hours == 23 and interval_minutes >= 59) or
                    (interval_days == 13 and interval_hours == 23 and interval_minutes >= 59)
            )

            if not is_standard_config:
                abnormal_activity = {
                    'id': activity_id,
                    'name': name,
                    'open_time': open_time,
                    'end_time': end_time,
                    'duration_days': interval_days,
                    'duration_hours': interval_hours,
                    'duration_minutes': interval_minutes,
                    'duration_text': f"{interval_days} days {interval_hours} hours {interval_minutes} minutes",
                    'total_duration_hours': round(delta.total_seconds() / 3600, 2)
                }
                abnormal_duration_activities.append(abnormal_activity)

                # 保持原始的彩色输出格式
                print(f"{RED}需要注意的活动时间配置:{RESET} ID: {activity_id}, Name: {name}, "
                      f"openTime: {open_time}, endTime: {end_time}, "
                      f"{YELLOW}活动持续时间：{interval_days} days {interval_hours} hours {interval_minutes} minutes{RESET}")

        except ValueError as e:
            invalid_time_activities += 1
            # 修复原脚本中的typo
            print(f"{YELLOW}无效的活动时间配置： ID: {activity_id}, Name: {name}, "
                  f"open_time={open_time}, end_time={end_time}{RESET}")
            script.error(f"无效的时间格式: ID={activity_id}, Name={name}, 错误={str(e)}")
        except Exception as e:
            invalid_time_activities += 1
            script.error(f"处理活动时间时发生异常: ID={activity_id}, 错误={str(e)}")

    # 生成检查结果
    script.info(f"活动时间配置检查完成")
    script.info(f"总活动数: {total_activities}")
    script.info(f"时间格式无效的活动数: {invalid_time_activities}")
    script.info(f"持续时间异常的活动数: {len(abnormal_duration_activities)}")

    # 返回结果
    result_data = {
        'directory': directory,
        'file_path': file_path,
        'encoding_used': encoding,
        'file_exists': True,
        'total_activities': total_activities,
        'invalid_time_activities': invalid_time_activities,
        'abnormal_duration_count': len(abnormal_duration_activities),
        'abnormal_duration_activities': abnormal_duration_activities,
        'check_summary': {
            'has_issues': len(abnormal_duration_activities) > 0 or invalid_time_activities > 0,
            'issues_count': len(abnormal_duration_activities) + invalid_time_activities
        }
    }

    if result_data['check_summary']['has_issues']:
        message = f"发现 {result_data['check_summary']['issues_count']} 个活动时间配置问题"
        print(f"{YELLOW}{message}{RESET}")
        script.warning(message)
    else:
        message = "所有活动时间配置都符合标准"
        print(f"{GREEN}{message}{RESET}")
        script.info(message)

    return script.success_result(message, result_data)


# 如果直接运行此脚本
if __name__ == '__main__':
    create_simple_script('check_ConfigTime', check_activity_time_config)