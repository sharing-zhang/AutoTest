# 前端页面同步管理指南

## 概述

前端页面同步管理命令 (`sync_frontend_pages.py`) 是一个强大的Django管理命令，用于自动扫描前端页面并同步到数据库。它能够自动发现Vue页面、API文件和路由配置，并创建相应的数据库记录。

## 主要功能

### 1. 自动扫描功能
- **Vue页面扫描**: 自动扫描 `web/src/views/` 目录下的所有 `.vue` 文件
- **API文件扫描**: 扫描 `web/src/api/` 目录下的所有 `.ts` 文件
- **路由配置扫描**: 解析 `web/src/router/` 目录下的路由配置文件

### 2. 数据库同步
- **脚本配置更新**: 自动更新 `Script` 表中的脚本配置
- **页面配置同步**: 在 `ScanUpdate` 表中创建页面项目记录
- **项目配置更新**: 更新项目信息和最后更新时间

### 3. 配置管理
- **导出配置**: 将当前数据库配置导出到JSON文件
- **导入配置**: 从JSON文件导入页面配置
- **预览模式**: 支持预览模式，不实际执行操作

## 使用方法

### 基本用法

```bash
cd server
python manage.py sync_frontend_pages
```

### 高级选项

```bash
# 指定前端源码目录
python manage.py sync_frontend_pages --source-dir ../web/src

# 指定配置文件路径
python manage.py sync_frontend_pages --config-file myapp/management/commands/page_configs.json

# 预览模式（不实际执行）
python manage.py sync_frontend_pages --dry-run

# 导出当前配置
python manage.py sync_frontend_pages --export-config

# 从配置文件导入
python manage.py sync_frontend_pages --import-config

# 同步前备份数据库
python manage.py sync_frontend_pages --backup-db
```

## 扫描规则

### Vue页面扫描

扫描 `web/src/views/` 目录下的所有 `.vue` 文件：

```python
# 扫描规则
for filename in os.listdir(views_dir):
    if filename.endswith('.vue') and not filename.startswith('.'):
        page_name = filename.replace('.vue', '')
        # 分析页面内容
        has_script_manager = 'ScriptManagerLayout' in content
        has_api_calls = 'Api' in content or 'api' in content
```

### API文件扫描

扫描 `web/src/api/` 目录下的所有 `.ts` 文件：

```python
# 扫描规则
for filename in os.listdir(api_dir):
    if filename.endswith('.ts') and not filename.startswith('.'):
        api_name = filename.replace('.ts', '')
        # 读取API文件内容
```

### 路由配置扫描

解析 `web/src/router/` 目录下的路由配置：

```python
# 路由解析规则
route_matches = re.findall(r"path:\s*['\"]([^'\"]+)['\"].*?name:\s*['\"]([^'\"]+)['\"]", content)
for path, name in route_matches:
    routes.append({
        'path': path,
        'name': name,
        'file_path': file_path
    })
```

## 数据库操作

### 脚本配置更新

```python
def update_script_configs(self):
    """更新脚本配置"""
    # 重新加载脚本配置
    script_config_manager.reload_config()
    
    # 获取所有脚本
    all_scripts = script_config_manager.get_all_scripts()
    
    for script_name in all_scripts:
        script_config = script_config_manager.get_script_config(script_name)
        
        if script_config:
            script_record, created = Script.objects.get_or_create(
                name=script_name,
                defaults={
                    'description': f'动态脚本: {script_name}',
                    'script_path': f'celery_app/{script_name}.py',
                    'script_type': 'data_processing',
                    'parameters_schema': script_config,
                    'visualization_config': {},
                    'is_active': True
                }
            )
```

### 页面配置同步

```python
def sync_page_configs(self, vue_pages, routes):
    """同步页面配置"""
    route_map = {route['name']: route['path'] for route in routes}
    
    for page in vue_pages:
        page_name = page['name']
        page_route = route_map.get(page_name, f'/{page_name}')
        
        # 检查是否已存在项目配置
        project_exists = ScanUpdate.objects.filter(
            child_url_key=page_name
        ).exists()
        
        if not project_exists:
            # 创建新的项目配置
            ScanUpdate.objects.create(
                projectname=f'{page_name}页面',
                description=f'自动生成的{page_name}页面配置',
                versionnumber='V1.0.0',
                director='系统',
                remark='通过一键同步自动创建',
                status='0',
                child_url_key=page_name
            )
```

## 配置文件格式

### 导出配置格式

```json
{
  "pages": [
    {
      "projectname": "页面名称",
      "description": "页面描述",
      "versionnumber": "V1.0.0",
      "director": "负责人",
      "remark": "备注",
      "child_url_key": "页面键"
    }
  ],
  "scripts": [
    {
      "name": "脚本名称",
      "description": "脚本描述",
      "script_path": "脚本路径",
      "script_type": "脚本类型",
      "parameters_schema": {}
    }
  ],
  "routes": [
    {
      "page_route": "页面路由",
      "script_name": "脚本名称",
      "button_text": "按钮文本",
      "position": "按钮位置",
      "button_style": {}
    }
  ]
}
```

## 使用场景

### 1. 新项目初始化

```bash
# 扫描并同步所有前端页面
python manage.py sync_frontend_pages --source-dir ../web/src
```

### 2. 定期同步

```bash
# 定期同步，确保数据库与前端代码一致
python manage.py sync_frontend_pages --dry-run  # 先预览
python manage.py sync_frontend_pages            # 实际执行
```

### 3. 配置备份和恢复

```bash
# 备份当前配置
python manage.py sync_frontend_pages --export-config --config-file backup_config.json

# 从备份恢复
python manage.py sync_frontend_pages --import-config --config-file backup_config.json
```

### 4. 团队协作

```bash
# 团队成员可以共享配置文件
python manage.py sync_frontend_pages --export-config
# 将生成的配置文件提交到版本控制
# 其他团队成员可以导入配置
python manage.py sync_frontend_pages --import-config
```

## 错误处理

### 常见错误

1. **前端源码目录不存在**
   ```
   ❌ 前端源码目录不存在: ../web/src
   ```
   解决：检查路径是否正确，确保前端项目存在

2. **配置文件格式错误**
   ```
   ❌ 配置文件不存在: myapp/management/commands/page_configs.json
   ```
   解决：检查配置文件路径，或使用 `--export-config` 生成配置文件

3. **数据库操作失败**
   ```
   ❌ 同步失败: 数据库连接错误
   ```
   解决：检查数据库连接，确保Django配置正确

### 调试方法

1. **使用预览模式**
   ```bash
   python manage.py sync_frontend_pages --dry-run
   ```

2. **查看详细日志**
   ```bash
   python manage.py sync_frontend_pages --verbosity=2
   ```

3. **检查生成的文件**
   ```bash
   # 检查导出的配置文件
   cat myapp/management/commands/page_configs.json
   ```

## 最佳实践

### 1. 开发流程

1. 开发新的Vue页面
2. 运行同步命令预览变化
3. 确认无误后执行同步
4. 提交代码和配置

### 2. 团队协作

1. 定期同步配置
2. 将配置文件纳入版本控制
3. 新成员加入时先导入配置
4. 使用统一的命名规范

### 3. 维护建议

1. 定期备份配置
2. 监控同步日志
3. 及时处理错误
4. 保持文档更新

## 扩展功能

### 自定义扫描规则

可以修改扫描函数来支持更多文件类型：

```python
def scan_custom_files(self, source_dir):
    """扫描自定义文件类型"""
    custom_dir = os.path.join(source_dir, 'custom')
    if not os.path.exists(custom_dir):
        return []
    
    # 自定义扫描逻辑
    pass
```

### 集成CI/CD

可以将同步命令集成到CI/CD流程中：

```yaml
# .github/workflows/sync.yml
- name: Sync Frontend Pages
  run: |
    cd server
    python manage.py sync_frontend_pages --dry-run
    python manage.py sync_frontend_pages
```

## 总结

前端页面同步管理命令提供了：

1. **自动化扫描**: 自动发现前端页面和API文件
2. **数据库同步**: 自动更新数据库配置
3. **配置管理**: 支持导入导出配置
4. **预览功能**: 支持预览模式，避免误操作
5. **错误处理**: 完善的错误处理和调试功能

这个工具大大简化了前端页面与后端数据库的同步工作，提高了开发效率和系统一致性。
