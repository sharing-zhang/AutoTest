# 统一脚本执行 API 架构总结

## 🎯 统一目标
将所有脚本执行相关的 API 统一到 `execute_script_unified`，消除重复和混乱的接口。

## 📋 已清理的重复 API

### 已删除的重复路由：
- ❌ `admin/celery/execute-script` → 使用 `api/execute-script/`
- ❌ `admin/celery/script-task-result` → 使用 `api/get-script-task-result/`
- ❌ `admin/celery/scripts` → 使用 DRF ViewSet `api/scripts/`
- ❌ `admin/celery/scripts/<int:script_id>` → 使用 DRF ViewSet `api/scripts/{id}/`

### 已删除的重复函数：
- ❌ `execute_script_task_legacy()` → 使用 `execute_script_unified()`
- ❌ `list_scripts()` → 使用 DRF `ScriptViewSet`
- ❌ `get_script_detail()` → 使用 DRF `ScriptViewSet`

## 🚀 统一后的 API 结构

### 1. 脚本执行 API
```
POST /api/execute-script/
```
**功能**：统一的脚本执行接口，支持所有类型的脚本
**参数**：
- `script_id` (可选): 脚本数据库ID
- `script_name` (可选): 脚本名称
- `script_path` (可选): 脚本文件路径
- `parameters`: 脚本执行参数
- `page_context`: 页面上下文

### 2. DRF ViewSet APIs
```
GET    /api/scripts/              # 获取脚本列表
POST   /api/scripts/              # 创建新脚本
GET    /api/scripts/{id}/         # 获取脚本详情
PUT    /api/scripts/{id}/         # 更新脚本
DELETE /api/scripts/{id}/         # 删除脚本

GET    /api/page-configs/        # 获取页面脚本配置
GET    /api/task-executions/      # 获取任务执行记录
POST   /api/task-executions/execute_script/  # 执行脚本（DRF版本）
GET    /api/task-executions/task_status/     # 查询任务状态
POST   /api/task-executions/{id}/cancel_task/ # 取消任务
```

### 3. 脚本配置管理 APIs
```
GET  /api/script-configs/         # 获取脚本配置信息
GET  /api/get-script-task-result/ # 获取任务执行结果
POST /api/reload-script-configs/  # 重新加载脚本配置
```

## 🔧 核心功能

### 脚本执行流程
1. **接收请求** → `execute_script_unified()`
2. **确定脚本信息** → 根据 `script_id` 或 `script_name`
3. **创建/查找 Script 记录** → 自动管理数据库记录
4. **创建 TaskExecution 记录** → 任务执行记录
5. **启动 Celery 任务** → `execute_script_task.delay()`
6. **返回任务信息** → `task_id`, `execution_id`

### 自动脚本记录管理
- 当使用 `script_name` 时，系统会自动查找或创建对应的 `Script` 记录
- 确保 `TaskExecution` 记录始终有有效的 `script` 关联
- 解决 `script_id` 为 null 的数据库约束问题

## ✅ 优势

1. **统一性**：所有脚本执行都通过同一个 API
2. **简洁性**：消除了重复的接口和函数
3. **可维护性**：减少了代码重复，便于维护
4. **功能完整**：保持了所有原有功能
5. **向后兼容**：DRF ViewSet 提供了 RESTful 接口

## 🎯 使用建议

### 前端调用示例
```javascript
// 执行脚本
const response = await fetch('/api/execute-script/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    script_name: 'check_ConfigTime',
    parameters: {
      directory: 'F:\\fish_test',
      file_names: ['TIMER_MAIN.data.txt'],
      start_time_field: 'openTime',
      end_time_field: 'endTime',
      recursive: false,
      encoding: 'UTF-16'
    },
    page_context: 'dynamic_form'
  })
});

// 查询任务状态
const statusResponse = await fetch(`/api/get-script-task-result/?task_id=${taskId}`);
```

### DRF 接口使用
```javascript
// 获取脚本列表
const scripts = await fetch('/api/scripts/');

// 获取脚本详情
const script = await fetch('/api/scripts/1/');

// 获取任务执行记录
const executions = await fetch('/api/task-executions/');
```

## 🔄 迁移指南

如果您的前端代码使用了旧的 API，请按以下方式迁移：

1. **脚本执行**：`admin/celery/execute-script` → `api/execute-script/`
2. **任务结果**：`admin/celery/script-task-result` → `api/get-script-task-result/`
3. **脚本列表**：`admin/celery/scripts` → `api/scripts/`
4. **脚本详情**：`admin/celery/scripts/{id}` → `api/scripts/{id}/`

所有功能保持不变，只是接口路径发生了变化。