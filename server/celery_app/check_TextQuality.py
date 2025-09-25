#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本质量检查脚本

功能:
- 接收参数: directory(目录), file_name(文件名), field(可选，键名)
- 读取目标文件内容，按条目提取文本:
  * 若提供 field，则从形如 key="value"; 的配置块中提取对应字段值
  * 否则按行作为条目（非空行）
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


def detect_encoding(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        raw = f.read()
    res = chardet.detect(raw)
    return res['encoding'] or 'utf-8'


def read_file_text(script: ScriptBase, path: str) -> Optional[str]:
    try:
        enc = detect_encoding(path)
        with open(path, 'r', encoding=enc, errors='ignore') as f:
            return f.read()
    except Exception as e:
        script.error(f"读取文件失败: {e}")
        return None


def extract_entries(script: ScriptBase, content: str, field: Optional[str]) -> List[str]:
    entries: List[str] = []
    candidate_text_keys = { 'desc', 'description', 'text', 'title', 'name', 'label', 'tips', 'message', 'msg', 'content' }

    if field:
        # 1) 先按 key="value"; 直接匹配该字段
        pattern_key = rf'\b{re.escape(field)}\s*=\s*"([^"]+)"'
        direct = re.findall(pattern_key, content)
        if direct:
            entries.extend([m.strip() for m in direct if m and m.strip()])

        # 2) 如果没有匹配，尝试把 field 作为配置块名称，例如 progressRewards { ... };
        if not entries:
            block_pat = rf'{re.escape(field)}\s*\{{\s*([^}}]+)\s*\}};'
            blocks = re.findall(block_pat, content)
            if blocks:
                for blk in blocks:
                    # 提取所有 key="value"; 值，优先候选文本key，否则回退取所有 value
                    pairs = re.findall(r'(\w+)\s*=\s*"([^"]+)"', blk)
                    if not pairs:
                        continue
                    any_added = False
                    # 先收集候选文本字段
                    for k, v in pairs:
                        if k in candidate_text_keys and v and v.strip():
                            entries.append(v.strip())
                            any_added = True
                    # 若未找到候选文本字段，则收集所有较长的文本值
                    if not any_added:
                        for _, v in pairs:
                            if v and len(v.strip()) >= 2:
                                entries.append(v.strip())

        if not entries:
            script.warning(f"未找到与 '{field}' 相关的任何可检查条目（既非字段也非块名）")
    else:
        # 非空行作为条目
        for line in content.splitlines():
            line = line.strip()
            if line:
                entries.append(line)
    return entries


def deepseek_check(script: ScriptBase, items: List[str]) -> Dict[str, Any]:
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return {
            'error': 'DEEPSEEK_API_KEY 未设置',
            'issues': []
        }

    api_base = (os.getenv('DEEPSEEK_API_BASE') or 'https://api.deepseek.com').rstrip('/')
    # 优先使用环境变量，其次回退常见可用模型
    model_env = os.getenv('DEEPSEEK_MODEL') or 'deepseek-v3.1'
    model_candidates = [model_env, 'deepseek-chat', 'deepseek-reasoner']
    url = f"{api_base}/v1/chat/completions"

    # 将条目组装为可解析的 JSON 要求，避免逐条多次请求
    preview = items[:50]  # 限制最多50条，避免超长
    prompt = (
        "你是严格的中文文本校对助手。请对给定的多条文本逐条检查：\n"
        "- 拼写/错别字\n- 语法问题\n- 标点/格式问题\n- 简明性与可读性建议\n"
        "请输出严格的 JSON 数组，数组中每个元素包含: {index, original, issues: [string], suggestions: [string]}。"
    )
    user_content = json.dumps({
        'entries': [{ 'index': i, 'text': t } for i, t in enumerate(preview)]
    }, ensure_ascii=False)

    # 控制每条文本长度，避免提示过长导致请求无效
    def truncate_text(t: str, max_len: int = 500):
        try:
            return t if len(t) <= max_len else t[:max_len]
        except Exception:
            return t

    preview = [truncate_text(t) for t in preview]

    base_payload = {
        'messages': [
            { 'role': 'system', 'content': prompt },
            { 'role': 'user', 'content': user_content }
        ],
        'temperature': 0.2,
        'max_tokens': 1024,
        'stream': False,
        # 尝试请求严格 JSON（若服务端不支持也不影响）
        'response_format': { 'type': 'json_object' }
    }

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    last_error_text = None
    last_status = None

    try:
        data = None
        used_model = None
        for candidate in model_candidates:
            used_model = candidate
            payload = dict(base_payload, model=candidate)
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 400:
                # 记录错误并尝试下一个候选模型
                last_error_text = resp.text
                last_status = resp.status_code
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        if data is None:
            # 全部候选失败
            return {
                'checked_count': 0,
                'total_entries': len(items),
                'result': [],
                'error': f'HTTPError: {last_status} for {url}',
                'status_code': last_status,
                'response_text': (last_error_text or '')[:500]
            }
        choice = (data.get('choices') or [{}])[0]
        content = ((choice.get('message') or {}).get('content')) or ''

        # 解析模型返回的 JSON 数组
        issues: List[Dict[str, Any]] = []
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                issues = parsed
            else:
                # 尝试从混合文本中提取 JSON 数组
                m = re.search(r'\[.*?\]', content, re.S)
                if m:
                    issues = json.loads(m.group(0))
        except Exception:
            # 无法解析则以原文返回
            issues = [{
                'index': i,
                'original': t,
                'issues': ['无法解析模型输出'],
                'suggestions': [content[:500]]
            } for i, t in enumerate(preview)]

        return {
            'checked_count': len(preview),
            'total_entries': len(items),
            'result': issues,
            'model': data.get('model', used_model),
            'usage': data.get('usage', {})
        }
    except requests.HTTPError as http_err:
        status_code = getattr(http_err.response, 'status_code', None)
        resp_text = (getattr(http_err.response, 'text', '') or '')[:500]
        # 将 402 余额不足作为可识别的软失败，便于上层优雅提示并入库
        if status_code == 402:
            return {
                'checked_count': 0,
                'total_entries': len(items),
                'result': [],
                'error': 'Insufficient Balance',
                'status_code': status_code,
                'response_text': resp_text,
                'insufficient_balance': True
            }
        return {
            'checked_count': 0,
            'total_entries': len(items),
            'result': [],
            'error': f'HTTPError: {http_err}',
            'status_code': status_code,
            'response_text': resp_text
        }
    except Exception as e:
        return {
            'checked_count': 0,
            'total_entries': len(items),
            'result': [],
            'error': f'Exception: {str(e)}'
        }


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    directory = script.get_parameter('directory', r"D:\dev")
    file_name = script.get_parameter('file_name', '')
    field = script.get_parameter('field', '')

    if not directory or not file_name:
        return script.error_result('directory 与 file_name 不能为空', 'InvalidParameters')

    file_path = os.path.join(directory, file_name)
    if not os.path.exists(file_path):
        return script.error_result(f'文件不存在: {file_path}', 'FileNotFound')

    script.info(f"开始文本检查: {file_path}")
    script.info(f"抽取方式: {'字段 ' + field if field else '按行'}")

    content = read_file_text(script, file_path)
    if content is None:
        return script.error_result('读取文件失败', 'ReadError')

    entries = extract_entries(script, content, field if field else None)
    if not entries:
        return script.success_result('未找到可检查的条目', {
            'file_path': file_path,
            'extraction': 'field-as-key/field-as-block' if field else 'lines',
            'field': field,
            'entries_count': 0
        })

    start_ts = time.time()
    ds_result = deepseek_check(script, entries)
    duration = time.time() - start_ts

    # 统计存在问题的条目数（用于前端 message 展示）
    issues_list = ds_result.get('result') or []
    issues_count = 0
    try:
        for item in issues_list:
            if isinstance(item, dict):
                issues = item.get('issues') or []
                if any(str(x).strip() for x in issues):
                    issues_count += 1
    except Exception:
        pass

    return script.success_result(
        message=f"文本检查完成：共 {len(entries)} 条，分析 {ds_result.get('checked_count', 0)} 条，发现问题 {issues_count} 条",
        data={
            'file_path': file_path,
            'extraction': 'field' if field else 'lines',
            'field': field,
            'entries_count': len(entries),
            'deepseek': ds_result,
            'time_cost_sec': round(duration, 2)
        }
    )


if __name__ == '__main__':
    # 使用与前端/配置一致的脚本名，确保记录展示与筛选一致
    create_simple_script('check_TextQuality', main_logic)


