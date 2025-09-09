#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名合规性检查脚本
功能：检查Unity项目中的文件名规范，包括非法后缀和重名文件检测
支持国内外版本差异检测和基准文件对比
"""

import datetime
import os
import re
import sys
from collections import defaultdict
from script_base import ScriptBase, create_simple_script


# ==================== 导入和路径设置 ====================
def setup_imports():
    """设置导入路径并解决相对导入问题"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


# 设置导入路径
setup_imports()

# 安全导入模块
try:
    from checkConfigurationTableUpdate import find_all_Configuration_in_InBundle
except ImportError as e:
    print(f"警告: 无法导入 find_all_Configuration_in_InBundle: {e}")


    def find_all_Configuration_in_InBundle(file_list, directory):
        """替代函数：遍历目录获取所有文件"""
        if not os.path.exists(directory):
            print(f"目录不存在: {directory}")
            return
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_list.append(os.path.join(root, file))

# 导入 path_config
try:
    from . import path_config
except (ImportError, ValueError):
    try:
        import path_config
    except ImportError:
        print("警告: 无法导入 path_config，使用默认路径")


        class PathConfig:
            DOMESTIC_UNITY_ROOT_PATH = "D:/Unity/Project"
            GLOBAL_UNITY_ROOT_PATH = "D:/Unity/Project"


        path_config = PathConfig()


# ==================== 辅助函数区域 ====================
def validate_extension(script, ext):
    """严格校验后缀规则（只允许纯小写字母）"""
    script.debug(f"校验文件扩展名: {ext}")
    errors = []
    if ext:
        ext_part = ext[1:]  # 去除扩展名的点
        if not ext_part:
            errors.append("空后缀")
        elif not re.fullmatch(r'^[a-z]+$', ext_part):
            errors.append("非纯小写字母")
    return errors


def get_abnormal_extensions(script, directory):
    """获取非法后缀文件"""
    script.info(f"开始检查目录: {directory}")

    if not os.path.exists(directory):
        script.warning(f"目录不存在 - {directory}")
        return defaultdict(list)

    all_files = []
    try:
        find_all_Configuration_in_InBundle(all_files, directory)
        script.info(f"共扫描文件: {len(all_files)} 个")
    except Exception as e:
        script.error(f"文件遍历出错: {e}")
        return defaultdict(list)

    error_dict = defaultdict(list)
    for file_path in all_files:
        try:
            ext = os.path.splitext(file_path)[1]
            if errors := validate_extension(script, ext):
                error_type = "+".join(errors)
                normalized_path = os.path.normpath(file_path).lower()
                error_dict[error_type].append((file_path, normalized_path))
        except Exception as e:
            script.warning(f"处理文件时出错 {file_path}: {e}")
            continue

    script.info(f"发现异常后缀类型: {len(error_dict)} 种")
    return error_dict


def find_duplicate_prefab_files(script, directory, subdirectories=None):
    """查找重名prefab文件"""
    script.info("开始检查重名Prefab文件")

    files_dict = defaultdict(list)
    subdirectories = subdirectories or ['']

    for subdir in subdirectories:
        current_dir = os.path.join(directory, subdir)
        if not os.path.exists(current_dir):
            script.warning(f"子目录不存在 - {current_dir}")
            continue

        try:
            for root, _, files in os.walk(current_dir):
                for file in files:
                    if file.lower().endswith('.prefab'):
                        full_path = os.path.join(root, file)
                        normalized = os.path.normpath(full_path).lower()
                        files_dict[file.lower()].append((full_path, normalized))
        except Exception as e:
            script.error(f"遍历目录时出错 {current_dir}: {e}")
            continue

    duplicates = {}
    for name, paths in files_dict.items():
        if len(paths) > 1:
            duplicates[name] = sorted(paths, key=lambda x: x[1])

    script.info(f"发现重名文件组: {len(duplicates)} 组")
    return duplicates


def parse_benchmark(script, content):
    """解析基准文件内容"""
    script.debug("解析基准文件内容")

    benchmark = {
        'abnormal': defaultdict(set),
        'duplicates': defaultdict(set)
    }

    current_section = None
    current_group = None

    for line in content.split('\n'):
        line = line.strip()
        if '===' in line:
            if '非法文件后缀检查' in line:
                current_section = 'abnormal'
            elif '重名Prefab文件检查' in line:
                current_section = 'duplicates'
            else:
                current_section = None
            continue

        if current_section == 'abnormal' and line.startswith('→'):
            path = os.path.normpath(line[1:].strip()).lower()
            benchmark['abnormal']['非法文件后缀检查'].add(path)

        elif current_section == 'duplicates':
            if line.startswith(('1.', '2.', '3.')):
                if '同名文件: ' in line:
                    current_group = line.split('同名文件: ')[1].strip().lower()
            elif line.startswith('▸') and current_group:
                path = os.path.normpath(line[1:].strip()).lower()
                benchmark['duplicates'][current_group].add(path)

    return benchmark


def generate_full_report(script, abnormal, duplicates):
    """生成完整报告用于更新基准"""
    script.debug("生成完整报告")

    content = []
    if abnormal:
        content.append("=== 非法文件后缀检查 ===\n")
        for err_type, files in abnormal.items():
            sorted_files = sorted(files, key=lambda x: x[1])
            content.append(f"⛔ 违规类型：{err_type}（{len(sorted_files)}个）\n")
            for f in sorted_files:
                if 'InBundle' in f[0]:
                    relative_path = f[0].split('InBundle', 1)[-1]
                else:
                    relative_path = f[0]
                content.append(f"   → {relative_path}\n")
            content.append("\n")

    if duplicates:
        content.append("\n=== 重名Prefab文件检查 ===\n")
        for idx, (name, paths) in enumerate(duplicates.items(), 1):
            content.append(f"{idx}. 同名文件: {name}\n")
            sorted_paths = sorted(paths, key=lambda x: x[1])
            for p in sorted_paths:
                if 'InBundle' in p[0]:
                    relative_path = p[0].split('InBundle', 1)[-1]
                else:
                    relative_path = p[0]
                content.append(f"   ▸ {relative_path}\n")
            content.append("\n")

    return "".join(content)


def generate_diff_report(script, current_abnormal, current_dups, benchmark):
    """生成差异报告"""
    script.debug("生成差异报告")

    content = []
    new_abnormal = defaultdict(list)
    new_duplicates = defaultdict(list)
    removed_abnormal = defaultdict(list)
    removed_duplicates = defaultdict(list)

    bench_abnormal_paths = set(item for sublist in benchmark['abnormal'].values() for item in sublist)
    current_abnormal_paths = set(f[1] for files in current_abnormal.values() for f in files)

    # 检测新增非法后缀文件
    for err_type, files in current_abnormal.items():
        filtered = [f for f in files if f[1] not in bench_abnormal_paths]
        if filtered:
            new_abnormal[err_type].extend(filtered)

    # 检测减少非法后缀文件
    for path in bench_abnormal_paths - current_abnormal_paths:
        for err_type, files in benchmark['abnormal'].items():
            if path in files:
                removed_abnormal[err_type].append(path)
                break

    # 检测新增重名文件组
    for name, paths in current_dups.items():
        current_paths_set = set(p[1] for p in paths)
        bench_paths_set = benchmark['duplicates'].get(name.lower(), set())

        new_paths = current_paths_set - bench_paths_set
        if new_paths:
            new_duplicates[name].extend([p for p in paths if p[1] in new_paths])

    # 检测减少重名文件组
    bench_duplicates = set(benchmark['duplicates'])
    current_duplicates = set(current_dups)

    for name in bench_duplicates - current_duplicates:
        removed_duplicates[name.lower()].extend(list(benchmark['duplicates'][name]))

    # 生成报告内容
    if new_abnormal:
        content.append("=== 新增非法后缀文件 ===\n")
        for err_type, files in new_abnormal.items():
            content.append(f"⛔ 违规类型：{err_type}（{len(files)}个）\n")
            for f in files:
                if 'InBundle' in f[0]:
                    relative_path = f[0].split('InBundle', 1)[-1]
                else:
                    relative_path = f[0]
                content.append(f"   → {relative_path}\n")
            content.append("\n")

    if removed_abnormal:
        content.append("=== 减少非法后缀文件 ===\n")
        for err_type, files in removed_abnormal.items():
            content.append(f"⛔ 违规类型：{err_type}（{len(files)}个）\n")
            for f in files:
                if 'InBundle' in f:
                    relative_path = f.split('InBundle', 1)[-1]
                else:
                    relative_path = f
                content.append(f"   → {relative_path}\n")
            content.append("\n")

    if new_duplicates:
        content.append("\n=== 新增重名文件 ===\n")
        for idx, (name, paths) in enumerate(new_duplicates.items(), 1):
            content.append(f"{idx}. 同名文件: {name}\n")
            sorted_paths = sorted(paths, key=lambda x: x[1])
            for p in sorted_paths:
                if 'InBundle' in p[0]:
                    relative_path = p[0].split('InBundle', 1)[-1]
                else:
                    relative_path = p[0]
                content.append(f"   ▸ {relative_path}\n")
            content.append("\n")

    if removed_duplicates:
        if content:
            content.append("\n")
        content.append("=== 减少重名文件组 ===\n")
        for idx, (name, paths) in enumerate(removed_duplicates.items(), 1):
            content.append(f"{idx}. 同名文件组: {name}\n")
            sorted_paths = sorted(paths, key=lambda x: x if isinstance(x, str) else x[1])
            for p in sorted_paths:
                path_str = p if isinstance(p, str) else p[0]
                if 'InBundle' in path_str:
                    relative_path = path_str.split('InBundle', 1)[-1]
                else:
                    relative_path = path_str
                content.append(f"   ▸ {relative_path}\n")
            content.append("\n")

    report_content = "".join(content).strip()
    result = report_content if report_content else "✅ 无新增或减少异常文件"

    return result, new_abnormal, new_duplicates, removed_abnormal, removed_duplicates


def select_benchmark_path(script, region):
    """选择国内/海外基准文件路径"""
    script.debug(f"选择基准文件，区域: {region}")

    output_dir = "../result/domesticLogs/checkFileNameLogs"

    if str(region) == "1":
        script.info("选择国内版本")
        return (os.path.join(output_dir, "checkFileName.txt"), path_config.DOMESTIC_UNITY_ROOT_PATH)
    elif str(region) == "2":
        script.info("选择海外版本")
        return (os.path.join(output_dir, "checkFileName_global.txt"), path_config.GLOBAL_UNITY_ROOT_PATH)
    else:
        script.info("使用默认值（国内）")
        return (os.path.join(output_dir, "checkFileName.txt"), path_config.DOMESTIC_UNITY_ROOT_PATH)


def validate_data(script, data):
    """验证结果数据"""
    script.debug("验证结果数据")

    required_fields = ['current_abnormal', 'current_duplicates', 'diff_report']
    for field in required_fields:
        if field not in data:
            script.error(f"缺少必要字段: {field}")
            return False

    return True


# ==================== 主逻辑函数 ====================
def main_logic(script: ScriptBase):
    """
    文件名合规性检查主逻辑

    Args:
        script: ScriptBase实例
    """

    # 1. 获取参数
    region = script.get_parameter('region', '1')  # 默认国内
    directory = script.get_parameter('directory', 'C:\\temp')
    output_dir = script.get_parameter('output_dir', '../result/domesticLogs/checkFileNameLogs')

    script.info("文件名合规性检查开始执行")
    script.debug(f"参数 - 区域: {region}, 检查路径: {directory}")

    try:
        # 2. 选择基准文件和路径
        script.info("选择基准文件...")
        benchmark_path, unity_root_path = select_benchmark_path(script, region)
        script.info(f"Unity根路径: {unity_root_path}")
        script.info(f"基准文件路径: {benchmark_path}")

        # 3. 创建输出目录
        script.info("创建输出目录...")
        os.makedirs(output_dir, exist_ok=True)

        # 4. 检查目录路径
        script.info("检查目录路径...")
        full_inbundle_path = os.path.join(unity_root_path, inbundle_path)
        script.info(f"完整检查路径: {full_inbundle_path}")

        if not os.path.exists(full_inbundle_path):
            script.warning(f"路径不存在 - {full_inbundle_path}")
            script.info("程序将创建空报告")

        # 5. 获取异常文件
        script.info("开始获取异常文件...")
        current_abnormal = get_abnormal_extensions(script, full_inbundle_path)

        # 6. 查找重复文件
        script.info("开始查找重复文件...")
        duplicate_check_dirs = script.get_parameter('duplicate_check_dirs', [
            'client/MainProject/Assets/ArtImport/Fish',
            'client/MainProject/Assets/InBundle/Fish'
        ])
        current_dups = find_duplicate_prefab_files(script, unity_root_path, duplicate_check_dirs)

        # 7. 处理基准文件
        script.info("处理基准文件...")
        benchmark = {'abnormal': defaultdict(set), 'duplicates': defaultdict(set)}

        if os.path.exists(benchmark_path):
            try:
                with open(benchmark_path, 'r', encoding='utf-8') as f:
                    benchmark = parse_benchmark(script, f.read())
                script.info(f"基准文件已加载: {benchmark_path}")
            except Exception as e:
                script.warning(f"读取基准文件失败: {e}")
        else:
            # 创建新的基准文件
            try:
                with open(benchmark_path, 'w', encoding='utf-8') as f:
                    full_report = generate_full_report(script, current_abnormal, current_dups)
                    f.write(full_report)
                script.info(f"基准文件已创建: {benchmark_path}")
            except Exception as e:
                return script.error_result(f"创建基准文件失败: {e}", "FileCreateError")

        # 8. 生成差异报告
        script.info("生成差异报告...")
        diff_content, new_abnormal, new_duplicates, removed_abnormal, removed_duplicates = generate_diff_report(
            script, current_abnormal, current_dups, benchmark
        )

        # 9. 处理输出结果
        result_data = {
            'region': region,
            'unity_root_path': unity_root_path,
            'check_path': full_inbundle_path,
            'benchmark_path': benchmark_path,
            'current_abnormal': dict(current_abnormal),
            'current_duplicates': dict(current_dups),
            'diff_report': diff_content,
            'statistics': {
                'abnormal_types': len(current_abnormal),
                'total_abnormal_files': sum(len(files) for files in current_abnormal.values()),
                'duplicate_groups': len(current_dups),
                'new_abnormal_count': sum(len(v) for v in new_abnormal.values()),
                'removed_abnormal_count': sum(len(v) for v in removed_abnormal.values()),
                'new_duplicate_groups': len(new_duplicates),
                'removed_duplicate_groups': len(removed_duplicates)
            }
        }

        # 10. 保存差异报告文件
        if diff_content != "✅ 无新增或减少异常文件":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            result_path = os.path.join(output_dir, f"diff_{timestamp}.txt")
            try:
                with open(result_path, 'w', encoding='utf-8') as f:
                    f.write(diff_content)
                script.info(f"差异报告已保存: {result_path}")
                result_data['diff_report_file'] = result_path
            except Exception as e:
                script.warning(f"保存差异报告失败: {e}")

        # 11. 验证结果
        if not validate_data(script, result_data):
            return script.error_result("数据验证失败", "ValidationError")

        # 12. 输出统计信息
        stats = result_data['statistics']
        script.info(f"检查完成 - 异常类型: {stats['abnormal_types']}, 重名组: {stats['duplicate_groups']}")
        script.info(f"新增异常: {stats['new_abnormal_count']}, 减少异常: {stats['removed_abnormal_count']}")

        # 13. 返回成功结果
        if diff_content != "✅ 无新增或减少异常文件":
            message = f"发现文件变化 - 新增异常{stats['new_abnormal_count']}个，减少异常{stats['removed_abnormal_count']}个"
        else:
            message = "文件名检查完成，无异常变化"

        return script.success_result(message, result_data)

    except Exception as e:
        script.error(f"文件名检查执行失败: {e}")
        raise


if __name__ == '__main__':
    # 设置递归限制
    import sys

    sys.setrecursionlimit(3000)

    create_simple_script('filename_compliance_checker', main_logic)