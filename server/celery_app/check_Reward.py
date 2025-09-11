#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析检查脚本 - 检查 progressRewards 配置数据
根据用户输入：目录、文件名（可多项）、最大奖励数值，扫描并输出超过阈值的配置项
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
from typing import Pattern


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


def parse_file(
    file_path: str,
    max_reward: int,
    count: str,
    reward_id_regex: Optional[Pattern[str]] = None,
    reward_id_value: Optional[str] = None
) -> List[Dict[str, Any]]:
    """解析文件并提取大于阈值且匹配奖励ID条件的 progressRewards 配置块"""
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()

    # 匹配所有 progressRewards { ... } 块
    pattern = r'progressRewards\s*\{\s*([^}]+)\s*\};'
    blocks = re.findall(pattern, content)
    result: List[Dict[str, Any]] = []

    for block in blocks:
        # 匹配每一项 key="value";
        pairs = re.findall(r'(\w+)\s*=\s*"([^"]+)"', block)
        item = {k: v for k, v in pairs}

        # 奖励数值字段约定为 count（若后续有变化可扩展）
        try:
            count_value = int(item.get(count, '0'))
        except ValueError:
            count_value = 0

        # 奖励ID过滤（tpId），支持正则或精确匹配
        tp_id = item.get('tpId', '')
        id_match_ok = True
        if reward_id_regex is not None:
            try:
                id_match_ok = bool(reward_id_regex.search(tp_id))
            except Exception:
                id_match_ok = False
        elif reward_id_value:
            id_match_ok = (tp_id == str(reward_id_value))

        if id_match_ok and count_value > max_reward:
            item['count_value'] = count_value
            result.append(item)

    return result


def find_target_files(root_directory: str, file_names: List[str], recursive: bool = False) -> List[str]:
    """在目录中查找目标文件（支持多文件名与递归）"""
    normalized = {str(n).strip() for n in (file_names or []) if str(n).strip()}
    matched: List[str] = []

    if not normalized:
        return matched

    if recursive:
        for dirpath, _, files in os.walk(root_directory):
            for fname in files:
                if fname in normalized:
                    matched.append(os.path.join(dirpath, fname))
    else:
        try:
            for fname in os.listdir(root_directory):
                path = os.path.join(root_directory, fname)
                if os.path.isfile(path) and fname in normalized:
                    matched.append(path)
        except Exception:
            pass

    return matched


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """主要业务逻辑：扫描大于最大奖励数值的配置项"""

    # 读取参数
    directory = script.get_parameter('directory', r"D:\dev")
    file_names_param = script.get_parameter('file_names', [
        "POINT_PROGRESS_REWARD_ENDLESS.data.txt",
        "POINT_PROGRESS_REWARD.data.txt"
    ])
    count= script.get_parameter('count_id', "count")
    recursive = bool(script.get_parameter('recursive', False))
    max_reward_param = script.get_parameter('max_reward', 1)
    reward_id_param = script.get_parameter('reward_id', '')  # 支持正则或精确值

    # 归一化参数
    if isinstance(file_names_param, str):
        file_names = [seg.strip() for seg in file_names_param.split(',') if seg.strip()]
    elif isinstance(file_names_param, (list, tuple)):
        file_names = [str(x).strip() for x in file_names_param if str(x).strip()]
    else:
        file_names = [str(file_names_param)]

    try:
        max_reward = int(max_reward_param)
    except Exception:
        max_reward = 1

    # 解析奖励ID过滤器
    reward_id_regex: Optional[Pattern[str]] = None
    reward_id_value: Optional[str] = None
    reward_id_text = str(reward_id_param).strip() if reward_id_param is not None else ''
    if reward_id_text:
        # 尝试编译为正则；若失败则作为精确匹配值
        try:
            reward_id_regex = re.compile(reward_id_text)
        except re.error:
            reward_id_regex = None
            reward_id_value = reward_id_text

    script.info(f"开始检查，目录: {directory}")
    script.info(f"目标文件名: {file_names} (递归: {recursive})")
    script.info(f"最大奖励阈值: {max_reward}")
    script.info(f"配置表数量ID字段: {count}")
    if reward_id_text:
        script.info(f"奖励ID过滤: {'正则' if reward_id_regex else '精确'} = {reward_id_text}")

    # 查找文件
    target_files = find_target_files(directory, file_names, recursive)

    if not target_files:
        return script.success_result(
            message="未找到任何目标文件",
            data={
                "searched_directory": directory,
                "target_file_names": file_names,
                "recursive": recursive,
                "max_reward": max_reward,
                "files": [],
                "summary": {"total_files": 0, "problem_files": 0}
            }
        )

    all_results: Dict[str, Any] = {}
    warning_files: List[str] = []

    for file_path in target_files:
        script.debug(f"正在检查文件: {file_path}")
        try:
            filtered_blocks = parse_file(file_path, max_reward, count, reward_id_regex, reward_id_value)
            all_results[file_path] = {
                "file_path": file_path,
                "encoding": detect_encoding(file_path),
                "exceeded_blocks": filtered_blocks,
                "exceeded_count": len(filtered_blocks)
            }

            if filtered_blocks:
                script.warning(f"发现大于阈值的配置: {file_path}, 共 {len(filtered_blocks)} 条")
                warning_files.append(file_path)
            else:
                script.info(f"文件检查通过: {file_path}")

        except Exception as e:
            error_msg = f"解析文件失败: {file_path}, 错误: {str(e)}"
            script.error(error_msg)
            all_results[file_path] = {"error": error_msg, "exceeded_blocks": []}

    total_files = len(target_files)
    problem_files = len(warning_files)

    message = (
        f"检查完成，发现 {problem_files}/{total_files} 个文件存在大于阈值的配置"
        if problem_files > 0 else f"检查完成，所有 {total_files} 个文件都通过检查"
    )

    return script.success_result(
        message=message,
        data={
            "searched_directory": directory,
            "target_file_names": file_names,
            "recursive": recursive,
            "max_reward": max_reward,
            "count_field": count,
            "reward_id": reward_id_text,
            "summary": {
                "total_files": total_files,
                "problem_files": problem_files,
                "warning_files": warning_files
            },
            "detailed_results": all_results
        }
    )


def create_simple_script(script_name: str, main_logic):
    """创建简单脚本的快捷函数"""
    script = ScriptBase(script_name)
    script.run_with_error_handling(main_logic)


if __name__ == "__main__":
    create_simple_script('progress_rewards_checker', main_logic)