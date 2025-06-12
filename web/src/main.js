/*
main.js是整个Vue应用的入口文件
main.js负责初始化Vue应用实例、加载全局配置、注册全局组件、引入插件以及挂载Vue实例到DOM上。
通过main.js，我们可以配置Vue应用的各种选项、引入需要的库或者插件，以及进行一些全局的初始化操作
*/

// 从 Vue 库中导入 createApp 函数
import { createApp } from 'vue';
//Ant Design Vue的UI组件库全局引入
import Antd from 'ant-design-vue';

import App from './App.vue';
import router from './router';
import piniaStore from './store';

import bootstrap from './core/bootstrap';
import '/@/styles/reset.less';
import '/@/styles/index.less';

//Vue 应用的起点，所有组件、插件、路由等都需要通过这个实例进行注册和配置
const app = createApp(App);

//使用 .use() 方法安装插件
app.use(Antd);
app.use(router);
app.use(piniaStore);
app.use(bootstrap)

//最后，我们将应用挂载到页面的 #app 元素上
app.mount('#app');
