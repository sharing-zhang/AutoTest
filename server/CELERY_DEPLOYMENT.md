# Celery部署指南

## 概述
本项目已成功集成Celery异步任务处理框架。Celery是一个基于分布式消息传递的异步任务队列/作业队列。

## 系统要求
- Python 3.7+
- Django 3.2+
- Redis (消息代理)
- MySQL (Django数据库)

## 安装步骤

### 1. 安装依赖
```bash
cd server
pip install -r requirements.txt
```

### 2. 安装和启动Redis
```bash
# Windows (使用Chocolatey)
choco install redis-64

# 或者下载Redis for Windows
# https://github.com/microsoftarchive/redis/releases

# 启动Redis服务
redis-server
```

### 3. 数据库迁移
```bash
python manage.py makemigrations django_celery_beat
python manage.py makemigrations django_celery_results
python manage.py migrate
```

## 启动服务

### 方法一：使用Django管理命令（推荐）

1. **启动Celery Worker**
```bash
python manage.py celery_worker --loglevel=info --concurrency=4
celery -A celery_app worker --loglevel=info --pool=solo
```

2. **启动Celery Beat定时任务调度器**
```bash
python manage.py celery_beat --loglevel=info
```

### 方法二：直接使用Celery命令

1. **启动Celery Worker**
```bash
# Windows
celery -A server worker --loglevel=info --pool=solo

# Linux/Mac
celery -A server worker --loglevel=info --concurrency=4
```

2. **启动Celery Beat**
```bash
celery -A server beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 方法三：后台运行（生产环境）

1. **使用supervisord（推荐）**
```ini
# /etc/supervisor/conf.d/celery.conf
[program:celery_worker]
command=/path/to/venv/bin/celery -A server worker --loglevel=info
directory=/path/to/project/server
user=your_user
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10

[program:celery_beat]
command=/path/to/venv/bin/celery -A server beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/project/server
user=your_user
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
```

## 配置说明

### Celery设置（settings.py）
```python
# 消息代理
CELERY_BROKER_URL = 'redis://localhost:6379/0'

# 结果后端
CELERY_RESULT_BACKEND = 'django-db'

# 时区设置
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False

# 任务序列化
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
```

### 任务定义（myapp/tasks.py）
已创建以下示例任务：
- `test_task`: 测试任务
- `send_email_task`: 邮件发送任务
- `process_data_task`: 数据处理任务
- `cleanup_old_files`: 文件清理任务
- `generate_report_task`: 报告生成任务

## API接口

### 启动任务
- **测试任务**: `POST /api/celery/task/test`
- **邮件任务**: `POST /api/celery/task/email`
- **数据处理**: `POST /api/celery/task/data-process`
- **报告生成**: `POST /api/celery/task/report`

### 查询任务状态
- **任务状态**: `GET /api/celery/task/status/{task_id}`

### 请求示例

1. **启动测试任务**
```bash
curl -X POST http://localhost:8000/api/celery/task/test
```

2. **启动邮件任务**
```bash
curl -X POST http://localhost:8000/api/celery/task/email \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "测试邮件",
    "message": "这是通过Celery发送的邮件",
    "recipient_list": ["user@example.com"]
  }'
```

3. **查询任务状态**
```bash
curl http://localhost:8000/api/celery/task/status/your-task-id
```

## 监控

### Flower (Web监控界面)
```bash
pip install flower
celery -A server flower
```
访问 http://localhost:5555 查看监控界面

### Celery命令行监控
```bash
# 检查活跃任务
celery -A server inspect active

# 检查注册的任务
celery -A server inspect registered

# 检查统计信息
celery -A server inspect stats
```

## 定时任务

### 使用Django Admin管理定时任务
1. 登录Django Admin: http://localhost:8000/admin
2. 导航到 "Periodic Tasks" 部分
3. 添加新的定时任务：
   - Task: 选择要执行的任务
   - Schedule: 设置执行时间
   - Arguments: 设置任务参数

### 代码方式创建定时任务
```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

# 创建执行间隔
schedule, created = IntervalSchedule.objects.get_or_create(
    every=10,
    period=IntervalSchedule.SECONDS,
)

# 创建定时任务
PeriodicTask.objects.create(
    interval=schedule,
    name='清理旧文件',
    task='myapp.tasks.cleanup_old_files',
)
```

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 确保Redis服务正在运行
   - 检查CELERY_BROKER_URL配置

2. **任务不执行**
   - 确保Worker进程正在运行
   - 检查任务是否正确注册
   - 查看Worker日志

3. **Windows兼容性**
   - 使用 `--pool=solo` 参数
   - 考虑使用WSL或Docker

### 日志调试
```bash
# 增加日志详细程度
celery -A server worker --loglevel=debug

# 查看特定任务日志
celery -A server events
```

## 生产环境建议

1. **使用进程管理器**：supervisor、systemd
2. **负载均衡**：多个Worker进程
3. **监控告警**：集成监控系统
4. **日志轮转**：配置日志轮转策略
5. **安全配置**：Redis密码、网络安全

## 扩展功能

### 添加新任务
1. 在 `myapp/tasks.py` 中定义新任务
2. 使用 `@shared_task` 装饰器
3. 重启Worker进程

### 自定义队列
```python
# settings.py
CELERY_TASK_ROUTES = {
    'myapp.tasks.high_priority_task': {'queue': 'high_priority'},
    'myapp.tasks.low_priority_task': {'queue': 'low_priority'},
}

# 启动特定队列的Worker
celery -A server worker -Q high_priority --loglevel=info
```

## 技术支持
如遇问题，请检查：
1. Celery官方文档：https://docs.celeryproject.org/
2. Django-Celery-Beat文档：https://django-celery-beat.readthedocs.io/
3. 项目日志文件
4. Redis连接状态
