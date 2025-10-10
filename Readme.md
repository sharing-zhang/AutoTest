# AutoTest 自动化测试平台

> 基于 Python + Django + Vue.js + Celery 开发的统一脚本执行自动化测试平台

## 常用管理命令

### Django 基础命令
   ```bash
# 项目管理
python manage.py runserver 0.0.0.0:8000    # 启动开发服务器
python manage.py shell                      # 进入Django shell
python manage.py check                     # 检查项目配置
python manage.py collectstatic             # 收集静态文件
python manage.py createsuperuser           # 创建超级用户

# 数据库管理
python manage.py makemigrations            # 创建迁移文件
python manage.py migrate                   # 执行迁移
python manage.py makemigrations myapp    # 为特定应用创建迁移
python manage.py migrate myapp          # 执行特定应用的迁移
python manage.py showmigrations           # 显示迁移状态
python manage.py sqlmigrate myapp 0001    # 查看迁移SQL
python manage.py migrate --fake myapp 0001 # 标记迁移为已执行

```

## 🚀 快速开始

### 快速启动

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd AutoTest
   ```

2. **启动服务**
   ```bash
   # 后端
  cd server
  pip install -r requirements.txt
  python manage.py migrate

   启动Django服务器：
   ```bash

    python manage.py runserver 0.0.0.0:8000

  ```bash
   
   # 前端
   cd web
   npm install

   启动前端：
   ```bash

    npm run dev

  ```bash

3. **启动reids**

  redis-server

4. **启动celery**
```bash
  celery -A celery_app worker --loglevel=info --concurrency=4    # 指定并发数
  celery -A celery_app worker --loglevel=info --pool=solo        # Windows环境

5. **脚本注册**
  # 脚本管理命令,server下运行
  python manage.py register_scripts                        # 注册所有脚本到数据库
  python manage.py register_scripts --force                # 强制重新注册
  python manage.py register_scripts --script-name scanner_file  # 注册特定脚本

  # 页面脚本配置,server下运行
  python manage.py setup_page_scripts --config-file myapp/management/commands/button_configs.json

6. **访问应用**
   - 前端：http://localhost:3000
   - 后端：http://localhost:8000
   - 管理后台：http://localhost:8000/admin
