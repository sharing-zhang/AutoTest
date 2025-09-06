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

### 基本配置

```bash
# 在scanDevUpdate页面的右上角添加一个脚本按钮
python manage.py setup_page_scripts \
  --page-route /scanDevUpdate \
  --script-name hellowrld \
  --button-text "Hello World" \
  --position top-right

# 在页面左侧边栏添加文件检查按钮
python manage.py setup_page_scripts \
  --page-route /scanDevUpdate \
  --script-name check_file \
  --button-text "检查文件" \
  --position sidebar-left
```

### 高级配置

#### 自定义按钮样式
```bash
python manage.py setup_page_scripts \
  --page-route /scanDevUpdate \
  --script-name data_analysis \
  --button-text "数据分析" \
  --position top-center \
  --button-style '{"type":"success","size":"large","backgroundColor":"#67C23A"}'
```

#### 自定义位置
```bash
python manage.py setup_page_scripts \
  --page-route /scanDevUpdate \
  --script-name hellowrld \
  --button-text "自定义位置" \
  --position custom \
  --custom-position '{"top":"100px","right":"50px","position":"fixed"}'
```

### 批量管理

#### 复制页面配置
```bash
# 将scanDevUpdate页面的按钮配置复制到其他页面
python manage.py setup_page_scripts \
  --page-route /anotherPage \
  --copy-from-page /scanDevUpdate
```

#### 清除页面配置
```bash
# 清除指定页面的所有按钮配置
python manage.py setup_page_scripts \
  --page-route /scanDevUpdate \
  --clear-all
```

#### 查看页面配置
```bash
# 列出页面的所有按钮配置
python manage.py setup_page_scripts \
  --page-route /scanDevUpdate \
  --list
```

## 预设配置示例

### 示例1：多位置布局
```bash
# 顶部导航栏样式
python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name hellowrld --button-text "测试" --position top-left --button-style '{"type":"primary","size":"small"}'

python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name check_file --button-text "文件检查" --position top-center --button-style '{"type":"info","size":"small"}'

python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name data_analysis --button-text "数据分析" --position top-right --button-style '{"type":"success","size":"small"}'
```

### 示例2：侧边栏工具箱
```bash
# 左侧工具栏
python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name hellowrld --button-text "🔧 测试" --position sidebar-left --button-style '{"type":"primary","size":"default"}'

python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name check_file --button-text "📁 文件" --position sidebar-left --button-style '{"type":"info","size":"default"}'

python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name data_analysis --button-text "📊 分析" --position sidebar-left --button-style '{"type":"success","size":"default"}'
```

### 示例3：浮动操作面板
```bash
# 浮动在页面中央的操作面板
python manage.py setup_page_scripts --page-route /scanDevUpdate --script-name hellowrld --button-text "执行测试" --position floating --button-style '{"type":"primary","size":"large"}'
```

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
