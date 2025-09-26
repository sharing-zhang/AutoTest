#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件参数检查脚本
检查配置块中是否缺失指定参数
简化输出，只显示缺失参数的配置块位置
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


def check_missing_parameters(script, lines: List[str], parameters: List[str]) -> Dict:
    """检查配置块中缺失的参数"""
    script.info(f"开始检查缺失参数: {', '.join(parameters)}")

    missing_blocks = []  # 缺失参数的配置块
    total_blocks = 0
    found_blocks = 0

    current_block = None
    current_block_params = set()  # 当前块找到的参数
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
                current_block_params = set()

                # 计算初始大括号数量
                brace_count = line_stripped.count('{') - line_stripped.count('}')
                in_block = True
                total_blocks += 1

                script.debug(f"发现配置块: {block_type} - {block_id} (第{total_blocks}个，行 {line_num})")

                # 检查当前行是否包含目标参数
                for param in parameters:
                    if is_parameter_in_line(param, line_stripped):
                        current_block_params.add(param)

                continue

        if in_block and current_block:
            # 更新大括号计数
            brace_count += line_stripped.count('{') - line_stripped.count('}')

            # 检查当前行是否包含目标参数
            for param in parameters:
                if is_parameter_in_line(param, line_stripped):
                    current_block_params.add(param)

            # 检查块是否结束
            if brace_count <= 0:
                current_block['end_line'] = line_num

                # 检查是否有缺失的参数
                missing_params = set(parameters) - current_block_params
                if missing_params:
                    missing_blocks.append({
                        'block_id': current_block['id'],
                        'block_index': current_block['block_index'],
                        'start_line': current_block['start_line'],
                        'end_line': current_block['end_line'],
                        'missing_params': list(missing_params),
                        'found_params': list(current_block_params)
                    })
                    script.debug(
                        f"第{current_block['block_index']}个配置块 {current_block['id']} 缺失参数: {missing_params}")
                else:
                    found_blocks += 1
                    script.debug(f"第{current_block['block_index']}个配置块 {current_block['id']} 包含所有参数")

                in_block = False
                current_block = None
                current_block_params = set()
                brace_count = 0

    # 处理可能未正确关闭的块
    if in_block and current_block:
        current_block['end_line'] = len(lines)
        missing_params = set(parameters) - current_block_params
        if missing_params:
            missing_blocks.append({
                'block_id': current_block['id'],
                'block_index': current_block['block_index'],
                'start_line': current_block['start_line'],
                'end_line': current_block['end_line'],
                'missing_params': list(missing_params),
                'found_params': list(current_block_params)
            })
        else:
            found_blocks += 1

    return {
        'missing_blocks': missing_blocks,
        'total_blocks': total_blocks,
        'found_blocks': found_blocks,
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


def generate_chinese_message(results: Dict, parameters: List[str], file_path: str, used_encoding: str) -> str:
    """生成中文消息"""
    missing_blocks = results['missing_blocks']
    total_blocks = results['total_blocks']
    found_blocks = results['found_blocks']
    missing_count = results['missing_count']

    # 获取文件基本信息
    file_name = os.path.basename(file_path)
    file_size = format_file_size(file_path)

    # 构建消息头
    separator = "=" * 60
    message_parts = [
        separator,
        "配置文件参数检查报告",
        separator,
        f"文件信息:",
        f"  文件名: {file_name}",
        f"  文件大小: {file_size}",
        f"  文件编码: {used_encoding}",
        "",
        f"检查参数: {', '.join(parameters)}",
        f"参数数量: {len(parameters)} 个",
        "",
        f"检查结果:",
        f"  配置块总数: {total_blocks} 个",
        f"  合格配置块: {found_blocks} 个",
        f"  缺失参数的配置块: {missing_count} 个",
        ""
    ]

    # 计算合格率
    if total_blocks > 0:
        success_rate = (found_blocks / total_blocks) * 100
        message_parts.append(f"  合格率: {success_rate:.1f}%")
        message_parts.append("")

    # 检查结果状态
    if missing_count == 0:
        message_parts.extend([
            "检查状态: 通过",
            "所有配置块都包含所需的参数",
            separator
        ])
    else:
        message_parts.extend([
            "检查状态: 未通过",
            f"发现 {missing_count} 个配置块存在参数缺失问题",
            ""
        ])

        # 显示前10个缺失参数的配置块详情
        display_count = min(missing_count, 10)
        message_parts.append(f"缺失参数详情 (显示前 {display_count} 个):")

        for i, block in enumerate(missing_blocks[:display_count], 1):
            missing_params_str = ', '.join(sorted(block['missing_params']))
            found_params_str = ', '.join(sorted(block['found_params'])) if block['found_params'] else "无"

            message_parts.extend([
                f"  [{i}] 第 {block['block_index']} 个配置块 ({block['start_line']}-{block['end_line']} 行)",
                f"      配置块ID: {block['block_id']}",
                f"      缺失参数: {missing_params_str}",
                f"      已有参数: {found_params_str}",
                ""
            ])

        # 如果有更多缺失的配置块，显示省略信息
        if missing_count > 10:
            message_parts.append(f"  ... 还有 {missing_count - 10} 个配置块存在参数缺失")
            message_parts.append("")

        message_parts.append(separator)

    return "\n".join(message_parts)


# ==================== 主逻辑函数 ====================
def main_logic(script):
    """配置文件参数检查主逻辑"""

    try:
        # 1. 获取参数 - 使用正确的方法名
        file_path = script.get_parameter('file_path', 'D:\\TimeConfig\\FISH.data.txt')
        # 同时支持两种参数名
        parameters_str = script.get_parameter('parameters_str', script.get_parameter('parameters', 'id'))

        script.info("Configuration parameter check script started")
        script.debug(f"File path: {file_path}")
        script.debug(f"Parameters: {parameters_str}")

        # 2. 验证输入
        if not file_path:
            script.error("文件路径不能为空")
            return script.error_result("文件路径不能为空", "ParameterError")

        if not parameters_str:
            script.error("参数列表不能为空")
            return script.error_result("参数列表不能为空", "ParameterError")

        # 解析参数列表
        parameters = []
        if ',' in parameters_str:
            parameters = [p.strip() for p in parameters_str.split(',') if p.strip()]
        else:
            parameters = [p.strip() for p in parameters_str.split() if p.strip()]

        if not parameters:
            script.error("解析参数列表失败")
            return script.error_result("解析参数列表失败", "ParameterError")

        script.info(f"检查参数: {parameters}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            script.error(f"文件不存在: {file_path}")
            return script.error_result(f"文件不存在: {file_path}", "FileNotFoundError")

        # 3. 执行检查逻辑
        # 加载文件
        lines, used_encoding = load_config_file(script, file_path)

        # 检查缺失参数
        results = check_missing_parameters(script, lines, parameters)

        # 生成格式化的中文消息
        message = generate_chinese_message(results, parameters, file_path, used_encoding)

        script.info("参数检查完成")

        # 4. 返回结果
        return script.success_result(
            message=message,
            data={
                'file_info': {
                    'file_name': os.path.basename(file_path),
                    'file_path': file_path,
                    'file_size': format_file_size(file_path),
                    'file_encoding': used_encoding,
                    'total_lines': len(lines)
                },
                'check_summary': {
                    'checked_parameters': parameters,
                    'parameter_count': len(parameters),
                    'total_blocks': results['total_blocks'],
                    'found_blocks': results['found_blocks'],
                    'missing_count': results['missing_count'],
                    'success_rate': round((results['found_blocks'] / results['total_blocks']) * 100, 1) if results[
                                                                                                               'total_blocks'] > 0 else 0,
                    'check_status': 'PASS' if results['missing_count'] == 0 else 'FAIL'
                },
                'missing_blocks': results['missing_blocks'][:10] if len(results['missing_blocks']) > 10 else results[
                    'missing_blocks'],  # 限制返回数量避免数据过大
                'has_more_missing': len(results['missing_blocks']) > 10
            }
        )

    except Exception as e:
        script.error(f"检查过程中发生错误: {e}")
        import traceback
        script.error(f"详细错误: {traceback.format_exc()}")
        return script.error_result(str(e), "ExecutionError")


if __name__ == '__main__':
    from script_base import create_simple_script

    create_simple_script('config_parameter_checker', main_logic)