#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本质量检查脚本

功能:
- 接收参数: directory(目录), file_name(文件名), field(可选，键名)
- 读取目标文件内容，按条目提取文本
- 调用 DeepSeek Chat Completions API，对条目进行语法/错别字等文本问题分析
- 返回包含每条目的问题列表与建议

环境变量:
- DEEPSEEK_API_KEY (必填)
- DEEPSEEK_API_BASE (可选，默认 https://api.deepseek.com)
- DEEPSEEK_MODEL    (可选，默认 deepseek-v3.1)
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


def deepseek_check(script: ScriptBase, items: List[str]) -> Dict[str, Any]:
    """调用 DeepSeek API 进行文本质量检查"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
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

    # 限制条目数量和长度
    preview = items[:30]
    preview = [t[:300] if len(t) > 300 else t for t in preview]

    prompt = (
        "你是中文文本校对助手。检查以下文本的：拼写错误、语法问题、标点问题。"
        "输出JSON数组，格式：[{\"index\": 0, \"original\": \"原文\", \"issues\": [\"问题1\"], \"suggestions\": [\"建议1\"]}]"
    )

    base_payload = {
        'messages': [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': json.dumps({'entries': [
                {'index': i, 'text': t} for i, t in enumerate(preview)
            ]}, ensure_ascii=False)}
        ],
        'temperature': 0.2,
        'max_tokens': 1024,
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
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
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

            return {
                'checked_count': len(preview),
                'total_entries': len(items),
                'result': issues,
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

    lines.append("文本质量检查结果：")
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
    lines.append(f"共检查 {checked_count} 条文本，发现 {problem_count} 个问题，给出 {suggestion_count} 条建议")

    return "\n".join(lines)


def validate_parameters(script: ScriptBase, directory: str, file_name: str) -> bool:
    """验证输入参数"""
    if not directory or not file_name:
        return False
    return os.path.exists(os.path.join(directory, file_name))


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
    文本质量检查主要业务逻辑函数

    Args:
        script: ScriptBase实例
    """

    # 1. 获取参数
    directory = script.get_parameter('directory', r"D:\dev")
    file_name = script.get_parameter('file_name', '')
    field = script.get_parameter('field', '')

    script.info("开始文本质量检查")

    # 2. 参数验证
    if not validate_parameters(script, directory, file_name):
        return script.error_result('参数无效或文件不存在', 'InvalidParameters')

    file_path = os.path.join(directory, file_name)
    script.info(f"目标文件: {file_path}")

    try:
        # 3. 读取文件内容
        content = read_file_text(script, file_path)
        if content is None:
            return script.error_result('读取文件失败', 'ReadError')

        # 4. 提取文本条目
        entries = extract_entries(script, content, field if field else None)
        if not entries:
            return script.success_result('未找到可检查的条目', {
                'file_path': file_path,
                'entries_count': 0
            })

        # 5. 执行质量检查
        script.info("调用 DeepSeek API 检查...")
        start_time = time.time()
        ds_result = deepseek_check(script, entries)
        duration = time.time() - start_time

        # 6. 生成详细消息（包含所有issues和suggestions）
        detailed_message = format_detailed_message(script, ds_result)

        # 7. 统计信息
        statistics = calculate_statistics(script, ds_result.get('result', []))

        script.info("检查完成")

        # 8. 返回结果
        return script.success_result(
            message=detailed_message,  # 详细消息包含所有issues和suggestions
            data={
                'file_path': file_path,
                'extraction_mode': 'field' if field else 'lines',
                'field': field,
                'entries_count': len(entries),
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
        # 9. 错误处理
        script.error(f"执行失败: {e}")
        raise


if __name__ == '__main__':
    create_simple_script('check_TextQuality', main_logic)