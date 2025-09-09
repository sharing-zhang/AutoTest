# 脚本模板系统实现指南

## 概述

本文档详细说明了脚本模板系统的实现流程，以及如何在`check_Reward.py`中套用模板系统，并添加相应的参数配置。

## 模板系统架构

### 1. 核心组件

```
script_template.py (模板文件)
    ↓ 继承
script_base.py (基础库)
    ↓ 提供
ScriptBase类 (核心功能)
```

### 2. ScriptBase类功能

#### 参数管理
- 从环境变量获取`SCRIPT_PARAMETERS`、`SCRIPT_NAME`、`PAGE_CONTEXT`等
- 提供`get_parameter(key, default)`方法获取参数
- 自动解析JSON格式的参数

#### 日志系统
- `debug(message)`: 调试信息
- `info(message)`: 普通信息
- `warning(message)`: 警告信息
- `error(message)`: 错误信息

#### 结果格式化
- `success_result(message, data)`: 创建成功结果
- `error_result(message, error_type)`: 创建错误结果
- 统一的结果格式，包含执行时间、元数据等

#### 错误处理
- `run_with_error_handling(main_func)`: 自动捕获异常
- 统一的错误格式化和输出

## 模板使用流程

### 1. 基本使用模式

```python
from script_base import create_simple_script

def main_logic(script):
    """主要业务逻辑函数"""
    # 获取参数
    param1 = script.get_parameter('param1', 'default_value')
    
    # 执行业务逻辑
    result_data = {
        'processed_data': param1.upper(),
        'status': 'completed'
    }
    
    # 返回结果
    return script.success_result("执行成功", result_data)

if __name__ == '__main__':
    create_simple_script('script_name', main_logic)
```

### 2. 执行流程

```
1. 环境变量设置
   ↓
2. ScriptBase初始化
   ↓
3. 参数解析
   ↓
4. 主逻辑执行
   ↓
5. 结果格式化
   ↓
6. 输出到stdout
```

## check_Reward.py模板套用

### 原始实现问题

原始的`check_Reward.py`存在以下问题：
1. 重复实现了ScriptBase的功能
2. 没有统一的参数配置管理
3. 缺少标准化的配置接口
4. 硬编码的配置参数

### 模板化改造

#### 1. 创建基于模板的版本

创建了`check_Reward_template.py`，主要改进：

```python
# 使用模板系统
from script_base import create_simple_script

def main_logic(script):
    # 从参数获取配置
    root_path = script.get_parameter('root_path', r"D:\dev")
    mission_paths = script.get_parameter('mission_paths', [...])
    check_tp_id_prefix = script.get_parameter('check_tp_id_prefix', '971')
    min_count = script.get_parameter('min_count', 1)
    
    # 执行业务逻辑...
    
    return script.success_result(message, data)

if __name__ == '__main__':
    create_simple_script('progress_rewards_checker', main_logic)
```

#### 2. 辅助函数模块化

将复杂逻辑拆分为辅助函数：
- `detect_encoding()`: 文件编码检测
- `parse_file()`: 文件解析
- `validate_file_path()`: 文件路径验证

#### 3. 参数化配置

所有硬编码的配置都改为参数化：
- `root_path`: 根路径
- `mission_paths`: 检查文件列表
- `check_tp_id_prefix`: tpId前缀检查
- `min_count`: 最小count值
- `enable_detailed_logging`: 详细日志开关

## 参数配置系统

### 1. script_configs.json结构

```json
{
  "script_name.py": [
    {
      "name": "parameter_name",
      "type": "text|number|switch|select|checkbox|textarea",
      "label": "显示标签",
      "required": true|false,
      "default": "默认值",
      "placeholder": "占位符文本",
      "description": "参数说明",
      "options": ["选项1", "选项2"],  // 仅select和checkbox类型
      "min": 0,  // 仅number类型
      "max": 100,  // 仅number类型
      "multiple": true  // 仅checkbox类型
    }
  ]
}
```

### 2. check_Reward.py参数配置

```json
{
  "check_Reward.py": [
    {
      "name": "root_path",
      "type": "text",
      "label": "根路径",
      "required": true,
      "default": "D:\\dev",
      "placeholder": "例如: D:\\dev 或 /home/user/project"
    },
    {
      "name": "mission_paths",
      "type": "textarea",
      "label": "检查文件路径列表",
      "required": true,
      "default": "datapool\\ElementData\\BaseData\\POINT_PROGRESS_REWARD_ENDLESS.data.txt\ndatapool\\ElementData\\BaseData\\POINT_PROGRESS_REWARD.data.txt",
      "placeholder": "每行一个文件路径，相对于根路径",
      "description": "要检查的文件路径列表，每行一个路径"
    },
    {
      "name": "check_tp_id_prefix",
      "type": "text",
      "label": "检查的tpId前缀",
      "required": false,
      "default": "971",
      "placeholder": "例如: 971",
      "description": "只检查tpId以此前缀开头的数据块"
    },
    {
      "name": "min_count",
      "type": "number",
      "label": "最小count值",
      "required": false,
      "default": 1,
      "min": 0,
      "max": 1000,
      "description": "只检查count大于此值的数据块"
    },
    {
      "name": "enable_detailed_logging",
      "type": "switch",
      "label": "启用详细日志",
      "required": false,
      "default": true,
      "description": "是否输出详细的调试信息"
    }
  ]
}
```

## 使用方式

### 1. 环境变量设置

脚本通过环境变量接收参数：

```bash
export SCRIPT_NAME="progress_rewards_checker"
export SCRIPT_PARAMETERS='{"root_path":"D:\\dev","mission_paths":["datapool\\ElementData\\BaseData\\POINT_PROGRESS_REWARD.data.txt"],"check_tp_id_prefix":"971","min_count":1}'
export PAGE_CONTEXT="admin_panel"
export EXECUTION_ID="exec_123456"
```

### 2. 脚本执行

```bash
python check_Reward_template.py
```

### 3. 结果输出

脚本会输出JSON格式的结果到stdout：

```json
{
  "status": "success",
  "message": "检查完成，发现 1/2 个文件存在问题，共找到 3 个问题数据块",
  "timestamp": 1703123456.789,
  "data": {
    "check_summary": {
      "total_files": 2,
      "problem_files": 1,
      "total_blocks_found": 3,
      "warning_files": [...],
      "check_conditions": {...}
    },
    "detailed_results": {...},
    "root_path": "D:\\dev",
    "execution_parameters": {...}
  },
  "metadata": {
    "script_name": "progress_rewards_checker",
    "execution_time": "2023-12-21T10:30:56.789",
    "execution_duration": 1.234,
    "version": "1.0.0",
    "method": "subprocess_execution"
  }
}
```

## 优势对比

### 原始实现 vs 模板化实现

| 方面 | 原始实现 | 模板化实现 |
|------|----------|------------|
| 代码复用 | 重复实现基础功能 | 复用ScriptBase类 |
| 参数管理 | 硬编码配置 | 参数化配置 |
| 错误处理 | 手动处理 | 自动统一处理 |
| 日志输出 | 简单print | 分级日志系统 |
| 结果格式 | 自定义格式 | 标准化JSON格式 |
| 配置管理 | 无 | 统一配置文件 |
| 维护性 | 低 | 高 |
| 扩展性 | 差 | 好 |

## 最佳实践

### 1. 脚本开发流程

1. 复制`script_template.py`作为起点
2. 修改脚本名称和描述
3. 实现`main_logic`函数
4. 添加必要的辅助函数
5. 在`script_configs.json`中添加参数配置
6. 测试脚本执行

### 2. 参数设计原则

- 所有配置都应该参数化
- 提供合理的默认值
- 添加参数验证
- 提供清晰的参数说明

### 3. 错误处理

- 使用`script.error_result()`返回错误
- 提供有意义的错误信息
- 记录详细的调试信息

### 4. 日志使用

- 使用适当的日志级别
- 提供足够的调试信息
- 避免敏感信息泄露

## 总结

模板系统提供了：
1. **统一的开发模式**: 所有脚本都遵循相同的结构
2. **参数化配置**: 通过配置文件管理所有参数
3. **标准化输出**: 统一的结果格式和错误处理
4. **易于维护**: 减少重复代码，提高可维护性
5. **良好的扩展性**: 易于添加新功能和参数

通过使用模板系统，`check_Reward.py`从硬编码的独立脚本转变为可配置、可维护的标准化脚本，大大提高了代码质量和可维护性。
