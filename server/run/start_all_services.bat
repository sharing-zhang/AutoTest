@echo off
chcp 65001 >nul
echo =====================================
echo     AutoTest 一键启动所有服务
echo =====================================
echo.

REM 切换到server目录
cd /d "D:\proj\test\AutoTest\server"

echo [1/3] 检查并启动Redis服务...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [警告] Redis服务未启动，正在尝试启动...
    start "Redis服务" cmd /k "redis-server"
    timeout /t 3 >nul
    echo [等待] 等待Redis服务启动...
    timeout /t 5 >nul
) else (
    echo [成功] Redis服务已运行
)

echo.
echo [2/3] 启动Django服务...
start "Django服务" cmd /k "cd /d D:\proj\test\AutoTest\server && call conda activate aotutest && python manage.py runserver 0.0.0.0:8000"

echo.
echo [3/3] 启动Celery Worker...
timeout /t 3 >nul
start "Celery Worker" cmd /k "cd /d D:\proj\test\AutoTest\server && conda activate aotutest && python -m celery -A celery_app worker --loglevel=info --pool=solo"

echo.
echo =====================================
echo     所有服务启动完成！
echo =====================================
echo.
echo 服务访问地址：
echo - Django管理后台: http://localhost:8000
echo - API接口: http://localhost:8000/api/
echo.
echo 按任意键关闭此窗口...
pause >nul
