# AutoTest 快速上手指南

## 🚀 5分钟快速体验

### 1. 启动项目
```bash
# 启动后端服务
cd server
python manage.py runserver

# 启动前端服务
cd web
npm run dev

# 启动Celery任务队列
python manage.py celery_worker
```

### 2. 访问应用
- 前端地址：http://localhost:3000
- 后端地址：http://localhost:8000
- 管理后台：http://localhost:8000/admin

### 3. 体验核心功能
1. 打开前端页面
2. 点击任意脚本按钮
3. 观察脚本执行过程
4. 查看执行结果

## 📚 30分钟深入理解

### 第1步：理解项目结构（5分钟）
```
AutoTest/
├── web/           # 前端Vue项目
├── server/        # 后端Django项目
├── docker/        # Docker部署配置
└── doc/           # 项目文档
```

### 第2步：理解核心概念（10分钟）

#### 脚本类型
- **统一脚本**：所有脚本都通过UnifiedScriptExecutor执行
- **支持方式**：script_id（数据库）、script_name（名称）、script_path（路径）

#### 执行流程
```
用户点击 → 前端组件 → execute_script_unified → execute_script_task → UnifiedScriptExecutor → subprocess → 脚本执行
```

#### 数据存储
- **Script模型**：存储脚本配置信息
- **TaskExecution模型**：记录执行历史
- **PageScriptConfig模型**：页面按钮配置

### 第3步：查看关键代码（15分钟）

#### 前端核心文件
- `web/src/composables/useScriptManager.ts` - 脚本管理逻辑
- `web/src/components/ScriptManagerLayout.vue` - 脚本布局组件
- `web/src/components/ScriptButtons.vue` - 脚本按钮组件

#### 后端核心文件
- `server/myapp/views/celery_views.py` - 脚本执行API
- `server/myapp/models.py` - 数据模型定义
- `server/celery_app/celery.py` - Celery配置

## 🔍 1小时实践练习

### 练习1：添加新脚本（20分钟）

#### 步骤1：创建脚本文件
```python
# server/celery_app/my_test_script.py
import json
import os
from script_base import ScriptBase

class MyTestScript(ScriptBase):
    def run(self):
        # 获取参数
        params = self.get_parameters()
        name = params.get('name', 'World')
        
        # 执行逻辑
        result = {
            'status': 'success',
            'message': f'Hello, {name}!',
            'timestamp': self.get_execution_id()
        }
        
        return result

if __name__ == '__main__':
    script = MyTestScript()
    result = script.run()
    print(json.dumps(result, ensure_ascii=False))
```

#### 步骤2：添加配置
```json
// server/myapp/management/commands/script_configs.json
{
  "my_test_script": {
    "dialog_title": "我的测试脚本",
    "parameters": [
      {
        "name": "name",
        "type": "text",
        "label": "姓名",
        "required": true,
        "default": "测试用户",
        "placeholder": "请输入您的姓名"
      }
    ]
  }
}
```

#### 步骤3：同步到数据库
```bash
cd server
python manage.py sync_frontend_pages
```

#### 步骤4：在页面添加按钮
```json
// server/myapp/management/commands/button_configs.json
[
  {
    "page_route": "/scanDevUpdate",
    "script_name": "my_test_script",
    "button_text": "我的测试",
    "position": "top-right",
    "button_style": {
      "type": "primary",
      "size": "default"
    }
  }
]
```

### 练习2：修改现有功能（20分钟）

#### 修改脚本参数
1. 编辑 `script_configs.json`
2. 添加新的参数配置
3. 重新加载配置
4. 测试参数验证

#### 修改前端界面
1. 编辑 `ScriptButtons.vue`
2. 修改按钮样式
3. 添加新的交互逻辑
4. 测试界面效果

### 练习3：调试和排错（20分钟）

#### 常见问题排查
1. **脚本执行失败**
   - 检查脚本文件是否存在
   - 查看Celery日志
   - 验证参数格式

2. **前端按钮不显示**
   - 检查数据库配置
   - 验证API返回数据
   - 查看浏览器控制台

3. **参数验证失败**
   - 检查script_configs.json格式
   - 验证参数类型
   - 查看验证错误信息

## 🎯 学习检查点

### 基础理解（30分钟）
- [ ] 能说出项目的核心功能
- [ ] 能理解脚本执行流程
- [ ] 能区分传统脚本和动态脚本
- [ ] 能说出主要技术栈

### 实践能力（1小时）
- [ ] 能成功启动项目
- [ ] 能添加新脚本
- [ ] 能修改现有功能
- [ ] 能解决常见问题

### 深入理解（2小时）
- [ ] 能理解Celery任务系统
- [ ] 能解释动态脚本系统
- [ ] 能理解前端组件架构
- [ ] 能分析数据流

## 🚨 常见问题解决

### Q1: 项目启动失败
**问题**：无法启动Django服务
**解决**：
```bash
# 安装依赖
pip install -r requirements.txt

# 检查数据库配置
python manage.py check

# 运行迁移
python manage.py migrate
```

### Q2: 前端页面空白
**问题**：前端页面无法加载
**解决**：
```bash
# 安装前端依赖
cd web
npm install

# 检查构建配置
npm run build

# 查看控制台错误
```

### Q3: 脚本执行失败
**问题**：点击脚本按钮无响应
**解决**：
```bash
# 检查Celery服务
python manage.py celery_worker

# 查看任务日志
tail -f celery.log

# 检查Redis连接
redis-cli ping
```

### Q4: 参数验证错误
**问题**：动态脚本参数验证失败
**解决**：
1. 检查 `script_configs.json` 格式
2. 验证参数类型和必填项
3. 查看后端验证错误信息
4. 重新加载配置

## 📖 推荐学习资源

### 官方文档
- [Vue 3 官方文档](https://vuejs.org/)
- [Django 官方文档](https://docs.djangoproject.com/)
- [Celery 官方文档](https://docs.celeryproject.org/)

### 项目文档
- `doc/PROJECT_LEARNING_GUIDE.md` - 详细学习指南
- `doc/PROJECT_ARCHITECTURE_OVERVIEW.md` - 架构概览
- `doc/DYNAMIC_SCRIPT_SYSTEM_GUIDE.md` - 动态脚本系统

### 代码示例
- `server/celery_app/scanner_file.py` - 扫描文件脚本示例
- `web/src/components/ScriptManagerLayout.vue` - 前端组件示例
- `server/myapp/views/celery_views.py` - 后端API示例

## 🎉 下一步学习

完成快速上手后，建议继续学习：

1. **深入学习架构**：理解系统设计原理
2. **实践开发**：添加更多功能
3. **性能优化**：提升系统性能
4. **部署运维**：学习生产环境部署

记住：学习是一个渐进的过程，不要急于求成。每学一个概念，都要确保理解透彻，再继续下一个。
