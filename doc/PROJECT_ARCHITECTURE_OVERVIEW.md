# AutoTest 项目架构概览

## 🏗️ 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        AutoTest 自动化测试平台                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   前端 (Vue 3)   │    │   后端 (Django) │    │   任务队列 (Celery) │ │
│  │                 │    │                 │    │                 │ │
│  │ • 脚本管理界面   │    │ • REST API      │    │ • 异步任务执行   │ │
│  │ • 参数配置弹窗   │    │ • 数据模型      │    │ • 任务监控       │ │
│  │ • 执行结果展示   │    │ • 业务逻辑      │    │ • 错误处理       │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │       │
│           │                       │                       │       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   数据库 (MySQL) │    │   消息代理 (Redis) │    │   脚本执行 (subprocess) │ │
│  │                 │    │                 │    │                 │ │
│  │ • 脚本配置       │    │ • 任务队列       │    │ • Python脚本    │ │
│  │ • 执行记录       │    │ • 结果存储       │    │ • Shell脚本     │ │
│  │ • 页面配置       │    │ • 状态管理       │    │ • 环境变量传递   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 核心数据流

### 1. 脚本执行流程
```
用户点击脚本按钮
    ↓
前端组件 (ScriptManagerLayout)
    ↓
useScriptManager.executeScript()
    ↓
API调用 (ScriptExecutionViewSet.execute)
    ↓
后端验证和处理
    ↓
Celery任务队列 (execute_script_task)
    ↓
UnifiedScriptExecutor统一执行器
    ↓
subprocess执行脚本
    ↓
返回执行结果
    ↓
前端轮询状态并展示结果
```

### 2. 脚本管理流程
```
管理员配置脚本
    ↓
script_configs.json (动态脚本配置)
    ↓
sync_frontend_pages.py (同步到数据库)
    ↓
Script模型 (数据库存储)
    ↓
前端获取脚本列表
    ↓
生成脚本按钮
```

## 📁 项目结构详解

### 前端结构 (web/)
```
web/
├── src/
│   ├── components/          # 组件
│   │   ├── ScriptManagerLayout.vue    # 脚本管理布局
│   │   ├── ScriptButtons.vue          # 脚本按钮
│   │   └── DynamicScriptForm.vue      # 动态脚本表单
│   ├── composables/        # 组合式函数
│   │   └── useScriptManager.ts        # 脚本管理核心逻辑
│   ├── views/              # 页面视图
│   │   ├── scanDevUpdate.vue          # 扫描更新页面
│   │   ├── CheckReward.vue            # 检查奖励页面
│   │   └── ...
│   ├── api/                # API接口
│   │   └── scanDevUpdate.ts           # 扫描更新API
│   └── store/              # 状态管理
└── package.json            # 依赖配置
```

### 后端结构 (server/)
```
server/
├── myapp/                  # 主应用
│   ├── models.py           # 数据模型
│   ├── views/              # 视图
│   │   ├── celery_views.py             # Celery任务视图
│   │   └── page_creator.py             # 页面创建视图
│   ├── management/         # 管理命令
│   │   └── commands/
│   │       ├── script_config_manager.py    # 脚本配置管理
│   │       ├── sync_frontend_pages.py      # 前端页面同步
│   │       └── script_configs.json         # 脚本配置文件
│   └── urls.py             # URL路由
├── celery_app/             # Celery应用
│   ├── celery.py           # Celery配置
│   ├── script_base.py      # 脚本基类
│   ├── scanner_file.py     # 扫描文件脚本
│   └── ...
└── server/                 # 项目配置
    ├── settings.py          # Django设置
    └── urls.py              # 根URL配置
```

## 🎯 核心概念

### 1. 脚本类型

#### 传统脚本（暂无）
- **特点**：简单、直接、预配置
- **配置**：数据库Script模型
- **执行**：通过script_id调用
- **适用**：测试脚本、系统维护脚本

#### 动态脚本
- **特点**：复杂、灵活、参数化
- **配置**：script_configs.json
- **执行**：通过script_name调用
- **适用**：需要用户配置参数的脚本

### 2. 任务执行

#### Celery任务
- **UnifiedScriptExecutor**：统一脚本执行器类
- **特点**：使用subprocess执行脚本，支持所有类型的脚本

#### 脚本执行
- **环境变量传递**：SCRIPT_PARAMETERS、PAGE_CONTEXT等
- **超时控制**：540秒软限制，600秒硬限制
- **错误处理**：完整的异常捕获和重试机制

### 3. 关键数据模型

#### Script模型
```python
class Script(models.Model):
    name = models.CharField(max_length=200)          # 脚本名称
    description = models.TextField()                 # 脚本描述
    script_path = models.CharField(max_length=500)   # 脚本路径
    script_type = models.CharField(max_length=50)    # 脚本类型
    parameters_schema = models.JSONField()           # 参数模式
    is_active = models.BooleanField()                # 是否启用
```

#### TaskExecution模型
```python
class TaskExecution(models.Model):
    task_id = models.CharField(max_length=255)       # Celery任务ID
    script = models.ForeignKey(Script)               # 关联脚本
    user = models.ForeignKey(User)                   # 执行用户
    status = models.CharField(max_length=20)         # 执行状态
    parameters = models.JSONField()                  # 执行参数
    result = models.JSONField()                      # 执行结果
    execution_time = models.FloatField()             # 执行耗时
```

## 🔧 关键技术点

### 1. 前端脚本管理
- **useScriptManager**：核心组合式函数，管理脚本状态和执行
- **ScriptManagerLayout**：布局组件，提供脚本按钮和参数弹窗
- **DynamicScriptForm**：动态表单组件，根据配置生成参数输入

### 2. 后端任务处理
- **Celery配置**：支持环境变量、任务路由、监控等
- **任务执行**：统一的subprocess执行引擎
- **统一执行器**：UnifiedScriptExecutor支持所有脚本类型
- **DRF ViewSets**：ScriptViewSet、PageScriptConfigViewSet、TaskExecutionViewSet、ScriptExecutionViewSet
- **错误处理**：完整的重试机制和日志记录

### 3. 动态配置系统
- **script_config_manager**：配置管理器，加载和验证脚本配置
- **script_configs.json**：配置文件，定义脚本参数和UI组件
- **参数验证**：类型检查、必填验证、默认值处理

## 🚀 开发指南

### 1. 添加新脚本
1. 在`celery_app/`创建脚本文件
2. 在`script_configs.json`添加配置（可选）
3. 运行`register_scripts.py`注册脚本到数据库
4. 在页面添加脚本按钮配置

### 2. 修改现有功能
1. 理解现有代码结构
2. 确定修改范围
3. 进行修改和测试
4. 更新相关文档

### 3. 调试技巧
1. 查看Celery日志
2. 检查数据库记录
3. 分析前端网络请求
4. 使用Django调试工具

## 📊 性能考虑

### 1. 任务执行
- **并发控制**：worker_prefetch_multiplier=1
- **内存管理**：worker_max_tasks_per_child=50
- **超时控制**：避免长时间运行的任务

### 2. 数据库优化
- **索引优化**：在常用查询字段上建立索引
- **查询优化**：使用select_related和prefetch_related
- **连接池**：配置数据库连接池

### 3. 前端优化
- **组件懒加载**：按需加载组件
- **状态管理**：合理使用响应式状态
- **网络请求**：避免重复请求

## 🔒 安全考虑

### 1. 脚本执行安全
- **路径验证**：确保脚本路径安全
- **参数验证**：防止注入攻击
- **权限控制**：限制脚本执行权限

### 2. API安全
- **CSRF保护**：使用CSRF token
- **认证授权**：用户身份验证
- **输入验证**：参数类型和范围检查

### 3. 数据安全
- **敏感信息**：避免在日志中记录敏感信息
- **数据加密**：重要数据加密存储
- **访问控制**：限制数据访问权限

## 📈 扩展方向

### 1. 功能扩展
- **脚本模板**：提供更多脚本模板
- **结果可视化**：图表和报表展示
- **批量执行**：支持批量脚本执行

### 2. 技术升级
- **微服务架构**：拆分为多个服务
- **容器化部署**：使用Kubernetes
- **监控告警**：集成监控系统

### 3. 用户体验
- **移动端支持**：响应式设计
- **实时通知**：WebSocket推送
- **个性化配置**：用户自定义设置
