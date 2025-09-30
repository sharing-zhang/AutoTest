<template>
  <div class="script-manager-layout">
    <!-- 脚本列表组件 -->
    <ScriptButtons
      :scripts="allConfiguredScripts"
      :page-route="pageRoute"
      @script-executed="handleScriptExecuted"
    />
    
    <!-- 页面内容插槽 - 允许父组件在此处插入页面主要内容 -->
    <slot></slot>
    
    <!-- 钉钉机器人消息同步弹窗 -->
    <DingtalkRobot
      ref="dingtalkRobotRef"
      :visible="dingtalkDialog.visible"
      :title="dingtalkDialog.title"
      :record-data="dingtalkDialog.recordData"
      @update:visible="dingtalkDialog.visible = $event"
      @success="handleDingtalkSuccess"
      @error="handleDingtalkError"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DingtalkRobot from './DingtalkRobot.vue'
import ScriptButtons from './ScriptButtons.vue'
import { useScriptManager } from '/@/composables/useScriptManager'
import { BASE_URL } from '/@/store/constants'

// 组件props接口定义
interface Props {
  pageRoute: string // 页面路由，用于确定当前页面的脚本配置
}

// 接收父组件传入的props
const props = defineProps<Props>()

// 使用脚本管理组合式函数，获取脚本相关的状态和方法
const {
  allConfiguredScripts, // 所有已配置的脚本列表
  availableScripts,     // 可用脚本列表
  loadScripts,          // 加载脚本列表的方法
  executeScript,        // 执行脚本的方法
  onRefreshData,        // 注册数据刷新回调的方法
  emitRefreshData       // 触发数据刷新的方法
} = useScriptManager(props.pageRoute)

// 参数弹窗状态管理已移除，现在在页面组件中直接处理

// 钉钉机器人组件的引用
const dingtalkRobotRef = ref()

// 钉钉机器人弹窗状态管理
const dingtalkDialog = reactive({
  visible: false,
  title: '扫描结果同步钉钉机器人',
  recordData: null as any
})

// 组件挂载时的初始化操作
onMounted(() => {
  loadScripts() // 加载当前页面的脚本配置
})

// 监听数据变化，确保父组件能获取到最新数据
watch([availableScripts, allConfiguredScripts], () => {
  console.log('ScriptManagerLayout 数据变化:', {
    availableScripts: availableScripts.value.length,
    allConfiguredScripts: allConfiguredScripts.value.length
  })
}, { deep: true })

// 处理脚本执行完成的回调
const handleScriptExecuted = (result: any) => {
  console.log('脚本执行完成:', result)
  
  // 触发数据刷新
  emitRefreshData()
}

// 弹窗处理逻辑已移除，现在在页面组件中直接处理

/**
 * 刷新脚本数据，向外暴露的方法
 */
const refreshData = () => {
  loadScripts()
}

/**
 * 允许父组件注册数据刷新回调
 * @param callback 回调函数
 */
const onDataRefresh = (callback: Function) => {
  onRefreshData(callback)
}

/**
 * 打开钉钉机器人消息同步弹窗
 * @param recordData 要发送的记录数据
 */
const openDingtalkDialog = (recordData: any) => {
  dingtalkDialog.recordData = recordData
  dingtalkDialog.visible = true
}

/**
 * 处理钉钉机器人发送成功
 */
const handleDingtalkSuccess = () => {
  console.log('钉钉机器人消息发送成功')
  // 可以在这里触发数据刷新
  emitRefreshData()
}

/**
 * 处理钉钉机器人发送失败
 * @param error 错误信息
 */
const handleDingtalkError = (error: any) => {
  console.error('钉钉机器人消息发送失败:', error)
}

// 通过defineExpose暴露方法给父组件使用
defineExpose({
  refreshData,        // 刷新数据方法
  onDataRefresh,      // 注册刷新回调方法
  loadScripts,        // 加载脚本方法
  executeScript,      // 执行脚本方法
  openDingtalkDialog, // 打开钉钉机器人弹窗方法
  emitRefreshData,    // 触发数据刷新方法
  availableScripts,   // 暴露可用脚本列表
  allConfiguredScripts // 暴露已配置脚本列表
})
</script>

<style scoped>
/* 脚本管理器布局容器 */
.script-manager-layout {
  position: relative;
  width: 100%;
  height: 100%;
}

/* 脚本按钮包装器样式已移除 */
</style>