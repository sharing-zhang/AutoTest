from .celery import app
import time
import json

@app.task(bind=True)
def hello_task(self):
    """打印测试任务"""
    try:
        print(f'开始执行hello_task: {self.request.id}')
        
        # 模拟一些处理过程
        time.sleep(1)
        
        message = "hello_task,我叫阿青"
        print(message)
        
        result = {
            'status': 'success',
            'message': message,
            'timestamp': time.time(),
            'task_id': self.request.id,
            'data': {
                'greeting': '你好！',
                'author': '阿青',
                'task_type': 'print_test'
            }
        }
        
        print(f'任务执行完成: {result}')
        return result
        
    except Exception as e:
        error_msg = f'任务执行失败: {str(e)}'
        print(error_msg)
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': time.time(),
            'task_id': self.request.id if hasattr(self, 'request') else 'unknown'
        }