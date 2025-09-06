@echo off
chcp 65001 >nul
echo =====================================
echo     AutoTest Celery 启动脚本
echo =====================================
echo.

echo 检查Redis服务...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [错误] Redis服务未启动，请先启动Redis
    echo 请运行: redis-server
    pause
    exit /b 1
)
echo [成功] Redis服务正常运行

echo.
@REM echo 执行数据库迁移...
@REM python manage.py migrate django_celery_beat
@REM python manage.py migrate django_celery_results

echo.
echo 选择启动模式:
echo 1. 启动Celery Worker
echo 2. 启动Celery Beat (定时任务调度器)
echo 3. 启动Flower监控 (需要先安装: pip install flower)
echo 4. 查看任务状态
echo.

set /p choice="请选择 (1-4): "

if "%choice%"=="1" (
    echo 启动Celery Worker...
    @REM python manage.py celery_worker --loglevel=info --concurrency=4
    conda activate autotest
    celery -A celery_app worker --loglevel=info --pool=solo
) else if "%choice%"=="2" (
    echo 启动Celery Beat...
    python manage.py celery_beat --loglevel=info
) else if "%choice%"=="3" (
    echo 启动Flower监控...
    celery -A server flower
) else if "%choice%"=="4" (
    echo 检查Celery状态...
    celery -A server inspect active
) else (
    echo 无效选择
    pause
)

pause
