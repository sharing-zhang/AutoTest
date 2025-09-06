import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { listScriptsApi, executeScriptApi, getScriptTaskResultApi } from '/@/api/scanDevUpdate'

/**
 * 脚本管理组合式函数
 * 提供脚本加载、执行、状态管理等功能
 */
export function useScriptManager(pageRoute: string) {
  // 响应式状态
  const availableScripts = ref<any[]>([])
  const pageConfigs = ref<any[]>([])
  const allConfiguredScripts = ref<any[]>([])
  const loading = ref(false)

  /**
   * 加载指定页面的脚本配置
   */
  const loadScripts = async () => {
    try {
      loading.value = true
      console.log(`开始加载页面 ${pageRoute} 的脚本列表...`)
      
      const response = await listScriptsApi({ page_route: pageRoute })
      const data = response.data || response
      
      if (data && data.success && Array.isArray(data.scripts)) {
        console.log('成功获取脚本数据，开始处理...')
        
        availableScripts.value = data.scripts.map((script, index) => ({
          id: script.id || index,
          name: script.name || `脚本${index}`,
          description: script.description || '',
          loading: false,
          tasks: Array.isArray(script.tasks) ? script.tasks : []
        }))
        
        pageConfigs.value = data.page_configs || []
        allConfiguredScripts.value = mergeScriptsWithConfigs(
          availableScripts.value, 
          pageConfigs.value
        )
        
        console.log(`页面 ${pageRoute} 脚本加载完成:`, {
          scripts: availableScripts.value.length,
          configs: pageConfigs.value.length,
          configured: allConfiguredScripts.value.length
        })
      } else {
        console.error('脚本数据格式错误:', data)
        resetScripts()
      }
    } catch (error) {
      console.log('脚本加载异常，检查是否为成功响应:', error)
      
      // 处理axios拦截器可能导致的"成功响应被当作异常"的情况
      if (error && typeof error === 'object' && (error as any).success === true && Array.isArray((error as any).scripts)) {
        console.log('检测到成功响应被当作异常处理，进行修正...')
        
        try {
          availableScripts.value = (error as any).scripts.map((script: any, index: number) => ({
            id: script.id || index,
            name: script.name || `脚本${index}`,
            description: script.description || '',
            loading: false,
            tasks: Array.isArray(script.tasks) ? script.tasks : []
          }))
          
          pageConfigs.value = (error as any).page_configs || []
          allConfiguredScripts.value = mergeScriptsWithConfigs(
            availableScripts.value, 
            pageConfigs.value
          )
        } catch (processError) {
          console.error('处理成功响应时出错:', processError)
          resetScripts()
        }
      } else {
        console.error('脚本加载失败:', error)
        resetScripts()
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 执行脚本任务
   */
  const executeScript = async (script: any, task: any) => {
    if (!script || !task) {
      message.error('脚本或任务参数无效')
      return
    }
    
    try {
      script.loading = true
      message.info(`正在启动脚本 ${script.name} - ${task.name}...`)
      
      const executionData = {
        script_id: script.id,
        task_name: task.full_name,
        parameters: getDefaultParameters(task.parameters),
        page_context: pageRoute
      }
      
      const response = await executeScriptApi(executionData)
      const data = response.data || response
      
      if (data && data.success) {
        const taskId = data.task_id
        const executionId = data.execution_id
        message.success(`${script.name} 已启动，任务ID: ${taskId.substring(0, 8)}...`)
        
        // 监控任务状态
        monitorTaskStatus(script, taskId, executionId)
      } else {
        message.error(data?.message || '启动脚本失败')
        script.loading = false
      }
    } catch (error) {
      console.log('脚本执行异常，检查是否为成功响应:', error)
      
      if (error && typeof error === 'object' && (error as any).success === true && (error as any).task_id) {
        console.log('检测到成功响应被当作异常处理，进行修正...')
        const taskId = (error as any).task_id
        const executionId = (error as any).execution_id
        message.success(`${script.name} 已启动，任务ID: ${taskId.substring(0, 8)}...`)
        monitorTaskStatus(script, taskId, executionId)
      } else {
        console.error('执行脚本失败:', error)
        message.error('执行脚本失败，请检查网络连接')
        script.loading = false
      }
    }
  }

  /**
   * 监控任务执行状态
   */
  const monitorTaskStatus = async (script: any, taskId: string, executionId?: string) => {
    const maxAttempts = 30
    let attempts = 0
    
    const poll = async () => {
      try {
        attempts++
        const result = await getScriptTaskResultApi(taskId, executionId)
        const taskData = result.data || result
        
        if (taskData && taskData.ready) {
          script.loading = false
          
          if (taskData.success) {
            message.success(`${script.name} 执行成功！`)
            
            if (taskData.result && taskData.result.message) {
              message.info(`执行结果: ${taskData.result.message}`)
            }
            
            // 触发数据刷新事件
            emitRefreshData()
          } else {
            message.error(`${script.name} 执行失败: ${taskData.error || '未知错误'}`)
          }
        } else if (attempts >= maxAttempts) {
          script.loading = false
          message.warning(`${script.name} 任务查询超时`)
        } else {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        handleTaskStatusError(script, error, attempts, maxAttempts, poll)
      }
    }
    
    setTimeout(poll, 1000)
  }

  /**
   * 处理任务状态查询错误
   */
  const handleTaskStatusError = (script: any, error: any, attempts: number, maxAttempts: number, poll: Function) => {
    if (error && typeof error === 'object' && error.success === true) {
      const taskData = error
      
      if (taskData && taskData.ready) {
        script.loading = false
        
        if (taskData.success) {
          message.success(`${script.name} 执行成功！`)
          if (taskData.result && taskData.result.message) {
            message.info(`执行结果: ${taskData.result.message}`)
          }
          emitRefreshData()
        } else {
          message.error(`${script.name} 执行失败: ${taskData.error || '未知错误'}`)
        }
      } else if (attempts >= maxAttempts) {
        script.loading = false
        message.warning(`${script.name} 任务查询超时`)
      } else {
        setTimeout(poll, 2000)
      }
    } else {
      console.error('任务状态查询失败:', error)
      if (attempts >= maxAttempts) {
        script.loading = false
        message.error(`${script.name} 状态查询失败`)
      } else {
        setTimeout(poll, 2000)
      }
    }
  }

  /**
   * 获取默认参数
   */
  const getDefaultParameters = (parametersSchema: any) => {
    const params = {}
    
    if (parametersSchema) {
      for (const [key, config] of Object.entries(parametersSchema)) {
        if (typeof config === 'object' && config !== null) {
          const paramConfig = config as any
          switch (paramConfig.type) {
            case 'number':
              params[key] = paramConfig.default || 100
              break
            case 'string':
              params[key] = paramConfig.default || ''
              break
            case 'boolean':
              params[key] = paramConfig.default || false
              break
            default:
              params[key] = paramConfig.default || ''
          }
        }
      }
    }
    
    return params
  }

  /**
   * 合并脚本和页面配置
   */
  const mergeScriptsWithConfigs = (scripts: any[], configs: any[]) => {
    const configMap = new Map()
    
    // 将页面配置按脚本ID分组
    configs.forEach(config => {
      if (!configMap.has(config.script_id)) {
        configMap.set(config.script_id, [])
      }
      configMap.get(config.script_id)?.push(config)
    })
    
    const result: any[] = []
    
    // 为每个脚本创建按钮配置
    scripts.forEach(script => {
      const scriptConfigs = configMap.get(script.id) || []
      
      if (scriptConfigs.length > 0) {
        // 如果有配置，为每个配置创建一个按钮实例
        scriptConfigs.forEach(config => {
          result.push({
            ...script,
            button_text: config.button_text || script.name,
            button_style: config.button_style || {},
            position: config.position || 'top-right',
            display_order: config.display_order || 0,
            config_id: config.id
          })
        })
      }
      // 没有配置则不创建按钮
    })
    
    return result
  }

  /**
   * 重置脚本状态
   */
  const resetScripts = () => {
    availableScripts.value = []
    pageConfigs.value = []
    allConfiguredScripts.value = []
  }

  /**
   * 数据刷新回调函数集合
   */
  const refreshCallbacks = ref<Function[]>([])

  /**
   * 注册数据刷新回调
   */
  const onRefreshData = (callback: Function) => {
    refreshCallbacks.value.push(callback)
  }

  /**
   * 触发数据刷新
   */
  const emitRefreshData = () => {
    refreshCallbacks.value.forEach(callback => {
      try {
        callback()
      } catch (error) {
        console.error('数据刷新回调执行失败:', error)
      }
    })
  }

  // 返回公共接口
  return {
    // 状态
    availableScripts,
    pageConfigs,
    allConfiguredScripts,
    loading,
    
    // 方法
    loadScripts,
    executeScript,
    onRefreshData,
    resetScripts
  }
}
