#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译质量检查脚本 - 调用AI模型检查中英文翻译的正确性，给出问题列表和建议
"""

import os
import re
import json
import time
import chardet
import requests
from typing import Any, Dict, List, Optional, Tuple

from script_base import ScriptBase, create_simple_script


# ==================== 辅助函数区域 ====================

def detect_encoding(file_path: str) -> str:
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw = f.read()
    res = chardet.detect(raw)
    return res['encoding'] or 'utf-8'


def read_file_text(script: ScriptBase, path: str) -> Optional[str]:
    """读取文件内容，自动检测编码"""
    try:
        enc = detect_encoding(path)
        with open(path, 'r', encoding=enc, errors='ignore') as f:
            return f.read()
    except Exception as e:
        script.error(f"读取文件失败: {e}")
        return None


def extract_field_entries(script: ScriptBase, content: str, field: str) -> Dict[int, str]:
    """从文件内容中提取指定字段的文本条目，返回行号和内容的字典"""
    entries: Dict[int, str] = {}
    lines = content.splitlines()

    def smart_extract_quoted_text(text_content: str, context: str = "") -> Optional[str]:
        """智能提取双引号内的文本"""
        script.debug(f"尝试从以下内容提取文本: {text_content[:100]}...")

        # 方法1: 寻找 = 号后的双引号内容
        eq_pos = text_content.find('=')
        if eq_pos != -1:
            after_eq = text_content[eq_pos + 1:].strip()
            if after_eq.startswith('"'):
                # 找到起始双引号，现在寻找结束双引号
                content_start = 1
                i = content_start
                escaped = False

                while i < len(after_eq):
                    char = after_eq[i]

                    if escaped:
                        escaped = False
                    elif char == '\\':
                        escaped = True
                    elif char == '"':
                        # 检查这是否真的是结束引号
                        # 简单启发式：如果后面紧跟着结束字符，认为是结束
                        remaining = after_eq[i + 1:].strip()
                        if not remaining or remaining[0] in ',;})\n\r':
                            # 找到结束引号
                            extracted = after_eq[content_start:i]
                            # 处理转义字符
                            result = extracted.replace('\\"', '"').replace('\\\\', '\\')
                            script.debug(f"方法1成功提取: {len(result)}字符, {len(result.split())}单词")
                            return result.strip()

                    i += 1

                # 如果没找到明确的结束引号，取到字符串末尾
                extracted = after_eq[content_start:].rstrip('"')
                result = extracted.replace('\\"', '"').replace('\\\\', '\\')
                script.debug(f"方法1备用提取: {len(result)}字符")
                return result.strip()

        # 方法2: 多种正则模式尝试
        patterns = [
            (r'text\s*=\s*"([^"]*(?:"[^"]*"[^"]*)*)"', "包含双引号模式"),
            (r'text\s*=\s*"(.*?)"(?=\s*[,;})]|$)', "到结束符模式"),
            (r'=\s*"([^"]*(?:"[^"]*"[^"]*)*)"', "通用等号模式"),
            (r'"([^"]+(?:"[^"]*"[^"]*)*)"', "直接双引号模式"),
        ]

        for pattern, desc in patterns:
            try:
                match = re.search(pattern, text_content, re.DOTALL)
                if match:
                    result = match.group(1).replace('\\"', '"').replace('\\\\', '\\').strip()
                    script.debug(f"{desc}成功: {len(result)}字符, {len(result.split())}单词")
                    return result
            except Exception as e:
                script.debug(f"{desc}失败: {e}")
                continue

        script.debug("所有提取方法都失败")
        return None

    # 方法1: 直接匹配字段的键值对，记录行号
    for line_num, line in enumerate(lines, 1):
        script.debug(f"处理第{line_num}行: {line[:50]}...")

        # 匹配 key = field { ... } 格式
        pattern = rf'\w+\s*=\s*{re.escape(field)}\s*\{{\s*([^}}]+)\s*\}}'
        match = re.search(pattern, line)
        if match:
            block_content = match.group(1)
            extracted_text = smart_extract_quoted_text(block_content, f"第{line_num}行方法1")
            if extracted_text:
                entries[line_num] = extracted_text
                script.info(f"第{line_num}行方法1成功提取: {len(extracted_text.split())}单词")

        # 方法2: 匹配 field = { key = "value" } 格式
        if line_num not in entries:
            block_pattern = rf'{re.escape(field)}\s*=\s*\{{\s*([^}}]+)\s*\}}'
            block_match = re.search(block_pattern, line)
            if block_match:
                block = block_match.group(1)
                extracted_text = smart_extract_quoted_text(block, f"第{line_num}行方法2")
                if extracted_text:
                    entries[line_num] = extracted_text
                    script.info(f"第{line_num}行方法2成功提取: {len(extracted_text.split())}单词")

        # 方法3: 简单的键值对匹配
        if line_num not in entries:
            if field in line and '=' in line:
                extracted_text = smart_extract_quoted_text(line, f"第{line_num}行方法3")
                if extracted_text:
                    entries[line_num] = extracted_text
                    script.info(f"第{line_num}行方法3成功提取: {len(extracted_text.split())}单词")

    # 如果上述方法都没有结果，尝试多行匹配
    if not entries:
        script.info("尝试多行匹配...")
        full_content = '\n'.join(lines)

        # 查找包含字段的所有位置
        field_positions = []
        for match in re.finditer(re.escape(field), full_content):
            start_pos = match.start()
            line_num = full_content[:start_pos].count('\n') + 1
            field_positions.append((line_num, start_pos))

        for line_num, pos in field_positions:
            # 从字段位置开始，寻找后续的双引号内容
            context = full_content[pos:pos + 2000]  # 取后续2000字符作为上下文
            extracted_text = smart_extract_quoted_text(context, f"第{line_num}行多行匹配")
            if extracted_text:
                entries[line_num] = extracted_text
                script.info(f"第{line_num}行多行匹配成功: {len(extracted_text.split())}单词")

    script.info(f"从 {field} 字段提取到 {len(entries)} 个文本条目")

    # 详细的调试输出
    for line_num, text in entries.items():
        word_count = len(text.split())
        char_count = len(text)
        script.info(f"第{line_num}行最终结果: {word_count}个单词, {char_count}个字符")
        script.info(f"内容预览: {text[:100]}{'...' if len(text) > 100 else ''}")

        # 检查是否可能被截断
        if '"' in text and not text.endswith('"'):
            script.warning(f"第{line_num}行可能包含未正确处理的双引号")

    return entries


def align_translations(script: ScriptBase, chinese_entries: Dict[int, str],
                       english_entries: Dict[int, str]) -> List[Dict[str, Any]]:
    """对齐中英文翻译条目，按行号匹配"""
    aligned_pairs: List[Dict[str, Any]] = []

    # 按行号匹配
    common_lines = set(chinese_entries.keys()) & set(english_entries.keys())
    for line_num in sorted(common_lines):
        aligned_pairs.append({
            'line_number': line_num,
            'chinese': chinese_entries[line_num],
            'english': english_entries[line_num]
        })

    # 处理不匹配的条目
    chinese_only = set(chinese_entries.keys()) - set(english_entries.keys())
    english_only = set(english_entries.keys()) - set(chinese_entries.keys())

    if chinese_only:
        script.warning(f"仅在中文配置中存在的行号: {sorted(chinese_only)}")
    if english_only:
        script.warning(f"仅在英文配置中存在的行号: {sorted(english_only)}")

    script.info(f"成功对齐 {len(aligned_pairs)} 组翻译条目")
    return aligned_pairs


def deepseek_translation_check(script: ScriptBase, pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """调用 DeepSeek API 进行翻译质量检查"""
    api_key = "sk-8f18bde8ff294c1580ee050a2baf26b8"
    if not api_key:
        return {'error': 'DEEPSEEK_API_KEY 未设置', 'result': []}

    api_base = (os.getenv('DEEPSEEK_API_BASE') or 'https://api.deepseek.com').rstrip('/')
    url = f"{api_base}/v1/chat/completions"

    # 兼容常见模型名；优先使用外部指定
    preferred_model = os.getenv('DEEPSEEK_MODEL')
    model_candidates: List[str] = []
    if preferred_model:
        model_candidates.append(preferred_model)
    # 官方公开可用模型（按优先顺序）
    model_candidates.extend(['deepseek-chat', 'deepseek-reasoner'])

    # 限制条目数量
    preview = pairs[:20]

    prompt = (
        "你是专业的中英文翻译质量检查助手。请检查以下中英文翻译对的质量，重点关注："
        "1. 翻译准确性（意思是否正确传达）"
        "2. 语法正确性（英文语法是否正确）"
        "3. 用词适当性（是否使用合适的词汇）"
        "4. 语言自然度（是否符合英语表达习惯）"
        "5. 专业术语使用（是否准确使用行业术语）"
        "请用中文回复所有问题和建议。"
        "输出JSON数组，格式：[{\"line_number\": 行号, \"chinese\": \"中文原文\", \"english\": \"英文翻译\", "
        "\"issues\": [\"具体的翻译问题描述（中文）\"], \"suggestions\": [\"具体的修改建议（中文）\"]}]"
        "如果翻译质量良好无问题，issues和suggestions可以为空数组。"
    )

    base_payload = {
        'messages': [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': json.dumps({'translation_pairs': preview}, ensure_ascii=False)}
        ],
        'temperature': 0.2,
        'max_tokens': 8192,
        'response_format': {'type': 'json_object'}
    }

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    last_error_text: Optional[str] = None
    last_status: Optional[int] = None
    used_model: Optional[str] = None

    for candidate in model_candidates:
        used_model = candidate
        payload = dict(base_payload, model=candidate)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=90)
            if resp.status_code == 400:
                # 记录错误并尝试下一个候选模型
                last_error_text = resp.text
                last_status = resp.status_code
                script.warning(f"DeepSeek 400 错误，尝试备用模型: {candidate} -> {last_error_text[:200]}")
                continue
            resp.raise_for_status()
            data = resp.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            # 解析返回的JSON
            try:
                result = json.loads(content)
                if not isinstance(result, list):
                    # 容错：如果不是数组，尝试从文本中抓取首个JSON数组
                    array_match = re.search(r"$$\s*\{[\s\S]*\}\s*$$", content)
                    result = json.loads(array_match.group(0)) if array_match else []
            except Exception:
                result = []

            return {
                'checked_count': len(preview),
                'total_pairs': len(pairs),
                'result': result,
                'model': used_model or ''
            }
        except requests.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 402:
                    return {'error': '余额不足', 'result': []}
                last_status = e.response.status_code
                try:
                    last_error_text = e.response.text
                except Exception:
                    last_error_text = str(e)
            else:
                last_error_text = str(e)
        except Exception as e:
            last_error_text = str(e)

    # 所有候选模型均失败
    detail = f"HTTP {last_status}: {last_error_text[:300]}" if last_status else (last_error_text or '未知错误')
    return {'error': f'API请求失败: {detail}', 'result': []}


def format_translation_report(script: ScriptBase, ds_result: Dict[str, Any]) -> str:
    """格式化翻译检查报告"""
    if ds_result.get('error'):
        return f"翻译检查失败: {ds_result['error']}"

    result_list = ds_result.get('result', [])
    if not result_list:
        return "翻译检查完成，但未获得有效结果"

    lines = []
    lines.append("翻译质量检查结果：")
    lines.append("")

    # 统计信息
    total_issues = 0
    total_suggestions = 0
    items_with_issues = 0

    for idx, item in enumerate(result_list, 1):
        if not isinstance(item, dict):
            continue

        line_number = item.get('line_number', f'第{idx}行')
        chinese = item.get('chinese', '')
        english = item.get('english', '')
        issues = item.get('issues', [])
        suggestions = item.get('suggestions', [])

        # 过滤有效内容
        valid_issues = [str(x).strip() for x in issues if str(x).strip()] if isinstance(issues, list) else []
        valid_suggestions = [str(x).strip() for x in suggestions if str(x).strip()] if isinstance(suggestions,
                                                                                                  list) else []

        if valid_issues:
            items_with_issues += 1
            total_issues += len(valid_issues)
        total_suggestions += len(valid_suggestions)

        lines.append(f"【第{idx}条】行号: {line_number}")
        lines.append(f"中文: {chinese}")
        lines.append(f"英文: {english}")

        if valid_issues:
            lines.append("问题:")
            for issue in valid_issues:
                lines.append(f"  • {issue}")

        if valid_suggestions:
            lines.append("建议:")
            for suggestion in valid_suggestions:
                lines.append(f"  • {suggestion}")

        if not valid_issues and not valid_suggestions:
            lines.append("状态: 翻译质量良好，无明显问题")

        lines.append("")

    # 总体统计
    lines.append(f"共检查 {len(result_list)} 组翻译，发现 {items_with_issues} 组存在问题，")
    lines.append(f"共计 {total_issues} 个问题，给出 {total_suggestions} 条建议")

    return "\n".join(lines)


def validate_translation_parameters(script: ScriptBase, directory: str, file_name1: str,
                                    file_name2: str, field: str) -> bool:
    """验证翻译检查参数"""
    if not all([directory, file_name1, file_name2, field]):
        script.error("缺少必要参数")
        return False

    path1 = os.path.join(directory, file_name1)
    path2 = os.path.join(directory, file_name2)

    if not os.path.exists(path1):
        script.error(f"中文配置文件不存在: {path1}")
        return False

    if not os.path.exists(path2):
        script.error(f"英文配置文件不存在: {path2}")
        return False

    return True


def calculate_translation_statistics(script: ScriptBase, result_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算翻译检查统计信息"""
    if not result_list:
        return {'count': 0, 'items_with_issues': 0, 'total_issues': 0, 'total_suggestions': 0}

    items_with_issues = 0
    total_issues = 0
    total_suggestions = 0

    for item in result_list:
        if isinstance(item, dict):
            issues = item.get('issues', [])
            suggestions = item.get('suggestions', [])

            valid_issues = [str(x).strip() for x in issues if str(x).strip()] if isinstance(issues, list) else []
            valid_suggestions = [str(x).strip() for x in suggestions if str(x).strip()] if isinstance(suggestions,
                                                                                                      list) else []

            if valid_issues:
                items_with_issues += 1
                total_issues += len(valid_issues)
            total_suggestions += len(valid_suggestions)

    return {
        'count': len(result_list),
        'items_with_issues': items_with_issues,
        'total_issues': total_issues,
        'total_suggestions': total_suggestions
    }


# ==================== 主逻辑函数 ====================

def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """
    翻译质量检查主要业务逻辑函数

    Args:
        script: ScriptBase实例
    """

    # 1. 获取参数
    directory = script.get_parameter('directory', r"D:\\")
    file_name1 = script.get_parameter('file_name1', "chinese_config.txt")
    file_name2 = script.get_parameter('file_name2', "english_config.txt")
    field = script.get_parameter('field', 'description')

    script.info("开始翻译质量检查")

    # 2. 参数验证
    if not validate_translation_parameters(script, directory, file_name1, file_name2, field):
        return script.error_result('参数验证失败', 'InvalidParameters')

    chinese_path = os.path.join(directory, file_name1)
    english_path = os.path.join(directory, file_name2)

    script.info(f"中文配置文件: {chinese_path}")
    script.info(f"英文配置文件: {english_path}")
    script.info(f"检查字段: {field}")

    try:
        # 3. 读取文件内容
        chinese_content = read_file_text(script, chinese_path)
        english_content = read_file_text(script, english_path)

        if chinese_content is None or english_content is None:
            return script.error_result('读取配置文件失败', 'ReadError')

        # 4. 提取字段条目（按行号）
        chinese_entries = extract_field_entries(script, chinese_content, field)
        english_entries = extract_field_entries(script, english_content, field)

        if not chinese_entries and not english_entries:
            return script.success_result('未找到可检查的翻译条目', {
                'chinese_path': chinese_path,
                'english_path': english_path,
                'field': field,
                'pairs_count': 0
            })

        # 5. 对齐翻译条目（按行号）
        aligned_pairs = align_translations(script, chinese_entries, english_entries)

        if not aligned_pairs:
            return script.success_result('未找到匹配的翻译对', {
                'chinese_entries': len(chinese_entries),
                'english_entries': len(english_entries),
                'pairs_count': 0
            })

        # 6. 执行翻译质量检查
        script.info("调用 DeepSeek API 进行翻译检查...")
        start_time = time.time()
        ds_result = deepseek_translation_check(script, aligned_pairs)
        duration = time.time() - start_time

        # 7. 生成详细报告
        detailed_report = format_translation_report(script, ds_result)

        # 8. 统计信息
        statistics = calculate_translation_statistics(script, ds_result.get('result', []))

        script.info("翻译检查完成")

        # 9. 返回结果
        return script.success_result(
            message=detailed_report,
            data={
                'chinese_path': chinese_path,
                'english_path': english_path,
                'field': field,
                'chinese_entries_count': len(chinese_entries),
                'english_entries_count': len(english_entries),
                'aligned_pairs_count': len(aligned_pairs),
                'time_cost_sec': round(duration, 2),
                'deepseek_result': ds_result,
                'summary': {
                    'checked_count': ds_result.get('checked_count', 0),
                    'items_with_issues': statistics['items_with_issues'],
                    'total_issues': statistics['total_issues'],
                    'total_suggestions': statistics['total_suggestions']
                }
            }
        )

    except Exception as e:
        # 10. 错误处理
        script.error(f"执行失败: {e}")
        raise


if __name__ == '__main__':
    create_simple_script('check_Translation', main_logic)