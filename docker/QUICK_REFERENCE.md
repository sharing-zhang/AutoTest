# 🚀 AutoTest Docker 快速参考

## 快速启动

### 个人开发
```bash
cd docker
# Windows: start.bat
# Linux/Mac: ./start.sh
```

### 团队协作
```bash
cd docker
# Windows: team-start.bat
# Linux/Mac: ./team-start.sh
```

### 命令行
```bash
cd docker
# 开发环境
docker-compose -f docker-compose.yml --env-file docker.env.dev up --build -d

# 生产环境
docker-compose -f docker-compose.yml --env-file docker.env.prod up --build -d
```

## 访问地址

- 🌐 前端: http://localhost
- 🔧 后端API: http://localhost/api/
- ⚙️ 管理后台: http://localhost/admin/
- 🗄️ 数据库: localhost:3306 (root/123456)
- 📦 Redis: localhost:6379

## 常用命令

### 服务管理
```bash
# 查看状态
docker-compose -f docker-compose.yml ps

# 重启服务
docker-compose -f docker-compose.yml restart

# 停止服务
docker-compose -f docker-compose.yml down

# 查看日志
docker-compose -f docker-compose.yml logs -f backend
```

### 数据库操作
```bash
# 进入数据库
docker-compose -f docker-compose.yml exec mysql mysql -u root -p

# 备份数据库
docker-compose -f docker-compose.yml exec mysql mysqldump -u root -p autotest_db > backup.sql

# 恢复数据库
docker-compose -f docker-compose.yml exec -T mysql mysql -u root -p autotest_db < backup.sql
```

### Django命令
```bash
# 数据库迁移
docker-compose -f docker-compose.yml exec backend python manage.py migrate

# 创建超级用户
docker-compose -f docker-compose.yml exec backend python manage.py createsuperuser

# 收集静态文件
docker-compose -f docker-compose.yml exec backend python manage.py collectstatic

# 运行测试
docker-compose -f docker-compose.yml exec backend python manage.py test
```

### 进入容器
```bash
# 后端容器
docker-compose -f docker-compose.yml exec backend bash

# 前端容器
docker-compose -f docker-compose.yml exec frontend sh

# 数据库容器
docker-compose -f docker-compose.yml exec mysql bash

# Redis容器
docker-compose -f docker-compose.yml exec redis sh
```

## 环境配置

### 开发环境 (docker.env.dev)
- 调试模式: 启用
- 数据库: autotest_db_dev
- Redis: DB1
- 日志级别: DEBUG

### 生产环境 (docker.env.prod)
- 调试模式: 禁用
- 数据库: autotest_db_prod
- Redis: DB0
- 日志级别: INFO
- 安全配置: 启用

## 故障排除

### 常见问题
1. **端口冲突**: 修改docker-compose.yml中的端口映射
2. **数据库连接失败**: 检查MySQL容器状态
3. **前端无法访问**: 检查Nginx配置和后端服务

### 日志查看
```bash
# 所有服务日志
docker-compose -f docker-compose.yml logs -f

# 特定服务日志
docker-compose -f docker-compose.yml logs -f backend
docker-compose -f docker-compose.yml logs -f frontend
docker-compose -f docker-compose.yml logs -f mysql
docker-compose -f docker-compose.yml logs -f redis
```

### 清理资源
```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的容器
docker container prune -f

# 清理未使用的网络
docker network prune -f

# 清理未使用的数据卷
docker volume prune -f
```

## 团队协作

### 开发流程
1. 拉取最新代码: `git pull origin main`
2. 创建功能分支: `git checkout -b feature/your-feature`
3. 启动开发环境: `./team-start.sh` (选择开发环境)
4. 开发代码
5. 运行测试: `docker-compose -f docker-compose.yml exec backend python manage.py test`
6. 提交代码: `git add . && git commit -m "feat: 描述"`
7. 推送分支: `git push origin feature/your-feature`
8. 创建Pull Request

### 代码审查
1. 拉取代码: `git checkout feature/your-feature`
2. 启动测试环境: `./team-start.sh` (选择测试环境)
3. 运行测试: `docker-compose -f docker-compose.yml exec backend python manage.py test`
4. 功能测试: 访问 http://localhost
5. 代码审查: 检查代码质量、安全性、性能

### 部署流程
1. 代码审查通过
2. 合并到主分支: `git merge feature/your-feature`
3. 备份生产数据
4. 部署到生产环境: `./team-start.sh` (选择生产环境)
5. 执行数据库迁移: `docker-compose -f docker-compose.yml exec backend python manage.py migrate`
6. 验证部署结果

## 服务架构

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │
│   (Nginx+Vue)   │◄──►│   (Django)      │
│   Port: 80      │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐
│   MySQL         │    │   Redis         │
│   Port: 3306    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Celery        │
                    │   (Worker+Beat) │
                    └─────────────────┘
```

## 联系信息

- 📖 详细文档: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- 👥 团队协作: [TEAM_COLLABORATION.md](TEAM_COLLABORATION.md)
- 🚀 部署文档: [../DOCKER_DEPLOYMENT.md](../DOCKER_DEPLOYMENT.md)

---

**提示**: 首次启动需要下载镜像和构建应用，可能需要几分钟时间。
