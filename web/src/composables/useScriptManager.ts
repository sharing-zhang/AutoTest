import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { listScriptsApi, executeScriptApi, getScriptTaskResultApi, getPageConfigsApi } from '/@/api/scanDevUpdate'
import { BASE_URL } from '/@/store/constants'

/**
 * 脚本管理组合式函数
 * @param pageRoute string 当前页面路由，用于后端过滤脚本/作为执行上下文
 * @returns 暴露用于页面使用的状态与方法
 */
export function useScriptManager(pageRoute: string) {
  // 可用脚本（后端返回的原始脚本清单，不带位置与按钮样式）
  const availableScripts = ref<any[]>([])

  // 页面配置（决定按钮如何在页面展示）
  const pageConfigs = ref<any[]>([])

  // 完整配置后的脚本按钮（用于直接渲染）
  const allConfiguredScripts = ref<any[]>([])
  
  // 加载中状态（用于界面显示 loading 或防止重复请求）
  const loading = ref(false)

  /**
   * 加载指定页面的脚本配置
   * 流程：
   * 1) 请求 listScriptsApi，获取脚本清单与页面配置
   * 2) 归一化 availableScripts（保证字段存在与类型一致）
   * 3) 与 pageConfigs 合并为 allConfiguredScripts（一个脚本可对应多个页面按钮）
   * 4) 支持“成功响应被当作异常”的修复逻辑
   *
   * 注意：
   * - 必须保证 data.scripts 为数组；否则重置状态
   * - 合并逻辑放在 mergeScriptsWithConfigs 中
   */
  const loadScripts = async () => {
    try {
      loading.value = true
      console.log(`开始加载页面 ${pageRoute} 的脚本列表...`)
      
      // 分别调用脚本列表和页面配置API，分别处理错误
      let scriptsData = null
      let configsData = []
      
      try {
        console.log('正在获取脚本列表...')
        const scriptsResponse = await listScriptsApi()
        scriptsData = scriptsResponse.data || scriptsResponse
        console.log('脚本列表响应:', scriptsData)
      } catch (scriptsError) {
        console.error('获取脚本列表失败:', scriptsError)
        throw scriptsError
      }
      
      try {
        console.log('正在获取页面配置...')
        const configsResponse = await getPageConfigsApi(pageRoute)
        configsData = configsResponse.data || configsResponse
        console.log('页面配置响应:', configsData)
      } catch (configsError) {
        console.error('获取页面配置失败:', configsError)
        configsData = []
      }
      
      if (scriptsData && (scriptsData as any).success && Array.isArray((scriptsData as any).scripts)) {
        console.log('成功获取脚本数据，开始处理...')
        
        // 规范化脚本列表（防御性处理：确保 tasks 是数组，name/description 有默认值）
        availableScripts.value = (scriptsData as any).scripts.map((script: any, index: number) => ({
          id: script.id || index,                      // 无 id 时回退 index，避免渲染 key 报错
          name: script.name || `脚本${index}`,         // 保底名称
          description: script.description || '',       // 保底描述
          loading: false,                              // 初始非加载状态
          tasks: Array.isArray(script.tasks) ? script.tasks : [] // 非数组则回退为空数组
        }))
        
        // 页面层面的按钮/布局配置
        pageConfigs.value = Array.isArray(configsData) ? configsData : []

        // 合并为“可直接渲染”的按钮集合
        allConfiguredScripts.value = mergeScriptsWithConfigs(
          availableScripts.value, 
          pageConfigs.value
        )
        
        // console.log(`页面 ${pageRoute} 脚本加载完成:`, {
        //   scripts: availableScripts.value.length,
        //   configs: pageConfigs.value.length,
        //   configured: allConfiguredScripts.value.length
        // })

      console.log(`页面 ${pageRoute} 脚本加载完成:`)

      } else {
        // 返回结构不符合预期
        console.error('脚本数据格式错误:', scriptsData)
        resetScripts()
      }
    } catch (error) {
      console.error('脚本加载失败:', error)
      resetScripts()
    } finally {
      loading.value = false
    }
  }

  /**
   * 执行脚本任务（统一API入口）
   *
   * 使用统一的脚本执行API：
   * - 不再区分脚本类型，统一处理
   * - 统一的参数格式和响应格式
   * - 简化的错误处理逻辑
   *
   * 流程：
   * 1) 参数校验（script/task 必须存在）
   * 2) 构建统一的执行请求体
   * 3) 调用统一API /myapp/api/execute-script/
   * 4) 解析响应并进入轮询 monitorTaskStatus
   */
  const executeScript = async (script: any, task: any) => {
    // 基本参数校验
    if (!script || !task) {
      message.error('脚本或任务参数无效')
      return
    }
    
    try {
      // UI 加载中
      script.loading = true
      message.info(`正在启动脚本 ${script.name}...`)
      
      // 构建统一的执行请求体
      const executionData = {
        script_id: script.id,  // 优先使用数据库ID
        script_name: script.name,  // 脚本名称
        parameters: getDefaultParameters(task.parameters),
        page_context: pageRoute
      }
      
      console.log('脚本执行数据:', executionData)
      
      // 使用axios调用ScriptExecutionViewSet 
      const responseData = await executeScriptApi(executionData)
      
      // 兼容 data 嵌套与直出
      const responseDataFinal = responseData.data || responseData
      
      console.log('脚本执行响应数据:', responseDataFinal)
      
      if (responseDataFinal && responseDataFinal.success) {
        // 成功启动：提取任务标识
        const taskId = responseDataFinal.task_id
        const executionId = responseDataFinal.execution_id
        const scriptName = responseDataFinal.script_name || script.name

        message.success(`${scriptName} 已启动`)
        
        // 启动轮询监控
        monitorTaskStatus(script, taskId, executionId)
      } else {
        // 后端返回 success=false 或者结构异常
        message.error(responseDataFinal?.error || responseDataFinal?.message || '启动脚本失败')
        script.loading = false
      }
    } catch (error) {
      // 处理执行错误
      console.error('执行脚本失败:', error)
      
      // 统一API的错误处理
      if (error && typeof error === 'object') {
        const errorData = error as any
        if (errorData.validation_errors && Array.isArray(errorData.validation_errors)) {
          message.error(`参数验证失败: ${errorData.validation_errors.join(', ')}`)
        } else {
          message.error(errorData.error || '执行脚本失败，请检查网络连接')
        }
      } else {
        message.error('执行脚本失败，请检查网络连接')
      }
      
      script.loading = false
    }
  }

  /**
   * 监控任务执行状态（轮询）
   *
   * 策略：
   * - 最多尝试 maxAttempts 次（默认 30 次）
   * - 每次轮询间隔 2 秒；初次延迟 1 秒启动
   * - ready=true 且 success=true -> 成功；ready=true 且 success=false -> 失败
   * - 超时或错误时有对应提示，并适当触发数据刷新
   *
   * @param script 正在执行的脚本对象（用于控制 loading 与提示文案）
   * @param taskId 任务 ID（后端返回）
   * @param executionId 执行 ID（部分后端实现可能需要）
   */
  const monitorTaskStatus = async (script: any, taskId: string, executionId?: string) => {
    const maxAttempts = 30
    let attempts = 0
    
    // 递归轮询函数
    const poll = async () => {
      try {
        attempts++
        // 查询任务状态（兼容 axios 与直出）
        const result = await getScriptTaskResultApi(taskId, executionId)
        const taskData = result.data || result
        
        if (taskData && taskData.ready) {
          // 已完成，停止加载
          script.loading = false
          
          if (taskData.success) {
            message.success(`${script.name} 执行成功！`)
            
            // 如果有附加信息，友好展示
            if (taskData.result && taskData.result.message) {
              message.info(`执行结果: ${taskData.result.message}`)
            }
            
            // 延迟刷新，确保后端已写库
            setTimeout(() => {
              console.log('脚本执行成功，自动刷新数据列表...')
              emitRefreshData()
              
              // 额外延迟一次刷新，确保数据完全同步
              setTimeout(() => {
                console.log('二次刷新，确保数据同步...')
                emitRefreshData()
              }, 1000)
            }, 2000) // 增加延迟时间，确保数据库写入完成
          } else {
            // 已完成但失败
            message.error(`${script.name} 执行失败: ${taskData.error || '未知错误'}`)
            
            // 失败也可能产生部分数据，适度刷新
            setTimeout(() => {
              console.log('脚本执行结束（失败），刷新数据列表...')
              emitRefreshData()
            }, 1000) // 失败时也增加延迟
          }
        } else if (attempts >= maxAttempts) {
          // 超过最大轮询次数
          script.loading = false
          message.warning(`${script.name} 任务查询超时`)
        } else {
          // 尚未完成，继续下一轮
          setTimeout(poll, 2000)
        }
      } catch (error) {
        // 错误统一交给专门的处理器（包含“成功响应被当异常”的修复）
        handleTaskStatusError(script, error, attempts, maxAttempts, poll)
      }
    }
    
    // 初次延迟 1s 再开始轮询，给后端一点启动时间
    setTimeout(poll, 1000)
  }

  /**
   * 处理任务状态查询错误
   * 覆盖点：
   * - 如果 error 内实际是成功结构（success=true），走与成功相同的分支（容错）
   * - 否则根据 attempts 判断是否继续轮询或告警
   *
   * @param script 当前脚本对象
   * @param error 异常对象（可能是“被拦截的成功响应”）
   * @param attempts 已轮询次数
   * @param maxAttempts 最大轮询次数
   * @param poll 轮询函数引用（用于 setTimeout 继续轮询）
   */
  const handleTaskStatusError = (script: any, error: any, attempts: number, maxAttempts: number, poll: Function) => {
    if (error && typeof error === 'object' && error.success === true) {
      // 修正：异常里其实是成功响应
      const taskData = error
      
      if (taskData && taskData.ready) {
        script.loading = false
        
        if (taskData.success) {
          message.success(`${script.name} 执行成功！`)
          if (taskData.result && taskData.result.message) {
            message.info(`执行结果: ${taskData.result.message}`)
          }
          // 延迟触发数据刷新，确保数据库已经完全保存
          setTimeout(() => {
            console.log('脚本执行成功，自动刷新数据列表...')
            emitRefreshData()
            
            // 额外延迟一次刷新，确保数据完全同步
            setTimeout(() => {
              console.log('二次刷新，确保数据同步...')
              emitRefreshData()
            }, 1000)
          }, 2000) // 增加延迟时间，确保数据库写入完成
        } else {
          message.error(`${script.name} 执行失败: ${taskData.error || '未知错误'}`)
          // 即使失败也刷新数据，可能有部分结果需要显示
          setTimeout(() => {
            console.log('脚本执行结束（失败），刷新数据列表...')
            emitRefreshData()
          }, 1000) // 失败时也增加延迟
        }
      } else if (attempts >= maxAttempts) {
        // 达到上限仍未 ready
        script.loading = false
        message.warning(`${script.name} 任务查询超时`)
      } else {
        // 继续轮询
        setTimeout(poll, 2000)
      }
    } else {
      // 真正的查询失败（网络/服务端异常等）
      console.error('任务状态查询失败:', error)
      if (attempts >= maxAttempts) {
        script.loading = false
        message.error(`${script.name} 状态查询失败`)
      } else {
        // 暂时失败，过会儿再试
        setTimeout(poll, 2000)
      }
    }
  }

  /**
   * 根据参数 schema 生成默认参数
   * 说明：
   * - 后端返回的 task.parameters 通常是一个形如：
   *   {
   *     page: { type: 'number', default: 1 },
   *     keyword: { type: 'string', default: '' },
   *     force: { type: 'boolean', default: false }
   *   }
   * - 本函数会根据 type 填充默认值，若 default 未提供，则使用兜底值
   *
   * @param parametersSchema 参数定义对象
   * @returns params 形如 { page: 1, keyword: '', force: false }
   */
  const getDefaultParameters = (parametersSchema: any) => {
    const params: Record<string, any> = {}
    
    if (parametersSchema) {
      for (const [key, config] of Object.entries(parametersSchema)) {
        if (typeof config === 'object' && config !== null) {
          const paramConfig = config as any
          switch (paramConfig.type) {
            case 'number':
              // 注意：0 会被认为 falsy，这里用 ?? 更安全
              params[key] = paramConfig.default ?? 100
              break
            case 'string':
              params[key] = paramConfig.default ?? ''
              break
            case 'boolean':
              params[key] = paramConfig.default ?? false
              break
            default:
              // 未知类型用字符串兜底
              params[key] = paramConfig.default ?? ''
          }
        }
      }
    }
    
    return params
  }

  /**
   * 合并脚本与页面配置，生成“可渲染按钮集”
   * 规则：
   * - 一个脚本可对应多个页面配置 config，最终产出多个按钮（文案/样式/位置可不同）
   * - 没有页面配置的脚本不产出按钮（即“配置驱动渲染”）
   *
   * @param scripts 原始脚本列表 availableScripts
   * @param configs 页面配置列表 pageConfigs
   * @returns result 最终用于渲染的按钮数组
   */
  const mergeScriptsWithConfigs = (scripts: any[], configs: any[]) => {
    const configMap = new Map<number, any[]>()
    
    // 按 script.id 将页面配置分组（一个脚本可能有多个 config）
    configs.forEach(config => {
      const scriptId = config.script?.id || config.script_id
      if (scriptId) {
        if (!configMap.has(scriptId)) {
          configMap.set(scriptId, [])
        }
        configMap.get(scriptId)?.push(config)
      }
    })
    
    const result: any[] = []
    
    // 遍历每个脚本，按分组到的配置生成按钮
    scripts.forEach(script => {
      const scriptConfigs = configMap.get(script.id) || []
      
      if (scriptConfigs.length > 0) {
        // 有配置时，为每条配置生成一个“按钮实例”
        scriptConfigs.forEach(config => {
          result.push({
            ...script,                                // 继承脚本基础信息（任务、loading等）
            button_text: config.button_text || script.name,
            button_style: config.button_style || {},
            position: config.position || 'top-right', // 按钮位置，默认为 top-right
            customPosition: config.custom_position || config.customPosition || {}, // 自定义位置配置
            display_order: config.display_order || 0, // 用于排序
            dialog_title: config.dialog_title,        // 参数弹窗标题（若用于参数收集）
            display_name: config.display_name,
            config_id: config.id                      // 记录该按钮来自哪条配置
          })
        })
      }
      // 无配置则不生成按钮（即不显示）
    })
    
    return result
  }

  /**
   * 重置脚本相关状态
   * - 用于加载失败或需要清空时
   */
  const resetScripts = () => {
    availableScripts.value = []
    pageConfigs.value = []
    allConfiguredScripts.value = []
  }

  /**
   * 存放外部注册的“数据刷新回调”
   * - 例如：脚本执行成功后，通知列表页刷新数据
   */
  const refreshCallbacks = ref<Function[]>([])

  /**
   * 注册数据刷新回调
   * - 父组件/使用方通过 onRefreshData(fn) 注册
   * - 在脚本完成后 emitRefreshData 时逐个调用
   */
  const onRefreshData = (callback: Function) => {
    refreshCallbacks.value.push(callback)
  }

  /**
   * 触发数据刷新（执行所有注册回调）
   * - 内部 catch 保护，避免某个回调抛错影响其他回调执行
   * - 添加重试机制，确保刷新能够成功执行
   */
  const emitRefreshData = (retryCount = 0) => {
    const maxRetries = 2
    
    console.log(`触发数据刷新，注册的回调数量: ${refreshCallbacks.value.length}`)
    
    refreshCallbacks.value.forEach((callback, index) => {
      try {
        console.log(`执行刷新回调 ${index + 1}/${refreshCallbacks.value.length}`)
        callback()
        console.log(`数据刷新回调 ${index + 1} 执行成功`)
      } catch (error) {
        console.error(`数据刷新回调 ${index + 1} 执行失败:`, error)
        
        // 如果失败且还有重试次数，延迟重试
        if (retryCount < maxRetries) {
          console.log(`数据刷新重试 ${retryCount + 1}/${maxRetries}`)
          setTimeout(() => {
            emitRefreshData(retryCount + 1)
          }, 1000 * (retryCount + 1)) // 递增延迟
        }
      }
    })
  }


  // 暴露给外部使用的状态与方法
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
    emitRefreshData,  // 暴露触发数据刷新的方法
    resetScripts
  }
}