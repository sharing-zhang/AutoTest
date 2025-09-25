# 脚本管理系统使用指南

## 概述

现在系统支持在 `server\celery_app` 目录下管理和执行不同的脚本，通过前端页面的动态按钮来运行不同的脚本任务。系统利用现有的数据库表来管理脚本配置、执行记录和结果。

## 数据库表说明

### 核心表结构
- `c_scripts`: 脚本配置表，存储脚本元信息
- `c_task_executions`: 任务执行记录表
- `c_page_script_configs`: 页面脚本配置表
- `c_execution_summaries`: 执行汇总统计表（待添加）

## 使用流程

### 1. 添加新脚本

1. 在 `server/celery_app/` 目录下创建新的 Python 脚本文件
2. 脚本必须导入 celery app: `from .celery import app`
3. 使用 `@app.task(bind=True)` 装饰器定义任务函数

示例脚本结构：
```python
"""
脚本描述
"""
from .celery import app
import time

@app.task(bind=True)
def my_task(self, param1="default", param2=100):
    \"\"\"
    任务描述
    
    Args:
        param1: 参数1描述
        param2: 参数2描述
    \"\"\"
    try:
        # 任务逻辑
        result = {
            'status': 'success',
            'message': '任务完成',
            'timestamp': time.time(),
            'data': {
                # 结果数据
            }
        }
        return result
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': time.time()
        }
```

### 2. 更新 Celery 配置

在 `server/celery_app/celery.py` 的 `include` 列表中添加新脚本：

```python
app = Celery('autotest',
             broker='redis://localhost:6379/0',
             backend='django-db',
             include=[
                 'celery_app.hellowrld',
                 'celery_app.check_file',
                 'celery_app.data_analysis',
                 'celery_app.your_new_script'  # 添加这行
             ])
```

### 3. 注册脚本到数据库

运行管理命令注册脚本：

```bash
cd server
python manage.py register_scripts
```

可选参数：
- `--force`: 强制重新注册所有脚本
- `--script filename.py`: 只注册指定脚本

### 4. 配置页面脚本按钮

为页面配置脚本按钮：

```bash
# 为 scanDevUpdate 页面设置默认脚本配置
python manage.py setup_page_scripts --page-route /scanDevUpdate --setup-default

# 或者单独配置脚本
python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name my_script --button-text "我的脚本"

# 查看页面配置
python manage.py setup_page_scripts --page-route /scanDevUpdate --list
```

### 5. 重启服务

重启 Celery Worker 以加载新脚本：

```bash
cd server
celery -A celery_app worker --loglevel=info --pool=solo
```

## 现有脚本

### 1. hellowrld.py
- **功能**: 调试任务，测试基本功能
- **任务**: `debug_task`
- **参数**: 无

### 2. check_file.py
- **功能**: 文件检查脚本
- **任务**: `check_files_task`
- **参数**: 
  - `directory_path`: 检查目录（默认: "."）
  - `file_pattern`: 文件匹配模式（默认: "*"）

### 3. data_analysis.py
- **功能**: 数据分析脚本
- **任务**: 
  - `analyze_data_task`: 数据分析
  - `generate_report_task`: 生成报告
- **参数**:
  - 分析任务: `data_size`, `analysis_type`
  - 报告任务: `report_type`, `include_charts`

### 4. scanner_file.py（基于模板系统）
- **功能**: 文件扫描脚本，支持递归扫描和多种文件类型
- **任务**: `unified_execution`
- **参数**: 
  - `directory`: 目录路径
  - `file_extensions`: 文件后缀名（多选）
  - `recursive`: 递归扫描（开关）
  - `max_depth`: 最大深度
  - `include_hidden`: 包含隐藏文件
  - `output_format`: 输出格式

### 5. check_Reward_template.py（基于模板系统）
- **功能**: 奖励配置检查脚本，解析配置文件并验证数据
- **任务**: `unified_execution`
- **参数**:
  - `directory`: 目录路径
  - `file_name`: 需要检查的文件名
  - `block_name`: 配置块名称
  - `rules`: 配置项组（分组列表）

### 6. check_ConfigTime.py（基于模板系统）
- **功能**: 配置时间检查脚本，验证活动时间配置
- **任务**: `unified_execution`
- **参数**:
  - `directory`: 目录路径
  - `file_names`: 需要检查的配置文件（标签输入）
  - `start_time_field`: 开始时间对应参数
  - `end_time_field`: 结束时间对应参数
  - `recursive`: 递归扫描子目录
  - `encoding`: 文件编码
  - `expected_days`: 正确的活动天数

### 7. checkFileName.py（基于模板系统）
- **功能**: 文件名检查脚本，验证文件名是否符合规范
- **任务**: `unified_execution`
- **参数**:
  - `root_path`: 目录路径
  - `regex_pattern`: 正则表达式
  - `file_extensions`: 文件后缀名（多选）

## API 接口

### 脚本管理
- `GET /myapp/admin/celery/scripts`: 获取脚本列表
- `GET /myapp/admin/celery/scripts/{id}`: 获取脚本详情
- `POST /myapp/admin/celery/execute-script`: 执行脚本任务
- `GET /myapp/admin/celery/task-result`: 查询任务结果

### 兼容接口
- `POST /myapp/admin/celery/test-task`: 运行测试任务（保留）

## 前端使用

### 页面按钮
- 系统会自动在 `scanDevUpdate.vue` 页面生成脚本按钮
- 如果脚本有多个任务，会显示为下拉菜单
- 按钮会显示执行状态和进度

### 执行流程
1. 点击脚本按钮
2. 系统自动传递默认参数
3. 显示执行状态和进度
4. 执行完成后显示结果
5. 自动刷新数据列表

## 监控和日志

### 执行记录
- 所有脚本执行都会记录在 `c_task_executions` 表中
- 包含执行时间、状态、参数、结果等信息

### 输出日志
- 脚本的标准输出和错误输出记录在 `c_execution_outputs` 表中

### 统计分析
- 系统会生成执行汇总统计（`c_execution_summaries`）
- 可用于分析脚本性能和使用情况

## 脚本执行流程

### 完整执行流程

系统支持两种脚本执行方式：

#### 1. 传统脚本执行（方案1）
- 基于数据库Script表配置
- 使用统一任务执行器 `execute_python_script`
- 通过 `script_id` 识别脚本

#### 2. 动态脚本执行
- 基于 `script_configs.json` 配置
- 使用动态脚本执行器 `execute_dynamic_script_task`
- 通过 `script_name` 识别脚本

### 执行流程步骤

1. **用户点击按钮** → 前端判断脚本类型
2. **API调用** → 调用对应的执行接口
3. **参数验证** → 验证脚本和参数
4. **创建执行记录** → 创建TaskExecution记录
5. **启动Celery任务** → 异步执行脚本
6. **subprocess执行** → 在独立进程中运行
7. **环境变量传递** → 传递参数到脚本
8. **脚本执行** → 脚本执行业务逻辑
9. **结果输出** → 输出标准JSON格式
10. **状态更新** → 更新执行状态
11. **前端轮询** → 轮询执行状态
12. **页面刷新** → 刷新页面数据

### 环境变量

脚本执行时自动设置的环境变量：

```bash
SCRIPT_PARAMETERS='{"param1": "value1", "param2": "value2"}'
PAGE_CONTEXT="/scanDevUpdate"
SCRIPT_NAME="script_name"
EXECUTION_ID="1704038400.123456"
```

详细执行流程请参考：[脚本执行完整流程详解](SCRIPT_EXECUTION_FLOW_GUIDE.md)

## 故障排除

### 脚本未显示
1. 检查脚本是否已注册：`python manage.py register_scripts --list`
2. 检查页面配置：`python manage.py setup_page_scripts --page-route /scanDevUpdate --list`
3. 检查 Celery 配置是否包含新脚本

### 任务执行失败
1. 查看 Celery Worker 日志
2. 检查脚本语法和导入
3. 检查 Redis 连接状态
4. 查看数据库中的错误记录

### 前端按钮不显示
1. 检查前端控制台错误
2. 确认 API 接口返回正确数据
3. 检查脚本的 `parameters_schema` 是否正确

### 脚本执行超时
1. 检查脚本执行时间是否超过540秒
2. 优化脚本性能
3. 考虑分批处理大数据量

## 扩展功能

### 添加参数配置界面
可以扩展前端页面，添加参数配置对话框，让用户在执行前设置参数。

### 结果可视化
利用 `c_execution_artifacts` 表存储图表和报告，在前端展示执行结果。

### 定时任务
结合 `django_celery_beat` 实现脚本的定时执行。

### 权限控制
添加用户权限检查，控制不同用户对脚本的访问权限。
