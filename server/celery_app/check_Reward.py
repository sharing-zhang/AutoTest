#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析检查脚本 - 检查progressRewards配置数据
解析指定文件并提取满足条件的数据块
"""

import os
import os.path
import re
import chardet
import json
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List


class ScriptBase:
    """脚本基础类，提供通用功能"""

    def __init__(self, script_name: Optional[str] = None):
        """初始化脚本基础环境

        Args:
            script_name: 脚本名称，如果不提供则从环境变量获取
        """
        self.script_name = script_name or self._get_script_name()
        self.parameters = self._get_parameters()
        self.page_context = self._get_page_context()
        self.execution_id = self._get_execution_id()
        self.start_time = time.time()

        # 输出初始化信息
        self.debug(f"{self.script_name} 脚本开始执行")
        self.debug(f"参数: {self.parameters}")
        self.debug(f"页面上下文: {self.page_context}")

    def _get_script_name(self) -> str:
        """从环境变量获取脚本名称"""
        return os.environ.get('SCRIPT_NAME', 'progress_rewards_checker')

    def _get_parameters(self) -> Dict[str, Any]:
        """从环境变量获取脚本参数"""
        try:
            params_str = os.environ.get('SCRIPT_PARAMETERS', '{}')
            return json.loads(params_str)
        except json.JSONDecodeError:
            return {}

    def _get_page_context(self) -> str:
        """从环境变量获取页面上下文"""
        return os.environ.get('PAGE_CONTEXT', 'unknown')

    def _get_execution_id(self) -> str:
        """从环境变量获取执行ID"""
        return os.environ.get('EXECUTION_ID', str(time.time()))

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取指定参数

        Args:
            key: 参数名
            default: 默认值

        Returns:
            参数值
        """
        return self.parameters.get(key, default)

    def debug(self, message: str):
        """输出调试信息到stderr"""
        print(f"[DEBUG] {message}", file=sys.stderr)

    def info(self, message: str):
        """输出信息到stderr"""
        print(f"[INFO] {message}", file=sys.stderr)

    def warning(self, message: str):
        """输出警告信息到stderr"""
        print(f"[WARNING] {message}", file=sys.stderr)

    def error(self, message: str):
        """输出错误信息到stderr"""
        print(f"[ERROR] {message}", file=sys.stderr)

    def success_result(self, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建成功结果

        Args:
            message: 成功消息
            data: 附加数据

        Returns:
            标准格式的成功结果
        """
        execution_time = time.time() - self.start_time

        result = {
            'status': 'success',
            'message': message,
            'timestamp': time.time(),
            'data': data or {},
            'metadata': {
                'script_name': self.script_name,
                'execution_time': datetime.now().isoformat(),
                'execution_duration': execution_time,
                'version': '1.0.0',
                'method': 'subprocess_execution'
            }
        }

        # 确保data中包含基本信息
        result['data'].update({
            'script_name': self.script_name,
            'execution_context': self.page_context,
            'processed_parameters': self.parameters
        })

        return result

    def error_result(self, error_message: str, error_type: str = 'RuntimeError') -> Dict[str, Any]:
        """创建错误结果

        Args:
            error_message: 错误消息
            error_type: 错误类型

        Returns:
            标准格式的错误结果
        """
        execution_time = time.time() - self.start_time

        return {
            'status': 'error',
            'message': f'{self.script_name}执行出错: {error_message}',
            'timestamp': time.time(),
            'script_name': self.script_name,
            'error_type': error_type,
            'execution_duration': execution_time
        }

    def output_result(self, result: Dict[str, Any]):
        """输出结果到stdout

        Args:
            result: 结果字典
        """
        self.debug(f"{self.script_name}执行完成，准备输出结果")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    def run_with_error_handling(self, main_func):
        """运行主函数并处理错误

        Args:
            main_func: 主要业务逻辑函数
        """
        try:
            result = main_func(self)
            if isinstance(result, dict):
                self.output_result(result)
            else:
                # 如果返回的不是字典，包装成成功结果
                success_result = self.success_result(str(result) if result else "脚本执行完成")
                self.output_result(success_result)

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            error_traceback = traceback.format_exc()

            self.error(f"脚本执行失败: {error_msg}")
            self.error(f"错误堆栈: {error_traceback}")

            error_result = self.error_result(error_msg, error_type)
            self.output_result(error_result)
            sys.exit(1)


# 业务逻辑函数
def detect_encoding(file_path: str) -> str:
    """检测文件的编码格式"""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']


def parse_file(file_path: str) -> List[Dict[str, str]]:
    """解析文件并提取指定条件的数据块"""
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()

    # 找到所有 progressRewards { ... };
    pattern = r'progressRewards\s*\{\s*([^}]+)\s*\};'
    blocks = re.findall(pattern, content)
    result = []

    for block in blocks:
        # 匹配每一项 key="value";
        pairs = re.findall(r'(\w+)\s*=\s*"([^"]+)"', block)
        d = {k: v for k, v in pairs}
        # 满足 tpId 以"971"开头 且 count > 1
        if d.get("tpId", "").startswith("971") and int(d.get("count", "0")) > 1:
            result.append(d)

    return result


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """主要业务逻辑"""

    # 从参数获取配置，如果没有则使用默认值
    root_path = script.get_parameter('root_path', r"D:\dev")
    mission_paths = script.get_parameter('mission_paths', [
        r"datapool\ElementData\BaseData\POINT_PROGRESS_REWARD_ENDLESS.data.txt",
        r"datapool\ElementData\BaseData\POINT_PROGRESS_REWARD.data.txt",
    ])

    script.info(f"开始检查文件，根路径: {root_path}")
    script.info(f"检查文件列表: {mission_paths}")

    all_results = {}
    warning_files = []  # 有问题的文件

    for mission_path in mission_paths:
        file_path = os.path.join(root_path, mission_path)

        script.debug(f"正在检查文件: {file_path}")

        if not os.path.exists(file_path):
            error_msg = f"文件不存在：{file_path}"
            script.warning(error_msg)
            all_results[mission_path] = {"error": error_msg, "filtered_blocks": []}
            continue

        try:
            filtered_blocks = parse_file(file_path)
            all_results[mission_path] = {
                "file_path": file_path,
                "filtered_blocks": filtered_blocks,
                "block_count": len(filtered_blocks)
            }

            if filtered_blocks:
                script.warning(f"发现问题文件: {file_path}, 找到 {len(filtered_blocks)} 个匹配的数据块")
                warning_files.append(file_path)
            else:
                script.info(f"文件检查通过: {file_path}")

        except Exception as e:
            error_msg = f"解析文件失败: {file_path}, 错误: {str(e)}"
            script.error(error_msg)
            all_results[mission_path] = {"error": error_msg, "filtered_blocks": []}

    # 准备返回结果
    total_files = len(mission_paths)
    problem_files = len(warning_files)

    if problem_files > 0:
        message = f"检查完成，发现 {problem_files}/{total_files} 个文件存在问题"
    else:
        message = f"检查完成，所有 {total_files} 个文件都通过检查"

    return script.success_result(
        message=message,
        data={
            "check_summary": {
                "total_files": total_files,
                "problem_files": problem_files,
                "warning_files": warning_files
            },
            "detailed_results": all_results,
            "root_path": root_path
        }
    )


def create_simple_script(script_name: str, main_logic):
    """创建简单脚本的快捷函数"""
    script = ScriptBase(script_name)
    script.run_with_error_handling(main_logic)


if __name__ == "__main__":
    create_simple_script('progress_rewards_checker', main_logic)