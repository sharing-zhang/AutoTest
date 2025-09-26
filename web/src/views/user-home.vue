<template>
  <div class="user-home">
    <a-layout>
      <a-layout-header class="header">
        <div class="header-content">
          <img class="logo" :src="logo" alt="Logo">
          <span class="title">自动化测试运行系统</span>
          <div class="user-info">
            <span>欢迎，{{ userStore.user_name }}</span>
            <a-button type="link" @click="handleLogout">退出</a-button>
          </div>
        </div>
      </a-layout-header>
      
      <a-layout-content class="content">
        <div class="welcome-section">
          <h1>欢迎使用自动化测试系统</h1>
          <p>您已成功登录普通用户系统</p>
          
          <div class="feature-cards">
            <a-card title="脚本执行" class="feature-card">
              <p>执行各种自动化测试脚本</p>
              <a-button type="primary" @click="goToScripts">进入脚本管理</a-button>
            </a-card>
            
            <a-card title="任务查看" class="feature-card">
              <p>查看您的任务执行记录</p>
              <a-button type="primary" @click="goToTasks">查看任务</a-button>
            </a-card>
            
            <a-card title="个人信息" class="feature-card">
              <p>管理您的个人信息</p>
              <a-button type="primary" @click="goToProfile">个人中心</a-button>
            </a-card>
          </div>
        </div>
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useUserStore } from '/@/store'
import logo from '/@/assets/images/logo2.png'

const router = useRouter()
const userStore = useUserStore()

onMounted(() => {
  // 检查用户是否已登录
  if (!userStore.user_name) {
    message.warning('请先登录')
    router.push({ name: 'userLogin' })
  }
})

const goToScripts = () => {
  message.info('脚本管理功能开发中...')
}

const goToTasks = () => {
  message.info('任务查看功能开发中...')
}

const goToProfile = () => {
  message.info('个人中心功能开发中...')
}

const handleLogout = () => {
  userStore.userLogout().then(() => {
    message.success('退出成功')
    router.push({ name: 'userLogin' })
  })
}
</script>

<style scoped lang="less">
.user-home {
  min-height: 100vh;
}

.header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  .header-content {
    display: flex;
    align-items: center;
    height: 100%;
    padding: 0 24px;
    
    .logo {
      width: 32px;
      height: 32px;
      margin-right: 16px;
    }
    
    .title {
      font-size: 20px;
      font-weight: bold;
      color: #333;
      flex: 1;
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 16px;
      
      span {
        color: #666;
      }
    }
  }
}

.content {
  padding: 40px;
  background: #f5f5f5;
  min-height: calc(100vh - 64px);
}

.welcome-section {
  max-width: 1200px;
  margin: 0 auto;
  
  h1 {
    text-align: center;
    color: #333;
    margin-bottom: 8px;
  }
  
  p {
    text-align: center;
    color: #666;
    margin-bottom: 40px;
    font-size: 16px;
  }
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-top: 40px;
}

.feature-card {
  text-align: center;
  
  :deep(.ant-card-body) {
    padding: 24px;
  }
  
  p {
    margin: 16px 0 24px 0;
    color: #666;
  }
  
  .ant-btn {
    width: 100%;
  }
}
</style>
