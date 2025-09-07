# 动态脚本系统使用指南

## 概述

动态脚本系统通过JSON配置文件来管理脚本的参数和前端组件，实现用户在前端输入参数并执行脚本的功能。

## 系统架构

```
前端 Vue 组件 (DynamicScriptForm.vue)
    ↓
后端 API (celery_views.py)
    ↓
配置管理器 (script_config_manager.py)
    ↓
JSON配置文件 (script_configs.json)
    ↓
脚本执行 (celery_app/*.py)
```

## 配置文件格式

### 基本格式

```json
{
  "script_name.py": [
    {
      "name": "参数名",
      "type": "组件类型",
      "label": "显示标签",
      "required": true/false,
      "default": "默认值",
      "placeholder": "占位符文本",
      "options": ["选项1", "选项2"],
      "multiple": true/false,
      "min": 最小值,
      "max": 最大值
    }
  ]
}
```

### 支持的组件类型

1. **text** - 文本输入框
```json
{
  "name": "directory",
  "type": "text",
  "label": "目录路径",
  "required": true,
  "default": "C:\\temp",
  "placeholder": "请输入目录路径"
}
```

2. **number** - 数字输入框
```json
{
  "name": "max_depth",
  "type": "number",
  "label": "最大深度",
  "required": false,
  "default": 3,
  "min": 0,
  "max": 10
}
```

3. **switch** - 开关
```json
{
  "name": "recursive",
  "type": "switch",
  "label": "递归扫描",
  "required": false,
  "default": true
}
```

4. **select** - 下拉选择
```json
{
  "name": "output_format",
  "type": "select",
  "label": "输出格式",
  "options": ["list", "detailed", "tree"],
  "required": false,
  "default": "list"
}
```

5. **checkbox** - 多选框
```json
{
  "name": "file_extensions",
  "type": "checkbox",
  "label": "文件后缀名",
  "options": [".txt", ".log", ".json"],
  "required": false,
  "multiple": true,
  "default": [".txt", ".log"]
}
```

## 脚本开发规范

### 使用脚本基础库

所有脚本应该继承 `script_base.py` 提供的基础功能：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from script_base import ScriptBase, create_simple_script

def main_logic(script: ScriptBase):
    # 获取参数
    param1 = script.get_parameter('param1', '默认值')
    param2 = script.get_parameter('param2', False)
    
    # 输出日志
    script.info(f"开始处理，参数1: {param1}")
    
    # 处理逻辑
    try:
        # 你的业务逻辑
        result_data = {
            'message': '处理成功',
            'data': {}
        }
        
        return script.success_result("处理完成", result_data)
    except Exception as e:
        return script.error_result(f"处理失败: {str(e)}")

if __name__ == '__main__':
    create_simple_script('script_name', main_logic)
```

### 参数获取

```python
# 基本参数获取
value = script.get_parameter('parameter_name', 'default_value')

# 不同类型的参数处理
text_value = script.get_parameter('text_param', '')
number_value = script.get_parameter('number_param', 0)
bool_value = script.get_parameter('switch_param', False)
list_value = script.get_parameter('checkbox_param', [])
```

### 结果返回

```python
# 成功结果
return script.success_result("操作成功", {
    'processed_files': file_list,
    'total_count': len(file_list),
    'statistics': stats_data
})

# 错误结果
return script.error_result("操作失败：文件不存在", "FileNotFound")
```

## API 接口

### 1. 获取脚本配置列表
```
GET /api/script-configs/
```

响应：
```json
{
  "success": true,
  "scripts": [
    {
      "script_name": "test_script.py",
      "display_name": "Test Script",
      "parameter_count": 3,
      "has_required_params": true
    }
  ],
  "total_count": 1
}
```

### 2. 获取单个脚本配置
```
GET /api/script-configs/?script_name=test_script.py
```

响应：
```json
{
  "success": true,
  "script_config": {
    "script_name": "test_script.py",
    "parameters": [...],
    "form_layout": {...}
  }
}
```

### 3. 执行动态脚本
```
POST /api/execute-dynamic-script/
Content-Type: application/json

{
  "script_name": "test_script.py",
  "parameters": {
    "dir_path": "C:\\temp",
    "suffixes": [".py", ".txt"],
    "confirm": true
  },
  "page_context": "dynamic_form"
}
```

响应：
```json
{
  "success": true,
  "task_id": "task-uuid",
  "execution_id": 123,
  "script_name": "test_script.py",
  "validated_parameters": {...},
  "message": "动态脚本已启动执行",
  "status": "PENDING"
}
```

### 4. 查询执行结果
```
GET /api/get-script-task-result/?task_id=task-uuid&execution_id=123
```

响应：
```json
{
  "code": 200,
  "task_id": "task-uuid",
  "execution_id": 123,
  "status": "SUCCESS",
  "ready": true,
  "success": true,
  "result": {
    "status": "success",
    "message": "处理完成",
    "data": {...}
  }
}
```

### 5. 重新加载配置
```
POST /api/reload-script-configs/
```

响应：
```json
{
  "success": true,
  "message": "脚本配置已重新加载",
  "total_scripts": 4
}
```

## 前端组件使用

### 基本用法

```vue
<template>
  <DynamicScriptForm
    :show-script-selector="true"
    :show-advanced="true"
    @script-executed="handleScriptExecuted"
    @script-changed="handleScriptChanged"
  />
</template>

<script setup>
import DynamicScriptForm from '/@/components/DynamicScriptForm.vue'

const handleScriptExecuted = (result) => {
  console.log('脚本执行结果:', result)
}

const handleScriptChanged = (scriptName) => {
  console.log('选择的脚本:', scriptName)
}
</script>
```

### 指定特定脚本

```vue
<DynamicScriptForm
  script-name="test_script.py"
  :show-script-selector="false"
/>
```

### 组件属性

- `scriptName`: 指定要加载的脚本名称
- `showScriptSelector`: 是否显示脚本选择器
- `showAdvanced`: 是否显示高级选项
- `autoExecute`: 是否自动执行（需要确认）

### 组件事件

- `script-executed`: 脚本执行完成
- `script-changed`: 选择的脚本发生变化
- `form-updated`: 表单数据更新

## 部署步骤

### 1. 后端配置

1. 确保 `script_configs.json` 文件位于 `server/myapp/management/commands/` 目录
2. 在 Django 的 URL 配置中添加动态脚本 API 路由
3. 重启 Django 和 Celery 服务

### 2. 前端配置

1. 确保 `DynamicScriptForm.vue` 组件已正确放置
2. 在需要的页面中导入并使用组件
3. 确保 Element Plus 组件库已正确配置

### 3. 脚本配置

1. 将新的脚本文件放置在 `server/celery_app/` 目录
2. 在 `script_configs.json` 中添加相应配置
3. 调用重新加载配置 API 或重启服务

## 示例：文件扫描脚本

### 配置文件
```json
{
  "file_scanner.py": [
    {
      "name": "directory",
      "type": "text",
      "label": "目录路径",
      "required": true,
      "default": "C:\\temp",
      "placeholder": "请输入要扫描的目录路径"
    },
    {
      "name": "file_extensions",
      "type": "checkbox",
      "label": "文件后缀名",
      "options": [".txt", ".log", ".json", ".csv", ".py"],
      "required": false,
      "multiple": true,
      "default": [".txt", ".log"]
    },
    {
      "name": "recursive",
      "type": "switch",
      "label": "递归扫描",
      "required": false,
      "default": true
    }
  ]
}
```

### 脚本实现
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from script_base import ScriptBase, create_simple_script

def scan_files(script: ScriptBase):
    directory = script.get_parameter('directory', '')
    extensions = script.get_parameter('file_extensions', [])
    recursive = script.get_parameter('recursive', True)
    
    if not os.path.exists(directory):
        return script.error_result(f"目录不存在: {directory}")
    
    found_files = []
    # 扫描逻辑...
    
    return script.success_result(
        f"扫描完成，找到 {len(found_files)} 个文件",
        {'files': found_files}
    )

if __name__ == '__main__':
    create_simple_script('file_scanner', scan_files)
```

## 故障排除

### 常见问题

1. **脚本配置不生效**
   - 检查 JSON 格式是否正确
   - 调用重新加载配置 API
   - 检查文件路径和权限

2. **脚本执行失败**
   - 查看 Celery 日志
   - 检查脚本文件是否存在
   - 验证参数类型和值

3. **前端组件不显示**
   - 检查 API 接口是否正常
   - 确认组件导入路径
   - 查看浏览器控制台错误

### 调试方法

1. **后端调试**
```bash
# 查看 Celery 日志
celery -A celery worker --loglevel=info

# 测试 API 接口
curl -X GET "http://localhost:8000/api/script-configs/"
```

2. **前端调试**
```javascript
// 在浏览器控制台测试 API
fetch('/api/script-configs/')
  .then(r => r.json())
  .then(console.log)
```

## 扩展功能

### 自定义组件类型

可以通过修改 `DynamicScriptForm.vue` 添加新的组件类型：

```vue
<!-- 日期选择器示例 -->
<el-form-item 
  v-else-if="param.type === 'date'" 
  :label="param.label" 
  :prop="param.name"
>
  <el-date-picker
    v-model="formData[param.name]"
    type="date"
    placeholder="选择日期"
  />
</el-form-item>
```

### 参数验证增强

在 `script_config_manager.py` 中添加更复杂的验证逻辑：

```python
def _validate_parameter_value(self, param_config, value):
    # 添加自定义验证规则
    if param_config.get('custom_validation'):
        # 实现自定义验证逻辑
        pass
    
    return super()._validate_parameter_value(param_config, value)
```

这个动态脚本系统提供了一个灵活、可扩展的框架，让您可以快速创建和部署新的脚本功能，而无需修改前端代码。
