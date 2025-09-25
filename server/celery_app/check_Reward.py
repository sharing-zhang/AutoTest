#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析检查脚本 - 检查指定配置块数据
根据用户输入：目录、文件名（可多项）、配置块名称、最大奖励数值，扫描并输出超过阈值的配置项
支持多个 reward_id 输入项的依次检查
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
from typing import Dict, Any, Optional, List, Union
from typing import Pattern


class ScriptBase:
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
        return os.environ.get('SCRIPT_NAME', 'config_block_checker')

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

        # 修复编码问题：确保JSON输出兼容性
        try:
            # 先尝试使用ensure_ascii=False
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            print(json_str)
        except UnicodeEncodeError:
            # 如果出现编码错误，使用ensure_ascii=True
            json_str = json.dumps(result, ensure_ascii=True, indent=2)
            print(json_str)

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


def parse_reward_ids(reward_id_param: Union[str, List[str]]) -> List[Dict[str, Any]]:
    """解析多个奖励ID输入项，返回格式化的奖励ID检查列表

    Args:
        reward_id_param: 单个字符串或字符串列表

    Returns:
        List[Dict]: 包含 'pattern', 'regex', 'value', 'raw' 字段的字典列表
    """
    reward_ids = []

    # 归一化输入为列表
    if isinstance(reward_id_param, str):
        # 尝试按逗号分割字符串
        raw_ids = [item.strip() for item in reward_id_param.split(',') if item.strip()]
    elif isinstance(reward_id_param, (list, tuple)):
        raw_ids = [str(item).strip() for item in reward_id_param if str(item).strip()]
    else:
        raw_ids = [str(reward_id_param).strip()] if reward_id_param else []

    for raw_id in raw_ids:
        if not raw_id:
            continue

        # 尝试编译为正则表达式
        try:
            regex_pattern = re.compile(raw_id)
            reward_ids.append({
                'pattern': raw_id,
                'regex': regex_pattern,
                'value': None,
                'raw': raw_id,
                'type': 'regex'
            })
        except re.error:
            # 正则编译失败，作为精确匹配值
            reward_ids.append({
                'pattern': raw_id,
                'regex': None,
                'value': raw_id,
                'raw': raw_id,
                'type': 'exact'
            })

    return reward_ids


def check_reward_id_match(tp_id: str, reward_id_checkers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """检查 tp_id 是否匹配任何一个奖励ID检查器

    Args:
        tp_id: 要检查的奖励ID
        reward_id_checkers: 奖励ID检查器列表

    Returns:
        匹配的检查器信息，如果没有匹配返回 None
    """
    for checker in reward_id_checkers:
        try:
            if checker['regex'] is not None:
                # 正则匹配
                if checker['regex'].search(tp_id):
                    return checker
            elif checker['value'] is not None:
                # 精确匹配
                if tp_id == checker['value']:
                    return checker
        except Exception:
            continue

    return None


def parse_file(
        file_path: str,
        block_name: str,
        max_reward: int,
        count: str,
        reward_id_checkers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """解析文件并提取大于阈值且匹配奖励ID条件的指定配置块"""
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()

    # 动态构建正则表达式匹配指定的配置块
    escaped_block_name = re.escape(block_name)
    pattern = rf'{escaped_block_name}\s*\{{\s*([^}}]+)\s*\}};'
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

        # 奖励ID过滤（tpId），支持多个正则或精确匹配
        tp_id = item.get('tpId', '')
        matched_checker = None

        if reward_id_checkers:
            matched_checker = check_reward_id_match(tp_id, reward_id_checkers)
            id_match_ok = matched_checker is not None
        else:
            # 如果没有提供奖励ID过滤器，则全部通过
            id_match_ok = True

        if id_match_ok and count_value > max_reward:
            item['count_value'] = count_value
            if matched_checker:
                item['matched_reward_id'] = {
                    'pattern': matched_checker['pattern'],
                    'type': matched_checker['type'],
                    'raw': matched_checker['raw']
                }
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
    """主要业务逻辑：扫描大于最大奖励数值的配置项，支持多个reward_id检查"""

    # 读取参数
    directory = script.get_parameter('directory', r"D:\dev")
    file_name = script.get_parameter('file_name', "POINT_PROGRESS_REWARD.data.txt")
    block_name = script.get_parameter('block_name', 'progressRewards')
    rules_param = script.get_parameter('rules', "[]")

    # 规范化路径：处理多重转义的反斜杠
    if directory:
        # 处理多重转义：\\\\\\\\ -> \\ -> /
        directory = directory.replace('\\\\\\\\', '\\').replace('\\\\', '\\').replace('\\', os.sep)

    # 目标文件
    target_files = [os.path.join(directory, file_name)] if file_name else []

    # 解析规则数组
    try:
        parsed_rules = json.loads(rules_param) if isinstance(rules_param, str) else rules_param
        if not isinstance(parsed_rules, list):
            raise ValueError('rules 需为数组')
    except Exception as e:
        return script.error_result(f"rules 参数解析失败: {e}")

    script.info(f"开始检查，目录: {directory}")
    script.info(f"目标文件名: {file_name}")
    script.info(f"配置块名称: {block_name}")
    script.info(f"规则组数量: {len(parsed_rules)}")

    if not target_files:
        return script.success_result(
            message="未找到任何目标文件",
            data={
                "searched_directory": directory,
                "target_file_name": file_name,
                "block_name": block_name,
                "rules": parsed_rules,
                "files": [],
                "summary": {"total_files": 0, "problem_files": 0, "total_exceeded_items": 0}
            }
        )

    all_results: Dict[str, Any] = {}
    warning_files: List[str] = []

    for file_path in target_files:
        script.debug(f"正在检查文件: {file_path}")
        try:
            # 针对每条规则执行匹配统计
            encoding = detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            escaped_block_name = re.escape(block_name)
            block_pattern = rf'{escaped_block_name}\s*\{{\s*([^}}]+)\s*\}};'
            blocks = re.findall(block_pattern, content)

            # 为了返回行号：建立每个匹配块的起始行
            lines = content.splitlines()
            line_offsets: List[int] = []
            for m in re.finditer(block_pattern, content):
                start_pos = m.start()
                start_line = content.count('\n', 0, start_pos) + 1
                line_offsets.append(start_line)

            exceeded: List[Dict[str, Any]] = []

            for idx, block in enumerate(blocks):
                pairs = re.findall(r'(\w+)\s*=\s*"([^"]+)"', block)
                item = {k: v for k, v in pairs}
                tp_id = item.get('tpId', '')

                for rule in parsed_rules:
                    rid = str(rule.get('reward_id', '')).strip()
                    count_field = str(rule.get('count_id', 'count')).strip() or 'count'
                    try:
                        threshold = int(rule.get('max_reward', 0))
                    except Exception:
                        threshold = 0

                    # 匹配奖励ID（支持正则/精确）
                    match_ok = False
                    if rid:
                        try:
                            rgx = re.compile(rid)
                            match_ok = bool(rgx.search(tp_id))
                        except re.error:
                            match_ok = (tp_id == rid)
                    else:
                        match_ok = True

                    # 数量对比
                    try:
                        count_val = int(item.get(count_field, '0'))
                    except ValueError:
                        count_val = 0

                    if match_ok and count_val > threshold:
                        exceeded.append({
                            "line": line_offsets[idx] if idx < len(line_offsets) else None,
                            "tpId": tp_id,
                            "count_field": count_field,
                            "count_value": count_val,
                            "max_reward": threshold,
                            "rule": rule,
                            "block": item
                        })

            filtered_blocks = exceeded
            all_results[file_path] = {
                "file_path": file_path,
                "encoding": encoding,
                "exceeded_blocks": filtered_blocks,
                "exceeded_count": len(filtered_blocks)
            }

            if filtered_blocks:
                script.warning(f"发现大于阈值的配置: {file_path}, 共 {len(filtered_blocks)} 条")
                warning_files.append(file_path)

                # 输出详细的匹配信息
                for blk in filtered_blocks:
                    script.debug(
                        f"  行{blk.get('line')}: tpId={blk.get('tpId')}, {blk.get('count_field')}={blk.get('count_value')} > {blk.get('max_reward')} 规则={blk.get('rule')}")
            else:
                script.info(f"文件检查通过: {file_path}")

        except Exception as e:
            error_msg = f"解析文件失败: {file_path}, 错误: {str(e)}"
            script.error(error_msg)
            all_results[file_path] = {"error": error_msg, "exceeded_blocks": []}

    # 统计信息
    total_files = len(target_files)
    problem_files = len(warning_files)

    # 统计所有超过阈值的配置项
    total_exceeded_items = 0
    exceeded_details = []

    for file_path, result in all_results.items():
        if "exceeded_blocks" in result:
            exceeded_blocks = result["exceeded_blocks"]
            total_exceeded_items += len(exceeded_blocks)

            # 收集详细信息
            for block in exceeded_blocks:
                exceeded_details.append({
                    "file": os.path.basename(file_path),
                    "line": block.get('line'),
                    "tpId": block.get('tpId'),
                    "count_field": block.get('count_field'),
                    "count_value": block.get('count_value'),
                    "max_reward": block.get('max_reward')
                })

    # 生成消息 - 修复编码问题，使用ASCII字符
    if total_exceeded_items > 0:
        # 构建详细列表（如果配置项太多，可以考虑只显示前几个）
        if len(exceeded_details) <= 10:  # 如果配置项不多，全部显示
            details_text = []
            for detail in exceeded_details:
                # 使用ASCII字符替代Unicode字符 "•"
                details_text.append(
                    f"  - {detail['file']}(行{detail['line']}) {detail['tpId']}: "
                    f"{detail['count_field']}={detail['count_value']} > {detail['max_reward']}"
                )
            details_str = "\n" + "\n".join(details_text)
        else:  # 如果配置项太多，只显示前几个
            details_text = []
            for detail in exceeded_details[:5]:
                # 使用ASCII字符替代Unicode字符 "•"
                details_text.append(
                    f"  - {detail['file']}(行{detail['line']}) {detail['tpId']}: "
                    f"{detail['count_field']}={detail['count_value']} > {detail['max_reward']}"
                )
            details_str = "\n" + "\n".join(details_text) + f"\n  ... 还有{len(exceeded_details) - 5}个配置项"

        message = f"检查发现{total_exceeded_items}个配置大于阈值，分别为：{details_str}"
    else:
        message = "所有配置项都通过检查"

    return script.success_result(
        message=message,
        data={
            "searched_directory": directory,
            "target_file_name": file_name,
            "block_name": block_name,
            "rules": parsed_rules,
            "summary": {
                "total_files": total_files,
                "problem_files": problem_files,
                "warning_files": warning_files,
                "total_rules": len(parsed_rules),
                "total_exceeded_items": total_exceeded_items
            },
            "detailed_results": all_results,
            "exceeded_details": exceeded_details
        }
    )


def create_simple_script(script_name: str, main_logic):
    """创建简单脚本的快捷函数"""
    script = ScriptBase(script_name)
    script.run_with_error_handling(main_logic)


if __name__ == "__main__":
    create_simple_script('config_block_checker', main_logic)