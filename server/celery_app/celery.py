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
                 'myapp.views.celery_views',  # 方案1统一任务执行器 (已整合到views中)
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
    # 方案1特定配置
    task_track_started=True,  # 跟踪任务开始状态
    task_time_limit=600,      # 任务执行时间限制(10分钟)
    task_soft_time_limit=540, # 软时间限制(9分钟)
    worker_max_tasks_per_child=50,  # 防止内存泄漏
)

# 自动发现Django应用中的任务
app.autodiscover_tasks()
