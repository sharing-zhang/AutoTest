#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名正则表达式检查脚本 - 高性能完整展示版本
功能：根据用户提供的正则表达式和选择的文件后缀检查项目中的文件名是否符合规范
"""

import os
import re
import sys
import time
import traceback
import gc
from pathlib import Path
from script_base import ScriptBase, create_simple_script


# ==================== 高性能配置 ====================
class PerformanceConfig:
    MAX_FILES = 20000  # 增加文件数量限制
    MAX_DEPTH = 8  # 增加深度限制
    PROGRESS_INTERVAL = 2000  # 减少进度报告频率
    MEMORY_CHECK_INTERVAL = 5000  # 减少内存检查频率
    MAX_PATH_LENGTH = 280
    BATCH_SIZE = 1000  # 批处理大小


# ==================== 性能优化：预编译跳过模式 ====================
class SkipPatterns:
    """预编译跳过模式，避免重复计算"""

    def __init__(self):
        # 跳过目录（使用集合，O(1)查找）
        self.skip_dirs = frozenset({
            '.git', '.svn', '__pycache__', 'node_modules',
            '.idea', '.vscode', 'temp', 'library', 'bin', 'obj',
            'build', 'dist', 'debug', 'release', '.pytest_cache',
            'coverage', '.nyc_output', 'logs'
        })

        # 跳过文件
        self.skip_files = frozenset({
            'thumbs.db', 'desktop.ini', '.ds_store',
            '.gitignore', '.gitkeep', '.env'
        })

        # 预编译文件名模式（避免重复startswith检查）
        self.hidden_prefixes = ('.', '~', '#')

    def should_skip_dir(self, dirname):
        """快速目录跳过检查"""
        return (dirname.lower() in self.skip_dirs or
                dirname.startswith(self.hidden_prefixes))

    def should_skip_file(self, filename):
        """快速文件跳过检查"""
        filename_lower = filename.lower()
        return (filename_lower in self.skip_files or
                filename.startswith(self.hidden_prefixes) or
                filename.endswith(('.tmp', '.bak', '.log')))


# ==================== 性能优化：快速扩展名解析 ====================
def fast_parse_extensions(extensions):
    """快速解析文件后缀"""
    if not extensions:
        return None

    # 使用集合，提供O(1)查找性能
    result = set()

    if isinstance(extensions, str):
        # 优化字符串分割
        exts = extensions.replace(',', ' ').split()
    else:
        exts = extensions if isinstance(extensions, (list, tuple)) else [extensions]

    for ext in exts:
        ext = str(ext).strip().lower()
        if ext and len(ext) < 10:
            # 标准化扩展名格式
            result.add(ext if ext.startswith('.') else '.' + ext)

    return result if result else None


# ==================== 性能优化：高速文件扫描 ====================
def fast_scan_files(directory, target_extensions, script):
    """高速文件扫描 - 使用pathlib和优化算法"""

    skip_patterns = SkipPatterns()
    matched_files = []
    total_files = 0
    skipped_files = 0

    script.info(f"开始高速扫描目录: {directory}")
    start_time = time.time()

    try:
        # 使用pathlib，性能更好
        root_path = Path(directory)
        if not root_path.is_dir():
            raise ValueError(f"目录不存在或不可访问: {directory}")

        # 获取根目录深度（pathlib版本）
        root_depth = len(root_path.parts)

        # 使用iterdir()而不是os.walk()，在某些情况下更快
        def scan_directory(current_path, current_depth):
            nonlocal total_files, skipped_files, matched_files

            try:
                # 深度检查
                if current_depth - root_depth > PerformanceConfig.MAX_DEPTH:
                    return

                # 路径长度检查
                if len(str(current_path)) > PerformanceConfig.MAX_PATH_LENGTH:
                    return

                # 获取目录内容，一次性读取
                try:
                    items = list(current_path.iterdir())
                except (PermissionError, OSError):
                    return

                # 分离文件和目录
                files = []
                dirs = []

                for item in items:
                    if item.is_file():
                        files.append(item)
                    elif item.is_dir():
                        dirs.append(item)

                # 批量处理文件
                for file_path in files:
                    filename = file_path.name

                    # 快速跳过检查
                    if skip_patterns.should_skip_file(filename):
                        continue

                    # 文件名长度检查
                    if len(filename) > 200:
                        continue

                    # 扩展名检查（优化版本）
                    if target_extensions:
                        file_suffix = file_path.suffix.lower()
                        if file_suffix not in target_extensions:
                            skipped_files += 1
                            continue

                    # 路径长度检查
                    if len(str(file_path)) > PerformanceConfig.MAX_PATH_LENGTH:
                        continue

                    matched_files.append(str(file_path))
                    total_files += 1

                    # 文件数量限制
                    if total_files >= PerformanceConfig.MAX_FILES:
                        raise StopIteration("文件数量限制")

                # 进度报告（减少频率）
                if total_files % PerformanceConfig.PROGRESS_INTERVAL == 0:
                    script.info(f"已扫描 {total_files} 个文件，深度: {current_depth - root_depth}")

                # 内存管理（减少频率）
                if total_files % PerformanceConfig.MEMORY_CHECK_INTERVAL == 0:
                    gc.collect()

                # 递归处理子目录
                for dir_path in dirs:
                    dirname = dir_path.name

                    # 快速跳过检查
                    if skip_patterns.should_skip_dir(dirname):
                        continue

                    # 路径长度检查
                    if len(str(dir_path)) > PerformanceConfig.MAX_PATH_LENGTH:
                        continue

                    # 递归扫描
                    scan_directory(dir_path, current_depth + 1)

            except Exception as e:
                script.warning(f"扫描目录异常 {current_path}: {e}")

        # 开始扫描
        scan_directory(root_path, root_depth)

    except StopIteration:
        script.info("达到文件数量限制，停止扫描")
    except Exception as e:
        script.error(f"文件扫描异常: {e}")
        raise

    scan_time = time.time() - start_time
    script.info(f"高速扫描完成: {total_files} 个文件, {skipped_files} 个跳过, 耗时 {scan_time:.2f}秒")

    return matched_files, skipped_files


# ==================== 性能优化：批量正则检查 ====================
def fast_regex_check(files, regex_pattern, case_sensitive, check_full_name, script):
    """批量正则检查 - 使用批处理优化"""

    script.info(f"开始高速正则检查 {len(files)} 个文件...")
    start_time = time.time()

    # 预编译正则表达式
    try:
        if len(regex_pattern) > 150:
            raise ValueError("正则表达式过长")

        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_pattern = re.compile(regex_pattern, flags)
        script.info(f"正则表达式编译成功")
    except re.error as e:
        raise ValueError(f"正则表达式无效: {e}")

    # 结果容器
    compliant_paths = []
    non_compliant_info = []
    error_info = []

    # 批量处理优化
    total_files = len(files)
    processed = 0

    for batch_start in range(0, total_files, PerformanceConfig.BATCH_SIZE):
        batch_end = min(batch_start + PerformanceConfig.BATCH_SIZE, total_files)
        batch_files = files[batch_start:batch_end]

        # 批量处理文件
        for file_path in batch_files:
            try:
                # 基础验证（优化版本）
                if not isinstance(file_path, str) or len(file_path) > PerformanceConfig.MAX_PATH_LENGTH:
                    continue

                # 文件名提取（优化）
                if os.sep in file_path:
                    basename = file_path.split(os.sep)[-1]  # 比os.path.basename更快
                else:
                    basename = file_path

                # 检查名称确定
                if check_full_name:
                    check_name = basename
                else:
                    # 优化的扩展名移除
                    dot_pos = basename.rfind('.')
                    check_name = basename[:dot_pos] if dot_pos != -1 else basename

                # 文件名长度检查
                if len(check_name) > 80:
                    continue

                # 正则匹配
                if compiled_pattern.match(check_name):
                    compliant_paths.append(file_path)
                else:
                    non_compliant_info.append({
                        'path': file_path,
                        'name': check_name,
                        'full_name': basename
                    })

                processed += 1

            except Exception as fe:
                error_info.append({
                    'path': str(file_path)[:100],
                    'name': 'ERROR',
                    'error': str(fe)[:100]
                })
                processed += 1

        # 批次完成后的进度报告
        if batch_end % PerformanceConfig.PROGRESS_INTERVAL < PerformanceConfig.BATCH_SIZE:
            script.info(f"已检查 {batch_end}/{total_files} 个文件 ({(batch_end / total_files * 100):.1f}%)")

        # 批次间内存管理
        if batch_end % PerformanceConfig.MEMORY_CHECK_INTERVAL < PerformanceConfig.BATCH_SIZE:
            gc.collect()

    check_time = time.time() - start_time
    script.info(f"高速正则检查完成: 耗时 {check_time:.2f}秒")

    return compliant_paths, non_compliant_info, error_info


# ==================== 性能优化：中文ASCII格式的消息生成 ====================
def format_chinese_ascii_message(compliant_count, non_compliant_info, error_info, total_time, regex_pattern):
    """生成中文ASCII格式的检查结果消息"""

    total_checked = compliant_count + len(non_compliant_info) + len(error_info)
    total_issues = len(non_compliant_info) + len(error_info)

    # 使用列表拼接，确保每部分都分行显示
    message_parts = []

    # ====== 头部标题 ======
    message_parts.append("=" * 80)
    message_parts.append("                         文件名规范检查结果报告")
    message_parts.append("=" * 80)

    # ====== 概览统计 ======
    compliance_rate = (compliant_count / total_checked * 100) if total_checked > 0 else 0
    message_parts.append("\n[检查概览] 统计信息:")
    message_parts.append(f"   +-- 总计检查文件: {total_checked} 个")
    message_parts.append(f"   +-- 符合规范文件: {compliant_count} 个")
    message_parts.append(f"   +-- 不符合规范文件: {len(non_compliant_info)} 个")
    message_parts.append(f"   +-- 检查异常文件: {len(error_info)} 个")
    message_parts.append(f"   +-- 符合率: {compliance_rate:.1f}%")
    message_parts.append(f"   +-- 执行耗时: {total_time:.2f} 秒")

    # ====== 正则表达式信息 ======
    message_parts.append(f"\n[正则规则] 使用的表达式:")
    message_parts.append(f"   {regex_pattern}")

    # ====== 检查结果判定 ======
    if total_issues == 0:
        message_parts.append("\n[检查结果] 状态: 通过")
        message_parts.append("   所有文件都符合命名规范!")
    else:
        message_parts.append("\n[检查结果] 状态: 未通过")
        message_parts.append(f"   发现 {total_issues} 个问题文件需要处理")

    # ====== 不符合规范的文件详情 ======
    if non_compliant_info:
        message_parts.append(f"\n[不符合规范] 文件列表 (共 {len(non_compliant_info)} 个):")
        message_parts.append("   " + "-" * 76)

        # 按文件名排序，便于查看
        sorted_non_compliant = sorted(non_compliant_info, key=lambda x: x['full_name'])

        for i, info in enumerate(sorted_non_compliant, 1):
            # 格式化序号和文件名
            prefix = f"   {i:>3}."
            filename = info['full_name']

            # 如果文件名太长，适当截断并添加省略号
            if len(filename) > 60:
                display_name = filename[:57] + "..."
            else:
                display_name = filename

            message_parts.append(f"{prefix} {display_name}")

        message_parts.append("   " + "-" * 76)

    # ====== 检查异常的文件详情 ======
    if error_info:
        message_parts.append(f"\n[检查异常] 文件列表 (共 {len(error_info)} 个):")
        message_parts.append("   " + "-" * 76)

        for i, info in enumerate(error_info, 1):
            # 获取文件名
            error_filename = "未知文件"
            if 'path' in info:
                try:
                    if os.sep in info['path']:
                        error_filename = info['path'].split(os.sep)[-1]
                    else:
                        error_filename = info['path']
                except:
                    error_filename = str(info['path'])[:50]

            error_reason = info.get('error', '未知错误')

            # 截断过长的错误信息
            if len(error_reason) > 40:
                error_reason = error_reason[:37] + "..."

            message_parts.append(f"   {i:>3}. {error_filename}")
            message_parts.append(f"        错误: {error_reason}")

        message_parts.append("   " + "-" * 76)

    # ====== 建议和总结 ======
    message_parts.append("\n[处理建议] 操作指南:")
    if non_compliant_info:
        message_parts.append("   +-- 根据正则表达式规则重命名不符合规范的文件")
        message_parts.append("   +-- 建议优先处理使用频率较高的核心文件")
    if error_info:
        message_parts.append("   +-- 检查异常文件的访问权限和文件完整性")
    if total_issues == 0:
        message_parts.append("   +-- 文件命名规范良好，请继续保持")
    else:
        message_parts.append("   +-- 建议建立文件命名规范文档，避免类似问题")

    # ====== 性能统计 ======
    files_per_second = total_checked / total_time if total_time > 0 else 0
    message_parts.append(f"\n[性能统计] 执行效率:")
    message_parts.append(f"   +-- 处理速度: {files_per_second:.0f} 文件/秒")
    message_parts.append(
        f"   +-- 平均每文件: {(total_time / total_checked * 1000):.2f} 毫秒") if total_checked > 0 else message_parts.append(
        "   +-- 平均每文件: 0 毫秒")

    # ====== 结尾 ======
    message_parts.append("\n" + "=" * 80)

    # 使用换行符连接所有部分
    return "\n".join(message_parts)


# ==================== 输出优化函数 (中文ASCII版本) ====================
def print_detailed_results_chinese_ascii(script, compliant_count, non_compliant_info, error_info, total_time,
                                         regex_pattern):
    """分段打印详细结果，使用中文和ASCII字符"""

    total_checked = compliant_count + len(non_compliant_info) + len(error_info)
    compliance_rate = (compliant_count / total_checked * 100) if total_checked > 0 else 0

    # 打印概览信息
    script.info("=" * 80)
    script.info("                         文件名规范检查结果报告")
    script.info("=" * 80)

    script.info("[检查概览] 统计信息:")
    script.info(f"   +-- 总计检查文件: {total_checked} 个")
    script.info(f"   +-- 符合规范文件: {compliant_count} 个")
    script.info(f"   +-- 不符合规范文件: {len(non_compliant_info)} 个")
    script.info(f"   +-- 检查异常文件: {len(error_info)} 个")
    script.info(f"   +-- 符合率: {compliance_rate:.1f}%")
    script.info(f"   +-- 执行耗时: {total_time:.2f} 秒")

    script.info(f"\n[正则规则] 使用的表达式:")
    script.info(f"   {regex_pattern}")

    # 打印结果判定
    total_issues = len(non_compliant_info) + len(error_info)
    if total_issues == 0:
        script.info("\n[检查结果] 状态: 通过")
        script.info("   所有文件都符合命名规范!")
    else:
        script.info("\n[检查结果] 状态: 未通过")
        script.info(f"   发现 {total_issues} 个问题文件需要处理")

    # 分批打印不符合规范的文件
    if non_compliant_info:
        script.info(f"\n[不符合规范] 文件列表 (共 {len(non_compliant_info)} 个):")
        script.info("   " + "-" * 76)

        # 按文件名排序
        sorted_non_compliant = sorted(non_compliant_info, key=lambda x: x['full_name'])

        # 分批显示，每批20个
        batch_size = 20
        for batch_start in range(0, len(sorted_non_compliant), batch_size):
            batch_end = min(batch_start + batch_size, len(sorted_non_compliant))
            batch = sorted_non_compliant[batch_start:batch_end]

            for i, info in enumerate(batch, batch_start + 1):
                filename = info['full_name']
                if len(filename) > 60:
                    display_name = filename[:57] + "..."
                else:
                    display_name = filename

                script.info(f"   {i:>3}. {display_name}")

        script.info("   " + "-" * 76)

    # 分批打印异常文件
    if error_info:
        script.info(f"\n[检查异常] 文件列表 (共 {len(error_info)} 个):")
        script.info("   " + "-" * 76)

        for i, info in enumerate(error_info, 1):
            error_filename = "未知文件"
            if 'path' in info:
                try:
                    if os.sep in info['path']:
                        error_filename = info['path'].split(os.sep)[-1]
                    else:
                        error_filename = info['path']
                except:
                    error_filename = str(info['path'])[:50]

            error_reason = info.get('error', '未知错误')
            if len(error_reason) > 40:
                error_reason = error_reason[:37] + "..."

            script.info(f"   {i:>3}. {error_filename}")
            script.info(f"        错误: {error_reason}")

        script.info("   " + "-" * 76)

    # 打印建议
    script.info("\n[处理建议] 操作指南:")
    if non_compliant_info:
        script.info("   +-- 根据正则表达式规则重命名不符合规范的文件")
        script.info("   +-- 建议优先处理使用频率较高的核心文件")
    if error_info:
        script.info("   +-- 检查异常文件的访问权限和文件完整性")
    if total_issues == 0:
        script.info("   +-- 文件命名规范良好，请继续保持")
    else:
        script.info("   +-- 建议建立文件命名规范文档，避免类似问题")

    # 打印性能统计
    files_per_second = total_checked / total_time if total_time > 0 else 0
    avg_time_per_file = (total_time / total_checked * 1000) if total_checked > 0 else 0

    script.info(f"\n[性能统计] 执行效率:")
    script.info(f"   +-- 处理速度: {files_per_second:.0f} 文件/秒")
    script.info(f"   +-- 平均每文件: {avg_time_per_file:.2f} 毫秒")

    script.info("\n" + "=" * 80)


# ==================== 高性能主逻辑 ====================
def main_logic(script: ScriptBase):
    """高性能主逻辑"""
    total_start = time.time()

    try:
        script.info("=== 高性能文件名检查开始 (中文ASCII版本) ===")

        # 快速参数获取
        root_path = script.get_parameter('root_path', 'D:\\fishdev')
        regex_pattern = script.get_parameter('regex_pattern', None)
        file_extensions = script.get_parameter('file_extensions', [])
        case_sensitive = script.get_parameter('case_sensitive', True)
        check_full_name = script.get_parameter('check_full_name', False)

        script.info(f"参数配置: {root_path}, 正则: {regex_pattern}")

        # 快速验证
        if not regex_pattern or not regex_pattern.strip():
            return script.error_result("regex_pattern 参数不能为空", "ParameterError")

        regex_pattern = regex_pattern.strip()

        if not os.path.exists(root_path):
            return script.error_result(f"路径不存在: {root_path}", "PathNotFound")

        if not os.path.isdir(root_path):
            return script.error_result(f"路径不是目录: {root_path}", "PathNotDirectory")

        # 快速解析扩展名
        target_extensions = fast_parse_extensions(file_extensions)
        script.info(f"目标扩展名: {list(target_extensions) if target_extensions else '全部文件'}")

        # 高速文件扫描
        matched_files, skipped_count = fast_scan_files(root_path, target_extensions, script)

        if not matched_files:
            return script.success_result("未找到匹配的文件", {
                'statistics': {'total_files': 0, 'skipped_files': skipped_count}
            })

        # 高速正则检查
        compliant_paths, non_compliant_info, error_info = fast_regex_check(
            matched_files, regex_pattern, case_sensitive, check_full_name, script
        )

        # 计算统计数据
        total_time = time.time() - total_start
        compliant_count = len(compliant_paths)
        total_checked = compliant_count + len(non_compliant_info) + len(error_info)
        compliance_rate = (compliant_count / total_checked * 100) if total_checked > 0 else 0

        # 使用中文ASCII版本的分段打印
        print_detailed_results_chinese_ascii(script, compliant_count, non_compliant_info, error_info, total_time,
                                             regex_pattern)

        # 生成中文ASCII格式的消息（用于返回结果）
        message = format_chinese_ascii_message(compliant_count, non_compliant_info, error_info, total_time,
                                               regex_pattern)

        result_data = {
            'statistics': {
                'total_checked': total_checked,
                'compliant_files': compliant_count,
                'non_compliant_files': len(non_compliant_info),
                'error_files': len(error_info),
                'compliance_rate': round(compliance_rate, 2),
                'execution_time': round(total_time, 3)
            },
            'regex_pattern': regex_pattern,
            'non_compliant_files': non_compliant_info,
            'error_files': error_info
        }

        script.info(f"=== 高性能检查完成 ===")

        return script.success_result(message, result_data)

    except Exception as e:
        script.error(f"高性能检查失败: {e}")
        script.error(f"异常堆栈: {traceback.format_exc()}")
        return script.error_result(f"检查失败: {e}", "UnknownError")

    finally:
        # 最终清理
        gc.collect()


if __name__ == '__main__':
    create_simple_script('checkFileName', main_logic)