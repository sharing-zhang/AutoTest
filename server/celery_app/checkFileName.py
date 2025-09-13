#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名合规性检查脚本（优化版）
功能：检查项目中的文件名规范，包括非法后缀和重名文件检测
"""

import os
import re
import sys
import gc
import time
import threading
from collections import defaultdict
from script_base import ScriptBase, create_simple_script

# 设置更保守的递归限制
sys.setrecursionlimit(500)


# ==================== 全局配置 ====================
class CheckConfig:
    MAX_FILES = 20000  # 降低文件数量限制
    BATCH_SIZE = 500  # 批处理大小
    GC_FREQUENCY = 200  # 垃圾回收频率
    TIMEOUT_SECONDS = 30  # 超时时间
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


# ==================== 优化的检查函数 ====================
def validate_extension_safe(script, ext):
    """安全的扩展名验证"""
    try:
        if not ext:
            return ["无扩展名"]

        ext_part = ext[1:] if ext.startswith('.') else ext

        if not ext_part:
            return ["空扩展名"]

        # 只检查基本规则，避免复杂正则
        if not ext_part.islower():
            return ["非小写"]

        if not ext_part.isalpha():
            return ["包含非字母"]

        return []

    except Exception:
        return ["验证异常"]


def check_illegal_extensions_optimized(script, directory):
    """优化的非法扩展名检查"""
    script.info("开始优化的扩展名检查")

    if not os.path.exists(directory):
        script.warning(f"目录不存在: {directory}")
        return defaultdict(list)

    try:
        # 使用安全遍历
        all_files = safe_walk_directory(directory, script, CheckConfig.MAX_FILES)

        illegal_files = defaultdict(list)

        # 分批处理文件
        for i in range(0, len(all_files), CheckConfig.BATCH_SIZE):
            batch = all_files[i:i + CheckConfig.BATCH_SIZE]

            for file_path in batch:
                try:
                    _, ext = os.path.splitext(file_path)
                    errors = validate_extension_safe(script, ext)

                    if errors:
                        error_type = "+".join(errors)
                        illegal_files[error_type].append(file_path)

                except Exception as e:
                    script.debug(f"处理文件异常 {file_path}: {e}")
                    continue

            # 批处理后垃圾回收
            gc.collect()

        script.info(f"扩展名检查完成，发现 {len(illegal_files)} 种问题类型")
        return illegal_files

    except Exception as e:
        script.error(f"扩展名检查失败: {e}")
        return defaultdict(list)


def check_duplicate_files_optimized(script, directory):
    """优化的重名文件检查"""
    script.info("开始优化的重名文件检查")

    if not os.path.exists(directory):
        script.warning(f"目录不存在: {directory}")
        return {}

    try:
        files_dict = defaultdict(list)

        # 直接遍历，不使用递归存储
        for root, dirs, files in os.walk(directory):
            # 过滤目录
            dirs[:] = [d for d in dirs if not _is_dangerous_dir(d)]

            # 只处理prefab文件
            prefab_files = [f for f in files if f.lower().endswith('.prefab')]

            for file in prefab_files:
                try:
                    full_path = os.path.join(root, file)
                    if os.path.isfile(full_path):
                        files_dict[file.lower()].append(full_path)
                except Exception:
                    continue

        # 只保留重名的
        duplicates = {name: paths for name, paths in files_dict.items() if len(paths) > 1}

        script.info(f"重名检查完成，发现 {len(duplicates)} 组重名文件")
        return duplicates

    except Exception as e:
        script.error(f"重名文件检查失败: {e}")
        return {}


# ==================== 主逻辑（优化版） ====================
def main_logic(script: ScriptBase):
    """优化的主逻辑"""
    start_time = time.time()

    try:
        # 设置超时保护
        timer = threading.Timer(CheckConfig.TIMEOUT_SECONDS, timeout_handler)
        timer.start()

        try:
            # 初始化
            gc.collect()
            script.info("文件名合规性检查开始（优化版）")

            # 1. 获取和验证参数
            root_path = script.get_parameter('root_path', 'D:\\fishdev')
            check_extension = script.get_parameter('check_extension', True)
            check_duplicate = script.get_parameter('check_duplicate', True)
            inbundle_path = script.get_parameter('inbundle_path', None)

            # 参数验证
            if not check_extension and not check_duplicate:
                return script.error_result("至少需要启用一种检查类型", "ParameterError")

            # 2. 构建检查路径
            check_path = os.path.join(root_path, inbundle_path) if inbundle_path else root_path

            script.info(f"检查路径: {check_path}")
            script.info(f"检查类型: 扩展名={check_extension}, 重名={check_duplicate}")

            if not os.path.exists(check_path):
                return script.error_result(f"路径不存在: {check_path}", "PathNotFound")

            # 3. 执行检查
            illegal_extensions = defaultdict(list)
            duplicate_files = {}

            if check_extension:
                script.info("执行扩展名检查...")
                illegal_extensions = check_illegal_extensions_optimized(script, check_path)
                gc.collect()

            if check_duplicate:
                script.info("执行重名文件检查...")
                duplicate_files = check_duplicate_files_optimized(script, check_path)
                gc.collect()

            # 4. 统计结果
            total_illegal = sum(len(files) for files in illegal_extensions.values()) if check_extension else 0
            total_duplicate_groups = len(duplicate_files) if check_duplicate else 0

            # 5. 构建结果
            result_data = {
                'root_path': root_path,
                'check_path': check_path,
                'check_extension': check_extension,
                'check_duplicate': check_duplicate,
                'statistics': {
                    'total_illegal_files': total_illegal,
                    'illegal_extension_types': len(illegal_extensions) if check_extension else 0,
                    'duplicate_groups': total_duplicate_groups,
                    'execution_time': time.time() - start_time
                }
            }

            # 只在启用检查时添加详细数据
            if check_extension and illegal_extensions:
                result_data['illegal_extensions'] = dict(illegal_extensions)
            if check_duplicate and duplicate_files:
                result_data['duplicate_files'] = dict(duplicate_files)

            # 6. 判断结果
            has_issues = (check_extension and total_illegal > 0) or (check_duplicate and total_duplicate_groups > 0)

            if has_issues:
                issues = []
                if check_extension and total_illegal > 0:
                    issues.append(f"发现 {total_illegal} 个非法扩展名文件")
                if check_duplicate and total_duplicate_groups > 0:
                    issues.append(f"发现 {total_duplicate_groups} 组重名文件")
                message = "文件检查发现问题: " + ", ".join(issues)
            else:
                message = "文件检查完成，未发现问题"

            script.info(f"检查完成，耗时: {time.time() - start_time:.2f}秒")
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