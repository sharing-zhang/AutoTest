#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动时间配置检查脚本
检查TIMER_MAIN.data文件中的活动时间配置是否符合标准
"""

import os
import re
import datetime
import json
import sys
from typing import Dict, Any

# 如果无法导入script_base，提供备用实现
try:
    from script_base import ScriptBase, create_simple_script

    USE_SCRIPT_BASE = True
except ImportError:
    USE_SCRIPT_BASE = False
    print("警告: 无法导入script_base，使用简化版本", file=sys.stderr)


class SimpleScriptBase:
    """简化版本的脚本基础类，用于在无法导入script_base时使用"""

    def __init__(self, script_name: str):
        self.script_name = script_name
        self.parameters = self._safe_get_parameters()

    def _safe_get_parameters(self) -> Dict[str, Any]:
        """安全获取脚本参数"""
        try:
            params_str = os.environ.get('SCRIPT_PARAMETERS', '{}')

            # 检查是否为空
            if not params_str.strip():
                return {}

            # 检查是否为HTML内容
            if params_str.strip().startswith(('<!DOCTYPE', '<html', '<HTML', '<?xml')):
                print(f"[WARNING] 检测到HTML内容，使用默认参数", file=sys.stderr)
                return {}

            # 尝试解析JSON
            return json.loads(params_str)

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON解析失败: {e}", file=sys.stderr)
            print(f"[ERROR] 内容预览: {params_str[:200] if 'params_str' in locals() else 'N/A'}", file=sys.stderr)
            return {}
        except Exception as e:
            print(f"[ERROR] 获取参数时发生异常: {e}", file=sys.stderr)
            return {}

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取指定参数"""
        return self.parameters.get(key, default)

    def info(self, message: str):
        """输出信息"""
        print(f"[INFO] {message}", file=sys.stderr)

    def warning(self, message: str):
        """输出警告"""
        print(f"[WARNING] {message}", file=sys.stderr)

    def error(self, message: str):
        """输出错误"""
        print(f"[ERROR] {message}", file=sys.stderr)

    def success_result(self, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建成功结果"""
        return {
            'status': 'success',
            'message': message,
            'data': data or {},
            'script_name': self.script_name
        }

    def output_result(self, result: Dict[str, Any]):
        """输出结果"""
        print(json.dumps(result, ensure_ascii=False, indent=2))


def check_activity_time_config(script):
    """检查活动时间配置的主要逻辑"""

    try:
        # 从参数获取文件路径，如果没有则使用默认路径
        file_path = script.get_parameter('file_path', r'D:\dev\datapool\ElementData\BaseData\TIMER_MAIN.data.txt')
        encoding = script.get_parameter('encoding', 'UTF-16')

        script.info(f"开始检查活动时间配置文件: {file_path}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"文件不存在: {file_path}"
            script.error(error_msg)
            return script.success_result(error_msg, {'error': True, 'file_exists': False})

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
                script.info(f"使用UTF-8编码成功读取文件")
            except Exception as e2:
                error_msg = f"读取文件失败(多种编码尝试): {str(e2)}"
                script.error(error_msg)
                return script.success_result(error_msg, {'error': True, 'encoding_error': True})
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            script.error(error_msg)
            return script.success_result(error_msg, {'error': True, 'read_error': True})

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
                script.warning(f"配置块 {i + 1} 信息不完整，跳过: {block[:50]}...")
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

                    script.warning(
                        f"异常活动时间配置: ID={activity_id}, Name={name}, "
                        f"开始时间={open_time}, 结束时间={end_time}, "
                        f"持续时间={abnormal_activity['duration_text']}"
                    )

            except ValueError as e:
                invalid_time_activities += 1
                script.error(f"无效的时间格式: ID={activity_id}, Name={name}, "
                             f"开始时间={open_time}, 结束时间={end_time}, 错误={str(e)}")
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
            'file_path': file_path,
            'file_exists': True,
            'total_activities': total_activities,
            'invalid_time_activities': invalid_time_activities,
            'abnormal_duration_count': len(abnormal_duration_activities),
            'abnormal_duration_activities': abnormal_duration_activities,
            'check_summary': {
                'has_issues': len(abnormal_duration_activities) > 0 or invalid_time_activities > 0,
                'issues_count': len(abnormal_duration_activities) + invalid_time_activities
            },
            'error': False
        }

        if result_data['check_summary']['has_issues']:
            message = f"发现 {result_data['check_summary']['issues_count']} 个活动时间配置问题"
            script.warning(message)
        else:
            message = "所有活动时间配置都符合标准"
            script.info(message)

        return script.success_result(message, result_data)

    except Exception as e:
        error_msg = f"脚本执行过程中发生未预期的错误: {str(e)}"
        script.error(error_msg)
        return script.success_result(error_msg, {
            'error': True,
            'error_type': type(e).__name__,
            'error_message': str(e)
        })


def main():
    """主函数"""
    if USE_SCRIPT_BASE:
        # 使用完整的script_base
        create_simple_script('activity_time_checker', check_activity_time_config)
    else:
        # 使用简化版本
        script = SimpleScriptBase('activity_time_checker')
        try:
            result = check_activity_time_config(script)
            script.output_result(result)
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'脚本执行失败: {str(e)}',
                'error_type': type(e).__name__
            }
            script.output_result(error_result)


# 如果直接运行此脚本
if __name__ == '__main__':
    main()