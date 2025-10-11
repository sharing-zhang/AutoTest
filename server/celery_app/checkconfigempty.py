#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件参数检查脚本
检查配置块中是否缺失指定参数
支持多个参数独立检查，分别输出报告
"""

import re
import os
from typing import List, Dict, Optional


# ==================== 辅助函数区域 ====================
def detect_file_encoding_simple(script, file_path: str) -> Optional[str]:
    """简单的文件编码检测"""
    script.debug(f"检测文件编码: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)

        if header.startswith(b'\xff\xfe\x00\x00'):
            return 'utf-32le'
        elif header.startswith(b'\x00\x00\xfe\xff'):
            return 'utf-32be'
        elif header.startswith(b'\xff\xfe'):
            return 'utf-16le'
        elif header.startswith(b'\xfe\xff'):
            return 'utf-16be'
        elif header.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'

        return None
    except Exception as e:
        script.debug(f"编码检测异常: {e}")
        return None


def try_read_with_encodings(script, file_path: str, encodings: List[str]) -> tuple:
    """尝试用多种编码读取文件"""
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                lines = f.readlines()
            script.info(f"成功使用编码 {encoding} 读取文件")
            return True, lines, encoding
        except (UnicodeDecodeError, Exception) as e:
            script.debug(f"编码 {encoding} 失败: {e}")
            continue
    return False, [], None


def detect_block_start(line: str, line_num: int) -> tuple:
    """检测配置块开始"""
    line_stripped = line.strip()

    # 格式1: blocktype{ 或 blocktype {
    block_match = re.match(r'^(\w+)\s*\{', line_stripped)
    if block_match:
        block_type = block_match.group(1)
        return block_type, f"{block_type}_Line{line_num}"

    # 格式2: 单独的 {
    if line_stripped.endswith('{'):
        prefix = line_stripped[:-1].strip()
        if prefix:
            type_match = re.search(r'(\w+)$', prefix)
            if type_match:
                block_type = type_match.group(1)
                return block_type, f"{block_type}_Line{line_num}"
        return "unknown", f"Block_Line{line_num}"

    return None, None


def is_parameter_in_line(param_name: str, line: str) -> bool:
    """检查参数是否在行中（精确匹配）"""
    patterns = [
        rf'\b{re.escape(param_name)}\s*=',  # param=
        rf'\b{re.escape(param_name)}\s*:',  # param:
        rf'"{re.escape(param_name)}"\s*:',  # "param":
    ]

    for pattern in patterns:
        if re.search(pattern, line):
            return True
    return False


def load_config_file(script, file_path: str) -> tuple:
    """加载配置文件"""
    script.info(f"加载配置文件: {file_path}")

    common_encodings = [
        'utf-8-sig', 'utf-8', 'utf-16', 'utf-16le', 'utf-16be',
        'gbk', 'gb2312', 'gb18030', 'cp1252', 'cp936', 'latin1', 'ascii'
    ]

    try:
        detected_encoding = detect_file_encoding_simple(script, file_path)
        encodings_to_try = []

        if detected_encoding:
            encodings_to_try.append(detected_encoding)

        for enc in common_encodings:
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)

        success, lines, used_encoding = try_read_with_encodings(script, file_path, encodings_to_try)

        if success:
            script.info(f"成功加载文件，使用编码: {used_encoding}，共 {len(lines)} 行")
            return lines, used_encoding
        else:
            # 最后尝试：忽略错误读取
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                script.warning("使用UTF-8忽略错误模式读取文件")
                return lines, 'utf-8-ignore'
            except Exception:
                raise Exception("无法读取文件")

    except Exception as e:
        script.error(f"读取文件失败: {e}")
        raise


def check_single_parameter(script, lines: List[str], parameter: str) -> Dict:
    """检查单个参数在配置块中的缺失情况"""
    script.debug(f"检查参数: {parameter}")

    missing_blocks = []  # 缺失参数的配置块
    found_blocks = []  # 包含参数的配置块
    total_blocks = 0

    current_block = None
    parameter_found = False
    brace_count = 0
    in_block = False

    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()

        # 跳过空行和注释行
        if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('//'):
            continue

        # 检测配置块开始
        if not in_block and '{' in line_stripped:
            block_type, block_id = detect_block_start(line_stripped, line_num)

            if block_type:  # 成功检测到块
                current_block = {
                    'id': block_id,
                    'type': block_type,
                    'start_line': line_num,
                    'end_line': None,
                    'block_index': total_blocks + 1  # 配置块的序号（从1开始）
                }
                parameter_found = False

                # 计算初始大括号数量
                brace_count = line_stripped.count('{') - line_stripped.count('}')
                in_block = True
                total_blocks += 1

                script.debug(f"发现配置块: {block_type} - {block_id} (第{total_blocks}个，行 {line_num})")

                # 检查当前行是否包含目标参数
                if is_parameter_in_line(parameter, line_stripped):
                    parameter_found = True

                continue

        if in_block and current_block:
            # 更新大括号计数
            brace_count += line_stripped.count('{') - line_stripped.count('}')

            # 检查当前行是否包含目标参数
            if not parameter_found and is_parameter_in_line(parameter, line_stripped):
                parameter_found = True

            # 检查块是否结束
            if brace_count <= 0:
                current_block['end_line'] = line_num

                # 检查参数是否存在
                if parameter_found:
                    found_blocks.append({
                        'block_id': current_block['id'],
                        'block_index': current_block['block_index'],
                        'start_line': current_block['start_line'],
                        'end_line': current_block['end_line']
                    })
                    script.debug(f"第{current_block['block_index']}个配置块 {current_block['id']} 包含参数 {parameter}")
                else:
                    missing_blocks.append({
                        'block_id': current_block['id'],
                        'block_index': current_block['block_index'],
                        'start_line': current_block['start_line'],
                        'end_line': current_block['end_line']
                    })
                    script.debug(f"第{current_block['block_index']}个配置块 {current_block['id']} 缺失参数 {parameter}")

                in_block = False
                current_block = None
                parameter_found = False
                brace_count = 0

    # 处理可能未正确关闭的块
    if in_block and current_block:
        current_block['end_line'] = len(lines)
        if parameter_found:
            found_blocks.append({
                'block_id': current_block['id'],
                'block_index': current_block['block_index'],
                'start_line': current_block['start_line'],
                'end_line': current_block['end_line']
            })
        else:
            missing_blocks.append({
                'block_id': current_block['id'],
                'block_index': current_block['block_index'],
                'start_line': current_block['start_line'],
                'end_line': current_block['end_line']
            })

    return {
        'parameter': parameter,
        'missing_blocks': missing_blocks,
        'found_blocks': found_blocks,
        'total_blocks': total_blocks,
        'found_count': len(found_blocks),
        'missing_count': len(missing_blocks)
    }


def format_file_size(file_path: str) -> str:
    """格式化文件大小"""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "未知大小"


def generate_single_parameter_report(parameter_result: Dict, file_info: Dict) -> str:
    """生成单个参数的检查报告"""
    param = parameter_result['parameter']
    missing_blocks = parameter_result['missing_blocks']
    found_blocks = parameter_result['found_blocks']
    total_blocks = parameter_result['total_blocks']
    found_count = parameter_result['found_count']
    missing_count = parameter_result['missing_count']

    report_parts = [
        f"参数 '{param}' 检查报告",
        f"检查结果: 配置块总数 {total_blocks} 个，包含该参数 {found_count} 个，缺失该参数 {missing_count} 个"
    ]

    # 计算覆盖率
    if total_blocks > 0:
        coverage_rate = (found_count / total_blocks) * 100
        report_parts.append(f"参数覆盖率: {coverage_rate:.1f}%")

    # 状态判断
    if missing_count == 0:
        report_parts.extend([
            f"状态: ✓ 通过",
            f"所有配置块都包含参数 '{param}'"
        ])
    else:
        report_parts.extend([
            f"状态: ✗ 未通过",
            f"发现 {missing_count} 个配置块缺失参数 '{param}'"
        ])

        # 显示缺失参数的配置块详情（最多显示5个）
        display_count = min(missing_count, 5)
        if display_count > 0:
            report_parts.append(f"缺失详情 (显示前 {display_count} 个):")

            for i, block in enumerate(missing_blocks[:display_count], 1):
                report_parts.append(
                    f"  [{i}] 第 {block['block_index']} 个配置块 - {block['block_id']} "
                    f"({block['start_line']}-{block['end_line']} 行)"
                )

            # 如果有更多缺失的配置块，显示省略信息
            if missing_count > display_count:
                report_parts.append(f"  ... 还有 {missing_count - display_count} 个配置块缺失该参数")

    return "\n".join(report_parts)


def generate_summary_report(all_results: List[Dict], file_info: Dict, parameters: List[str]) -> str:
    """生成总体汇总报告"""
    summary_parts = [
        "配置文件参数检查汇总报告",
        f"文件信息: {file_info['file_name']} ({file_info['file_size']}, {file_info['file_encoding']}, {file_info['total_lines']} 行)",
        f"检查概况: 检查参数数量 {len(parameters)} 个，参数列表 [{', '.join(parameters)}]"
    ]

    if all_results:
        total_blocks = all_results[0]['total_blocks']  # 所有参数的total_blocks应该相同
        summary_parts.append(f"配置块总数: {total_blocks} 个")

        # 各参数检查结果概览
        summary_parts.append("参数检查结果概览:")
        pass_count = 0
        fail_count = 0

        for result in all_results:
            param = result['parameter']
            missing_count = result['missing_count']
            found_count = result['found_count']
            coverage_rate = (found_count / total_blocks) * 100 if total_blocks > 0 else 0

            status = "✓ 通过" if missing_count == 0 else "✗ 未通过"
            if missing_count == 0:
                pass_count += 1
            else:
                fail_count += 1

            summary_parts.append(
                f"  {param}: {status} (覆盖率: {coverage_rate:.1f}%, 缺失: {missing_count} 个)"
            )

        # 整体状态
        summary_parts.extend([
            f"整体检查结果: 通过参数 {pass_count} 个，未通过参数 {fail_count} 个",
            f"总体状态: {'✓ 全部通过' if fail_count == 0 else '✗ 存在问题'}"
        ])

    return "\n".join(summary_parts)


def generate_complete_report(all_results: List[Dict], file_info: Dict, parameters: List[str]) -> str:
    """生成完整的检查报告"""
    # 生成汇总报告
    summary_report = generate_summary_report(all_results, file_info, parameters)

    # 生成各参数的详细报告
    detail_reports = []
    for result in all_results:
        detail_report = generate_single_parameter_report(result, file_info)
        detail_reports.append(detail_report)

    # 组合完整报告
    complete_report_parts = [summary_report]

    if detail_reports:
        complete_report_parts.append("详细检查报告:")
        complete_report_parts.extend(detail_reports)

    return "\n\n".join(complete_report_parts)


# ==================== 主逻辑函数 ====================
def main_logic(script):
    """配置文件参数检查主逻辑"""

    try:
        # 1. 获取参数
        file_path = script.get_parameter('file_path', 'D:\\TimeConfig\\FISH.data.txt')

        # 获取参数 - 支持tags类型的数组和字符串类型
        parameters_input = script.get_parameter('parameters_str', script.get_parameter('parameters', ['id']))

        script.info("Configuration parameter check script started")
        script.debug(f"File path: {file_path}")
        script.debug(f"Parameters input type: {type(parameters_input)}")
        script.debug(f"Parameters input: {parameters_input}")

        # 2. 验证输入
        if not file_path:
            script.error("文件路径不能为空")
            return script.error_result("文件路径不能为空", "ParameterError")

        if not parameters_input:
            script.error("参数列表不能为空")
            return script.error_result("参数列表不能为空", "ParameterError")

        # 处理不同类型的参数输入
        parameters = []

        try:
            if isinstance(parameters_input, list):
                # 如果是数组类型（tags组件返回的标准格式）
                script.debug("处理list类型参数")
                parameters = [str(p).strip() for p in parameters_input if str(p).strip()]
            elif isinstance(parameters_input, str):
                # 如果是字符串类型（兼容旧的输入方式）
                script.debug("处理string类型参数")
                if ',' in parameters_input:
                    parameters = [p.strip() for p in parameters_input.split(',') if p.strip()]
                else:
                    parameters = [p.strip() for p in parameters_input.split() if p.strip()]
            else:
                # 尝试转换为字符串再处理
                script.debug(f"尝试转换类型: {type(parameters_input)}")
                parameters_str = str(parameters_input)
                if ',' in parameters_str:
                    parameters = [p.strip() for p in parameters_str.split(',') if p.strip()]
                else:
                    parameters = [p.strip() for p in parameters_str.split() if p.strip()]
        except Exception as e:
            script.error(f"参数解析失败: {e}")
            return script.error_result(f"参数解析失败: {e}", "ParameterError")

        if not parameters:
            script.error("解析参数列表后为空")
            return script.error_result("解析参数列表后为空，请检查输入格式", "ParameterError")

        # 验证每个参数不为空
        valid_parameters = []
        for param in parameters:
            param_str = str(param).strip()
            if param_str:
                valid_parameters.append(param_str)
            else:
                script.warning(f"跳过空参数: {param}")

        if not valid_parameters:
            script.error("没有有效的参数")
            return script.error_result("所有参数都为空，请检查输入", "ParameterError")

        parameters = valid_parameters
        script.info(f"最终检查参数: {parameters}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            script.error(f"文件不存在: {file_path}")
            return script.error_result(f"文件不存在: {file_path}", "FileNotFoundError")

        # 3. 执行检查逻辑
        # 加载文件
        lines, used_encoding = load_config_file(script, file_path)

        # 准备文件信息
        file_info = {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'file_size': format_file_size(file_path),
            'file_encoding': used_encoding,
            'total_lines': len(lines)
        }

        # 对每个参数分别进行检查
        all_results = []
        for parameter in parameters:
            script.info(f"开始检查参数: {parameter}")
            result = check_single_parameter(script, lines, parameter)
            all_results.append(result)
            coverage_rate = (result['found_count'] / result['total_blocks'] * 100) if result['total_blocks'] > 0 else 0
            script.info(f"参数 {parameter} 检查完成 - 覆盖率: {coverage_rate:.1f}%")

        # 生成完整报告
        complete_message = generate_complete_report(all_results, file_info, parameters)

        script.info("所有参数检查完成")

        # 4. 计算汇总数据
        total_blocks = all_results[0]['total_blocks'] if all_results else 0
        pass_count = sum(1 for result in all_results if result['missing_count'] == 0)
        fail_count = len(all_results) - pass_count

        # 构建返回的数据结构
        return_data = {
            'file_info': file_info,
            'check_summary': {
                'checked_parameters': parameters,
                'parameter_count': len(parameters),
                'total_blocks': total_blocks,
                'pass_parameters': pass_count,
                'fail_parameters': fail_count,
                'overall_status': 'PASS' if fail_count == 0 else 'FAIL'
            },
            'parameter_results': []
        }

        # 添加每个参数的详细结果（限制数量避免数据过大）
        for result in all_results:
            param_data = {
                'parameter': result['parameter'],
                'total_blocks': result['total_blocks'],
                'found_count': result['found_count'],
                'missing_count': result['missing_count'],
                'coverage_rate': round((result['found_count'] / result['total_blocks']) * 100, 1) if result[
                                                                                                         'total_blocks'] > 0 else 0,
                'status': 'PASS' if result['missing_count'] == 0 else 'FAIL',
                'missing_blocks': result['missing_blocks'][:5],  # 只返回前5个
                'has_more_missing': len(result['missing_blocks']) > 5
            }
            return_data['parameter_results'].append(param_data)

        return script.success_result(
            message=complete_message,
            data=return_data
        )

    except Exception as e:
        script.error(f"检查过程中发生错误: {e}")
        import traceback
        script.error(f"详细错误: {traceback.format_exc()}")
        return script.error_result(str(e), "ExecutionError")


if __name__ == '__main__':
    from script_base import create_simple_script

    create_simple_script('config_parameter_checker', main_logic)