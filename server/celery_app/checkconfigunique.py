#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件参数唯一性检查脚本
检查配置块中指定参数是否存在重复值
只显示有重复的参数值及其位置
"""

import sys
import os
import re
import traceback
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from script_base import create_simple_script
except ImportError as e:
    print(f"导入script_base失败: {e}")
    sys.exit(1)


# ==================== 辅助函数区域 ====================
def detect_file_encoding_simple(script, file_path: str) -> Optional[str]:
    """简单的文件编码检测"""
    try:
        script.debug(f"检测文件编码: {file_path}")

        if not os.path.exists(file_path):
            script.error(f"文件不存在: {file_path}")
            return None

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
        script.error(f"编码检测异常: {e}")
        return None


def safe_read_file(script, file_path: str, encoding: str) -> Tuple[bool, List[str], str]:
    """安全地读取文件"""
    try:
        script.debug(f"尝试使用编码 {encoding} 读取文件")

        with open(file_path, 'r', encoding=encoding, errors='strict') as f:
            lines = f.readlines()

        script.debug(f"成功使用编码 {encoding} 读取 {len(lines)} 行")
        return True, lines, encoding

    except UnicodeDecodeError as e:
        script.debug(f"编码 {encoding} 解码失败: {e}")
        return False, [], ""
    except Exception as e:
        script.error(f"读取文件时发生未知错误 (编码: {encoding}): {e}")
        return False, [], ""


def try_read_with_encodings(script, file_path: str, encodings: List[str]) -> Tuple[bool, List[str], str]:
    """尝试用多种编码读取文件"""
    script.debug(f"尝试读取文件: {file_path}")

    for encoding in encodings:
        success, lines, used_encoding = safe_read_file(script, file_path, encoding)
        if success:
            script.info(f"成功使用编码 {encoding} 读取文件")
            return True, lines, used_encoding

    return False, [], ""


def detect_block_start(line: str, line_num: int) -> Tuple[Optional[str], Optional[str]]:
    """检测配置块开始"""
    try:
        line_stripped = line.strip()

        if not line_stripped:
            return None, None

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

    except Exception as e:
        # 返回None而不是抛出异常
        return None, None


def extract_parameter_value(param_name: str, line: str) -> Optional[str]:
    """从行中提取参数值"""
    try:
        if not param_name or not line:
            return None

        # 转义参数名以避免正则表达式特殊字符问题
        escaped_param = re.escape(param_name)

        patterns = [
            rf'\b{escaped_param}\s*=\s*"([^"]*)"',  # param="value"
            rf'\b{escaped_param}\s*=\s*([^;]+);',  # param=value;
            rf'\b{escaped_param}\s*:\s*"([^"]*)"',  # param:"value"
            rf'\b{escaped_param}\s*:\s*([^,}}]+)',  # param:value
        ]

        for pattern in patterns:
            try:
                match = re.search(pattern, line)
                if match:
                    value = match.group(1).strip()
                    # 移除可能的分号
                    value = value.rstrip(';').strip()
                    return value if value else None
            except Exception:
                continue

        return None

    except Exception:
        return None


def load_config_file(script, file_path: str) -> Tuple[List[str], str]:
    """加载配置文件"""
    script.info(f"开始加载配置文件: {file_path}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 检查文件大小
    try:
        file_size = os.path.getsize(file_path)
        script.debug(f"文件大小: {file_size} 字节")

        if file_size == 0:
            script.warning("文件为空")
            return [], 'utf-8'

        if file_size > 100 * 1024 * 1024:  # 100MB
            script.warning(f"文件较大 ({file_size / (1024 * 1024):.1f}MB)，处理可能较慢")

    except Exception as e:
        script.error(f"获取文件大小失败: {e}")

    # 编码检测和读取
    common_encodings = [
        'utf-8-sig', 'utf-8', 'utf-16', 'utf-16le', 'utf-16be',
        'gbk', 'gb2312', 'gb18030', 'cp1252', 'cp936', 'latin1'
    ]

    try:
        # 检测编码
        detected_encoding = detect_file_encoding_simple(script, file_path)
        encodings_to_try = []

        if detected_encoding and detected_encoding not in encodings_to_try:
            encodings_to_try.append(detected_encoding)

        for enc in common_encodings:
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)

        # 尝试读取
        success, lines, used_encoding = try_read_with_encodings(script, file_path, encodings_to_try)

        if success:
            script.info(f"成功加载文件，使用编码: {used_encoding}，共 {len(lines)} 行")
            return lines, used_encoding
        else:
            # 最后尝试：忽略错误读取
            script.warning("尝试使用UTF-8忽略错误模式读取文件")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                script.info(f"使用UTF-8忽略错误模式成功读取 {len(lines)} 行")
                return lines, 'utf-8-ignore'
            except Exception as e:
                raise Exception(f"所有编码尝试失败，最终错误: {e}")

    except Exception as e:
        script.error(f"读取文件失败: {e}")
        raise


def check_parameter_uniqueness(script, lines: List[str], parameters: List[str]) -> Dict:
    """检查配置块中指定参数的唯一性"""
    script.info(f"开始检查参数唯一性: {', '.join(parameters)}")

    if not lines:
        script.warning("文件内容为空")
        return {
            'duplicates': {param: {} for param in parameters},
            'total_blocks': 0,
            'param_values': {param: defaultdict(list) for param in parameters}
        }

    # 存储每个参数的值和位置信息
    param_values = {}
    for param in parameters:
        param_values[param] = defaultdict(list)

    total_blocks = 0
    current_block = None
    current_block_index = 0
    brace_count = 0
    in_block = False

    try:
        for line_num, line in enumerate(lines, 1):
            try:
                line_stripped = line.strip()

                # 跳过空行和注释行
                if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('//'):
                    continue

                # 检测配置块开始
                if not in_block and '{' in line_stripped:
                    block_type, block_id = detect_block_start(line_stripped, line_num)

                    if block_type:
                        current_block_index += 1
                        current_block = {
                            'id': block_id,
                            'type': block_type,
                            'start_line': line_num,
                            'end_line': None,
                            'block_index': current_block_index
                        }

                        brace_count = line_stripped.count('{') - line_stripped.count('}')
                        in_block = True
                        total_blocks += 1

                        script.debug(f"发现第{current_block_index}个配置块: {block_type} - {block_id} (行 {line_num})")

                        # 检查当前行的参数
                        for param in parameters:
                            try:
                                value = extract_parameter_value(param, line_stripped)
                                if value is not None:
                                    param_values[param][value].append({
                                        'block_id': current_block['id'],
                                        'block_type': current_block['type'],
                                        'block_index': current_block_index,
                                        'start_line': current_block['start_line'],
                                        'param_line': line_num,
                                        'value': value
                                    })
                                    script.debug(
                                        f"在第{current_block_index}个配置块第{line_num}行找到参数 {param}={value}")
                            except Exception as e:
                                script.debug(f"提取参数 {param} 时出错 (行 {line_num}): {e}")

                        continue

                if in_block and current_block:
                    # 更新大括号计数
                    brace_count += line_stripped.count('{') - line_stripped.count('}')

                    # 检查当前行的参数
                    for param in parameters:
                        try:
                            value = extract_parameter_value(param, line_stripped)
                            if value is not None:
                                param_values[param][value].append({
                                    'block_id': current_block['id'],
                                    'block_type': current_block['type'],
                                    'block_index': current_block['block_index'],
                                    'start_line': current_block['start_line'],
                                    'param_line': line_num,
                                    'value': value
                                })
                                script.debug(
                                    f"在第{current_block['block_index']}个配置块第{line_num}行找到参数 {param}={value}")
                        except Exception as e:
                            script.debug(f"提取参数 {param} 时出错 (行 {line_num}): {e}")

                    # 检查块是否结束
                    if brace_count <= 0:
                        current_block['end_line'] = line_num
                        in_block = False
                        current_block = None
                        brace_count = 0

            except Exception as e:
                script.debug(f"处理行 {line_num} 时出错: {e}")
                continue

    except Exception as e:
        script.error(f"解析文件时发生错误: {e}")
        raise

    # 处理可能未正确关闭的块
    if in_block and current_block:
        current_block['end_line'] = len(lines)

    # 找出重复的参数值
    duplicates = {}
    for param in parameters:
        duplicates[param] = {}
        for value, block_list in param_values[param].items():
            if len(block_list) > 1:
                duplicates[param][value] = block_list

    script.info(f"解析完成: 共发现 {total_blocks} 个配置块")

    return {
        'duplicates': duplicates,
        'total_blocks': total_blocks,
        'param_values': param_values
    }


def generate_chinese_uniqueness_message(results: Dict, parameters: List[str]) -> str:
    """生成中文的唯一性检查消息"""
    try:
        duplicates = results['duplicates']
        total_blocks = results['total_blocks']

        # 检查是否有重复
        has_duplicates = False
        duplicate_count = 0

        for param in parameters:
            if duplicates.get(param):
                has_duplicates = True
                duplicate_count += len(duplicates[param])

        if not has_duplicates:
            return f"唯一性检查完成: 所有 {total_blocks} 个配置块的参数 {', '.join(parameters)} 都是唯一的"

        # 生成重复信息
        duplicate_info = []
        for param in parameters:
            if duplicates.get(param):
                for value, block_list in duplicates[param].items():
                    locations = []
                    for block_info in block_list:
                        locations.append(f"第{block_info['param_line']}行(第{block_info['block_index']}个配置块)")
                    duplicate_info.append(f"{param}='{value}' 重复出现在: {', '.join(locations)}")

        message = f"检查完成: 在 {total_blocks} 个配置块中发现 {duplicate_count} 个重复的参数值。重复详情: {'; '.join(duplicate_info)}"
        return message

    except Exception as e:
        return f"生成报告时出错: {e}"


# ==================== 主逻辑函数 ====================
def main_logic(script):
    """配置文件参数唯一性检查主逻辑"""

    try:
        script.info("配置文件参数唯一性检查脚本开始运行")

        # 1. 获取参数
        file_path = script.get_parameter('file_path', 'D:\\TimeConfig\\FISH.data.txt')
        parameters_str = script.get_parameter('parameters_str', 'id')  # 修正参数名

        script.debug(f"文件路径: {file_path}")
        script.debug(f"检查参数: {parameters_str}")

        # 2. 验证输入
        if not file_path:
            return script.error_result("文件路径不能为空", "ParameterError")

        if not parameters_str:
            return script.error_result("参数列表不能为空", "ParameterError")

        # 解析参数列表
        parameters = []
        try:
            if ',' in parameters_str:
                parameters = [p.strip() for p in parameters_str.split(',') if p.strip()]
            else:
                parameters = [p.strip() for p in parameters_str.split() if p.strip()]

            if not parameters:
                return script.error_result("解析参数列表失败", "ParameterError")

        except Exception as e:
            return script.error_result(f"解析参数列表时出错: {e}", "ParameterError")

        script.info(f"检查参数唯一性: {', '.join(parameters)}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return script.error_result(f"文件不存在: {file_path}", "FileNotFoundError")

        # 3. 执行检查逻辑
        try:
            # 加载文件
            script.info("开始加载配置文件...")
            lines, used_encoding = load_config_file(script, file_path)
            script.info(f"文件加载完成，编码: {used_encoding}")

            # 检查参数唯一性
            script.info("开始检查参数唯一性...")
            results = check_parameter_uniqueness(script, lines, parameters)
            script.info("参数唯一性检查完成")

            # 生成中文消息
            message = generate_chinese_uniqueness_message(results, parameters)

            # 统计重复数量
            duplicate_count = 0
            for param in parameters:
                duplicate_count += len(results['duplicates'].get(param, {}))

            script.info("唯一性检查任务完成")

            # 4. 返回结果
            return script.success_result(
                message=message,
                data={
                    'total_blocks': results['total_blocks'],
                    'duplicate_count': duplicate_count,
                    'duplicates': results['duplicates'],
                    'file_encoding': used_encoding,
                    'checked_parameters': parameters
                }
            )

        except FileNotFoundError as e:
            return script.error_result(f"文件未找到: {e}", "FileNotFoundError")
        except PermissionError as e:
            return script.error_result(f"文件访问权限不足: {e}", "PermissionError")
        except Exception as e:
            script.error(f"唯一性检查过程中发生错误: {str(e)}")
            script.error(f"错误详情: {traceback.format_exc()}")
            return script.error_result(f"执行过程中发生错误: {str(e)}", "ExecutionError")

    except Exception as e:
        # 最外层异常处理
        error_msg = f"脚本执行失败: {str(e)}"
        try:
            script.error(error_msg)
            script.error(f"完整错误信息: {traceback.format_exc()}")
            return script.error_result(error_msg, "ScriptError")
        except:
            # 如果连错误日志都无法记录，直接退出
            print(f"严重错误: {error_msg}")
            print(f"堆栈跟踪: {traceback.format_exc()}")
            sys.exit(1)


if __name__ == '__main__':
    try:
        create_simple_script('config_parameter_uniqueness_checker', main_logic)
    except Exception as e:
        print(f"脚本启动失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        sys.exit(1)