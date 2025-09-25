import { defineStore } from 'pinia';
import {loginApi} from '/@/api/user';
import { setToken, clearToken } from '/@/utils/auth';
import { UserState } from './types';
import {USER_ID, USER_NAME, USER_TOKEN, ADMIN_USER_ID,ADMIN_USER_NAME,ADMIN_USER_TOKEN} from "/@/store/constants";


/**
 * store简单来说就是数据仓库的意思，我们数据都放在store里面。
 * 当然你也可以把它理解为一个公共组件，只不过该公共组件只存放数据，这些数据我们其它所有的组件都能够访问且可以修改。
 * pinia中使用defineStore定义store
 * 第一个参数是应用程序中 store 的唯一 id
 * 第二个参数是是一个对象，store的配置项，比如配置store内的数据，修改数据的方法等等。
 *
 * 返回一个函数使用use+模块名命名
 */
export const useUserStore = defineStore('user', {
  //固定写法，调用UserState中的各个属性进行初始化定义，undefined表示未定义
  state: (): UserState => ({
    user_id: localStorage.getItem('USER_ID') || undefined,
    user_name: localStorage.getItem('USER_NAME') || undefined,
    user_token: localStorage.getItem('USER_TOKEN') || undefined,

    admin_user_id: localStorage.getItem(ADMIN_USER_ID) || undefined,
    admin_user_name: localStorage.getItem(ADMIN_USER_NAME) || undefined,
    admin_user_token: localStorage.getItem(ADMIN_USER_TOKEN) || undefined,
  }),
  //getters 是一种特殊的函数，用于处理和计算 state 中的数据,接收 state 作为参数，并返回一个新的值或对象。
  getters: {},
  //使用Pinia的actions来调用接口可以更清晰地管理异步操作和状态变化
  actions: {

    // 管理员登录
    async adminLogin(loginForm) {
      //await 用于等待一个Promise的解析结果。当执行到await表达式时，当前的async函数暂停执行，直到等待的Promise进入成功（resolve）或拒绝（reject）状态，然后继续执行后续代码
      //如果await接收到的是一个reject，则实际返回为err异常，可使用try、catch结构来捕获由await抛出的异常
      //比如用户名密码错误时，返回为err = {code:1，msg:'用户名或密码错误'}，遇到报错时则会直接终止运行，返回err
      const result = await loginApi(loginForm);
      console.log('result==>', result)

      if(result.code === 0) {
        this.$patch((state)=>{
          state.admin_user_id = result.data.id
          state.admin_user_name = result.data.username
          state.admin_user_token = result.data.admin_token
          console.log('state==>', state)
        })

        localStorage.setItem(ADMIN_USER_TOKEN, result.data.admin_token)
        localStorage.setItem(ADMIN_USER_NAME, result.data.username)
        localStorage.setItem(ADMIN_USER_ID, result.data.id)
      }

      return result;
    },
    // 管理员登出
    async adminLogout() {
      // await userLogout();
      this.$patch((state)=>{
        localStorage.removeItem(ADMIN_USER_ID)
        localStorage.removeItem(ADMIN_USER_NAME)
        localStorage.removeItem(ADMIN_USER_TOKEN)

        state.admin_user_id = undefined
        state.admin_user_name = undefined
        state.admin_user_token = undefined
      })
    },

    // 普通用户登录
    async userLogin(loginForm) {
      const { userLoginApi } = await import('/@/api/user');
      const result = await userLoginApi(loginForm);
      console.log('userLogin result==>', result)

      if(result.code === 0) {
        this.$patch((state)=>{
          state.user_id = result.data.id
          state.user_name = result.data.username
          state.user_token = result.data.token
          console.log('user state==>', state)
        })

        localStorage.setItem('USER_TOKEN', result.data.token)
        localStorage.setItem('USER_NAME', result.data.username)
        localStorage.setItem('USER_ID', result.data.id)
      }

      return result;
    },

    // 普通用户登出
    async userLogout() {
      this.$patch((state)=>{
        localStorage.removeItem('USER_ID')
        localStorage.removeItem('USER_NAME')
        localStorage.removeItem('USER_TOKEN')

        state.user_id = undefined
        state.user_name = undefined
        state.user_token = undefined
      })
    },
  },
});
