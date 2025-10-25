"""
AutoTest Celery配置文件
用于配置Django项目的异步任务处理系统

支持功能：
- 统一任务执行器 (execute_script_task) - 直接导入执行
- SVN差异检测任务 (svn_diff_checker_celery_task)
- 脚本模板系统集成
- 完整的任务监控和错误处理
"""
import os
from celery import Celery
from celery.signals import worker_ready, worker_shutdown

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

# 从环境变量获取配置，支持不同环境
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BACKEND = os.environ.get('CELERY_BACKEND', 'django-db')

# 创建Celery应用实例
app = Celery('autotest')

# 基础配置
app.conf.update(
    # 消息代理和结果后端
    broker_url=REDIS_URL,
    result_backend=CELERY_BACKEND,
    
    # 序列化配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 时区配置
    timezone='Asia/Shanghai',
    enable_utc=False,
    
    # 任务配置
    task_track_started=True,           # 跟踪任务开始状态
    task_acks_late=False,             # 任务开始后立即确认（避免重复执行）
    task_reject_on_worker_lost=True,  # Worker丢失时拒绝任务
    task_ignore_result=False,         # 不忽略任务结果
    
    # 时间限制配置
    task_time_limit=1200,             # 硬时间限制(20分钟)
    task_soft_time_limit=1080,       # 软时间限制(18分钟)
    task_default_retry_delay=60,     # 重试延迟(1分钟)
    task_max_retries=3,              # 最大重试次数
    
    # Worker配置 - Windows优化
    worker_pool='threads',            # Windows下使用threads池（避免prefork问题）
    worker_prefetch_multiplier=4,     # 预取任务数量（支持并发）
    worker_max_tasks_per_child=50,    # 防止内存泄漏
    worker_disable_rate_limits=False, # 启用速率限制
    worker_hijack_root_logger=False,  # 不劫持根日志器
    worker_concurrency=4,             # Worker并发数（支持4个并发任务）
    
    # 结果配置
    result_expires=3600,             # 结果过期时间(1小时)
    result_persistent=True,          # 持久化结果
    
    # 路由配置
    task_routes={
        'myapp.views.celery_views.execute_script_task': {'queue': 'script_execution'},
    },
    
    # 队列配置
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'script_execution': {
            'exchange': 'script_execution',
            'routing_key': 'script_execution',
        },
    },
    
    # 监控配置
    worker_send_task_events=True,     # 发送任务事件
    task_send_sent_event=True,       # 发送任务发送事件
    
    # 安全配置
    worker_pool_restarts=True,       # 允许Worker池重启
    worker_direct=True,              # 直接模式
)

# 包含的任务模块
app.autodiscover_tasks([
    'myapp.views.celery_views',      # 统一任务执行器（execute_script_task）
])

# 注意：不在这里明确导入任务，避免循环导入问题
# 任务会通过autodiscover_tasks自动发现和注册

# Worker信号处理
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Worker启动时的处理"""
    print("🚀 Celery Worker已启动，准备处理任务...")
    print(f"📊 配置信息:")
    print(f"   - Broker: {app.conf.broker_url}")
    print(f"   - Backend: {app.conf.result_backend}")
    print(f"   - 时区: {app.conf.timezone}")
    print(f"   - 任务时间限制: {app.conf.task_time_limit}秒")
    print(f"   - Worker最大任务数: {app.conf.worker_max_tasks_per_child}")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Worker关闭时的处理"""
    print("🛑 Celery Worker正在关闭...")

# 任务配置验证
def validate_config():
    """验证Celery配置"""
    try:
        # 测试Redis连接
        from celery import current_app
        with current_app.connection_for_read() as conn:
            conn.ensure_connection(max_retries=3)
        print("✅ Redis连接正常")
        
        # 测试Django数据库连接
        from django.db import connection
        connection.ensure_connection()
        print("✅ Django数据库连接正常")
        
        return True
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

# 如果直接运行此文件，进行配置验证
if __name__ == '__main__':
    print("🔧 验证Celery配置...")
    validate_config()
