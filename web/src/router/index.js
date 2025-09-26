/*创建路由器步骤：
1. 导入vue-router
2. 定义路由关系（root.js）中实现了
3. 创建路由器
4. export default router导出路由
* */

import {createRouter, createWebHistory} from 'vue-router';
// root代表路由表
import root from './root';

import { ADMIN_USER_TOKEN, USER_TOKEN } from '/@/store/constants'

// 路由权限白名单
const allowList = ['adminLogin', 'userLogin', 'userHome', 'loginSelect', 'login', 'register', 'portal', 'search', 'detail', '403', '404']
// 前台登录地址
const loginRoutePath = '/index/login'
// 后台登录地址
const adminLoginRoutePath = '/adminLogin'

//创建路由关系
const router = createRouter({
  //history模式,URL更加美观，不带有#，更接近传统的网站URL
  history: createWebHistory(),
  routes: root,
});


/*路由跳转的时候，我们需要做一些权限判断或者其他操作。这个时候就需要使用路由钩子函数。
定义：路由钩子主要是给使用者在路由发生变化时进行一些特殊的处理而定义的函数
next()：允许跳转到to路由。
next(false)：中止本次跳转，留在当前页面。
next('/login')：重定向到指定路径（如未登录时跳转到登录页）。
next(error)：传入一个Error对象，终止导航并触发错误处理‌*/
router.beforeEach(async (to, from, next) => {

  //控制台输出日志
  console.log(to,from)
  
  /** 路由权限控制 **/
  
  // 1. 登录页面白名单 - 优先处理
  if (allowList.includes(to.name)) {
    next()
    return
  }
  
  // 2. 管理员路由权限控制
  if (to.path.startsWith('/admin')) {
    //localStorage.getItem获取存储的ADMIN_USER_TOKEN的值，如果存在token值
    if (localStorage.getItem(ADMIN_USER_TOKEN)) {
      //===表示的是绝对的相等,先判断数据类型，再判断值，都一样时才行
      if (to.path === adminLoginRoutePath) {
        //跳转到根路径，不能直接跳转到/adminLogin,容易死循环
        next({ path: '/' })
      }
      else {
        next()
      }
    }
    // 如果存在普通用户token，也允许访问管理员页面
    else if (localStorage.getItem(USER_TOKEN)) {
      next()
    }
    //如果不存在任何token值
    else {
      //没有token，跳转到登录页面路由下，并且附带上query中的参数
      next(
            {
              path: adminLoginRoutePath,
              query:
                  {
                    redirect: to.fullPath
                  }
            }
          )
    }
  }
  // 3. 普通用户路由权限控制
  else if (to.path.startsWith('/user')) {
    if (localStorage.getItem(USER_TOKEN)) {
      // 已登录，允许访问
      next()
    } else {
      // 未登录，跳转到用户登录页
      if (to.name === 'userLogin') {
        next()
      } else {
        next({ path: '/userLogin' })
      }
    }
  }
  // 4. 其他路由（登录选择页等）
  else {
    // 默认跳转到登录选择页
    next({ path: '/login-select' })
  }

});

router.afterEach((_to) => {
  // 其中html的id对应index.html，表示所有页面的基础模板，这里控制所有页面在路由跳转完成后，滚动条要回到顶部
  let html = document.getElementById("html");
  if(html){
    html.scrollTo(0, 0)
  }
});

export default router;
