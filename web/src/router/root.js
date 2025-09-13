// 定义路由关系，路由表
const constantRouterMap = [

  {
    path: '/',
    redirect: '/admin',
  },
  {
    path: '/adminLogin',
    name: 'adminLogin',
    component: () => import('/@/views/admin-login.vue'),
  },
  {
    path: '/admin',
    name: 'admin',
    redirect: '/admin/thing',
    component: () => import('/@/views/main.vue'),
    children: [
      { path: 'scanUpdate', name: 'scanUpdate', component: () => import('/@/views/scanUpdate.vue') },
      { path: 'scanUpdate/scanDevUpdate', name: 'scanDevUpdate', component: () => import('/@/views/scanDevUpdate.vue') },
      { path: 'scanUpdate/CheckReward', name: 'CheckReward', component: () => import('/@/views/CheckReward.vue') },

      { path: 'overview', name: 'overview', component: () => import('/@/views/overview.vue') },
      { path: 'thing', name: 'thing', component: () => import('/@/views/thing.vue') },
      { path: 'plugin', name: 'plugin', component: () => import('/@/views/plugin.vue') },
      { path: 'user', name: 'user', component: () => import('/@/views/user.vue') },
      { path: 'loginLog', name: 'loginLog', component: () => import('/@/views/login-log.vue') },
      { path: 'opLog', name: 'opLog', component: () => import('/@/views/op-log.vue') },
      { path: 'errorLog', name: 'errorLog', component: () => import('/@/views/error-log.vue') },
      { path: 'sysInfo', name: 'sysInfo', component: () => import('/@/views/sys-info.vue') },
      { path: 'CheckConfigTime', name: 'CheckConfigTime', component: () => import('/@/views/CheckConfigTime.vue') },
    ]
  },
];

export default constantRouterMap;
