> 基于python+django+vue.js开发的自动化测试运行系统

### 功能介绍

平台采用B/S结构，后端采用主流的Python语言进行开发，前端采用主流的Vue.js进行开发。

功能包括：资源扫描、自动化钓鱼、日志管理、系统信息。

### 代码结构

- server目录是后端代码
- web目录是前端代码

### 部署运行

#### 后端运行步骤

(1) 安装python 3.8

(2) 安装依赖。进入server目录下，执行 pip install -r requirements.txt

<font color=red size=4>注意：协同开发人员，只需执行上方两步即可，严禁执行下方3、4、5，否则会将数据库重构。</font>

(3) 安装mysql 5.7数据库，并创建数据库，命名为xxx（自定义），创建SQL如下：
```
CREATE DATABASE IF NOT EXISTS xxx（自定义） DEFAULT CHARSET utf8 COLLATE utf8_general_ci
```
(4) 恢复xxx.sql数据。在mysql下依次执行如下命令：

```
mysql> use xxx;
mysql> source D:/xxx/xxx/xxx.sql;
```

(5) 在server目录下，启动django服务，执行命令：
```
python manage.py runserver 0.0.0.0:8000
```

#### 前端运行步骤

(1) 安装node 16.14

(2) 进入web目录下，安装依赖，执行:
```
npm install 
npm install element-plus --save
```
(3) 在web目录下，启动前端项目，执行命令：
```
npm run dev -- --port 8001
```

#### 常见问题

- 连接后端失败怎么办？

编辑前端的constants.js文件，将base_url设置为你自己电脑的ip和端口

- 需要什么数据库版本？

本系统采用的是mysql5.7开发的，理论上5.7以上都支持

- pip安装依赖失败怎么样？

建议使用国内镜像源安装


