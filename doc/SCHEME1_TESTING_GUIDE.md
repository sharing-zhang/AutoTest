# 方案1 - 统一任务执行器测试指南

## 概述
方案1已成功实现，采用"Celery + subprocess"架构，提供统一的脚本执行管理。

## 实现特点

### ✅ 已完成的功能
1. **统一任务执行器** (`tasks.py`)
   - `execute_python_script` Celery任务
   - 支持Python和Shell脚本
   - 完整的错误处理和重试机制
   - 资源使用监控

2. **增强的视图接口** (`celery_views.py`)
   - TaskExecutionViewSet (DRF)
   - 简化的API接口
   - 完整的任务状态管理

3. **示例脚本**
   - `example_script.py` - 完整功能演示
   - `print_test_script.py` - 从Celery任务转换的示例

4. **配置优化**
   - Celery配置支持方案1
   - 自动任务发现
   - 性能优化设置

## 快速测试

### 1. 启动服务
```bash
# 启动Redis (如果还没启动)
redis-server

# 启动Celery Worker
cd server
celery -A celery_app worker --loglevel=info

# 启动Django服务器
python manage.py runserver
```

### 2. 配置测试脚本
```bash
# 运行脚本配置
cd server
python setup_example_scripts.py
```

### 3. API测试

#### 使用DRF接口 (推荐)
```bash
# 执行示例脚本
curl -X POST http://localhost:8000/api/task-executions/execute_script/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "script_id": 1,
    "parameters": {
      "message": "Hello World!",
      "multiplier": 2,
      "delay": 1
    },
    "page_context": "test"
  }'

# 查询任务状态
curl "http://localhost:8000/api/task-executions/task_status/?task_id=TASK_ID"
```

#### 使用简化API
```bash
# 执行脚本
curl -X POST http://localhost:8000/api/execute-script/ \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": 1,
    "parameters": {
      "message": "Test from API",
      "multiplier": 3
    }
  }'

# 查询结果
curl "http://localhost:8000/api/script-task-result/?task_id=TASK_ID"
```

## 脚本开发规范

### 标准脚本结构
```python
#!/usr/bin/env python3
import os
import json
import sys
from datetime import datetime

def get_script_parameters():
    """从环境变量获取参数"""
    try:
        params_str = os.environ.get('SCRIPT_PARAMETERS', '{}')
        return json.loads(params_str)
    except json.JSONDecodeError:
        return {}

def main():
    """主要业务逻辑"""
    try:
        parameters = get_script_parameters()
        page_context = os.environ.get('PAGE_CONTEXT', 'unknown')
        script_name = os.environ.get('SCRIPT_NAME', 'unknown')
        
        # 业务逻辑处理
        result = process_data(parameters)
        
        # 输出标准JSON格式
        output = {
            'status': 'success',
            'message': '执行成功',
            'data': result,
            'metadata': {
                'script_name': script_name,
                'execution_time': datetime.now().isoformat()
            }
        }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        error_output = {
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### 环境变量说明
- `SCRIPT_PARAMETERS`: JSON格式的脚本参数
- `PAGE_CONTEXT`: 页面上下文信息
- `SCRIPT_NAME`: 脚本名称
- `EXECUTION_ID`: 执行ID时间戳

## 监控和调试

### Celery日志
```bash
# 查看Worker日志
celery -A celery_app worker --loglevel=debug

# 查看任务状态
celery -A celery_app inspect active
celery -A celery_app inspect scheduled
```

### Django日志
- 任务执行记录保存在 `TaskExecution` 表
- 详细的执行信息包括耗时、内存使用等
- 错误信息包含完整的堆栈跟踪

## 与方案2的对比

| 特性 | 方案1 (统一执行器) | 方案2 (直接任务) |
|------|-------------------|------------------|
| 脚本独立性 | ✅ 独立Python文件 | ❌ 耦合Celery |
| 开发便利性 | ✅ 可独立调试 | ❌ 需Celery环境 |
| 管理复杂度 | ✅ 数据库配置 | ❌ 代码级配置 |
| 性能开销 | ⚠️ subprocess开销 | ✅ 直接执行 |
| 扩展性 | ✅ 支持多语言 | ❌ Python限制 |
| 隔离性 | ✅ 进程隔离 | ❌ 共享进程 |

## 下一步计划
1. 前端集成测试
2. 性能基准测试
3. 生产环境部署配置
4. 监控面板开发
