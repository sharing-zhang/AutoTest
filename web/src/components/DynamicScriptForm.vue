<template>
  <div class="dynamic-script-form">
    <!-- 当前脚本信息 -->
    <div class="script-info" v-if="formConfig">
      <div class="script-title">
        <h3>{{ props.scriptDisplayName || formConfig.script_name.replace('.py', '').replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) }}</h3>
        <!-- <el-tag type="info" size="small">{{ formConfig.script_name }}</el-tag> -->
      </div>
      <p v-if="formConfig.parameters" class="script-desc">
        共 {{ formConfig.parameters.length }} 个参数
        <span v-if="formConfig.parameters.some(p => p.required)">，包含必填项</span>
      </p>
    </div>

    <!-- 脚本选择 -->
    
    <div class="script-selector" v-if="showScriptSelector">
      <el-form-item label="选择脚本">
        <el-select 
          v-model="selectedScript" 
          placeholder="请选择要执行的脚本"
          @change="handleScriptChange"
          style="width: 100%"
        >
          <el-option
            v-for="script in availableScripts"
            :key="script.script_name"
            :label="script.display_name"
            :value="script.script_name"
          >
            <span>{{ script.display_name }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">
              {{ script.parameter_count }} 个参数
            </span>
          </el-option>
        </el-select>
      </el-form-item>
    </div>
   

    <!-- 动态表单 -->
    <el-form 
      v-if="formConfig && formConfig.parameters"
      ref="dynamicFormRef"
      :model="formData"
      :rules="validationRules"
      class="dynamic-form"
    >
      <div v-for="param in formConfig.parameters" :key="param.name" class="form-item-wrapper">
        <!-- 组列表（可动态增删的一组字段集合，最终输出为数组） -->
        <el-form-item 
          v-if="param.type === 'group-list'" 
          :label="param.label" 
          :prop="param.name"
          :required="param.required"
        >
          <div style="width:100%">
            <div v-if="!Array.isArray(formData[param.name])" style="color:#909399;margin-bottom:8px;">无初始数据</div>
            <div v-for="(groupItem, gi) in (formData[param.name] as any[])" :key="gi" style="display:flex; gap:12px; align-items:flex-start; margin-bottom:12px; flex-wrap:wrap;">
              <template v-for="field in (param.item_fields || [])" :key="field.name">
                <el-input
                  v-if="field.type === 'text'"
                  v-model="groupItem[field.name]"
                  :placeholder="field.placeholder || field.label"
                  clearable
                  style="width: 220px;"
                />
                <div v-else-if="field.type === 'number'" class="number-input-container" style="display:flex; align-items:center; gap:8px;">
                  <el-input-number
                    v-model="groupItem[field.name]"
                    :min="field.min"
                    :max="field.max"
                    :step="1"
                    :placeholder="field.placeholder"
                    controls-position="right"
                  />
                  <span v-if="field.addonAfter" class="addon-after">{{ field.addonAfter }}</span>
                </div>
                <el-input
                  v-else
                  v-model="groupItem[field.name]"
                  :placeholder="field.placeholder || field.label"
                  clearable
                  style="width: 220px;"
                />
              </template>
              <el-button type="danger" plain @click="removeGroupItem(param.name, gi)">删除</el-button>
            </div>
            <el-button type="primary" plain @click="addGroupItem(param.name)">添加一组</el-button>
          </div>
        </el-form-item>

        <!-- 文本输入框 -->
        <el-form-item
          v-else-if="param.type === 'text'"
          :label="param.label"
          :prop="param.name"
          :required="param.required"
        >
          <el-input
            v-model="formData[param.name]"
            :placeholder="param.placeholder || `请输入${param.label}`"
            clearable
          />
        </el-form-item>
        <!-- 数字输入框 -->
         <!-- <div v-else-if="field.type === 'number'" class="field-wrapper">-->
<!--            <div class="number-input-container">-->
<!--              <el-input-number-->
<!--                v-model="groupItem[field.name]"-->
<!--                :min="field.min"-->
<!--                :max="field.max"-->
<!--                :step="1"-->
<!--                :placeholder="field.placeholder"-->
<!--                controls-position="right"-->
<!--                style="width: 180px;"-->
<!--              />-->
<!--              &lt;!&ndash; addonAfter 提示 &ndash;&gt;-->
<!--              <span v-if="field.addonAfter" class="addon-after">-->
<!--                {{ field.addonAfter }}-->
<!--              </span>-->
<!--            </div>-->
<!--            &lt;!&ndash; 字段描述 &ndash;&gt;-->
<!--            <div v-if="field.description" class="field-description">-->
<!--              {{ field.description }}-->
<!--            </div>-->
<!--            &lt;!&ndash; 帮助提示 &ndash;&gt;-->
<!--            <div v-if="field.help" class="field-help">-->
<!--              <el-icon><InfoFilled /></el-icon>-->
<!--              {{ field.help }}-->
<!--            </div>-->
<!--          </div>-->

       <!-- &lt;!&ndash; 数字输入框 &ndash;&gt; -->
        <el-form-item
          v-else-if="param.type === 'number'"
          :label="param.label"
         :prop="param.name"
          :required="param.required"
        >
          <el-input-number
            v-model="formData[param.name]"
            :min="param.min"
            :max="param.max"
            :step="1"
            style="width: 100%"
         />
        </el-form-item>

        <!-- 开关 -->
        <el-form-item 
          v-else-if="param.type === 'switch'" 
          :label="param.label" 
          :prop="param.name"
          :required="param.required"
        >
          <el-switch
            v-model="formData[param.name]"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>

        <!-- 下拉选择 -->
        <el-form-item 
          v-else-if="param.type === 'select'" 
          :label="param.label" 
          :prop="param.name"
          :required="param.required"
        >
          <el-select 
            v-model="formData[param.name]" 
            :placeholder="`请选择${param.label}`"
            style="width: 100%"
          >
            <el-option
              v-for="option in param.options"
              :key="option"
              :label="option"
              :value="option"
            />
          </el-select>
        </el-form-item>

        <!-- 多选下拉（带勾选） -->
        <el-form-item 
          v-else-if="param.type === 'checkbox'" 
          :label="param.label" 
          :prop="param.name"
          :required="param.required"
        >
          <el-select
            v-model="formData[param.name]"
            multiple
            :collapse-tags="false"
            clearable
            filterable
            style="width: 100%"
            :placeholder="param.placeholder || `请选择${param.label}`"
          >
            <el-option
              v-for="option in (param.options || [])"
              :key="option"
              :label="option"
              :value="option"
            >
              <div style="display:flex;align-items:center;gap:8px;">
                <el-checkbox :model-value="(formData[param.name] || []).includes(option)" />
                <span>{{ option }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 其他类型的默认处理 -->
        <el-form-item 
          v-else 
          :label="param.label" 
          :prop="param.name"
          :required="param.required"
        >
          <el-input
            v-model="formData[param.name]"
            :placeholder="param.placeholder || `请输入${param.label}`"
            clearable
          />
        </el-form-item>
      </div>

      <!-- 操作按钮 -->
      <el-form-item class="form-actions">
        <el-button type="primary" @click="handleSubmit" :loading="executing">
          <el-icon><VideoPlay /></el-icon>
          {{ executing ? '执行中...' : '执行脚本' }}
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
        <el-button v-if="showAdvanced" @click="toggleAdvanced">
          <el-icon><Setting /></el-icon>
          {{ showAdvancedOptions ? '隐藏高级选项' : '显示高级选项' }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 执行结果 -->
    <div v-if="executionResult" class="execution-result">
      <el-divider content-position="left">执行结果</el-divider>
      
      <!-- 成功结果 -->
      <el-alert
        v-if="executionResult.success"
        :title="executionResult.message || '脚本执行成功'"
        type="success"
        :closable="false"
        show-icon
      />
      
      <!-- 失败结果 -->
      <el-alert
        v-else
        :title="executionResult.error || '脚本执行失败'"
        type="error"
        :closable="false"
        show-icon
      />

      <!-- 详细结果数据 -->
      <el-collapse v-if="executionResult.result" class="result-details">
        <el-collapse-item title="详细结果" name="details">
          <pre class="result-json">{{ JSON.stringify(executionResult.result, null, 2) }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Refresh, Setting } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { BASE_URL } from '/@/store/constants'
import { executeScriptApi, getScriptTaskResultApi } from '/@/api/scanDevUpdate'

interface ScriptParameter {
  name: string
  type: string
  label: string
  required: boolean
  default?: any
  placeholder?: string
  options?: string[]
  multiple?: boolean
  min?: number
  max?: number
}

interface ScriptConfig {
  script_name: string
  parameters: ScriptParameter[]
  form_layout?: any
  dialog_title?: string
  display_name?: string
}

interface ScriptInfo {
  script_name: string
  display_name: string
  parameter_count: number
  has_required_params: boolean
}

interface Props {
  scriptName?: string
  scriptDisplayName?: string
  showScriptSelector?: boolean
  showAdvanced?: boolean
  autoExecute?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  scriptName: 'check_Reward.py', // 默认脚本
  scriptDisplayName: '',        // 默认脚本显示名称
  showScriptSelector: false,    // 默认不显示脚本选择器
  showAdvanced: false,
  autoExecute: false
})

const emit = defineEmits<{
  'script-executed': [result: any]
  'script-changed': [scriptName: string]
  'form-updated': [formData: any]
}>()

// 响应式数据
const dynamicFormRef = ref<FormInstance>()
const selectedScript = ref<string>(props.scriptName || '')
const availableScripts = ref<ScriptInfo[]>([])
const formConfig = ref<ScriptConfig | null>(null)
const formData = reactive<Record<string, any>>({})
const executing = ref(false)
const executionResult = ref<any>(null)
const showAdvancedOptions = ref(false)

// 计算属性
const validationRules = computed(() => {
  const rules: FormRules = {}
  
  if (formConfig.value?.parameters) {
    formConfig.value.parameters.forEach(param => {
      if (param.required) {
        rules[param.name] = [
          {
            required: true,
            message: `${param.label} 是必填项`,
            trigger: param.type === 'switch' ? 'change' : 'blur'
          }
        ]
      }
      
      // 数字类型的范围验证
      if (param.type === 'number') {
        if (!rules[param.name]) rules[param.name] = []
        if (param.min !== undefined) {
          rules[param.name].push({
            type: 'number',
            min: param.min,
            message: `值不能小于 ${param.min}`,
            trigger: 'blur'
          })
        }
        if (param.max !== undefined) {
          rules[param.name].push({
            type: 'number',
            max: param.max,
            message: `值不能大于 ${param.max}`,
            trigger: 'blur'
          })
        }
      }
    })
  }
  
  return rules
})

// 监听脚本名称变化
watch(() => props.scriptName, (newScriptName) => {
  if (newScriptName && newScriptName !== selectedScript.value) {
    selectedScript.value = newScriptName
    loadScriptConfig(newScriptName)
  }
}, { immediate: true })

// 监听表单数据变化
watch(formData, (newFormData) => {
  emit('form-updated', { ...newFormData })
}, { deep: true })


// 注释掉加载脚本列表的逻辑，因为现在直接指定脚本
// const loadAvailableScripts = async () => {
//   try {
//     const response = await fetch('/api/script-configs/')
//     const data = await response.json()
    
//     if (data.success) {
//       availableScripts.value = data.scripts || []
//     } else {
//       ElMessage.error('加载脚本列表失败')
//     }
//   } catch (error) {
//     console.error('加载脚本列表失败:', error)
//     ElMessage.error('加载脚本列表失败')
//   }
// }

const loadScriptConfig = async (scriptName: string) => {
  if (!scriptName) return
  
  try {
    const response = await fetch(`${BASE_URL}/myapp/api/script-configs/?script_name=${encodeURIComponent(scriptName)}`)
    const data = await response.json()
    
    if (data.success && data.script_config) {
      formConfig.value = data.script_config
      initializeFormData()
    } else {
      ElMessage.error('加载脚本配置失败')
    }
  } catch (error) {
    console.error('加载脚本配置失败:', error)
    ElMessage.error('加载脚本配置失败')
  }
}

const initializeFormData = () => {
  if (!formConfig.value?.parameters) return
  
  // 清空现有数据
  Object.keys(formData).forEach(key => {
    delete formData[key]
  })
  
  // 设置默认值
  formConfig.value.parameters.forEach(param => {
    if (param.default !== undefined) {
      formData[param.name] = param.type === 'checkbox' && param.multiple 
        ? (Array.isArray(param.default) ? [...param.default] : [param.default])
        : param.default
    } else {
      // 设置类型默认值
      switch (param.type) {
        case 'group-list':
          formData[param.name] = []
          break
        case 'text':
        case 'select':
          formData[param.name] = ''
          break
        case 'number':
          formData[param.name] = param.min || 0
          break
        case 'switch':
          formData[param.name] = false
          break
        case 'checkbox':
          formData[param.name] = param.multiple ? [] : ''
          break
        default:
          formData[param.name] = ''
      }
    }
  })
}

const handleScriptChange = (scriptName: string) => {
  selectedScript.value = scriptName
  executionResult.value = null
  loadScriptConfig(scriptName)
  emit('script-changed', scriptName)
}

// group-list helpers
const addGroupItem = (paramName: string) => {
  if (!Array.isArray(formData[paramName])) {
    formData[paramName] = []
  }
  ;(formData[paramName] as any[]).push({})
}

const removeGroupItem = (paramName: string, index: number) => {
  if (Array.isArray(formData[paramName])) {
    ;(formData[paramName] as any[]).splice(index, 1)
  }
}

const handleSubmit = async () => {
  if (!formConfig.value || !selectedScript.value) {
    ElMessage.warning('请先选择脚本')
    return
  }
  
  // 表单验证
  if (dynamicFormRef.value) {
    const valid = await dynamicFormRef.value.validate().catch(() => false)
    if (!valid) return
  }
  
  // 确认执行
  try {
    await ElMessageBox.confirm(
      // `确认要执行脚本 "${formConfig.value.script_name}" 吗？`,
      `确认要执行 "${formConfig.value.dialog_title}" 脚本吗？`,
      '确认执行',
      {
        confirmButtonText: '执行',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  
  // 执行脚本
  executing.value = true
  executionResult.value = null
  
  try {
    const requestData = {
      script_name: selectedScript.value,
      parameters: { ...formData },
      page_context: 'dynamic_form'
    }
    
    console.log('发送执行请求:', requestData)
    
    const response = await executeScriptApi({
      script_name: selectedScript.value,
      parameters: { ...formData },
      page_context: 'dynamic_form'
    })
    
    const data = response.data || response
    
    if (data.success) {
      ElMessage.success('脚本启动成功，正在执行...')
      
      // 监控执行状态
      await monitorExecution(data.task_id, data.execution_id)
    } else {
      executionResult.value = {
        success: false,
        error: data.error,
        validation_errors: data.validation_errors
      }
      ElMessage.error(`脚本启动失败: ${data.error}`)
    }
  } catch (error) {
    executionResult.value = {
      success: false,
      error: '网络请求失败'
    }
    ElMessage.error('网络请求失败')
  } finally {
    executing.value = false
  }
}

const monitorExecution = async (taskId: string, executionId: string) => {
  const maxAttempts = 30
  let attempts = 0
  
  const poll = async () => {
    try {
      attempts++
      const response = await getScriptTaskResultApi(taskId, executionId)
      const data = response.data || response
      
      if (data.ready) {
        executionResult.value = data
        emit('script-executed', data)
        
        if (data.success) {
          ElMessage.success('脚本执行成功！')
        } else {
          ElMessage.error(`脚本执行失败: ${data.error || '未知错误'}`)
        }
      } else if (attempts >= maxAttempts) {
        ElMessage.warning('脚本执行超时')
      } else {
        setTimeout(poll, 2000)
      }
    } catch (error) {
      console.error('查询执行状态失败:', error)
      if (attempts >= maxAttempts) {
        ElMessage.error('查询执行状态失败')
      } else {
        setTimeout(poll, 2000)
      }
    }
  }
  
  setTimeout(poll, 1000)
}

const handleReset = () => {
  initializeFormData()
  executionResult.value = null
  if (dynamicFormRef.value) {
    dynamicFormRef.value.clearValidate()
  }
}

const toggleAdvanced = () => {
  showAdvancedOptions.value = !showAdvancedOptions.value
}

// 生命周期
const init = async () => {
  // 注释掉脚本列表加载，直接加载指定脚本的配置
  // if (props.showScriptSelector) {
  //   await loadAvailableScripts()
  // }
  
  if (props.scriptName) {
    await loadScriptConfig(props.scriptName)
  }
}

// 初始化
init()

// 暴露方法给父组件
defineExpose({
  loadScriptConfig,
  handleSubmit,
  handleReset,
  getFormData: () => ({ ...formData }),
  setFormData: (data: Record<string, any>) => {
    Object.assign(formData, data)
  }
})
</script>

<style scoped lang="less">
.dynamic-script-form {
  .script-info {
    margin-bottom: 24px;
    padding: 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    color: white;
    
    .script-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }
      
      :deep(.el-tag) {
        background: rgba(255, 255, 255, 0.2);
        border: none;
        color: white;
      }
    }
    
    .script-desc {
      margin: 0;
      font-size: 14px;
      opacity: 0.9;
    }
  }
  
  .script-selector {
    margin-bottom: 20px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 6px;
  }
  
  .dynamic-form {
    .form-item-wrapper {
      margin-bottom: 16px;
    }
     .group-description {
    font-size: 13px;
    color: #606266;
    margin-bottom: 12px;
    padding: 8px 12px;
    background: #f5f7fa;
    border-radius: 4px;
    border-left: 3px solid #409eff;
  }

  // 组项目行样式
  .group-item-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-bottom: 12px;
    flex-wrap: wrap;
    padding: 12px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    background: #fafafa;

    &:hover {
      background: #f0f2f5;
      border-color: #c0c4cc;
    }
  }

  // 字段包装器
  .field-wrapper {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  // 数字输入框容器
  .number-input-container {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  // addonAfter 样式
  .addon-after {
    font-size: 12px;
    color: #909399;
    white-space: nowrap;
    padding: 0 8px;
    background: #f5f7fa;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    height: 32px;
    line-height: 30px;

    // 如果包含emoji或图标，调整样式
    &:contains("💰") {
      color: #e6a23c;
      background: #fdf6ec;
      border-color: #f5dab1;
    }
  }

  // 字段描述样式
  .field-description {
    font-size: 11px;
    color: #909399;
    line-height: 1.2;
    max-width: 220px;
  }

  // 字段帮助样式
  .field-help {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: #409eff;

    .el-icon {
      font-size: 12px;
    }
  }

    .form-actions {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #e4e7ed;
    }
    
    // 自适应标签宽度
    :deep(.el-form-item__label) {
      width: auto !important;
      min-width: auto !important;
      max-width: none !important;
      white-space: nowrap;
      text-align: left;
      padding-right: 12px;
    }
    
    :deep(.el-form-item__content) {
      margin-left: 0 !important;
      flex: 1;
    }
  }

  .execution-result {
    margin-top: 24px;
    
    .result-details {
      margin-top: 16px;
      
      .result-json {
        background: #f5f7fa;
        padding: 12px;
        border-radius: 4px;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .dynamic-script-form {
    :deep(.el-form-item__label) {
      width: auto !important;
      text-align: left;
    }
    
    :deep(.el-form-item__content) {
      margin-left: 0 !important;
    }
    
    .form-actions {
      :deep(.el-button) {
        width: 100%;
        margin-bottom: 8px;
      }
    }
  }
}
</style>
