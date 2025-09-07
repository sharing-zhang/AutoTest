
import os
import json
import time
import sys
from datetime import datetime

def main():
    """test2脚本主函数"""
    try:
        # 获取脚本参数
        parameters = {}
        try:
            params_str = os.environ.get('SCRIPT_PARAMETERS', '{}')
            parameters = json.loads(params_str)
        except json.JSONDecodeError:
            parameters = {}
        
        page_context = os.environ.get('PAGE_CONTEXT', 'unknown')
        script_name = os.environ.get('SCRIPT_NAME', 'test2')
        
        # 输出调试信息到stderr
        print(f"[DEBUG] test2脚本开始执行", file=sys.stderr)
        print(f"[DEBUG] 参数: {parameters}", file=sys.stderr)
        print(f"[DEBUG] 页面上下文: {page_context}", file=sys.stderr)
        
        # 模拟一些处理
        time.sleep(0.5)
        
        # 构建结果
        result = {
            'status': 'success',
            'message': '你好你好',
            'timestamp': time.time(),
            'data': {
                'script_name': script_name,
                'execution_context': page_context,
                'processed_parameters': parameters,
                'output_content': 'test2执行完成，所有print语句都已处理'
            },
            'metadata': {
                'script_name': script_name,
                'execution_time': datetime.now().isoformat(),
                'version': '1.0.0',
                'method': 'subprocess_execution'
            }
        }
        
        print(f"[DEBUG] test2执行完成，准备输出结果", file=sys.stderr)
        
        # 输出JSON结果到stdout（这是系统期望的格式）
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        # 错误处理
        error_msg = f'test2脚本执行失败: {str(e)}'
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        
        error_result = {
            'status': 'error',
            'message': f'test2执行出错: {str(e)}',
            'timestamp': time.time(),
            'script_name': os.environ.get('SCRIPT_NAME', 'test2'),
            'error_type': type(e).__name__
        }
        
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()