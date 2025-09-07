#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案1示例脚本 - 展示如何编写兼容的Python脚本
这个脚本演示了如何：
1. 从环境变量获取参数
2. 执行业务逻辑
3. 输出JSON格式的结果
"""

import os
import json
import time
import sys
from datetime import datetime

def get_script_parameters():
    """从环境变量获取脚本参数"""
    try:
        params_str = os.environ.get('SCRIPT_PARAMETERS', '{}')
        return json.loads(params_str)
    except json.JSONDecodeError:
        return {}

def get_page_context():
    """获取页面上下文"""
    return os.environ.get('PAGE_CONTEXT', 'unknown')

def get_script_name():
    """获取脚本名称"""
    return os.environ.get('SCRIPT_NAME', 'example_script')

def main():
    """主要业务逻辑"""
    try:
        # 获取参数
        parameters = get_script_parameters()
        page_context = get_page_context()
        script_name = get_script_name()
        
        # 打印调试信息到stderr（不会影响JSON输出）
        print(f"[DEBUG] 脚本启动: {script_name}", file=sys.stderr)
        print(f"[DEBUG] 参数: {parameters}", file=sys.stderr)
        print(f"[DEBUG] 页面上下文: {page_context}", file=sys.stderr)
        
        # 模拟一些处理时间
        processing_time = parameters.get('delay', 1)
        time.sleep(processing_time)
        
        # 执行业务逻辑
        message = parameters.get('message', 'Hello from example script!')
        multiplier = parameters.get('multiplier', 1)
        
        result_data = {
            'original_message': message,
            'repeated_message': message * multiplier,
            'processing_time': processing_time,
            'parameters_received': parameters,
            'page_context': page_context
        }
        
        # 构建标准输出格式
        output = {
            'status': 'success',
            'message': f'脚本 {script_name} 执行成功',
            'data': result_data,
            'metadata': {
                'script_name': script_name,
                'execution_time': datetime.now().isoformat(),
                'version': '1.0.0'
            }
        }
        
        # 输出JSON结果到stdout
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        # 错误处理
        error_output = {
            'status': 'error',
            'message': f'脚本执行失败: {str(e)}',
            'error_type': type(e).__name__,
            'metadata': {
                'script_name': get_script_name(),
                'execution_time': datetime.now().isoformat()
            }
        }
        
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()
