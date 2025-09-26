# 新脚本部署详细步骤指南

## 📋 您已完成的步骤
✅ 1. 在 `server/celery_app/` 创建了新脚本文件  
✅ 2. 运行了脚本注册命令  
✅ 3. 配置了对应的按钮  

## 🚀 接下来需要做的步骤

### 步骤1: 验证脚本注册状态

#### 检查数据库记录
```bash
cd server
python manage.py shell
```

```python
# 在Django shell中执行
from myapp.models import Script, PageScriptConfig

# 检查脚本是否正确注册
scripts = Script.objects.filter(is_active=True)
for script in scripts:
    print(f"脚本ID: {script.id}, 名称: {script.name}, 路径: {script.script_path}")

# 检查您的新脚本
your_script = Script.objects.filter(name='your_script_name').first()
if your_script:
    print(f"✅ 脚本已注册: {your_script.name}")
    print(f"   路径: {your_script.script_path}")
    print(f"   参数模式: {your_script.parameters_schema}")
else:
    print("❌ 脚本未找到，需要重新注册")
```

#### 检查按钮配置
```python
# 继续在Django shell中
page_configs = PageScriptConfig.objects.filter(is_enabled=True)
for config in page_configs:
    print(f"页面: {config.page_route}, 脚本: {config.script.name}, 按钮文本: {config.button_text}")
```

### 步骤2: 重启服务 (必须)

#### 停止现有服务
```bash
# 如果Celery Worker正在运行，按 Ctrl+C 停止
# 如果Django服务器正在运行，按 Ctrl+C 停止
```

#### 重新启动服务 (按顺序)
```bash
# 1. 确保Redis正在运行
redis-server

# 2. 启动Celery Worker (新终端)
cd server
celery -A celery_app worker --loglevel=info

# 3. 启动Django服务器 (新终端)
cd server  
python manage.py runserver
```

### 步骤3: 验证Celery任务发现

#### 检查Worker日志
启动Celery Worker时，查看输出是否包含您的任务：
```bash
[tasks]
  . myapp.views.celery_views.execute_python_script
  
[worker ready]
```

#### 测试任务发现
```bash
cd server
python manage.py shell
```

```python
# 测试Celery任务是否可用
from myapp.views.celery_views import execute_python_script
from celery_app.celery import app

# 检查任务是否已注册
registered_tasks = app.control.inspect().registered()
print("已注册的任务:", registered_tasks)

# 检查是否包含我们的任务
if 'myapp.views.celery_views.execute_python_script' in str(registered_tasks):
    print("✅ 统一执行器任务已注册")
else:
    print("❌ 任务未注册，检查Celery配置")
```

### 步骤4: 前端验证

#### 检查API端点
```bash
# 测试脚本列表API
curl "http://localhost:8000/myapp/admin/celery/scripts?page_route=/scanDevUpdate"
```

预期返回应该包含您的新脚本：
```json
{
  "success": true,
  "scripts": [
    {
      "id": 1,
      "name": "your_script_name",
      "description": "您的脚本描述",
      "script_path": "celery_app/your_script.py",
      "tasks": [
        {
          "name": "unified_execution",
          "parameters": {
            "param1": {"type": "string", "default": "value"}
          }
        }
      ]
    }
  ],
  "page_configs": [
    {
      "script_name": "your_script_name",
      "button_text": "您的按钮文本",
      "position": "top-right"
    }
  ]
}
```

#### 前端页面检查
1. 打开浏览器访问: `http://localhost:8000/scanDevUpdate`
2. 检查页面上是否显示了您的新按钮
3. 按钮位置是否正确
4. 按钮样式是否符合配置

### 步骤5: 功能测试

#### 手动点击测试
1. 在前端页面点击您的新按钮
2. 观察是否出现 "正在启动脚本..." 的提示
3. 查看按钮是否进入loading状态
4. 等待执行完成，检查是否有成功提示

#### API直接测试
```bash
# 直接调用执行API
curl -X POST http://localhost:8000/myapp/admin/celery/execute-script \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": YOUR_SCRIPT_ID,
    "parameters": {
      "param1": "test_value"
    },
    "page_context": "/scanDevUpdate"
  }'
```

预期返回：
```json
{
  "success": true,
  "task_id": "abc123...",
  "execution_id": 123,
  "script_name": "your_script_name",
  "message": "脚本已启动执行"
}
```

#### 查询执行结果
```bash
# 使用上面返回的task_id查询结果
curl "http://localhost:8000/myapp/admin/celery/script-task-result?task_id=abc123...&execution_id=123"
```

### 步骤6: 日志检查

#### Celery Worker日志
查看Celery Worker终端输出，应该看到：
```
[INFO] 开始执行脚本任务: task_id=abc123, script_id=YOUR_SCRIPT_ID
[INFO] 执行脚本: your_script_name (celery_app/your_script.py)
[INFO] 准备执行Python脚本: /path/to/your_script.py
[INFO] 参数: {"param1": "test_value"}
[INFO] 脚本执行完成，返回码: 0
[INFO] 脚本输出解析成功: <class 'dict'>
[INFO] 脚本执行成功: 耗时 1.23s, 内存使用 5.67MB
```

#### Django日志
如果有错误，检查Django控制台输出

#### 脚本自身日志
检查您的脚本是否正确输出到stderr (调试信息)：
```python
# 在您的脚本中
print(f"[DEBUG] 脚本参数: {parameters}", file=sys.stderr)
```

### 步骤7: 数据库结果验证

#### 检查执行记录
```bash
cd server
python manage.py shell
```

```python
from myapp.models import TaskExecution, ScanDevUpdate_scanResult

# 检查最新的执行记录
latest_execution = TaskExecution.objects.latest('created_at')
print(f"最新执行: {latest_execution.script.name}")
print(f"状态: {latest_execution.status}")
print(f"结果: {latest_execution.result}")

# 检查是否保存到扫描结果表
latest_result = ScanDevUpdate_scanResult.objects.latest('scandevresult_time')
print(f"最新结果: {latest_result.script_name}")
print(f"文件名: {latest_result.scandevresult_filename}")
```

### 步骤8: 故障排除

#### 常见问题及解决方案

**问题1: 按钮不显示**
```bash
# 检查页面配置
python manage.py shell
```
```python
from myapp.models import PageScriptConfig
configs = PageScriptConfig.objects.filter(page_route='/scanDevUpdate', is_enabled=True)
print(f"找到 {configs.count()} 个配置")
```

**问题2: 点击按钮无反应**
- 检查浏览器控制台错误
- 检查Django服务器日志
- 验证API端点是否正确

**问题3: 脚本执行失败**
```python
# 检查脚本路径是否正确
import os
from django.conf import settings
script_path = 'celery_app/your_script.py'
full_path = os.path.join(settings.BASE_DIR, script_path)
print(f"脚本路径: {full_path}")
print(f"文件存在: {os.path.exists(full_path)}")
```

**问题4: 任务超时**
- 检查脚本执行时间是否超过540秒
- 优化脚本性能
- 调整超时设置

### 步骤9: 性能监控

#### 执行时间监控
```python
from myapp.models import TaskExecution
import statistics

# 分析您的脚本执行时间
executions = TaskExecution.objects.filter(
    script__name='your_script_name',
    status='SUCCESS'
).values_list('execution_time', flat=True)

if executions:
    avg_time = statistics.mean(executions)
    print(f"平均执行时间: {avg_time:.2f}秒")
```

#### 内存使用监控
```python
memory_usage = TaskExecution.objects.filter(
    script__name='your_script_name',
    status='SUCCESS'
).values_list('memory_usage', flat=True)

if memory_usage:
    avg_memory = statistics.mean(filter(None, memory_usage))
    print(f"平均内存使用: {avg_memory:.2f}MB")
```

## 🎉 完成检查清单

- [ ] 脚本在数据库中正确注册
- [ ] 按钮配置生效
- [ ] Celery Worker重启并识别任务
- [ ] Django服务器重启
- [ ] 前端页面显示新按钮
- [ ] 点击按钮能正常执行
- [ ] 执行结果正确保存
- [ ] 页面数据自动刷新
- [ ] 日志输出正常
- [ ] 性能指标合理

## 📞 如果遇到问题

1. **重新注册脚本**:
   ```bash
   python manage.py register_scripts --force
   ```

2. **重新应用按钮配置**:
   ```bash
   python manage.py setup_page_scripts
   ```

3. **完全重启**:
   - 停止所有服务
   - 重启Redis
   - 重启Celery Worker
   - 重启Django
   - 刷新浏览器页面

4. **检查脚本格式**:
   确保您的脚本遵循方案1标准格式，包括环境变量获取和JSON输出

按照这些步骤，您的新脚本应该能够完美地集成到方案1系统中！
