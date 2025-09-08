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
    
    <!-- 参数输入弹窗 -->
    <el-dialog
      v-model="parameterDialog.visible"
      :title="`${parameterDialog.scriptName} - 参数配置`"
      width="600px"
      :before-close="handleDialogClose"
    >
      <div v-if="parameterDialog.visible">
        <DynamicScriptForm
          ref="parameterFormRef"
          :script-name="parameterDialog.scriptName"
          :show-script-selector="false"
          :show-advanced="false"
          @script-executed="handleParameterScriptExecuted"
        />
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ScriptButtons from './ScriptButtons.vue'
import DynamicScriptForm from './DynamicScriptForm.vue'
import { useScriptManager } from '/@/composables/useScriptManager'
import { BASE_URL } from '/@/store/constants'

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

// 参数弹窗状态
const parameterDialog = reactive({
  visible: false,
  scriptName: '',
  script: null as any,
  task: null as any
})

// 参数表单引用
const parameterFormRef = ref()

// 组件挂载时加载脚本
onMounted(() => {
  loadScripts()
})

// 检查脚本是否需要参数
const checkScriptParameters = async (scriptName: string) => {
  try {
    console.log('检查脚本参数:', scriptName)
    
    // 尝试不同的脚本名称格式
    const possibleNames = [
      scriptName,                    // 原始名称
      scriptName.replace('.py', ''), // 移除.py后缀（如果存在）
      scriptName + '.py'            // 添加.py后缀
    ]
    
    for (const name of possibleNames) {
      console.log('尝试脚本名称:', name)
      const response = await fetch(`${BASE_URL}/myapp/api/script-configs/?script_name=${encodeURIComponent(name)}`)
      const data = await response.json()
      
      console.log('API响应:', data)
      
      if (data.success && data.script_config) {
        const parameters = data.script_config.parameters || []
        const requiredParams = parameters.filter((p: any) => p.required)
        
        console.log('找到脚本配置:', { parameters: parameters.length, required: requiredParams.length })
        
        return {
          hasParameters: parameters.length > 0,
          hasRequiredParameters: requiredParams.length > 0,
          parameters: parameters
        }
      }
    }
    
    console.log('未找到脚本配置')
    return { hasParameters: false, hasRequiredParameters: false, parameters: [] }
  } catch (error) {
    console.error('检查脚本参数失败:', error)
    return { hasParameters: false, hasRequiredParameters: false, parameters: [] }
  }
}

// 处理脚本执行
const handleScriptExecution = async (script: any) => {
  if (!script.tasks || script.tasks.length === 0) {
    console.error('脚本没有可执行的任务:', script)
    return
  }

  const task = script.tasks[0] // 默认执行第一个任务
  
  // 检查脚本是否需要参数（对所有脚本检查）
  const scriptName = script.name || script.script_name
  if (scriptName) {
    const paramInfo = await checkScriptParameters(scriptName)
    
    if (paramInfo.hasRequiredParameters) {
      // 需要必填参数，显示参数输入弹窗
      parameterDialog.scriptName = scriptName
      parameterDialog.script = script
      parameterDialog.task = task
      parameterDialog.visible = true
      return
    } else if (paramInfo.hasParameters) {
      // 有可选参数，询问是否需要配置
      try {
        await ElMessageBox.confirm(
          `脚本 "${script.name}" 有可配置的参数，是否需要配置参数？`,
          '参数配置',
          {
            confirmButtonText: '配置参数',
            cancelButtonText: '直接执行',
            type: 'info'
          }
        )
        
        // 用户选择配置参数
        parameterDialog.scriptName = scriptName
        parameterDialog.script = script
        parameterDialog.task = task
        parameterDialog.visible = true
        return
      } catch {
        // 用户选择直接执行，继续执行脚本
      }
    }
  }
  
  // 直接执行脚本（无参数或用户选择直接执行）
  executeScript(script, task)
}

// 处理弹窗关闭
const handleDialogClose = () => {
  parameterDialog.visible = false
  parameterDialog.scriptName = ''
  parameterDialog.script = null
  parameterDialog.task = null
}

// 处理参数表单执行完成
const handleParameterScriptExecuted = (result: any) => {
  console.log('参数表单脚本执行完成:', result)
  
  // 关闭弹窗
  handleDialogClose()
  
  if (result.success) {
    ElMessage.success('脚本执行成功！')
  } else {
    ElMessage.error(`脚本执行失败: ${result.error || '未知错误'}`)
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
