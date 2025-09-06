#!/bin/bash

echo "====================================="
echo "     AutoTest Celery 启动脚本"
echo "====================================="
echo

# 检查Redis服务
echo "检查Redis服务..."
if redis-cli ping > /dev/null 2>&1; then
    echo "[成功] Redis服务正常运行"
else
    echo "[错误] Redis服务未启动，请先启动Redis"
    echo "请运行: redis-server"
    exit 1
fi

echo
echo "执行数据库迁移..."
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results

echo
echo "选择启动模式:"
echo "1. 启动Celery Worker"
echo "2. 启动Celery Beat (定时任务调度器)"
echo "3. 启动Flower监控 (需要先安装: pip install flower)"
echo "4. 查看任务状态"
echo

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "启动Celery Worker..."
        python manage.py celery_worker --loglevel=info --concurrency=4
        ;;
    2)
        echo "启动Celery Beat..."
        python manage.py celery_beat --loglevel=info
        ;;
    3)
        echo "启动Flower监控..."
        celery -A server flower
        ;;
    4)
        echo "检查Celery状态..."
        celery -A server inspect active
        ;;
    *)
        echo "无效选择"
        ;;
esac
