# AutoTest 实际架构总结

## 🎯 当前架构状态

基于对项目实际代码的深入分析，AutoTest项目已经完成了从双执行器架构到统一执行器架构的升级改造。

## 🏗️ 实际架构组件

### 1. 核心执行器

#### UnifiedScriptExecutor（统一脚本执行器）
- **位置**: `server/myapp/views/script_executor_base.py`
- **功能**: 支持所有类型脚本的统一执行
- **特点**: 
  - 继承自 `ScriptExecutorBase`
  - 支持 `script_id`、`script_name`、`script_path` 三种标识方式
  - 完整的资源监控和错误处理

#### ScriptExecutorBase（脚本执行基类）
- **功能**: 提供统一的任务状态管理、资源监控、错误处理
- **组件**:
  - `TaskExecutionManager`: 任务状态管理
  - `ResourceMonitor`: 资源使用监控
  - `ScriptExecutionResult`: 执行结果封装

### 2. Celery任务系统

#### execute_script_task（统一Celery任务）
- **位置**: `server/myapp/views/celery_views.py`
- **功能**: 统一的异步任务执行入口
- **特点**:
  - 支持重试机制（最多3次，间隔60秒）
  - 完整的错误处理和日志记录
  - 与UnifiedScriptExecutor深度集成

### 3. API接口系统

#### execute_script_unified（统一API接口）
- **路径**: `POST /api/execute-script/`
- **功能**: 统一的脚本执行API入口
- **参数支持**:
  - `script_id`: 数据库脚本ID（优先）
  - `script_name`: 脚本名称
  - `script_path`: 脚本文件路径
  - `parameters`: 执行参数
  - `page_context`: 页面上下文

#### DRF ViewSets
- **ScriptViewSet**: 脚本管理（CRUD操作）
- **PageScriptConfigViewSet**: 页面脚本配置（只读）
- **TaskExecutionViewSet**: 任务执行记录管理

### 4. 脚本基础库

#### ScriptBase（脚本基础类）
- **位置**: `server/celery_app/script_base.py`
- **功能**: 为脚本提供统一的开发接口
- **特点**:
  - 环境变量参数获取
  - 标准化的输出格式
  - 完整的错误处理机制
  - 支持 `create_simple_script` 快捷函数

### 5. 配置管理系统

#### ScriptConfigManager（脚本配置管理器）
- **位置**: `server/myapp/management/commands/script_config_manager.py`
- **功能**: 管理动态脚本的参数配置
- **特点**:
  - 支持 `script_configs.json` 配置文件
  - 参数验证和类型转换
  - 前端表单生成支持

## 🔄 实际执行流程

### 1. 前端调用
```typescript
// useScriptManager.ts
const executionData = {
  script_id: script.id,      // 数据库脚本ID（优先）
  script_name: script.name,   // 脚本名称
  parameters: getDefaultParameters(task.parameters),
  page_context: pageRoute
}

const response = await fetch('/api/execute-script/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(executionData)
})
```

### 2. 后端处理
```python
# execute_script_unified
def execute_script_unified(request):
    # 1. 解析请求参数
    # 2. 确定脚本信息（优先级：script_id > script_name+script_path > script_name）
    # 3. 创建TaskExecution记录
    # 4. 启动execute_script_task Celery任务
    # 5. 返回任务信息
```

### 3. Celery任务执行
```python
# execute_script_task
@shared_task(bind=True)
def execute_script_task(self, task_execution_id, script_info, parameters, user_id, page_context):
    # 使用UnifiedScriptExecutor执行脚本
    result = UnifiedScriptExecutor.execute_unified(
        task_execution_id, script_info, parameters, user_id, page_context
    )
    return result.to_dict()
```

### 4. 脚本实际执行
```python
# UnifiedScriptExecutor._run_script
def _run_script(self, script_path, parameters, page_context, script_name):
    # 1. 验证脚本文件存在
    # 2. 处理路径（相对路径转绝对路径）
    # 3. 根据文件类型分发执行
    # 4. 通过subprocess执行脚本
    # 5. 解析输出结果
```

## 📊 数据模型

### Script模型
```python
class Script(models.Model):
    name = models.CharField(max_length=200)           # 脚本名称
    description = models.TextField()                  # 脚本描述
    script_path = models.CharField(max_length=500)    # 脚本路径
    script_type = models.CharField(max_length=50)     # 脚本类型
    parameters_schema = models.JSONField()            # 参数模式
    visualization_config = models.JSONField()         # 可视化配置
    is_active = models.BooleanField()                 # 是否启用
```

### TaskExecution模型
```python
class TaskExecution(models.Model):
    task_id = models.CharField(max_length=255)        # Celery任务ID
    script = models.ForeignKey(Script)               # 关联脚本
    user = models.ForeignKey(User)                   # 执行用户
    status = models.CharField(max_length=20)         # 执行状态
    parameters = models.JSONField()                  # 执行参数
    result = models.JSONField()                      # 执行结果
    execution_time = models.FloatField()             # 执行耗时
    memory_usage = models.FloatField()               # 内存使用
```

### PageScriptConfig模型
```python
class PageScriptConfig(models.Model):
    page_name = models.CharField(max_length=200)     # 页面名称
    page_route = models.CharField(max_length=200)    # 页面路由
    script = models.ForeignKey(Script)               # 关联脚本
    button_text = models.CharField(max_length=100)   # 按钮文本
    button_style = models.JSONField()               # 按钮样式
    position = models.CharField(max_length=50)        # 按钮位置
    is_enabled = models.BooleanField()               # 是否启用
    display_order = models.IntegerField()            # 显示顺序
```

## 🎯 关键特性

### 1. 统一性
- 所有脚本都通过相同的执行器处理
- 统一的API接口和参数格式
- 统一的错误处理和重试机制

### 2. 灵活性
- 支持多种脚本标识方式
- 支持动态参数配置
- 支持页面级别的脚本配置

### 3. 可靠性
- 完整的任务状态管理
- 资源使用监控
- 多层错误处理机制

### 4. 可扩展性
- 模块化的架构设计
- 支持新的脚本类型
- 支持新的执行方式

## 🔧 环境变量传递

脚本执行时通过环境变量传递参数：
```python
env = os.environ.copy()
env['SCRIPT_PARAMETERS'] = json.dumps(parameters, ensure_ascii=False)
env['PAGE_CONTEXT'] = page_context
env['SCRIPT_NAME'] = script_name
env['EXECUTION_ID'] = str(timezone.now().timestamp())
```

## 📝 脚本开发规范

### 使用ScriptBase类
```python
from celery_app.script_base import create_simple_script

def main_logic(script):
    # 获取参数
    param1 = script.get_parameter('param1', 'default_value')
    
    # 执行业务逻辑
    result = process_data(param1)
    
    # 返回结果
    return script.success_result("处理完成", {'processed_count': len(result)})

if __name__ == '__main__':
    create_simple_script('my_script', main_logic)
```

### 输出格式
```json
{
  "status": "success",
  "message": "脚本执行成功！",
  "timestamp": 1698321600.123,
  "data": {
    "script_name": "my_script",
    "execution_context": "/scanDevUpdate",
    "processed_parameters": {...}
  },
  "metadata": {
    "script_name": "my_script",
    "execution_time": "2023-10-27T10:00:00Z",
    "execution_duration": 2.5,
    "version": "1.0.0",
    "method": "subprocess_execution"
  }
}
```

## 🚀 部署和配置

### 1. 数据库配置
- MySQL数据库：`autotest_db`
- 支持Django ORM和Celery结果存储

### 2. Celery配置
- Redis作为消息代理
- 支持任务路由和监控
- 配置了超时和重试机制

### 3. 前端配置
- Vue 3 + TypeScript
- 支持动态组件和状态管理
- 与后端API深度集成

## 📈 性能优化

### 1. 任务执行
- 进程隔离：使用subprocess执行脚本
- 超时控制：540秒软限制，600秒硬限制
- 资源监控：实时监控内存和CPU使用

### 2. 数据库优化
- 索引优化：在常用查询字段上建立索引
- 查询优化：使用select_related和prefetch_related
- 连接池：配置数据库连接池

### 3. 前端优化
- 组件懒加载：按需加载组件
- 状态管理：合理使用响应式状态
- 网络请求：避免重复请求

## 🔒 安全考虑

### 1. 脚本执行安全
- 路径验证：确保脚本路径安全
- 参数验证：防止注入攻击
- 权限控制：限制脚本执行权限

### 2. API安全
- CSRF保护：使用CSRF token
- 认证授权：用户身份验证
- 输入验证：参数类型和范围检查

### 3. 数据安全
- 敏感信息：避免在日志中记录敏感信息
- 数据加密：重要数据加密存储
- 访问控制：限制数据访问权限

## 📋 总结

AutoTest项目已经成功实现了统一脚本执行架构，具有以下优势：

1. **架构统一**: 消除了传统脚本和动态脚本的区分
2. **代码简化**: 减少了重复代码，提高了可维护性
3. **功能完整**: 保持了所有原有功能，同时增加了新的特性
4. **易于扩展**: 支持新脚本类型和执行方式
5. **用户友好**: 简化的API调用和配置方式

这种架构为系统的长期维护和扩展奠定了良好的基础，同时保持了系统的稳定性和兼容性。
