<template>
  <div class="script-manager-layout">
    <!-- 动态脚本按钮区域 -->
    <div class="script-buttons-wrapper">
      <!-- 渲染所有可能的位置 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="top-left" 
        @execute-script="handleScriptExecution"
      />
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="top-right" 
        @execute-script="handleScriptExecution"
      />
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="top-center" 
        @execute-script="handleScriptExecution"
      />
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="bottom-left" 
        @execute-script="handleScriptExecution"
      />
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="bottom-right" 
        @execute-script="handleScriptExecution"
      />
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="bottom-center" 
        @execute-script="handleScriptExecution"
      />
    </div>
    
    <!-- 页面内容插槽 -->
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import ScriptButtons from './ScriptButtons.vue'
import { useScriptManager } from '/@/composables/useScriptManager'

interface Props {
  pageRoute: string
}

const props = defineProps<Props>()

// 使用脚本管理组合式函数
const {
  allConfiguredScripts,
  loadScripts,
  executeScript,
  onRefreshData
} = useScriptManager(props.pageRoute)

// 组件挂载时加载脚本
onMounted(() => {
  loadScripts()
})

// 处理脚本执行
const handleScriptExecution = (script: any) => {
  if (script.tasks && script.tasks.length > 0) {
    const task = script.tasks[0] // 默认执行第一个任务
    executeScript(script, task)
  } else {
    console.error('脚本没有可执行的任务:', script)
  }
}

// 向外暴露刷新数据的方法
const refreshData = () => {
  loadScripts()
}

// 允许父组件注册数据刷新回调
const onDataRefresh = (callback: Function) => {
  onRefreshData(callback)
}

// 暴露方法给父组件
defineExpose({
  refreshData,
  onDataRefresh,
  loadScripts
})
</script>

<style scoped>
.script-manager-layout {
  position: relative;
  width: 100%;
  height: 100%;
}

.script-buttons-wrapper {
  position: relative;
  width: 100%;
  min-height: 60px;
  margin-bottom: 16px;
}
</style>
