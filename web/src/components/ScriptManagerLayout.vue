<template>
  <div class="script-manager-layout">
    <!-- 动态脚本按钮区域 - 在页面的不同位置显示脚本执行按钮 -->
    <div class="script-buttons-wrapper">
      <!-- 渲染所有可能的位置，每个位置对应页面的不同区域 -->
      <!-- 左上角按钮区域 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="top-left" 
        @execute-script="handleScriptExecution"
      />
      <!-- 右上角按钮区域 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="top-right" 
        @execute-script="handleScriptExecution"
      />
      <!-- 顶部中央按钮区域 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="top-center" 
        @execute-script="handleScriptExecution"
      />
      <!-- 左下角按钮区域 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="bottom-left" 
        @execute-script="handleScriptExecution"
      />
      <!-- 右下角按钮区域 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="bottom-right" 
        @execute-script="handleScriptExecution"
      />
      <!-- 底部中央按钮区域 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="bottom-center" 
        @execute-script="handleScriptExecution"
      />
      <!-- 左侧边栏按钮区域 -->
      <!-- <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="sidebar-left" 
        @execute-script="handleScriptExecution"
      /> -->
      <!-- 右侧边栏按钮区域 -->
      <!-- <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="sidebar-right" 
        @execute-script="handleScriptExecution"
      /> -->
      <!-- 浮动按钮区域
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="floating" 
        @execute-script="handleScriptExecution"
      /> -->
      <!-- 自定义位置按钮区域 -->
      <ScriptButtons 
        :scripts="allConfiguredScripts" 
        position="custom" 
        @execute-script="handleScriptExecution"
      />
    </div>
    
    <!-- 页面内容插槽 - 允许父组件在此处插入页面主要内容 -->
    <slot></slot>
    
    <!-- 参数输入弹窗 - 当脚本需要参数时显示此弹窗 -->
    <el-dialog
      v-model="parameterDialog.visible"
      :title="parameterDialog.dialogTitle || `${parameterDialog.scriptName} - 参数配置`"
      width="600px"
      :before-close="handleDialogClose"
    >
      <!-- 只有在弹窗可见时才渲染表单，避免不必要的组件初始化 -->
      <div v-if="parameterDialog.visible">
        <!-- 动态脚本表单组件 - 用于收集脚本执行所需的参数 -->
        <DynamicScriptForm
          ref="parameterFormRef"
          :script-name="parameterDialog.scriptName"
          :script-display-name="parameterDialog.scriptDisplayName"
          :show-script-selector="false"
          :show-advanced="false"
          @script-executed="handleParameterScriptExecuted"
        />
      </div>
      
      <!-- 弹窗底部按钮区域 -->
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
        </span>
      </template>
    </el-dialog>
    
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
import { onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ScriptButtons from './ScriptButtons.vue'
import DynamicScriptForm from './DynamicScriptForm.vue'
import DingtalkRobot from './DingtalkRobot.vue'
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
  loadScripts,          // 加载脚本列表的方法
  executeScript,        // 执行脚本的方法
  onRefreshData,        // 注册数据刷新回调的方法
  emitRefreshData       // 触发数据刷新的方法
} = useScriptManager(props.pageRoute)

// 参数弹窗的状态管理 - 使用reactive创建响应式对象
const parameterDialog = reactive({
  visible: false,           // 弹窗是否可见
  scriptName: '',          // 要执行的脚本名称
  dialogTitle: '',         // 弹窗标题
  scriptDisplayName: '',   // 脚本显示名称
  script: null as any,     // 脚本对象
  task: null as any        // 任务对象
})

// 参数表单组件的引用，用于调用子组件方法
const parameterFormRef = ref()

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

/**
 * 检查脚本是否需要参数配置
 * @param scriptName 脚本名称
 * @returns 返回脚本参数信息
 */
const checkScriptParameters = async (scriptName: string) => {
  try {
    console.log('检查脚本参数:', scriptName)
    
    // 尝试不同的脚本名称格式，增加查找成功率
    const possibleNames = [
      scriptName,                    // 原始名称
      scriptName.replace('.py', ''), // 移除.py后缀（如果存在）
      scriptName + '.py'            // 添加.py后缀
    ]
    
    // 遍历所有可能的脚本名称格式
    for (const name of possibleNames) {
      console.log('尝试脚本名称:', name)
      
      // 向后端API查询脚本配置信息
      const response = await fetch(`${BASE_URL}/myapp/api/script-configs/?script_name=${encodeURIComponent(name)}`)
      const data = await response.json()
      
      console.log('API响应:', data)
      
      // 如果找到了脚本配置
      if (data.success && data.script_config) {
        const parameters = data.script_config.parameters || []
        const requiredParams = parameters.filter((p: any) => p.required) // 筛选必填参数
        
        console.log('找到脚本配置:', { parameters: parameters.length, required: requiredParams.length })
        
        return {
          hasParameters: parameters.length > 0,           // 是否有参数
          hasRequiredParameters: requiredParams.length > 0, // 是否有必填参数
          parameters: parameters,                         // 参数列表
          dialog_title: data.script_config.dialog_title, // 弹窗标题
          display_name: data.script_config.display_name // 脚本显示名称
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

/**
 * 显示参数配置弹窗
 * @param scriptName 脚本名称
 * @param script 脚本对象
 * @param task 任务对象
 * @param paramInfo 参数信息
 */
const showParameterDialog = (scriptName: string, script: any, task: any, paramInfo: any) => {
  parameterDialog.scriptName = scriptName
  parameterDialog.dialogTitle = paramInfo.dialog_title || script.dialog_title || `${scriptName} - 参数配置`
  parameterDialog.scriptDisplayName = '请配置所需参数'
  parameterDialog.script = script
  parameterDialog.task = task
  parameterDialog.visible = true
}

/**
 * 处理脚本执行逻辑
 * @param script 要执行的脚本对象
 */
const handleScriptExecution = async (script: any) => {
  // 检查脚本是否有可执行的任务
  if (!script.tasks || script.tasks.length === 0) {
    console.error('脚本没有可执行的任务:', script)
    return
  }

  const task = script.tasks[0] // 默认执行第一个任务
  
  // 检查脚本是否需要参数配置
  const scriptName = script.name || script.script_name
  if (scriptName) {
    const paramInfo = await checkScriptParameters(scriptName)
    
    // 如果有必填参数，必须显示参数配置弹窗
    if (paramInfo.hasRequiredParameters) {
      showParameterDialog(scriptName, script, task, paramInfo)
      return
    } 
    // 如果有可选参数，询问用户是否需要配置
    else if (paramInfo.hasParameters) {
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
        
        // 用户选择配置参数，显示弹窗
        showParameterDialog(scriptName, script, task, paramInfo)
        return
      } catch {
        // 用户选择直接执行，继续下面的执行逻辑
      }
    }
  }
  
  // 直接执行脚本（无参数或用户选择直接执行）
  executeScript(script, task)
}

/**
 * 处理弹窗关闭，重置所有状态
 */
const handleDialogClose = () => {
  parameterDialog.visible = false
  parameterDialog.scriptName = ''
  parameterDialog.dialogTitle = ''
  parameterDialog.scriptDisplayName = ''
  parameterDialog.script = null
  parameterDialog.task = null
}

/**
 * 处理参数表单执行完成的回调
 * @param result 执行结果
 */
const handleParameterScriptExecuted = (result: any) => {
  console.log('参数表单脚本执行完成:', result)
  
  // 关闭参数配置弹窗
  handleDialogClose()
  
  // 根据执行结果显示相应的提示信息
  if (result.success) {
    ElMessage.success('脚本执行成功！')
    
    // 延迟触发数据刷新，确保后端已写库
    setTimeout(() => {
      console.log('参数表单脚本执行成功，触发数据刷新...')
      emitRefreshData()
    }, 2000)
  } else {
    ElMessage.error(`脚本执行失败: ${result.error || '未知错误'}`)
    
    // 即使失败也触发刷新，可能有部分结果
    setTimeout(() => {
      console.log('参数表单脚本执行失败，触发数据刷新...')
      emitRefreshData()
    }, 1000)
  }
}

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
  openDingtalkDialog  // 打开钉钉机器人弹窗方法
})
</script>

<style scoped>
/* 脚本管理器布局容器 */
.script-manager-layout {
  position: relative;
  width: 100%;
  height: 100%;
}

/* 脚本按钮包装器 */
.script-buttons-wrapper {
  position: relative;
  width: 100%;
  min-height: 60px;     /* 最小高度确保按钮有足够显示空间 */
  margin-bottom: 16px;  /* 与下方内容保持间距 */
}
</style>