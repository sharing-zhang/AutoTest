# tasks.py
from celery import shared_task
from django.utils import timezone
import subprocess
import json
import os
import sys
import traceback
import importlib.util
from .models import TaskExecution, Script

@shared_task(bind=True)
def execute_python_script(self, task_execution_id, script_id, parameters, user_id, page_context):
    """执行Python脚本任务"""
    task_execution = None
    try:
        # 获取任务记录
        task_execution = TaskExecution.objects.get(id=task_execution_id)
        task_execution.status = 'STARTED'
        task_execution.save()
        
        # 获取脚本配置
        script = Script.objects.get(id=script_id)
        
        # 记录开始时间
        start_time = timezone.now()
        
        # 执行脚本
        result = run_script(script.script_path, parameters, page_context)
        
        # 计算执行时间
        execution_time = (timezone.now() - start_time).total_seconds()
        
        # 更新任务状态
        task_execution.status = 'SUCCESS'
        task_execution.result = result
        task_execution.execution_time = execution_time
        task_execution.completed_at = timezone.now()
        task_execution.save()
        
        return {
            'status': 'success',
            'result': result,
            'execution_time': execution_time
        }
        
    except Exception as exc:
        error_message = str(exc)
        error_traceback = traceback.format_exc()
        
        if task_execution:
            task_execution.status = 'FAILURE'
            task_execution.error_message = f"{error_message}\n\n{error_traceback}"
            task_execution.completed_at = timezone.now()
            task_execution.save()
        
        # 重试机制
        if self.request.retries < 3:
            raise self.retry(exc=exc, countdown=60, max_retries=3)
        
        return {
            'status': 'error',
            'error': error_message,
            'traceback': error_traceback
        }

def run_script(script_path, parameters, page_context):
    """运行脚本的核心逻辑"""
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"脚本文件不存在: {script_path}")
    
    # 方式1: 通过subprocess运行脚本
    if script_path.endswith('.py'):
        return run_python_file(script_path, parameters, page_context)
    else:
        raise ValueError("不支持的脚本类型")

def run_python_file(script_path, parameters, page_context):
    """运行Python文件"""
    # 准备环境变量
    env = os.environ.copy()
    env['SCRIPT_PARAMETERS'] = json.dumps(parameters)
    env['PAGE_CONTEXT'] = page_context
    
    # 执行脚本
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,  # 5分钟超时
            cwd=os.path.dirname(script_path)
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"脚本执行失败: {result.stderr}")
        
        # 尝试解析JSON输出
        try:
            output_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            # 如果不是JSON，就作为普通文本处理
            output_data = {
                'type': 'text',
                'content': result.stdout,
                'stderr': result.stderr
            }
        
        return output_data
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("脚本执行超时")