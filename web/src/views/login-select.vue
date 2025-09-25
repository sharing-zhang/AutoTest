<template>
  <div class="login-select-container">
    <div class="welcome-section">
      <img class="logo" :src="logo" alt="Logo">
      <h1 class="title">自动化测试运行系统</h1>
      <p class="subtitle">请选择您的登录方式</p>
    </div>
    
    <div class="login-options">
      <a-card class="login-card" @click="goToAdminLogin">
        <div class="card-content">
          <div class="icon admin-icon">
            <UserOutlined />
          </div>
          <h3>管理员登录</h3>
          <p>系统管理员专用登录入口</p>
          <a-button type="primary" size="large" block>
            管理员登录
          </a-button>
        </div>
      </a-card>
      
      <a-card class="login-card" @click="goToUserLogin">
        <div class="card-content">
          <div class="icon user-icon">
            <TeamOutlined />
          </div>
          <h3>普通用户登录</h3>
          <p>普通用户登录入口</p>
          <a-button type="primary" size="large" block>
            用户登录
          </a-button>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { UserOutlined, TeamOutlined } from '@ant-design/icons-vue'
import logo from '/@/assets/images/logo2.png'

const router = useRouter()

const goToAdminLogin = () => {
  router.push({ name: 'adminLogin' })
}

const goToUserLogin = () => {
  router.push({ name: 'userLogin' })
}
</script>

<style scoped lang="less">
.login-select-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.welcome-section {
  text-align: center;
  margin-bottom: 60px;
  
  .logo {
    width: 80px;
    height: 80px;
    margin-bottom: 24px;
  }
  
  .title {
    font-size: 32px;
    font-weight: bold;
    color: white;
    margin: 0 0 16px 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }
  
  .subtitle {
    color: rgba(255, 255, 255, 0.9);
    margin: 0;
    font-size: 18px;
  }
}

.login-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 40px;
  max-width: 800px;
  width: 100%;
}

.login-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  }
  
  :deep(.ant-card-body) {
    padding: 40px 30px;
  }
}

.card-content {
  text-align: center;
  
  .icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;
    font-size: 32px;
    color: white;
    
    &.admin-icon {
      background: linear-gradient(135deg, #ff6b6b, #ee5a24);
    }
    
    &.user-icon {
      background: linear-gradient(135deg, #4ecdc4, #44a08d);
    }
  }
  
  h3 {
    font-size: 24px;
    font-weight: bold;
    color: #333;
    margin: 0 0 12px 0;
  }
  
  p {
    color: #666;
    margin: 0 0 24px 0;
    font-size: 16px;
    line-height: 1.5;
  }
  
  .ant-btn {
    height: 44px;
    font-size: 16px;
    font-weight: 500;
  }
}
</style>
