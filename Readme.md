# 自动化测试运行系统 (AutoTest)

> 基于 Python + Django + Vue.js + Celery开发的自动化测试运行平台系统

## 📋 项目概述

本系统是一个完整的自动化测试运行平台，采用前后端分离架构。主要功能包括资源扫描、自动化脚本执行、任务管理、日志监控等。系统支持动态脚本管理，可以通过前端界面执行各种自动化任务。

### 🎯 主要功能

- **资源扫描** - 扫描系统资源和设备信息
- **自动化脚本执行** - 支持 Python 脚本的异步执行
- **任务管理** - Celery 分布式任务队列
- **脚本管理** - 动态脚本配置和按钮布局
- **日志管理** - 操作日志、错误日志、登录日志
- **插件管理** - 可扩展的插件系统
- **系统监控** - 系统信息和性能监控

### 🏗️ 技术架构

**后端技术栈：**
- Python 3.8+
- Django 3.2.11
- Django REST Framework 3.13.0
- Celery 5.2.7 (异步任务)
- Redis (缓存和消息队列)
- MySQL 5.7+ (数据库)

**前端技术栈：**
- Vue.js 3.2.45
- Vue Router 4.1.6
- Pinia 2.0.28 (状态管理)
- Ant Design Vue 3.2.20
- Element Plus 2.11.2
- Vite 4.0.3 (构建工具)
- TypeScript 4.9.4

## 📁 项目结构

```
AutoTest/
├── server/                     # 后端代码
│   ├── myapp/                  # 主应用
│   │   ├── models.py          # 数据模型
│   │   ├── views/             # 视图控制器
│   │   ├── serializers.py     # 序列化器
│   │   ├── urls.py            # 路由配置
│   │   ├── celery_view.py     # Celery 任务
│   │   ├── management/        # Django 管理命令
│   │   └── migrations/        # 数据库迁移
│   ├── celery_app/            # Celery 配置和脚本
│   ├── server/                # Django 项目配置
│   ├── upload/                # 文件上传目录
│   ├── requirements.txt       # Python 依赖
│   └── manage.py             # Django 管理脚本
├── web/                       # 前端代码
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 公共组件
│   │   ├── composables/       # 组合式函数
│   │   ├── api/              # API 接口
│   │   ├── router/           # 路由配置
│   │   ├── store/            # 状态管理
│   │   └── utils/            # 工具函数
│   ├── public/               # 静态资源
│   ├── package.json          # 前端依赖
│   └── vite.config.ts        # Vite 配置
└── README.md                 # 项目文档
```

## 📋 详细文件说明

### 后端文件结构

#### 🗂️ server/myapp/ (主应用)

**核心文件：**

- **`models.py`** - 数据模型定义
  - `User` - 用户模型
  - `ScanDevUpdate_scanResult` - 扫描结果模型
  - `Thing` - 事物管理模型
  - `Script` - 脚本配置模型
  - `TaskExecution` - 任务执行记录模型
  - `Address` - 地址模型

- **`celery_view.py`** - Celery 异步任务
  - `execute_python_script()` - 执行 Python 脚本任务
  - `run_script()` - 脚本运行核心逻辑
  - `run_python_file()` - Python 文件执行器

- **`serializers.py`** - DRF 序列化器
  - 各模型的序列化和反序列化配置
  - API 数据格式定义

- **`urls.py`** - URL 路由配置
  - API 接口路由映射
  - 视图函数绑定

#### 🗂️ server/myapp/views/ (视图控制器)

- **`celery_views.py`** - Celery 相关视图
  - 脚本列表接口
  - 脚本执行接口
  - 任务状态查询接口
  - 页面配置管理

- **`admin/`** - 管理后台视图
  - 各种数据管理接口
  - CRUD 操作控制器

#### 🗂️ server/myapp/management/commands/ (管理命令)

- **`register_scripts.py`** - 脚本注册命令
  - 自动扫描和注册 celery_app 目录下的脚本
  - 更新数据库中的脚本配置

- **`setup_page_scripts.py`** - 页面脚本配置命令
  - 配置不同页面的脚本按钮布局
  - 管理脚本显示位置和顺序

- **`button_configs.json`** - 按钮配置文件
  - 定义各页面的按钮布局
  - 脚本与页面的映射关系

#### 🗂️ server/celery_app/ (Celery 配置)

- **`celery.py`** - Celery 应用配置
- **`__init__.py`** - 包初始化
- **各种 Python 脚本** - 具体的自动化任务脚本

#### 🗂️ server/server/ (Django 配置)

- **`settings.py`** - Django 核心配置
  - 数据库配置
  - Celery 配置
  - 中间件配置
  - 应用注册

- **`urls.py`** - 主路由配置
- **`wsgi.py`** - WSGI 部署配置
- **`asgi.py`** - ASGI 异步配置

#### 📝 部署文档

- **`CELERY_DEPLOYMENT.md`** - Celery 部署指南
- **`SCRIPT_MANAGEMENT_GUIDE.md`** - 脚本管理使用指南
- **`BUTTON_POSITION_GUIDE.md`** - 按钮位置配置指南

### 前端文件结构

#### 🗂️ web/src/views/ (页面组件)

**主要页面：**

- **`main.vue`** - 主布局页面
  - 顶部导航栏
  - 侧边菜单栏
  - 内容区域

- **`admin-login.vue`** - 管理员登录页面

- **`scanUpdate.vue`** - 资源扫描主页面
  - 包含子页面入口
  - 扫描功能概览

- **`scanDevUpdate.vue`** - 设备扫描页面
  - 设备扫描结果展示
  - 扫描数据管理
  - 脚本执行功能

- **`thing.vue`** - 自动化钓鱼页面
  - 钓鱼任务管理
  - 脚本执行界面
  - 结果查看

- **`plugin.vue`** - 插件管理页面
  - 插件列表
  - 插件配置
  - 状态管理

**日志管理页面：**
- **`login-log.vue`** - 登录日志
- **`op-log.vue`** - 操作日志
- **`error-log.vue`** - 错误日志

**系统管理页面：**
- **`sys-info.vue`** - 系统信息
- **`overview.vue`** - 概览页面

#### 🗂️ web/src/components/ (公共组件)

- **`ScriptManagerLayout.vue`** - 脚本管理布局组件
  - 统一的脚本执行界面
  - 动态按钮渲染
  - 任务状态管理

- **`ScriptButtons.vue`** - 脚本按钮组件
  - 可配置位置的按钮
  - 支持多种显示样式
  - 任务执行触发

#### 🗂️ web/src/composables/ (组合式函数)

- **`useScriptManager.ts`** - 脚本管理逻辑
  - 脚本加载和执行
  - 状态轮询
  - 错误处理

#### 🗂️ web/src/api/ (API 接口)

- **`scanDevUpdate.ts`** - 扫描相关 API
  - 扫描结果 CRUD
  - 脚本执行接口
  - 任务状态查询

- **其他 API 文件** - 各功能模块的接口定义

#### 🗂️ web/src/router/ (路由配置)

- **`index.js`** - 路由实例
- **`root.js`** - 路由表定义
  - 页面路由映射
  - 权限控制

#### 🗂️ web/src/store/ (状态管理)

- **`index.js`** - Pinia 配置
- **`constants.js`** - 常量定义
- **`modules/`** - 状态模块

#### 🗂️ web/src/utils/ (工具函数)

- **`auth.ts`** - 认证工具
- **`http/`** - HTTP 请求配置
- **`index.ts`** - 通用工具

### 配置文件

#### 前端配置

- **`package.json`** - NPM 包配置
- **`vite.config.ts`** - Vite 构建配置
- **`tsconfig.json`** - TypeScript 配置
- **`index.html`** - HTML 入口文件

#### 后端配置

- **`requirements.txt`** - Python 依赖
- **`manage.py`** - Django 管理脚本

#### 数据库

- **`autotest_db.sql`** - 数据库初始化脚本

## 🚀 快速开始

### 环境要求

- **Python 3.8+**
- **Node.js 16.14+**
- **MySQL 5.7+**
- **Redis** (用于 Celery)

### 后端部署

1. **安装 Python 依赖**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

2. **配置数据库**
   ```sql
   CREATE DATABASE IF NOT EXISTS autotest DEFAULT CHARSET utf8 COLLATE utf8_general_ci
   ```

3. **导入数据**
   ```sql
   mysql> use autotest;
   mysql> source autotest_db.sql的绝对路径;
   ```

4. **启动 Django 服务**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

5. **启动 Celery Worker** (新终端)
   ```bash
   # Windows
   start_celery.bat
   
   # Linux/Mac
   ./start_celery.sh
   ```

### 前端部署

1. **安装依赖**
   ```bash
   cd web
   npm install
   npm install element-plus --save
   ```

2. **启动开发服务器**
   ```bash
   npm run dev -- --port 8001
   ```

### 生产部署

1. **前端构建**
   ```bash
   cd web
   npm run build
   ```

2. **后端部署**
   - 配置 nginx/apache
   - 使用 gunicorn 部署 Django
   - 配置 Celery 守护进程

2. **数据库迁移**
   - # 为所有应用创建迁移
python manage.py makemigrations

    -# 为特定应用创建迁移
python manage.py makemigrations myapp

    -# 创建空迁移文件
python manage.py makemigrations --empty myapp

    -# 执行所有待处理的迁移
python manage.py migrate

    -# 执行特定应用的迁移
python manage.py migrate myapp

    -# 迁移到特定版本
python manage.py migrate myapp 0001

    -# 显示迁移计划
python manage.py showmigrations

    -# 显示特定应用的迁移状态
python manage.py showmigrations myapp

## 📖 使用指南

### 脚本管理

1. **添加新脚本**
   - 在 `server/celery_app/` 目录创建 Python 脚本
   - 使用 `@app.task(bind=True)` 装饰器
   - 运行 `python manage.py register_scripts` 注册

2. **配置页面按钮**
   - 编辑 `button_configs.json`
   - 运行 `python manage.py setup_page_scripts`

3. **执行脚本**
   - 通过前端页面点击按钮执行
   - 查看执行状态和结果

### 系统监控

- **任务监控** - 查看 Celery 任务执行状态
- **日志监控** - 查看系统运行日志
- **性能监控** - 监控系统资源使用情况

## 🔧 开发指南

### 添加新功能

1. **后端开发**
   - 在 `models.py` 中定义数据模型
   - 在 `serializers.py` 中添加序列化器
   - 在 `views/` 中创建视图
   - 在 `urls.py` 中配置路由

2. **前端开发**
   - 在 `views/` 中创建页面组件
   - 在 `api/` 中定义接口函数
   - 在 `router/` 中配置路由
   - 在 `components/` 中创建公共组件

### 代码规范

- **后端** - 遵循 PEP 8 规范
- **前端** - 使用 ESLint + Prettier
- **提交** - 使用语义化提交信息

## 🛠️ 常见问题

### 连接问题

**Q: 前端无法连接后端？**
A: 编辑 `web/src/store/constants.js`，设置正确的后端地址

**Q: Celery 任务执行失败？**
A: 检查 Redis 连接，确认 Celery Worker 正在运行

### 数据库问题

**Q: 数据库连接失败？**
A: 检查 `server/server/settings.py` 中的数据库配置

**Q: 迁移失败？**
A: 删除 `migrations/` 中的迁移文件，重新生成

### 部署问题

**Q: 前端构建失败？**
A: 检查 Node.js 版本，清除 `node_modules` 重新安装

**Q: 静态文件404？**
A: 配置 nginx 正确的静态文件路径

## 📝 更新日志

### v0.1.2 (当前版本)
- ✅ 完善脚本管理系统
- ✅ 优化前端组件架构
- ✅ 增强错误处理机制
- ✅ 添加详细的部署文档

### 计划功能
- 🔄 用户权限管理
- 🔄 API 接口文档
- 🔄 单元测试覆盖
- 🔄 Docker 容器化部署

## 👥 本地部署指南

1. 安装MySQL，Redis，配置好环境变量

2. 打开cmd，依次执行以下命令

  ·进入mysql：mysql -u root -p
  ·创建database：CREATE DATABASE IF NOT EXISTS 你的数据库名称 DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
  ·进入上述创建好的database中：use 你的数据库名称
  ·导入已有sql：source autotest_db.sql

3. 修改settings.py中的配置信息DATABASES

4. 安装依赖，虚拟环境中执行：
  ·pip install -r requirements.txt

5. server目录下启动Django服务：
python manage.py runserver 0.0.0.0:8000

6. 启动redis服务：
  ·redis-server

7. 启动celery worker：
  ·celery -A celery_app worker --loglevel=info --pool=solo

8. 启动前端

  ·安装node
  ·安装npm:
   npm install
   npm install element-plus --save
  ·运行：npm run dev -- --port 8001

> 🌟 如果这个项目对你有帮助，请给我们一个星星！