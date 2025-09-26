# 👥 AutoTest 团队协作指南

## 概述

本指南专为团队协作开发设计，帮助团队成员快速搭建开发环境，规范开发流程，提高协作效率。

## 🚀 快速开始

### 新成员入职

#### 1. 环境准备
```bash
# 1. 安装Docker Desktop
# Windows: https://www.docker.com/products/docker-desktop/
# Mac: https://www.docker.com/products/docker-desktop/
# Linux: https://docs.docker.com/engine/install/

# 2. 验证安装
docker --version
docker-compose --version
```

#### 2. 项目搭建
```bash
# 1. 克隆项目
git clone <repository-url>
cd AutoTest

# 2. 进入docker目录
cd docker

# 3. 启动开发环境
# Windows用户
team-start.bat

# Linux/Mac用户
chmod +x team-start.sh
./team-start.sh
```

#### 3. 验证环境
```bash
# 访问以下地址确认环境正常
# - 前端: http://localhost
# - 后端API: http://localhost/api/
# - 管理后台: http://localhost/admin/
```

## 🏗️ 开发环境

### 环境配置

#### 开发环境 (docker.env.dev)
- **数据库**: `autotest_db_dev`
- **Redis**: 使用DB1
- **调试模式**: 启用
- **日志级别**: DEBUG
- **跨域**: 允许所有来源

#### 测试环境 (docker.env.test)
- **数据库**: `autotest_db_test`
- **Redis**: 使用DB2
- **调试模式**: 禁用
- **日志级别**: INFO
- **跨域**: 限制来源

#### 生产环境 (docker.env.prod)
- **数据库**: `autotest_db_prod`
- **Redis**: 使用DB0
- **调试模式**: 禁用
- **日志级别**: INFO
- **安全**: 启用HTTPS等安全配置

### 环境切换

```bash
# 开发环境
docker-compose -f docker-compose.yml --env-file docker.env.dev up -d

# 测试环境
docker-compose -f docker-compose.yml --env-file docker.env.test up -d

# 生产环境
docker-compose -f docker-compose.yml --env-file docker.env.prod up -d
```

## 🔄 开发流程

### 日常开发

#### 1. 开始开发
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建功能分支
git checkout -b feature/your-feature-name

# 3. 启动开发环境
cd docker
./team-start.sh
# 选择 1 (开发环境)

# 4. 开始开发
# 修改代码...
```

#### 2. 本地测试
```bash
# 1. 运行Django测试
docker-compose -f docker-compose.yml exec backend python manage.py test

# 2. 检查代码质量
docker-compose -f docker-compose.yml exec backend python -m flake8 .

# 3. 前端测试
# 访问 http://localhost 进行手动测试
```

#### 3. 提交代码
```bash
# 1. 添加修改
git add .

# 2. 提交代码
git commit -m "feat: 添加新功能描述"

# 3. 推送分支
git push origin feature/your-feature-name

# 4. 创建Pull Request
```

### 代码审查

#### 审查者操作
```bash
# 1. 拉取代码
git checkout feature/your-feature-name

# 2. 启动测试环境
cd docker
./team-start.sh
# 选择 2 (测试环境)

# 3. 运行测试
docker-compose -f docker-compose.yml exec backend python manage.py test

# 4. 功能测试
# 访问 http://localhost 测试新功能

# 5. 代码审查
# 检查代码质量、安全性、性能等
```

#### 审查要点
- [ ] 代码质量：符合团队编码规范
- [ ] 功能完整性：实现需求中的所有功能
- [ ] 测试覆盖：包含必要的单元测试
- [ ] 安全性：无安全漏洞
- [ ] 性能：无明显性能问题
- [ ] 文档：更新相关文档

### 部署流程

#### 开发环境部署
```bash
# 1. 合并到主分支
git checkout main
git merge feature/your-feature-name

# 2. 更新开发环境
cd docker
docker-compose -f docker-compose.yml --env-file docker.env.dev up --build -d

# 3. 执行数据库迁移
docker-compose -f docker-compose.yml exec backend python manage.py migrate
```

#### 生产环境部署
```bash
# 1. 备份生产数据
docker-compose -f docker-compose.yml exec mysql mysqldump -u root -p autotest_db_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 更新生产环境
docker-compose -f docker-compose.yml --env-file docker.env.prod up --build -d

# 3. 执行数据库迁移
docker-compose -f docker-compose.yml exec backend python manage.py migrate

# 4. 验证部署
# 检查服务状态和功能
```

## 🛠️ 工具和脚本

### 团队启动脚本

#### Windows用户
```bash
# 使用团队启动脚本
team-start.bat
```

#### Linux/Mac用户
```bash
# 使用团队启动脚本
./team-start.sh
```

### 常用命令

#### 服务管理
```bash
# 查看服务状态
docker-compose -f docker-compose.yml ps

# 重启服务
docker-compose -f docker-compose.yml restart

# 查看日志
docker-compose -f docker-compose.yml logs -f backend
```

#### 数据库操作
```bash
# 进入数据库
docker-compose -f docker-compose.yml exec mysql mysql -u root -p

# 备份数据库
docker-compose -f docker-compose.yml exec mysql mysqldump -u root -p autotest_db > backup.sql

# 恢复数据库
docker-compose -f docker-compose.yml exec -T mysql mysql -u root -p autotest_db < backup.sql
```

#### Django命令
```bash
# 数据库迁移
docker-compose -f docker-compose.yml exec backend python manage.py migrate

# 创建超级用户
docker-compose -f docker-compose.yml exec backend python manage.py createsuperuser

# 收集静态文件
docker-compose -f docker-compose.yml exec backend python manage.py collectstatic
```

## 📊 监控和维护

### 健康检查

#### 服务状态
```bash
# 检查所有服务状态
docker-compose -f docker-compose.yml ps

# 检查特定服务健康状态
docker inspect autotest_backend | grep Health -A 10
```

#### 资源使用
```bash
# 查看资源使用情况
docker stats

# 查看特定容器资源使用
docker stats autotest_backend autotest_frontend
```

### 日志管理

#### 查看日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.yml logs -f backend
docker-compose -f docker-compose.yml logs -f frontend
```

#### 日志分析
```bash
# 查看最近的日志
docker-compose -f docker-compose.yml logs --tail=100 backend

# 查看特定时间段的日志
docker-compose -f docker-compose.yml logs --since="2024-01-01T00:00:00" backend
```

### 定期维护

#### 清理资源
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

#### 更新镜像
```bash
# 拉取最新镜像
docker-compose -f docker-compose.yml pull

# 重新构建镜像
docker-compose -f docker-compose.yml up --build -d
```

## 🔒 安全考虑

### 环境安全

#### 开发环境
- 使用弱密码（仅开发环境）
- 启用调试模式
- 允许所有跨域请求

#### 生产环境
- 使用强密码
- 禁用调试模式
- 限制跨域请求
- 启用HTTPS
- 配置安全头

### 数据安全

#### 敏感信息
```bash
# 不要在代码中硬编码敏感信息
# 使用环境变量
DB_PASSWORD=${DB_PASSWORD}
SECRET_KEY=${SECRET_KEY}
```

#### 数据备份
```bash
# 定期备份数据库
docker-compose -f docker-compose.yml exec mysql mysqldump -u root -p autotest_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份数据卷
docker run --rm -v autotest_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_data.tar.gz -C /data .
```

## 📋 最佳实践

### 开发规范

#### 分支管理
- `main`: 主分支，用于生产环境
- `develop`: 开发分支，用于集成测试
- `feature/*`: 功能分支，用于新功能开发
- `hotfix/*`: 热修复分支，用于紧急修复

#### 提交规范
```bash
# 提交信息格式
<type>(<scope>): <description>

# 示例
feat(auth): 添加用户登录功能
fix(api): 修复API响应错误
docs(readme): 更新README文档
```

#### 代码审查
- 所有代码必须经过审查
- 审查者至少2人
- 审查通过后才能合并

### 部署规范

#### 环境隔离
- 开发环境：用于日常开发
- 测试环境：用于功能测试
- 生产环境：用于正式发布

#### 部署流程
1. 代码审查通过
2. 合并到主分支
3. 备份生产数据
4. 部署到生产环境
5. 验证部署结果

### 监控规范

#### 日志记录
- 记录所有重要操作
- 使用结构化日志
- 定期清理旧日志

#### 性能监控
- 监控服务响应时间
- 监控资源使用情况
- 设置告警阈值

## 🆘 故障排除

### 常见问题

#### 环境问题
```bash
# Docker未启动
# 解决方案：启动Docker Desktop

# 端口冲突
# 解决方案：修改docker-compose.yml中的端口映射

# 权限问题
# 解决方案：检查文件权限，使用sudo（Linux/Mac）
```

#### 服务问题
```bash
# 数据库连接失败
# 解决方案：检查MySQL容器状态，重启服务

# 前端无法访问后端
# 解决方案：检查Nginx配置，检查后端服务状态

# Celery任务不执行
# 解决方案：检查Redis连接，检查Celery Worker状态
```

### 获取帮助

#### 内部支持
- 团队群组：询问团队成员
- 技术文档：查看项目文档
- 代码审查：请求代码审查

#### 外部资源
- Docker官方文档：https://docs.docker.com/
- Django官方文档：https://docs.djangoproject.com/
- Vue.js官方文档：https://vuejs.org/guide/

## 📞 联系信息

如有问题，请联系：
- 项目负责人：[姓名] [邮箱]
- 技术负责人：[姓名] [邮箱]
- 团队群组：[群组链接]

---

**注意**: 本指南会持续更新，请定期查看最新版本。
