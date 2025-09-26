# 页面创建器使用说明

## 概述

页面创建器是一个独立的Django视图模块，专门用于动态创建前端页面。它包含在 `server/myapp/views/page_creator.py` 文件中，提供了完整的页面自动生成功能。

## 文件结构

```
server/myapp/views/
├── __init__.py
├── page_creator.py          # 页面创建器主文件
├── celery_views.py          # 原有的Celery相关视图
└── admin/                   # 管理后台视图
```

## 主要功能

### 1. 创建前端页面API

**接口地址**: `POST /myapp/api/create-frontend-page/`

**请求参数**:
```json
{
    "route_key": "TestPage",           // 路由键，必填
    "project_name": "测试页面",         // 项目名称，可选
    "page_title": "测试页面管理"        // 页面标题，可选
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "前端页面 \"TestPage\" 创建成功",
    "route_key": "TestPage",
    "vue_file": "/path/to/web/src/views/TestPage.vue",
    "api_endpoints": {
        "list": "/myapp/admin/TestPage/list",
        "create": "/myapp/admin/TestPage/create",
        "update": "/myapp/admin/TestPage/update",
        "delete": "/myapp/admin/TestPage/delete",
        "detail": "/myapp/admin/TestPage/detail"
    }
}
```

### 2. 自动生成的文件

页面创建器会自动生成以下文件：

1. **Vue组件文件** (`web/src/views/{route_key}.vue`)
   - 包含完整的CRUD界面
   - 基于Ant Design Vue组件
   - 支持表格、表单、模态框等功能

2. **API接口文件** (`web/src/api/{route_key}.ts`)
   - 标准的RESTful API接口
   - 包含增删改查操作
   - 统一的错误处理

3. **路由配置更新** (`web/src/router/root.js`)
   - 自动添加新路由到Vue Router
   - 支持动态导入组件

4. **后端路由配置** (`server/myapp/urls.py`)
   - 添加对应的Django URL路由
   - 集成到现有的URL配置中

## 核心函数

### 1. `create_frontend_page(request)`
主要的API视图函数，处理页面创建请求。

**功能**:
- 验证请求参数
- 检查路由键唯一性
- 调用辅助函数创建各种文件
- 返回创建结果

### 2. `check_route_exists(route_key)`
检查路由键是否已存在。

**检查范围**:
- Vue路由配置文件
- Vue组件文件

### 3. `create_vue_component(route_key, project_name, page_title)`
创建Vue组件文件。

**生成内容**:
- 完整的Vue 3 Composition API组件
- 表格管理界面
- 表单验证
- 响应式设计

### 4. `update_router_config(route_key)`
更新Vue路由配置。

**功能**:
- 读取现有路由配置
- 添加新路由到children数组
- 保持原有格式和缩进

### 5. `create_api_endpoints(route_key, project_name)`
创建前端API接口文件。

**生成内容**:
- TypeScript API接口定义
- 标准的HTTP请求方法
- 统一的错误处理

### 6. `create_backend_api_endpoints(route_key, project_name)`
创建后端API路由配置。

**功能**:
- 更新Django URLs配置
- 添加RESTful API路由
- 集成到现有URL结构

## 使用方法

### 1. 在scanUpdate页面中使用

页面创建器已经集成到 `scanUpdate.vue` 页面中：

```javascript
// 在handleOk函数中调用
if (modal.form.child_url_key) {
  try {
    await createFrontendPage(modal.form.child_url_key, modal.form.projectname);
    message.success('项目创建成功，前端页面已自动生成！');
  } catch (error) {
    console.error('创建前端页面失败:', error);
    message.warning('项目创建成功，但前端页面生成失败，请手动创建');
  }
}
```

### 2. 直接调用API

```javascript
const response = await fetch('/myapp/api/create-frontend-page/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    route_key: 'MyNewPage',
    project_name: '我的新页面',
    page_title: '我的新页面管理'
  })
});

const result = await response.json();
if (result.success) {
  console.log('页面创建成功:', result);
} else {
  console.error('页面创建失败:', result.error);
}
```

### 3. 使用Python测试

```python
import requests
import json

data = {
    "route_key": "TestPage",
    "project_name": "测试页面",
    "page_title": "测试页面管理"
}

response = requests.post(
    'http://localhost:8000/myapp/api/create-frontend-page/',
    json=data,
    headers={'Content-Type': 'application/json'}
)

result = response.json()
print(result)
```

## 配置说明

### 1. URL配置

在 `server/myapp/urls.py` 中：

```python
# 动态创建前端页面的API
path('api/create-frontend-page/', views.page_creator.create_frontend_page),
```

### 2. 视图导入

在 `server/myapp/views/__init__.py` 中：

```python
from myapp.views.page_creator import *
```

### 3. 路径配置

页面创建器使用相对路径来定位文件：

```python
base_dir = os.path.dirname(settings.BASE_DIR)  # 获取server目录的父目录
vue_file_path = os.path.join(base_dir, 'web', 'src', 'views', f'{route_key}.vue')
```

## 错误处理

### 1. 参数验证错误

- 缺少route_key参数：返回400错误
- 路由键格式不正确：返回400错误
- 路由键已存在：返回400错误

### 2. 文件操作错误

- 文件路径不存在：自动创建目录
- 文件写入失败：返回500错误
- 权限不足：返回500错误

### 3. 系统错误

- JSON解析错误：返回400错误
- 其他异常：返回500错误，包含详细错误信息

## 调试功能

页面创建器包含详细的调试输出：

```python
print(f"收到创建前端页面请求: {request.body}")
print(f"解析后的数据: {data}")
print(f"路由键: {route_key}, 项目名: {project_name}, 页面标题: {page_title}")
print(f"BASE_DIR: {settings.BASE_DIR}")
print(f"Vue文件路径: {vue_file_path}")
print(f"路由文件路径: {router_file}")
print(f"API文件路径: {api_file_path}")
```

## 扩展功能

### 1. 自定义页面模板

可以修改 `create_vue_component` 函数中的 `vue_template` 变量来自定义生成的页面模板。

### 2. 添加更多字段

可以在Vue模板中添加更多表单字段，并在API模板中添加对应的接口。

### 3. 集成脚本系统

可以将新创建的页面与现有的脚本管理系统集成，添加动态脚本按钮。

## 注意事项

1. **路由键唯一性**：确保路由键不与现有页面冲突
2. **文件权限**：确保应用有权限在指定目录创建文件
3. **路径配置**：确保文件路径配置正确
4. **编码格式**：所有文件都使用UTF-8编码
5. **错误处理**：建议在生产环境中关闭调试输出

## 更新日志

- **v1.0.0**: 初始版本，支持基本的页面自动创建功能
- 支持Vue组件、API接口、路由配置的自动生成
- 集成到scanUpdate页面的新增项目流程中
- 独立的页面创建器模块，避免与现有代码冲突
