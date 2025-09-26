// 定义路由关系，路由表
const constantRouterMap = [

  {
    path: '/',
    redirect: '/login-select',
  },
  {
    path: '/login-select',
    name: 'loginSelect',
    component: () => import('/@/views/login-select.vue'),
  },
  {
    path: '/adminLogin',
    name: 'adminLogin',
    component: () => import('/@/views/admin-login.vue'),
  },
  {
    path: '/userLogin',
    name: 'userLogin',
    component: () => import('/@/views/user-login.vue'),
  },
  {
    path: '/userHome',
    name: 'userHome',
    component: () => import('/@/views/user-home.vue'),
  },
  {
    path: '/admin',
    name: 'admin',
    redirect: '/admin/scanUpdate',
    component: () => import('/@/views/main.vue'),
    children: [
      { path: 'scanUpdate', name: 'scanUpdate', component: () => import('/@/views/scanUpdate.vue') },
      { path: 'scanUpdate/scanDevUpdate', name: 'scanDevUpdate', component: () => import('/@/views/scanDevUpdate.vue') },

      { path: 'overview', name: 'overview', component: () => import('/@/views/overview.vue') },
      { path: 'thing', name: 'thing', component: () => import('/@/views/thing.vue') },
      { path: 'plugin', name: 'plugin', component: () => import('/@/views/plugin.vue') },
      { path: 'user', name: 'user', component: () => import('/@/views/user.vue') },
      { path: 'loginLog', name: 'loginLog', component: () => import('/@/views/login-log.vue') },
      { path: 'opLog', name: 'opLog', component: () => import('/@/views/op-log.vue') },
      { path: 'errorLog', name: 'errorLog', component: () => import('/@/views/error-log.vue') },
      { path: 'sysInfo', name: 'sysInfo', component: () => import('/@/views/sys-info.vue') },
      { path: 'CheckConfigTime', name: 'CheckConfigTime', component: () => import('/@/views/CheckConfigTime.vue') },
      { path: 'CheckReward', name: 'CheckReward', component: () => import('/@/views/CheckReward.vue') },
      { path: 'checkConfigExist', name: 'checkConfigExist', component: () => import('/@/views/checkConfigExist.vue') },
      { path: 'CheckText', name: 'CheckText', component: () => import('/@/views/CheckText.vue') },

    ]
  },
];

export default constantRouterMap;
