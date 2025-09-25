<template>
  <div class="user-login-container">
    <div class="login-form-wrapper">
      <div class="login-header">
        <img class="logo" :src="logo" alt="Logo">
        <h1 class="title">用户登录</h1>
        <p class="subtitle">普通用户登录系统</p>
      </div>
      
      <a-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        @finish="handleLogin"
        class="login-form"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            :prefix="h(UserOutlined)"
          />
        </a-form-item>
        
        <a-form-item name="password">
          <a-input-password
            v-model:value="loginForm.password"
            placeholder="请输入密码"
            size="large"
            :prefix="h(LockOutlined)"
          />
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="loading"
            block
          >
            登录
          </a-button>
        </a-form-item>
        
        <div class="login-footer">
          <a-button type="link" @click="showRegister = true">
            没有账号？立即注册
          </a-button>
          <a-button type="link" @click="goToAdminLogin">
            管理员登录
          </a-button>
        </div>
      </a-form>
    </div>
    
    <!-- 注册弹窗 -->
    <a-modal
      v-model:visible="showRegister"
      title="用户注册"
      :footer="null"
      width="400px"
    >
      <a-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        @finish="handleRegister"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="registerForm.username"
            placeholder="请输入用户名"
            :prefix="h(UserOutlined)"
          />
        </a-form-item>
        
        <a-form-item name="password">
          <a-input-password
            v-model:value="registerForm.password"
            placeholder="请输入密码"
            :prefix="h(LockOutlined)"
          />
        </a-form-item>
        
        <a-form-item name="confirmPassword">
          <a-input-password
            v-model:value="registerForm.confirmPassword"
            placeholder="请确认密码"
            :prefix="h(LockOutlined)"
          />
        </a-form-item>
        
        <a-form-item name="nickname">
          <a-input
            v-model:value="registerForm.nickname"
            placeholder="请输入昵称"
            :prefix="h(SmileOutlined)"
          />
        </a-form-item>
        
        <a-form-item name="email">
          <a-input
            v-model:value="registerForm.email"
            placeholder="请输入邮箱"
            :prefix="h(MailOutlined)"
          />
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="registerLoading"
            block
          >
            注册
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined, SmileOutlined, MailOutlined } from '@ant-design/icons-vue'
import { userLoginApi, userRegisterApi } from '/@/api/user'
import logo from '/@/assets/images/logo2.png'

const router = useRouter()

// 登录表单
const loginForm = reactive({
  username: '',
  password: ''
})

// 注册表单
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  email: ''
})

// 状态
const loading = ref(false)
const registerLoading = ref(false)
const showRegister = ref(false)

// 表单引用
const loginFormRef = ref()
const registerFormRef = ref()

// 登录验证规则
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 注册验证规则
const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string) => {
        if (value !== registerForm.password) {
          return Promise.reject('两次密码输入不一致')
        }
        return Promise.resolve()
      },
      trigger: 'blur'
    }
  ],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  try {
    loading.value = true
    const result = await userLoginApi(loginForm)
    
    if (result.code === 0) {
      message.success('登录成功')
      // 保存用户信息到localStorage
      localStorage.setItem('USER_TOKEN', result.data.token)
      localStorage.setItem('USER_ID', result.data.id)
      localStorage.setItem('USER_NAME', result.data.username)
      
      // 跳转到用户首页（这里可以自定义跳转页面）
      router.push({ name: 'userHome' })
    } else {
      message.error(result.msg || '登录失败')
    }
  } catch (error: any) {
    message.error(error.msg || '登录失败')
  } finally {
    loading.value = false
  }
}

// 处理注册
const handleRegister = async () => {
  try {
    registerLoading.value = true
    const result = await userRegisterApi({
      username: registerForm.username,
      password: registerForm.password,
      nickname: registerForm.nickname,
      email: registerForm.email
    })
    
    if (result.code === 0) {
      message.success('注册成功，请登录')
      showRegister.value = false
      // 清空注册表单
      Object.keys(registerForm).forEach(key => {
        registerForm[key] = ''
      })
    } else {
      message.error(result.msg || '注册失败')
    }
  } catch (error: any) {
    message.error(error.msg || '注册失败')
  } finally {
    registerLoading.value = false
  }
}

// 跳转到管理员登录
const goToAdminLogin = () => {
  router.push({ name: 'adminLogin' })
}
</script>

<style scoped lang="less">
.user-login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-form-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  
  .logo {
    width: 60px;
    height: 60px;
    margin-bottom: 16px;
  }
  
  .title {
    font-size: 24px;
    font-weight: bold;
    color: #333;
    margin: 0 0 8px 0;
  }
  
  .subtitle {
    color: #666;
    margin: 0;
    font-size: 14px;
  }
}

.login-form {
  .ant-form-item {
    margin-bottom: 20px;
  }
  
  .ant-btn {
    height: 44px;
    font-size: 16px;
    font-weight: 500;
  }
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  
  .ant-btn-link {
    padding: 0 8px;
    font-size: 14px;
  }
}

:deep(.ant-modal-body) {
  padding: 24px;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
