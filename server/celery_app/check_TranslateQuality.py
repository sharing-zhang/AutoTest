#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本翻译质量检查脚本 - 调用AI模型检查两个文件中指定字段的翻译质量，给出问题列表和建议
"""

import os
import re
import json
import time
import chardet
import requests
from typing import Any, Dict, List, Optional

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


def extract_entries(script: ScriptBase, content: str, field: Optional[str]) -> List[str]:
    """从文件内容中提取待检查的文本条目"""
    entries: List[str] = []
    candidate_keys = {'desc', 'description', 'text', 'title', 'name', 'label', 'tips', 'message', 'msg', 'content'}

    if field:
        # 直接匹配字段
        pattern = rf'\b{re.escape(field)}\s*=\s*"([^"]+)"'
        matches = re.findall(pattern, content)
        if matches:
            entries.extend([m.strip() for m in matches if m.strip()])

        # 作为配置块名称匹配
        if not entries:
            block_pattern = rf'{re.escape(field)}\s*\{{\s*([^}}]+)\s*\}};'
            blocks = re.findall(block_pattern, content)
            for block in blocks:
                pairs = re.findall(r'(\w+)\s*=\s*"([^"]+)"', block)
                for k, v in pairs:
                    if (k in candidate_keys or not entries) and v.strip():
                        entries.append(v.strip())
    else:
        # 按行提取
        for line in content.splitlines():
            line = line.strip()
            if line:
                entries.append(line)

    script.info(f"提取到 {len(entries)} 个文本条目")
    return entries


def deepseek_check(script: ScriptBase, items: List[str], language_check: str = "中英翻译检查") -> Dict[str, Any]:
    """调用 DeepSeek API 进行文本质量检查"""

    # api_key = os.getenv('DEEPSEEK_API_KEY')
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

    # 定义headers
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # 分批处理：每批处理5个条目，避免API限制
    batch_size = 5
    all_results = []
    total_checked = 0
    
    script.info(f"开始分批处理 {len(items)} 个条目，每批 {batch_size} 个")
    
    for i in range(0, len(items), batch_size):
        batch_items = items[i:i + batch_size]
        batch_preview = [t[:200] if len(t) > 200 else t for t in batch_items]
        
        script.info(f"处理第 {i//batch_size + 1} 批，条目 {i+1}-{min(i+batch_size, len(items))}")
        
        batch_result = _process_batch(script, url, headers, model_candidates, batch_preview, i, language_check)
        if batch_result:
            all_results.extend(batch_result)
            total_checked += len(batch_preview)
        else:
            script.warning(f"第 {i//batch_size + 1} 批处理失败")
    
    return {
        'checked_count': total_checked,
        'total_entries': len(items),
        'result': all_results,
        'model': 'deepseek-chat'  # 使用第一个成功的模型
    }


def _process_batch(script: ScriptBase, url: str, headers: dict, model_candidates: List[str], 
                  batch_items: List[str], start_index: int, language_check: str = "中英翻译检查") -> List[Dict[str, Any]]:
    """处理一批条目"""
    
    # 根据语言检查类型生成不同的提示词
    if language_check == "中英翻译检查":
        prompt = (
            "你是专业的中英文翻译质量检查助手。请检查以下文本对的翻译质量，重点关注："
            "1. 翻译准确性：中文原文和英文译文的意思是否一致"
            "2. 语言流畅性：英文译文是否符合英语的表达习惯"
            "3. 术语一致性：专业术语翻译是否统一"
            "4. 文化适应性：英文译文是否适合英语文化背景"
            "5. 语法正确性：英文译文语法是否正确"
            "输出JSON数组，格式：[{\"index\": 0, \"original\": \"原文\", \"issues\": [\"问题1\"], \"suggestions\": [\"建议1\"]}]"
        )
    elif language_check == "中日翻译检查":
        prompt = (
            "你是专业的中日文翻译质量检查助手。请检查以下文本对的翻译质量，重点关注："
            "1. 翻译准确性：中文原文和日文译文的意思是否一致"
            "2. 语言流畅性：日文译文是否符合日语的表达习惯"
            "3. 术语一致性：专业术语翻译是否统一"
            "4. 文化适应性：日文译文是否适合日本文化背景"
            "5. 语法正确性：日文译文语法是否正确"
            "6. 敬语使用：日文敬语使用是否恰当"
            "输出JSON数组，格式：[{\"index\": 0, \"original\": \"原文\", \"issues\": [\"问题1\"], \"suggestions\": [\"建议1\"]}]"
        )
    elif language_check == "中韩翻译检查":
        prompt = (
            "你是专业的中韩文翻译质量检查助手。请检查以下文本对的翻译质量，重点关注："
            "1. 翻译准确性：中文原文和韩文译文的意思是否一致"
            "2. 语言流畅性：韩文译文是否符合韩语的表达习惯"
            "3. 术语一致性：专业术语翻译是否统一"
            "4. 文化适应性：韩文译文是否适合韩国文化背景"
            "5. 语法正确性：韩文译文语法是否正确"
            "6. 敬语使用：韩文敬语使用是否恰当"
            "输出JSON数组，格式：[{\"index\": 0, \"original\": \"原文\", \"issues\": [\"问题1\"], \"suggestions\": [\"建议1\"]}]"
        )
    else:
        prompt = (
            "你是专业的翻译质量检查助手。请检查以下文本对的翻译质量，重点关注："
            "1. 翻译准确性：原文和译文的意思是否一致"
            "2. 语言流畅性：译文是否符合目标语言的表达习惯"
            "3. 术语一致性：专业术语翻译是否统一"
            "4. 文化适应性：译文是否适合目标语言的文化背景"
            "5. 语法正确性：译文语法是否正确"
            "输出JSON数组，格式：[{\"index\": 0, \"original\": \"原文\", \"issues\": [\"问题1\"], \"suggestions\": [\"建议1\"]}]"
        )

    base_payload = {
        'messages': [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': json.dumps({'entries': [
                {'index': i + start_index, 'text': t} for i, t in enumerate(batch_items)
            ]}, ensure_ascii=False)}
        ],
        'temperature': 0.2,
        'max_tokens': 8192,  # 增加token限制以处理更多结果
        'response_format': {'type': 'json_object'}
    }

    last_error_text: Optional[str] = None
    last_status: Optional[int] = None
    used_model: Optional[str] = None

    for candidate in model_candidates:
        used_model = candidate
        payload = dict(base_payload, model=candidate)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=300)
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
                issues = json.loads(content)
                if not isinstance(issues, list):
                    # 容错：如果不是数组，尝试从文本中抓取首个JSON数组
                    array_match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", content)
                    issues = json.loads(array_match.group(0)) if array_match else []
            except Exception:
                issues = []

            return issues
        except requests.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 402:
                    return []
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
    script.warning(f"批次处理失败: {last_error_text[:200] if last_error_text else '未知错误'}")
    return []


def format_detailed_message(script: ScriptBase, ds_result: Dict[str, Any]) -> str:
    """格式化详细消息，包含所有issues和suggestions"""
    if ds_result.get('error'):
        return f"检查失败: {ds_result['error']}"

    issues_list = ds_result.get('result', [])
    if not issues_list:
        return "文本检查完成，未发现任何问题"

    lines = []
    problem_count = 0
    suggestion_count = 0

    lines.append("翻译质量检查结果：")
    lines.append("")

    for idx, item in enumerate(issues_list, 1):
        if not isinstance(item, dict):
            continue

        original = item.get('original', '')
        issues = item.get('issues', [])
        suggestions = item.get('suggestions', [])

        # 过滤有效内容
        valid_issues = [str(x).strip() for x in issues if str(x).strip()]
        valid_suggestions = [str(x).strip() for x in suggestions if str(x).strip()]

        if not valid_issues and not valid_suggestions:
            continue

        lines.append(f"【第{idx}条】 {original}")

        if valid_issues:
            problem_count += len(valid_issues)
            lines.append("问题：")
            for issue in valid_issues:
                lines.append(f"  • {issue}")

        if valid_suggestions:
            suggestion_count += len(valid_suggestions)
            lines.append("建议：")
            for suggestion in valid_suggestions:
                lines.append(f"  • {suggestion}")

        lines.append("")

    # 添加统计
    checked_count = ds_result.get('checked_count', 0)
    lines.append(f"共检查 {checked_count} 对翻译文本，发现 {problem_count} 个问题，给出 {suggestion_count} 条建议")

    return "\n".join(lines)


def validate_dual_file_parameters(script: ScriptBase, directory1: str, file_name1: str, directory2: str, file_name2: str) -> bool:
    """验证双文件模式参数"""
    if not directory1 or not file_name1 or not directory2 or not file_name2:
        return False
    
    file1_path = os.path.join(directory1, file_name1)
    file2_path = os.path.join(directory2, file_name2)
    
    if not os.path.exists(file1_path):
        script.error(f"文件1不存在: {file1_path}")
        return False
    
    if not os.path.exists(file2_path):
        script.error(f"文件2不存在: {file2_path}")
        return False
    
    return True

def validate_single_file_parameters(script: ScriptBase, directory: str, file_name: str) -> bool:
    """验证单文件模式参数"""
    if not directory or not file_name:
        return False
    
    file_path = os.path.join(directory, file_name)
    
    if not os.path.exists(file_path):
        script.error(f"文件不存在: {file_path}")
        return False
    
    return True


def calculate_statistics(script: ScriptBase, issues_list: List[Dict[str, Any]]) -> Dict[str, int]:
    """计算统计信息"""
    stats = {'texts_with_issues': 0, 'total_issues': 0, 'total_suggestions': 0}

    for item in issues_list:
        if isinstance(item, dict):
            issues = [str(x).strip() for x in item.get('issues', []) if str(x).strip()]
            suggestions = [str(x).strip() for x in item.get('suggestions', []) if str(x).strip()]

            if issues:
                stats['texts_with_issues'] += 1
                stats['total_issues'] += len(issues)
            stats['total_suggestions'] += len(suggestions)

    return stats


# ==================== 主逻辑函数 ====================

def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """
    文本翻译质量检查主要业务逻辑函数

    Args:
        script: ScriptBase实例
    """

    # 1. 获取参数
    input_mode = script.get_parameter('input_mode', 'dual_file')
    language_check = script.get_parameter('language_check', '中英翻译检查')

    script.info(f"开始{language_check} - {input_mode}模式")

    # 根据输入模式选择处理方式
    if input_mode == 'dual_file':
        return process_dual_file_mode(script, language_check)
    elif input_mode == 'single_file':
        return process_single_file_mode(script, language_check)
    else:
        return script.error_result('不支持的输入模式', 'InvalidMode')


def process_dual_file_mode(script: ScriptBase, language_check: str) -> Dict[str, Any]:
    """处理双文件模式"""
    # 获取双文件模式参数
    directory1 = script.get_parameter('directory1', r"D:\\")
    file_name1 = script.get_parameter('file_name1', 'CH.txt')
    directory2 = script.get_parameter('directory2', r"D:\\")
    file_name2 = script.get_parameter('file_name2', 'Eng.txt')
    field = script.get_parameter('field', 'desc')

    # 参数验证
    if not validate_dual_file_parameters(script, directory1, file_name1, directory2, file_name2):
        return script.error_result('参数无效或文件不存在', 'InvalidParameters')

    file1_path = os.path.join(directory1, file_name1)
    file2_path = os.path.join(directory2, file_name2)
    script.info(f"目标文件1: {file1_path}")
    script.info(f"目标文件2: {file2_path}")

    try:
        # 读取两个文件内容
        content1 = read_file_text(script, file1_path)
        if content1 is None:
            return script.error_result('读取文件1失败', 'ReadError')
            
        content2 = read_file_text(script, file2_path)
        if content2 is None:
            return script.error_result('读取文件2失败', 'ReadError')

        # 提取文本条目
        entries1 = extract_entries(script, content1, field if field else None)
        entries2 = extract_entries(script, content2, field if field else None)
        
        if not entries1:
            return script.error_result('文件1中未找到可检查的条目', 'NoEntries')
            
        if not entries2:
            return script.error_result('文件2中未找到可检查的条目', 'NoEntries')

        # 合并两个文件的条目进行对比检查
        combined_entries = []
        max_len = max(len(entries1), len(entries2))
        
        for i in range(max_len):
            entry1 = entries1[i] if i < len(entries1) else ""
            entry2 = entries2[i] if i < len(entries2) else ""
            combined_entries.append(f"文件1: {entry1} | 文件2: {entry2}")

        script.info(f"合并后共 {len(combined_entries)} 个条目进行{language_check}")

        # 执行质量检查
        script.info("调用 DeepSeek API 检查...")
        start_time = time.time()
        ds_result = deepseek_check(script, combined_entries, language_check)
        duration = time.time() - start_time

        # 生成详细消息
        detailed_message = format_detailed_message(script, ds_result)

        # 统计信息
        statistics = calculate_statistics(script, ds_result.get('result', []))

        script.info("检查完成")

        # 返回结果
        return script.success_result(
            message=detailed_message,
            data={
                'input_mode': 'dual_file',
                'file1_path': file1_path,
                'file2_path': file2_path,
                'language_check': language_check,
                'extraction_mode': 'field' if field else 'lines',
                'field': field,
                'entries1_count': len(entries1),
                'entries2_count': len(entries2),
                'combined_entries_count': len(combined_entries),
                'time_cost_sec': round(duration, 2),
                'deepseek_result': ds_result,
                'summary': {
                    'analyzed_count': ds_result.get('checked_count', 0),
                    'texts_with_issues': statistics['texts_with_issues'],
                    'total_issues': statistics['total_issues'],
                    'total_suggestions': statistics['total_suggestions']
                }
            }
        )

    except Exception as e:
        script.error(f"执行失败: {e}")
        raise


def process_single_file_mode(script: ScriptBase, language_check: str) -> Dict[str, Any]:
    """处理单文件双字段模式"""
    # 获取单文件模式参数
    directory = script.get_parameter('single_directory', r"D:\\")
    file_name = script.get_parameter('single_file_name', 'config.txt')
    chinese_field = script.get_parameter('chinese_field', 'chinese_text')
    foreign_field = script.get_parameter('foreign_field', 'english_text')

    # 参数验证
    if not validate_single_file_parameters(script, directory, file_name):
        return script.error_result('参数无效或文件不存在', 'InvalidParameters')

    file_path = os.path.join(directory, file_name)
    script.info(f"目标文件: {file_path}")
    script.info(f"中文字段: {chinese_field}, 外文字段: {foreign_field}")

    try:
        # 读取文件内容
        content = read_file_text(script, file_path)
        if content is None:
            return script.error_result('读取文件失败', 'ReadError')

        # 提取中文字段条目
        chinese_entries = extract_entries(script, content, chinese_field)
        if not chinese_entries:
            return script.error_result(f'文件中未找到中文字段 {chinese_field} 的条目', 'NoChineseEntries')

        # 提取外文字段条目
        foreign_entries = extract_entries(script, content, foreign_field)
        if not foreign_entries:
            return script.error_result(f'文件中未找到外文字段 {foreign_field} 的条目', 'NoForeignEntries')

        # 合并两个字段的条目进行对比检查
        combined_entries = []
        max_len = max(len(chinese_entries), len(foreign_entries))
        
        for i in range(max_len):
            chinese_text = chinese_entries[i] if i < len(chinese_entries) else ""
            foreign_text = foreign_entries[i] if i < len(foreign_entries) else ""
            combined_entries.append(f"中文: {chinese_text} | 外文: {foreign_text}")

        script.info(f"合并后共 {len(combined_entries)} 个条目进行{language_check}")

        # 执行质量检查
        script.info("调用 DeepSeek API 检查...")
        start_time = time.time()
        ds_result = deepseek_check(script, combined_entries, language_check)
        duration = time.time() - start_time

        # 生成详细消息
        detailed_message = format_detailed_message(script, ds_result)

        # 统计信息
        statistics = calculate_statistics(script, ds_result.get('result', []))

        script.info("检查完成")

        # 返回结果
        return script.success_result(
            message=detailed_message,
            data={
                'input_mode': 'single_file',
                'file_path': file_path,
                'language_check': language_check,
                'chinese_field': chinese_field,
                'foreign_field': foreign_field,
                'chinese_entries_count': len(chinese_entries),
                'foreign_entries_count': len(foreign_entries),
                'combined_entries_count': len(combined_entries),
                'time_cost_sec': round(duration, 2),
                'deepseek_result': ds_result,
                'summary': {
                    'analyzed_count': ds_result.get('checked_count', 0),
                    'texts_with_issues': statistics['texts_with_issues'],
                    'total_issues': statistics['total_issues'],
                    'total_suggestions': statistics['total_suggestions']
                }
            }
        )

    except Exception as e:
        script.error(f"执行失败: {e}")
        raise



if __name__ == '__main__':
    create_simple_script('check_TranslateQuality', main_logic)