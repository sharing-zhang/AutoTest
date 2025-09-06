"""
Celery配置文件
用于配置Django项目的异步任务处理
"""
import os
from celery import Celery

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

# 创建Celery应用实例
app = Celery('autotest',
             broker='redis://localhost:6379/0',
             backend='django-db',
             include=[
                 
                 'celery_app.print_test'
             ])

# 基本配置
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=False,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
