#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名正则表达式检查脚本
功能：根据用户提供的正则表达式和选择的文件后缀检查项目中的文件名是否符合规范
"""

import os
import re
import sys
import gc
import time
import threading
from collections import defaultdict
from script_base import ScriptBase, create_simple_script

# 设置更保守递归限制
sys.setrecursionlimit(500)


# ==================== 全局配置 ====================
class CheckConfig:
    MAX_FILES = 20000  # 文件数量限制
    BATCH_SIZE = 500  # 批处理大小
    GC_FREQUENCY = 200  # 垃圾回收频率
    TIMEOUT_SECONDS = 3000  # 超时时间
    MAX_PATH_LENGTH = 260  # 最大路径长度


# ==================== 超时控制 ====================
class TimeoutException(Exception):
    pass


def timeout_handler():
    raise TimeoutException("脚本执行超时")


# ==================== 导入和路径设置 ====================
def setup_imports():
    """设置导入路径并解决相对导入问题"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


setup_imports()


# ==================== 安全文件遍历 ====================
def safe_walk_directory(directory_path, script, max_files=None):
    """安全的目录遍历，带有更多保护机制"""
    if max_files is None:
        max_files = CheckConfig.MAX_FILES

    all_files = []
    file_count = 0
    processed_dirs = 0

    try:
        script.info(f"开始遍历目录: {directory_path}")

        for root, dirs, files in os.walk(directory_path):
            # 检查超时
            if file_count > max_files:
                script.warning(f"文件数量超过限制 {max_files}，停止遍历")
                break

            # 过滤危险目录
            dirs[:] = [d for d in dirs if not _is_dangerous_dir(d)]

            # 限制目录深度
            processed_dirs += 1
            if processed_dirs > 1000:
                script.warning("目录数量过多，停止遍历")
                break

            # 批量处理文件
            batch_files = []
            for filename in files:
                if file_count >= max_files:
                    break

                try:
                    # 基本文件过滤
                    if not _is_valid_file(filename, root):
                        continue

                    full_path = os.path.join(root, filename)

                    # 路径长度检查
                    if len(full_path) > CheckConfig.MAX_PATH_LENGTH:
                        continue

                    # 文件存在性检查
                    if os.path.isfile(full_path):
                        batch_files.append(full_path)
                        file_count += 1

                except (OSError, UnicodeDecodeError, PermissionError):
                    continue

            # 批量添加到结果
            all_files.extend(batch_files)

            # 定期垃圾回收
            if file_count % CheckConfig.GC_FREQUENCY == 0:
                gc.collect()
                script.debug(f"已处理 {file_count} 个文件")

    except Exception as e:
        script.error(f"目录遍历异常: {str(e)}")
        raise RuntimeError(f"目录遍历失败: {str(e)}")

    script.info(f"遍历完成，共找到 {len(all_files)} 个文件")
    return all_files


def _is_dangerous_dir(dirname):
    """检查是否为危险目录"""
    dangerous_patterns = [
        '.',  # 隐藏目录
        '__pycache__',  # Python缓存
        'node_modules',  # Node.js模块
        '.git',  # Git目录
        '.svn',  # SVN目录
        'Temp',  # 临时目录
        'Library',  # Unity库目录
    ]
    return any(dirname.startswith(pattern) for pattern in dangerous_patterns)


def _is_valid_file(filename, root_path):
    """检查文件是否有效"""
    # 跳过隐藏文件和临时文件
    if filename.startswith('.') or filename.endswith('.tmp'):
        return False

    # 跳过特殊文件
    if filename in ['Thumbs.db', 'desktop.ini', '.DS_Store']:
        return False

    return True


# ==================== 正则表达式组合函数 ====================
def build_regex_patterns(base_pattern, file_extensions):
    """根据基础正则表达式和文件后缀构建完整的正则表达式列表"""
    patterns = []

    if not file_extensions:
        # 如果没有选择后缀，直接使用原始模式
        patterns.append(base_pattern)
    else:
        # 为每个选中的后缀构建正则表达式
        for ext in file_extensions:
            # 转义点号，因为在正则表达式中点号是特殊字符
            escaped_ext = ext.replace('.', '\\.')
            combined_pattern = base_pattern + escaped_ext
            patterns.append(combined_pattern)

    return patterns


# ==================== 正则表达式验证函数 ====================
def validate_regex_pattern(script, pattern):
    """验证正则表达式的有效性"""
    try:
        re.compile(pattern)
        script.info(f"正则表达式验证通过: {pattern}")
        return True, None
    except re.error as e:
        error_msg = f"正则表达式无效: {pattern} - 错误: {str(e)}"
        script.error(error_msg)
        return False, error_msg


def check_filename_against_multiple_regex(script, filename, regex_patterns, case_sensitive=True):
    """检查单个文件名是否符合多个正则表达式中的任意一个"""
    try:
        # 编译正则表达式
        flags = 0 if case_sensitive else re.IGNORECASE

        # 检查是否匹配任意一个模式
        for pattern in regex_patterns:
            try:
                compiled_pattern = re.compile(pattern, flags)
                if compiled_pattern.match(filename):
                    return True, f"匹配模式: {pattern}"
            except re.error as e:
                script.debug(f"正则表达式编译失败 {pattern}: {e}")
                continue

        return False, f"不匹配任何模式: {regex_patterns}"

    except Exception as e:
        script.debug(f"检查文件名时出错 {filename}: {e}")
        return False, f"检查异常: {str(e)}"


def should_check_file_by_extension(filename, selected_extensions):
    """根据选中的后缀判断是否需要检查该文件"""
    if not selected_extensions:
        # 如果没有选择后缀，检查所有文件
        return True

    # 获取文件的实际后缀
    _, file_ext = os.path.splitext(filename)
    file_ext = file_ext.lower()

    # 检查是否在选中的后缀列表中
    return file_ext in [ext.lower() for ext in selected_extensions]


def check_files_regex_compliance(script, directory, base_regex_pattern, file_extensions, case_sensitive=True,
                                 check_full_name=True):
    """检查目录中的文件名是否符合正则表达式规范（支持多后缀）"""

    # 构建正则表达式模式列表
    regex_patterns = build_regex_patterns(base_regex_pattern, file_extensions)

    script.info(f"开始正则表达式检查")
    script.info(f"基础模式: {base_regex_pattern}")
    script.info(f"选中后缀: {file_extensions if file_extensions else '全部'}")
    script.info(f"生成的模式: {regex_patterns}")
    script.info(f"检查配置 - 大小写敏感: {case_sensitive}, 检查完整文件名: {check_full_name}")

    if not os.path.exists(directory):
        script.warning(f"目录不存在: {directory}")
        return {
            'compliant_files': [],
            'non_compliant_files': [],
            'error_files': [],
            'skipped_files': 0
        }

    # 验证正则表达式
    for pattern in regex_patterns:
        is_valid, error_msg = validate_regex_pattern(script, pattern)
        if not is_valid:
            raise ValueError(f"正则表达式无效: {error_msg}")

    try:
        # 获取所有文件
        all_files = safe_walk_directory(directory, script, CheckConfig.MAX_FILES)

        compliant_files = []
        non_compliant_files = []
        error_files = []
        skipped_files = 0

        # 分批处理文件
        for i in range(0, len(all_files), CheckConfig.BATCH_SIZE):
            batch = all_files[i:i + CheckConfig.BATCH_SIZE]

            for file_path in batch:
                try:
                    # 获取文件名
                    full_filename = os.path.basename(file_path)

                    # 根据后缀过滤判断是否需要检查此文件
                    if not should_check_file_by_extension(full_filename, file_extensions):
                        skipped_files += 1
                        continue

                    # 根据配置决定检查什么
                    if check_full_name:
                        # 检查完整文件名（包含扩展名）
                        filename = full_filename
                    else:
                        # 只检查文件名部分（不包含扩展名）
                        filename = os.path.splitext(full_filename)[0]

                    # 检查是否符合任意一个正则表达式
                    is_compliant, reason = check_filename_against_multiple_regex(
                        script, filename, regex_patterns, case_sensitive
                    )

                    file_info = {
                        'file_path': file_path,
                        'filename': filename,
                        'full_filename': full_filename,
                        'reason': reason
                    }

                    if is_compliant:
                        compliant_files.append(file_info)
                    else:
                        non_compliant_files.append(file_info)

                except Exception as e:
                    error_info = {
                        'file_path': file_path,
                        'filename': os.path.basename(file_path) if file_path else 'unknown',
                        'error': str(e)
                    }
                    error_files.append(error_info)
                    script.debug(f"处理文件异常 {file_path}: {e}")

            # 批处理后垃圾回收
            gc.collect()

        result = {
            'compliant_files': compliant_files,
            'non_compliant_files': non_compliant_files,
            'error_files': error_files,
            'skipped_files': skipped_files
        }

        script.info(
            f"正则检查完成 - 符合: {len(compliant_files)}, 不符合: {len(non_compliant_files)}, 错误: {len(error_files)}, 跳过: {skipped_files}")
        return result

    except Exception as e:
        script.error(f"正则表达式检查失败: {e}")
        raise


# ==================== 主逻辑（正则表达式版） ====================
def main_logic(script: ScriptBase):
    """正则表达式检查主逻辑"""
    start_time = time.time()

    try:
        # 设置超时保护
        timer = threading.Timer(CheckConfig.TIMEOUT_SECONDS, timeout_handler)
        timer.start()

        try:
            # 初始化
            gc.collect()
            script.info("文件名正则表达式检查开始")

            # 1. 获取和验证参数
            root_path = script.get_parameter('root_path', 'D:\\fishdev')

            # 正则表达式相关参数
            regex_pattern = script.get_parameter('regex_pattern', None)  # 用户输入的基础正则表达式
            file_extensions = script.get_parameter('file_extensions', [])  # 用户选择的文件后缀
            case_sensitive = script.get_parameter('case_sensitive', True)
            check_full_name = script.get_parameter('check_full_name', True)

            # 参数验证
            if not regex_pattern:
                return script.error_result("必须提供 regex_pattern 参数", "ParameterError")

            if not isinstance(regex_pattern, str) or regex_pattern.strip() == "":
                return script.error_result("regex_pattern 参数不能为空", "ParameterError")

            # 清理正则表达式字符串
            regex_pattern = regex_pattern.strip()

            # 处理文件后缀参数
            if isinstance(file_extensions, str):
                file_extensions = [file_extensions] if file_extensions else []
            elif not isinstance(file_extensions, list):
                file_extensions = []

            # 2. 构建检查路径
            check_path = root_path

            script.info(f"检查路径: {check_path}")
            script.info(f"基础正则表达式: {regex_pattern}")
            script.info(f"选择的文件后缀: {file_extensions if file_extensions else '全部文件'}")
            script.info(f"检查配置 - 大小写敏感: {case_sensitive}, 检查完整文件名: {check_full_name}")

            if not os.path.exists(check_path):
                return script.error_result(f"路径不存在: {check_path}", "PathNotFound")

            # 3. 执行正则表达式检查
            script.info("开始执行正则表达式检查...")
            check_result = check_files_regex_compliance(
                script, check_path, regex_pattern, file_extensions, case_sensitive, check_full_name
            )

            # 4. 统计结果
            total_files = len(check_result['compliant_files']) + len(check_result['non_compliant_files']) + len(
                check_result['error_files'])
            compliant_count = len(check_result['compliant_files'])
            non_compliant_count = len(check_result['non_compliant_files'])
            error_count = len(check_result['error_files'])
            skipped_count = check_result.get('skipped_files', 0)

            # 5. 构建结果数据
            result_data = {
                'root_path': root_path,
                'check_path': check_path,
                'base_regex_pattern': regex_pattern,
                'file_extensions': file_extensions,
                'combined_patterns': build_regex_patterns(regex_pattern, file_extensions),
                'case_sensitive': case_sensitive,
                'check_full_name': check_full_name,
                'statistics': {
                    'total_files': total_files,
                    'compliant_files': compliant_count,
                    'non_compliant_files': non_compliant_count,
                    'error_files': error_count,
                    'skipped_files': skipped_count,
                    'compliance_rate': round((compliant_count / total_files * 100) if total_files > 0 else 0, 2),
                    'execution_time': time.time() - start_time
                },
                'compliant_files': check_result['compliant_files'],
                'non_compliant_files': check_result['non_compliant_files'],
                'error_files': check_result['error_files']
            }

            # 6. 生成结果消息
            if non_compliant_count > 0 or error_count > 0:
                issues = []
                if non_compliant_count > 0:
                    issues.append(f"{non_compliant_count} 个文件不符合规范")
                if error_count > 0:
                    issues.append(f"{error_count} 个文件检查异常")
                message = f"文件名检查完成，发现问题: " + ", ".join(issues)
                if skipped_count > 0:
                    message += f"，跳过 {skipped_count} 个不相关文件"
            else:
                message = f"文件名检查完成，所有 {total_files} 个文件都符合规范"
                if skipped_count > 0:
                    message += f"，跳过 {skipped_count} 个不相关文件"

            script.info(f"检查完成，耗时: {time.time() - start_time:.2f}秒")
            script.info(f"符合率: {result_data['statistics']['compliance_rate']}%")

            return script.success_result(message, result_data)

        finally:
            timer.cancel()

    except TimeoutException:
        script.error("脚本执行超时")
        return script.error_result("脚本执行超时", "TimeoutError")

    except Exception as e:
        script.error(f"执行失败: {str(e)}")
        return script.error_result(f"执行失败: {str(e)}", "UnknownError")

    finally:
        # 强制清理
        gc.collect()


if __name__ == '__main__':
    create_simple_script('checkFileName', main_logic)