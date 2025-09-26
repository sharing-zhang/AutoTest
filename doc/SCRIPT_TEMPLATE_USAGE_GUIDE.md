# 脚本模板系统使用指南

## 概述

脚本模板系统提供了一个标准化的脚本开发框架，让开发者可以快速创建高质量的脚本，而无需重复实现基础功能。系统包含基础库、模板文件和实际应用示例。

## 系统架构

```
脚本开发流程：
1. 选择模板 → 2. 复制模板 → 3. 修改业务逻辑 → 4. 配置参数 → 5. 测试运行
```

## 可用的模板文件

### 1. advanced_script_template.py（高级模板）

**适用场景**：复杂的业务逻辑，需要多步骤处理

**特点**：
- 包含完整的验证、处理、报告流程
- 支持多步骤处理和数据验证
- 提供资源清理机制

**使用示例**：
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复杂脚本描述
"""

from script_base import ScriptBase, create_simple_script
from advanced_script_template import AdvancedScript

def main_logic(script: ScriptBase):
    """使用高级模板的主逻辑"""
    advanced_script = AdvancedScript(script)
    return advanced_script.run()

if __name__ == '__main__':
    create_simple_script('advanced_script_name', main_logic)
```

### 2. check_Reward_template.py（实际应用示例）

**适用场景**：文件解析、数据验证等复杂逻辑

**特点**：
- 基于模板系统重构的实际脚本
- 展示了如何处理文件解析、数据验证
- 包含编码检测、错误处理等实用功能

## 脚本基础库功能

### ScriptBase类核心方法

#### 参数管理
```python
# 获取参数（支持默认值）
param1 = script.get_parameter('param1', 'default_value')
param2 = script.get_parameter('param2', 100)
param3 = script.get_parameter('param3', False)
```

#### 日志输出
```python
# 不同级别的日志（都输出到stderr）
script.debug("调试信息")
script.info("普通信息")
script.warning("警告信息")
script.error("错误信息")
```

#### 结果返回
```python
# 成功结果
return script.success_result("操作成功", {
    'processed_files': file_list,
    'total_count': len(file_list)
})

# 错误结果
return script.error_result("操作失败：文件不存在", "FileNotFound")
```

## 开发流程

### 1. 选择模板

根据脚本复杂度选择合适的模板：
- **所有脚本**：使用 `advanced_script_template.py`（推荐）
- **学习参考**：查看 `check_Reward_template.py`

### 2. 复制模板

```bash
# 复制高级模板（推荐）
cp server/celery_app/advanced_script_template.py server/celery_app/my_new_script.py
```

### 3. 修改脚本信息

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
我的新脚本 - 描述脚本功能
"""

from script_base import create_simple_script

def main_logic(script):
    """主要业务逻辑函数"""
    # TODO: 实现你的业务逻辑
    pass

if __name__ == '__main__':
    create_simple_script('my_new_script', main_logic)  # 修改脚本名称
```

### 4. 实现业务逻辑

```python
def main_logic(script):
    """主要业务逻辑函数"""
    # 1. 获取参数
    directory = script.get_parameter('directory', '.')
    file_pattern = script.get_parameter('file_pattern', '*')
    
    script.info("开始处理文件")
    
    # 2. 执行业务逻辑
    try:
        # 你的业务逻辑
        processed_files = process_files(directory, file_pattern)
        
        # 3. 返回成功结果
        return script.success_result(
            f"处理完成，共处理 {len(processed_files)} 个文件",
            {'files': processed_files}
        )
        
    except Exception as e:
        script.error(f"处理失败: {e}")
        return script.error_result(f"处理失败: {e}", "ProcessingError")
```

### 5. 配置参数（可选）

如果脚本需要动态参数配置，在 `script_configs.json` 中添加配置：

```json
{
  "my_new_script": {
    "dialog_title": "我的新脚本-参数配置",
    "parameters": [
      {
        "name": "directory",
        "type": "text",
        "label": "目录路径",
        "required": true,
        "default": "C:\\temp",
        "placeholder": "请输入目录路径"
      },
      {
        "name": "file_pattern",
        "type": "text",
        "label": "文件匹配模式",
        "required": false,
        "default": "*",
        "placeholder": "例如: *.txt"
      }
    ]
  }
}
```

### 6. 测试脚本

#### 本地测试
```bash
# 设置环境变量
export SCRIPT_NAME="my_new_script"
export SCRIPT_PARAMETERS='{"directory": "C:\\temp", "file_pattern": "*.txt"}'
export PAGE_CONTEXT="test"

# 运行脚本
cd server
python celery_app/my_new_script.py
```

#### 集成测试
```bash
# 注册脚本
python manage.py register_scripts

# 配置按钮（可选）
python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name my_new_script --button-text "我的新脚本"

# 重启服务
# 重启Celery Worker和Django服务器
```

## 最佳实践

### 1. 参数设计
- 提供合理的默认值
- 使用有意义的参数名
- 添加参数验证

### 2. 错误处理
- 使用 `script.error_result()` 返回错误
- 提供有意义的错误信息
- 记录详细的调试信息

### 3. 日志使用
- 使用适当的日志级别
- 提供足够的调试信息
- 避免敏感信息泄露

### 4. 结果格式
- 使用标准的结果格式
- 包含必要的元数据
- 提供有用的返回数据

## 故障排除

### 常见问题

1. **脚本无法执行**
   - 检查脚本语法
   - 确认环境变量设置正确
   - 查看错误日志

2. **参数获取失败**
   - 检查参数名是否正确
   - 确认JSON格式正确
   - 验证默认值类型

3. **结果格式错误**
   - 确保返回字典格式
   - 检查JSON序列化
   - 验证必需字段

### 调试技巧

1. **使用调试日志**
   ```python
   script.debug(f"参数: {script.parameters}")
   script.debug(f"当前处理: {current_item}")
   ```

2. **本地测试**
   ```bash
   # 设置环境变量后直接运行
   python celery_app/my_script.py
   ```

3. **查看Celery日志**
   ```bash
   celery -A celery_app worker --loglevel=debug
   ```

## 脚本执行流程

### 完整执行流程

脚本执行遵循以下完整流程：

1. **用户点击按钮** → 前端判断脚本类型（传统/动态）
2. **API调用** → 调用对应的执行接口
3. **参数验证** → 验证脚本存在性和参数有效性
4. **创建执行记录** → 在数据库中创建TaskExecution记录
5. **启动Celery任务** → 异步执行脚本
6. **subprocess执行** → 在独立进程中运行脚本
7. **环境变量传递** → 通过环境变量传递参数
8. **脚本内部执行** → 脚本获取参数并执行业务逻辑
9. **结果输出** → 脚本输出标准JSON格式结果
10. **状态更新** → 更新执行状态和结果
11. **前端轮询** → 前端轮询执行状态
12. **页面刷新** → 执行完成后刷新页面数据

### 环境变量

脚本执行时会自动设置以下环境变量：

```bash
SCRIPT_PARAMETERS='{"directory": "C:\\temp", "recursive": true}'
PAGE_CONTEXT="/scanDevUpdate"
SCRIPT_NAME="scanner_file"
EXECUTION_ID="1704038400.123456"
```

### 输出格式

脚本必须输出标准JSON格式：

```json
{
  "status": "success",
  "message": "执行成功",
  "data": {
    "result": "具体结果数据"
  },
  "metadata": {
    "script_name": "scanner_file",
    "execution_time": "2024-01-01T00:00:00",
    "execution_duration": 2.345
  }
}
```

详细执行流程请参考：[脚本执行完整流程详解](SCRIPT_EXECUTION_FLOW_GUIDE.md)

## 总结

脚本模板系统提供了：
- **统一的开发模式**：所有脚本都遵循相同的结构
- **参数化配置**：通过配置文件管理所有参数
- **标准化输出**：统一的结果格式和错误处理
- **易于维护**：减少重复代码，提高可维护性
- **良好的扩展性**：易于添加新功能和参数
- **完整的执行流程**：从用户点击到结果返回的全流程管理

通过使用模板系统，开发者可以专注于业务逻辑的实现，而无需重复实现基础功能，大大提高了开发效率和代码质量。
