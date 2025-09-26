# 动态脚本按钮位置管理指南

## 概述

系统现在支持在不同页面的不同位置动态配置脚本执行按钮。您可以灵活地指定按钮在页面的哪个位置显示，支持多种预设位置和自定义位置。

## 支持的位置

### 1. 顶部位置
- `top-left`: 页面左上角
- `top-right`: 页面右上角  
- `top-center`: 页面顶部中央

### 2. 底部位置
- `bottom-left`: 页面左下角
- `bottom-right`: 页面右下角
- `bottom-center`: 页面底部中央

### 3. 侧边栏位置
- `sidebar-left`: 左侧固定侧边栏
- `sidebar-right`: 右侧固定侧边栏

### 4. 特殊位置
- `floating`: 浮动在页面中央
- `custom`: 自定义位置（需要提供具体坐标）

## 使用方法
- button_configs.json中配置参数
- 运行命令同步到数据库：python manage.py setup_page_scripts --config-file myapp\management\commands\button_configs.json

## 按钮样式参数

### 基本样式
- `type`: 按钮类型 (`primary`, `success`, `warning`, `danger`, `info`, `text`)
- `size`: 按钮大小 (`large`, `default`, `small`)

### 自定义样式
- `color`: 文字颜色
- `backgroundColor`: 背景色
- `borderColor`: 边框颜色
- `borderRadius`: 圆角大小
- `padding`: 内边距
- `margin`: 外边距

## 自定义位置参数

对于 `position: custom`，可以使用以下CSS属性：
- `top`: 距离顶部距离
- `left`: 距离左侧距离
- `right`: 距离右侧距离
- `bottom`: 距离底部距离
- `position`: CSS定位类型 (`absolute`, `fixed`, `relative`)

## 多页面支持

系统支持为不同页面配置不同的按钮布局：

```bash
# 为主页配置按钮
python manage.py setup_page_scripts --page-route /main --script-name hellowrld --position top-right

# 为设置页配置按钮
python manage.py setup_page_scripts --page-route /settings --script-name check_file --position sidebar-left

# 为报告页配置按钮
python manage.py setup_page_scripts --page-route /reports --script-name data_analysis --position floating
```

## 响应式设计

按钮组件自动适配移动设备：
- 侧边栏按钮在移动设备上会移到底部
- 浮动按钮在小屏幕上会调整位置
- 按钮大小会根据屏幕尺寸调整

## 注意事项

1. **位置冲突**: 多个按钮配置相同位置时，会按 `display_order` 排序显示
2. **样式优先级**: 自定义样式会覆盖默认样式
3. **页面路由**: 确保页面路由名称与实际路由匹配
4. **脚本状态**: 只有已注册且激活的脚本才能配置按钮

## 故障排除

### 按钮不显示
1. 检查脚本是否已注册：`python manage.py register_scripts --list`
2. 检查页面配置：`python manage.py setup_page_scripts --page-route /yourpage --list`
3. 检查脚本是否激活

### 样式不生效
1. 检查JSON格式是否正确
2. 确认CSS属性名称正确
3. 检查浏览器控制台是否有错误

### 自定义位置问题
1. 确认position设置为 `custom`
2. 检查custom-position的JSON格式
3. 验证CSS属性值的有效性
