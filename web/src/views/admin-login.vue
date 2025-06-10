<!-- 登录页面 -->
<template>
  <div id="userLayout">
    <div class="user-layout-header">
      <img class="logo" :src="logoImage" alt="">
      <span>自动化测试运行系统</span>
    </div>
    <div class="main-container">
      <div class="main">
        <div class="main_right">
          <h2 class="sys_title">管理员登录</h2>
          <!-- 创建表单，验证和提交表单数据 -->
          <a-form
              ref="myform"
              layout="vertical"
              :model="data.loginForm"
              :rules="data.rules"
              :hideRequiredMark="true"
          >
            <a-form-item name="username" label="用户名" :colon="false">
              <a-input
                  size="large"
                  placeholder="请输入登录用户名"
                  v-model:value="data.loginForm.username"
                  @pressEnter="handleSubmit">
              </a-input>
            </a-form-item>
            <a-form-item name="password" label="密码" :colon="false">
              <a-input
                  size="large"
                  type="password"
                  placeholder="请输入登录密码"
                  v-model:value="data.loginForm.password"
                  @pressEnter="handleSubmit">
              </a-input>
            </a-form-item>
            <a-form-item style="padding-top: 24px">
              <a-button
                  class="login-button"
                  type="primary"
                  :loading="loginBtn"
                  size="large"
                  block
                  @click="handleSubmit"
              >
                登录
              </a-button>
            </a-form-item>
          </a-form>
          <div class="error-tip"></div>
        </div>
      </div>

    </div>
    <footer class="footer">
      <div class="copyright">
        <span></span>
      </div>
    </footer>
  </div>

</template>

<script setup lang="ts">
import {useUserStore} from '/@/store';
import logoImage from '/@/assets/images/logo2.png';

const router = useRouter();
const userStore = useUserStore();

import {message} from "ant-design-vue";

const myform = ref()

const loginBtn = ref<Boolean>(false)
const checked = ref<Boolean>(false)
const data = reactive({
  loginForm: {
    username: '',
    password: ''
  },
  rules: {
    username: [
      {required: true, message: '请输入用户名', trigger: 'blur'}
    ],
    password: [
      {required: true, message: '请输入密码', trigger: 'blur'}
    ]
  }
})

// 点击【登录】按钮的事件处理
const handleSubmit = () => {
  // 表单验证  validate触发表单验证，验证不通过会阻断后续操作
  myform.value?.validate().then(() => {
    handleLogin()
  }).catch(() => {
    message.warn('用户名与密码 不能为空')
  })
}

// 登录校验
const handleLogin = () => {
  userStore.adminLogin({
    username: data.loginForm.username,
    password: data.loginForm.password
  }).then(res=>{
    loginSuccess()
  }).catch(err=> {
      message.warn(err.msg || '登录失败，用户名或密码错误')
  })
}

const loginSuccess = () => {
  //跳转
  router.push({ path: '/admin' })
  message.success('登录成功！')
}


</script>

<!--
  1. <style>标签内的CSS代码是用Less语法编写的,scoped可以确保样式的局部性，避免全局污染
  2. #userLayout 表示布局组件，统一相似业务类型页面的布局，例如头部、底部和侧边栏等公共元素，这里指代登录页面的一些公共元素
-->
<style lang="less" scoped>

#userLayout {
  position: relative;
  height: 100vh;

  .user-layout-header {
    height: 80px;
    padding: 0 24px;
    color: fade(#000, 85%);
    font-size: 24px;
    font-weight: bold;
    line-height: 80px;

    .logo {
      width: 50px;
      height: 50px;
      margin-right: 16px;
      margin-top: -4px;
    }
  }

  .main-container {
    width: 100%;
    height: calc(100vh - 160px);
    background-image: url('../assets/images/admin-login-bg.jpg');
    background-position: center;
    background-repeat: no-repeat;
    background-size: cover;

    .main {
      position: absolute;
      right: 80px;
      top: 50%;
      display: flex;
      transform: translate(0, -50%);
      border-radius: 10px;
      overflow: hidden;
      -webkit-box-shadow: 2px 2px 6px #aaa;
      box-shadow: 2px 2px 6px #aaa;

      .main_right {
        background: #ffffff;
        padding: 24px;
        width: 420px;
        user-select: none;

        .sys_title {
          font-size: 24px;
          color: fade(#000, 85%);
          font-weight: bold;
          user-select: none;
          padding-bottom: 8px;
        }

        :deep(.ant-form-item label) {
          font-weight: bold;
        }

        .flex {
          align-items: center;
          display: flex;
          justify-content: space-between;
        }

        .forget_password {
          cursor: pointer;
        }

        .login-button {
          background: linear-gradient(128deg, #00aaeb, #00c1cd 59%, #0ac2b0 100%);
        }
      }

      .error-tip {
        text-align: center;
      }
    }
  }

  .footer {
    height: 80px;
  }
}

</style>
