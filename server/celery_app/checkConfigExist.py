#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件指定路径字段验证脚本（简化版）
根据用户指定的配置文件和字段名，检查对应的路径是否在工程目录中存在
只输出未找到的路径信息
"""

from script_base import create_simple_script
import os
import re
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


# ==================== 辅助函数区域 ====================

def safe_path_operation(func, *args, **kwargs):
    """安全执行路径操作"""
    try:
        return func(*args, **kwargs)
    except (OSError, PermissionError, ValueError, TypeError):
        return None
    except Exception:
        return None


def read_config_with_encoding(script, file_path: str, preferred_encoding: str) -> Tuple[str, str]:
    """使用合适的编码读取配置文件"""
    try:
        script.debug(f"尝试读取配置文件: {file_path}")

        # 检查文件是否存在和可读
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"路径不是文件: {file_path}")

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            script.warning("配置文件为空")
            return "", preferred_encoding

        if file_size > 50 * 1024 * 1024:  # 50MB限制
            raise ValueError(f"文件过大 ({file_size / (1024 * 1024):.1f}MB)，超过50MB限制")

        encodings_to_try = [preferred_encoding, 'utf-8-sig', 'utf-8', 'utf-16', 'gbk', 'cp1252', 'latin1']

        for encoding in encodings_to_try:
            try:
                script.debug(f"尝试编码: {encoding}")
                with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                    content = f.read()
                script.info(f"成功使用编码 {encoding} 读取文件")
                return content, encoding
            except UnicodeDecodeError as e:
                script.debug(f"编码 {encoding} 失败: {e}")
                continue
            except Exception as e:
                script.debug(f"读取文件时发生错误 (编码: {encoding}): {e}")
                continue

        # 最后尝试忽略错误
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            script.warning("使用UTF-8忽略错误模式读取文件")
            return content, 'utf-8-ignore'
        except Exception as e:
            raise Exception(f"所有编码方式都无法读取文件: {e}")

    except Exception as e:
        script.error(f"读取配置文件失败: {e}")
        raise


def clean_value(value: str) -> str:
    """清理配置值，去除多余的字符"""
    try:
        if not isinstance(value, str):
            return str(value) if value is not None else ""

        if not value:
            return ""

        cleaned = value.strip()
        if not cleaned:
            return ""

        # 移除引号
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]

        # 移除分号
        cleaned = cleaned.rstrip(';').strip()

        # 处理转义字符
        cleaned = cleaned.replace('\\"', '"').replace("\\'", "'")

        return cleaned

    except Exception:
        return str(value) if value is not None else ""


def scan_all_field_occurrences(script, content: str, target_fields: List[str]) -> List[Dict[str, Any]]:
    """扫描文件内容中所有指定字段的出现"""
    try:
        script.debug(f"开始扫描字段: {target_fields}")

        if not content:
            script.warning("配置文件内容为空")
            return []

        if not target_fields:
            script.warning("目标字段列表为空")
            return []

        all_field_items = []

        for field_name in target_fields:
            try:
                if not field_name or not isinstance(field_name, str):
                    continue

                script.debug(f"扫描字段: {field_name}")

                # 转义字段名以避免正则表达式问题
                escaped_field = re.escape(field_name)

                patterns = [
                    rf'({escaped_field})\s*=\s*"([^"]*)"',
                    rf'({escaped_field})\s*=\s*\'([^\']*)\'',
                    rf'({escaped_field})\s*=\s*([^;\s\n]+)',
                ]

                field_count = 0
                for pattern_idx, pattern in enumerate(patterns):
                    try:
                        matches = re.findall(pattern, content, re.MULTILINE)

                        for match in matches:
                            try:
                                if isinstance(match, tuple) and len(match) >= 2:
                                    found_field, found_value = match[0], match[1]
                                    field_count += 1

                                    field_item = {
                                        'field_name': found_field,
                                        'occurrence_index': field_count,
                                        'original_value': found_value,
                                        'cleaned_value': clean_value(found_value),
                                        'source_key': f"{found_field}[{field_count}]"
                                    }
                                    all_field_items.append(field_item)
                                    script.debug(f"找到字段值: {found_field} = {found_value}")
                            except Exception as e:
                                script.debug(f"处理匹配项时出错: {e}")
                                continue

                    except Exception as e:
                        script.debug(f"正则表达式匹配出错 (模式 {pattern_idx}): {e}")
                        continue

            except Exception as e:
                script.debug(f"处理字段 {field_name} 时出错: {e}")
                continue

        script.info(f"扫描完成，找到 {len(all_field_items)} 个字段项")
        return all_field_items

    except Exception as e:
        script.error(f"扫描字段时发生错误: {e}")
        return []


def safe_find_matching_items(script, root_path: Path, item_name: str, is_file: bool = False, max_depth: int = 6) -> \
List[Path]:
    """安全地在指定根目录下递归查找匹配的文件或文件夹"""
    try:
        if not root_path or not item_name:
            return []

        if not root_path.exists() or not root_path.is_dir():
            return []

        matching_paths = []
        processed_dirs = set()  # 防止循环引用

        def search_recursive(current_path: Path, current_depth: int):
            if current_depth > max_depth:
                return

            # 防止循环引用
            try:
                resolved_path = current_path.resolve()
                if resolved_path in processed_dirs:
                    return
                processed_dirs.add(resolved_path)
            except (OSError, ValueError):
                return

            try:
                # 限制每个目录下的项目数量，防止内存问题
                items = list(current_path.iterdir())
                if len(items) > 1000:  # 如果目录项目太多，跳过
                    script.debug(f"跳过大目录: {current_path} (包含 {len(items)} 项)")
                    return

                for item_path in items:
                    try:
                        if len(matching_paths) >= 100:  # 限制结果数量
                            return

                        item_name_lower = item_name.lower()
                        item_path_name_lower = item_path.name.lower()

                        if is_file and safe_path_operation(
                                item_path.is_file) and item_path_name_lower == item_name_lower:
                            matching_paths.append(item_path)
                        elif not is_file and safe_path_operation(
                                item_path.is_dir) and item_path_name_lower == item_name_lower:
                            matching_paths.append(item_path)
                        elif safe_path_operation(item_path.is_dir):
                            # 跳过常见的无关目录
                            if item_path.name not in {'.git', '.svn', '.vs', 'node_modules', 'Temp', 'Library', 'Logs',
                                                      '__pycache__', 'bin', 'obj', 'Debug', 'Release'}:
                                search_recursive(item_path, current_depth + 1)
                    except (PermissionError, OSError, ValueError) as e:
                        script.debug(f"访问路径出错 {item_path}: {e}")
                        continue
                    except Exception as e:
                        script.debug(f"处理路径时出错 {item_path}: {e}")
                        continue

            except (PermissionError, OSError, ValueError) as e:
                script.debug(f"读取目录出错 {current_path}: {e}")
                return
            except Exception as e:
                script.debug(f"搜索过程出错 {current_path}: {e}")
                return

        try:
            search_recursive(root_path, 0)
        except Exception as e:
            script.debug(f"搜索异常: {e}")

        return matching_paths

    except Exception as e:
        script.debug(f"查找匹配项时出错: {e}")
        return []


def find_all_matching_items_with_extensions(script, root_path: Path, item_name: str, extensions: List[str]) -> List[
    Path]:
    """在指定根目录下递归查找所有匹配的文件（包含指定扩展名）"""
    try:
        if not item_name:
            return []

        matching_paths = []
        item_path = Path(item_name)
        has_extension = len(item_path.suffix) > 0

        if has_extension:
            exact_matches = safe_find_matching_items(script, root_path, item_name, is_file=True)
            matching_paths.extend(exact_matches)
        else:
            exact_matches = safe_find_matching_items(script, root_path, item_name, is_file=True)
            matching_paths.extend(exact_matches)

            for ext in extensions[:5]:  # 限制扩展名数量
                if not ext:
                    continue
                filename_with_ext = f"{item_name}{ext}"
                ext_matches = safe_find_matching_items(script, root_path, filename_with_ext, is_file=True)
                matching_paths.extend(ext_matches)

        # 去重
        unique_paths = []
        seen_paths = set()
        for path in matching_paths:
            try:
                resolved_path = path.resolve()
                if resolved_path not in seen_paths:
                    unique_paths.append(path)
                    seen_paths.add(resolved_path)
            except (OSError, ValueError):
                continue

        return unique_paths

    except Exception as e:
        script.debug(f"查找扩展名匹配项时出错: {e}")
        return []


def validate_path_exists(script, path_value: str, project_root: Path, custom_extensions: List[str]) -> bool:
    """验证路径是否存在（简化版，只返回是否存在）"""
    try:
        if not isinstance(path_value, str) or not path_value:
            return False

        # 清理路径值
        cleaned_path = clean_value(path_value)
        if not cleaned_path:
            return False

        # 处理环境变量
        try:
            expanded_path = os.path.expandvars(cleaned_path)
        except Exception:
            expanded_path = cleaned_path

        # 检查路径长度，防止过长路径导致问题
        if len(expanded_path) > 260:  # Windows路径长度限制
            script.debug(f"路径过长，跳过: {expanded_path[:100]}...")
            return False

        path_obj = safe_path_operation(Path, expanded_path)
        if not path_obj:
            return False

        has_extension = len(path_obj.suffix) > 0

        # 直接路径检查
        possible_paths = []
        try:
            possible_paths = [
                project_root / expanded_path,
                project_root / expanded_path.lstrip('./\\'),
            ]
        except (ValueError, OSError):
            pass

        if not has_extension and custom_extensions:
            for ext in custom_extensions[:3]:  # 限制扩展名数量
                try:
                    possible_paths.extend([
                        project_root / (expanded_path + ext),
                    ])
                except (ValueError, OSError):
                    continue

        # 检查直接路径
        for path in possible_paths:
            try:
                if safe_path_operation(path.exists):
                    return True
            except Exception:
                continue

        # 简化的递归搜索
        try:
            path_components = [comp for comp in expanded_path.replace('\\', '/').split('/') if comp and comp != '.']

            if not path_components or len(path_components) > 10:  # 限制路径深度
                return False

            # 只搜索最后一个组件
            last_component = path_components[-1]

            # 搜索文件
            file_matches = find_all_matching_items_with_extensions(script, project_root, last_component,
                                                                   custom_extensions)
            if file_matches:
                return True

            # 搜索目录
            dir_matches = safe_find_matching_items(script, project_root, last_component, is_file=False)
            if dir_matches:
                return True

        except Exception as e:
            script.debug(f"递归搜索出错: {e}")

        return False

    except Exception as e:
        script.debug(f"验证路径存在性时出错: {e}")
        return False


def parse_config_file_for_scanning(script, config_path: str, encoding: str = 'utf-8') -> str:
    """读取配置文件内容用于扫描"""
    try:
        file_path = Path(config_path)

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        content, actual_encoding = read_config_with_encoding(script, config_path, encoding)
        script.info(f"成功读取配置文件，编码: {actual_encoding}")
        return content

    except Exception as e:
        script.error(f"解析配置文件失败: {e}")
        raise


def get_and_validate_parameters(script) -> Tuple[
    Optional[str], Optional[str], Optional[List[str]], Optional[str], Optional[List[str]], Optional[str]]:
    """获取并验证脚本参数"""
    try:
        script.debug("开始获取和验证参数")

        config_file = script.get_parameter('config_file', "D:\\TimeConfig\\FISH.data11.txt")
        project_root = script.get_parameter('project_root',
                                            "D:\\fishdev\\client\\MainProject\\Assets\\InBundle\\Character")
        path_fields_param = script.get_parameter('path_fields_param', "assetName")
        encoding = script.get_parameter('encoding', 'utf-8')
        custom_extensions_param = script.get_parameter('custom_extensions_param', ['.controller', '.prefab'])

        script.debug(f"原始参数 - config_file: {config_file}")
        script.debug(f"原始参数 - project_root: {project_root}")
        script.debug(f"原始参数 - path_fields_param: {path_fields_param}")
        script.debug(f"原始参数 - custom_extensions_param: {custom_extensions_param}")

        # 处理路径字段参数
        path_fields = []
        try:
            if isinstance(path_fields_param, str):
                path_fields = [field.strip() for field in path_fields_param.split(',') if field.strip()]
            elif isinstance(path_fields_param, (list, tuple)):
                path_fields = [str(field).strip() for field in path_fields_param if field]
            else:
                path_fields = [str(path_fields_param).strip()] if path_fields_param else []
        except Exception as e:
            script.debug(f"处理path_fields参数时出错: {e}")
            path_fields = ["assetName"]

        # 处理自定义扩展名参数
        custom_extensions = []
        try:
            if isinstance(custom_extensions_param, str):
                custom_extensions = [ext.strip() for ext in custom_extensions_param.split(',') if ext.strip()]
            elif isinstance(custom_extensions_param, (list, tuple)):
                custom_extensions = [str(ext).strip() for ext in custom_extensions_param if ext]
            else:
                custom_extensions = [str(custom_extensions_param).strip()] if custom_extensions_param else []
        except Exception as e:
            script.debug(f"处理custom_extensions参数时出错: {e}")
            custom_extensions = ['.controller', '.prefab']

        # 规范化扩展名
        normalized_extensions = []
        for ext in custom_extensions:
            if ext and isinstance(ext, str):
                ext = ext.strip()
                if ext and not ext.startswith('.'):
                    ext = '.' + ext
                if ext:
                    normalized_extensions.append(ext)

        if not normalized_extensions:
            normalized_extensions = ['.prefab', '.controller', '.asset', '.mat']

        # 验证参数
        config_file = str(config_file).strip() if config_file else None
        project_root = str(project_root).strip() if project_root else None

        if not config_file:
            return None, None, None, None, None, "配置文件路径不能为空"

        if not os.path.exists(config_file):
            return None, None, None, None, None, f"配置文件不存在: {config_file}"

        if not project_root:
            return None, None, None, None, None, "工程根目录不能为空"

        if not os.path.exists(project_root):
            return None, None, None, None, None, f"工程根目录不存在: {project_root}"

        if not path_fields:
            return None, None, None, None, None, "路径字段列表不能为空"

        script.info(f"参数验证成功 - 字段: {path_fields}, 扩展名: {normalized_extensions}")
        return config_file, project_root, path_fields, encoding, normalized_extensions, None

    except Exception as e:
        error_msg = f"获取参数时发生异常: {str(e)}"
        script.error(error_msg)
        return None, None, None, None, None, error_msg


def validate_field_items(script, field_items: List[Dict[str, Any]], project_root: Path, custom_extensions: List[str]) -> \
Tuple[int, List[Dict[str, str]]]:
    """验证字段项的路径是否存在"""
    try:
        script.info("开始验证路径...")
        missing_paths = []
        valid_count = 0
        total_items = len(field_items)

        for i, field_item in enumerate(field_items):
            try:
                if i % 10 == 0:  # 每10个项目报告一次进度
                    script.debug(f"验证进度: {i + 1}/{total_items}")

                exists = validate_path_exists(script, field_item['cleaned_value'], project_root, custom_extensions)

                if exists:
                    valid_count += 1
                else:
                    missing_paths.append({
                        'field': field_item['source_key'],
                        'value': field_item['cleaned_value'],
                        'original': field_item['original_value']
                    })

            except Exception as e:
                script.debug(f"验证路径时出错 {field_item.get('source_key', 'unknown')}: {e}")
                missing_paths.append({
                    'field': field_item.get('source_key', 'unknown'),
                    'value': field_item.get('cleaned_value', ''),
                    'original': field_item.get('original_value', '')
                })

        script.info(f"路径验证完成，有效: {valid_count}, 无效: {len(missing_paths)}")
        return valid_count, missing_paths

    except Exception as e:
        script.error(f"验证路径时发生错误: {e}")
        raise


# ==================== 主逻辑函数 ====================

def main_logic(script):
    """
    配置文件指定路径字段验证主逻辑

    Args:
        script: ScriptBase实例，提供以下方法：
            - script.get_parameter(key, default): 获取参数
            - script.debug(message): 输出调试信息
            - script.info(message): 输出普通信息
            - script.warning(message): 输出警告信息
            - script.error(message): 输出错误信息
            - script.success_result(message, data): 创建成功结果
            - script.error_result(message, error_type): 创建错误结果
    """

    script.info("配置文件路径字段验证脚本开始运行")

    # 1. 获取并验证参数
    config_file, project_root_str, path_fields, encoding, custom_extensions, param_error = get_and_validate_parameters(
        script)

    if param_error:
        return script.error_result(param_error, "ParameterError")

    # 2. 读取配置文件内容
    try:
        script.info("开始读取配置文件...")
        config_content = parse_config_file_for_scanning(script, config_file, encoding)
        script.info("配置文件读取完成")
    except Exception as e:
        error_msg = f"读取配置文件失败: {e}"
        script.error(error_msg)
        return script.error_result(error_msg, "ConfigReadError")

    # 3. 初始化工程根目录
    try:
        project_root = Path(project_root_str).resolve()
        script.info(f"工程根目录: {project_root}")
    except Exception as e:
        error_msg = f"工程根目录路径无效: {e}"
        script.error(error_msg)
        return script.error_result(error_msg, "PathError")

    # 4. 扫描所有目标字段的配置项
    try:
        script.info("开始扫描配置项...")
        all_field_items = scan_all_field_occurrences(script, config_content, path_fields)
        total_items = len(all_field_items)
        script.info(f"扫描完成，找到 {total_items} 个配置项")
    except Exception as e:
        error_msg = f"扫描配置项失败: {e}"
        script.error(error_msg)
        return script.error_result(error_msg, "ScanError")

    if total_items == 0:
        message = "未找到任何目标字段的配置项"
        return script.success_result(message, {
            'total_paths': 0,
            'valid_paths': 0,
            'invalid_paths': 0,
            'success_rate': 0,
            'missing_paths': []
        })

    # 5. 验证每个配置项的路径
    try:
        valid_count, missing_paths = validate_field_items(script, all_field_items, project_root, custom_extensions)
    except Exception as e:
        error_msg = f"验证路径时发生错误: {e}"
        script.error(error_msg)
        return script.error_result(error_msg, "ValidationError")

    # 6. 生成结果消息
    try:
        invalid_count = len(missing_paths)

        if invalid_count == 0:
            message = f"✓ 验证完成: 所有 {total_items} 个配置项的路径都存在"
        else:
            message = f"验证完成: {valid_count}/{total_items} 个路径存在，{invalid_count} 个路径不存在"

        script.info("结果消息生成完成")

    except Exception as e:
        script.error(f"生成结果消息时出错: {e}")
        message = f"验证完成: {valid_count}/{total_items} 个路径存在"

    # 7. 返回结果
    try:
        success_rate = (valid_count / total_items) * 100 if total_items > 0 else 0

        result_data = {
            'total_paths': total_items,
            'valid_paths': valid_count,
            'invalid_paths': invalid_count,
            'success_rate': success_rate,
            'missing_paths': missing_paths[:50]  # 限制返回的缺失路径数量
        }

        script.info("脚本执行完成")
        return script.success_result(message, result_data)

    except Exception as e:
        error_msg = f"构造返回结果时出错: {e}"
        script.error(error_msg)
        return script.error_result(error_msg, "ResultError")


if __name__ == '__main__':
    create_simple_script('config_field_path_validator_simple', main_logic)