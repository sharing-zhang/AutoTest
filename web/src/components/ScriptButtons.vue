<template>
  <!-- 脚本列表组件 - 统一显示页面配置的脚本 -->
  <div class="script-list-section">
    <el-card shadow="never" class="script-list-card">
      <template #header>
        <div class="script-list-header">
          <el-icon class="header-icon"><List /></el-icon>
          <span class="header-title">可用脚本列表</span>
          <el-tag type="info" size="small" class="script-count">
            共 {{ availableScripts.length }} 个脚本
          </el-tag>
        </div>
      </template>
      <div class="script-list-content">
        <el-row :gutter="16">
          <el-col 
            v-for="script in availableScripts" 
            :key="script.id" 
            :xs="24" 
            :sm="24" 
            :md="24" 
            :lg="24" 
            :xl="24"
            class="script-item-col"
          >
            <el-card 
              shadow="hover" 
              class="script-item-card"
            >
              <div class="script-item-content">
                <div class="script-icon-container">
                  <div class="script-icon">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="script-status">
                    <el-tag 
                      :type="script.is_active ? 'success' : 'danger'" 
                      size="small"
                    >
                      {{ script.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </div>
                </div>
                <div class="script-info">
                  <div class="script-name">{{ script.dialog_title || script.name }}</div>
                  <div class="script-description">{{ script.description || '暂无描述' }}</div>
                </div>
                <div class="script-buttons">
                  <el-button 
                    type="primary" 
                    size="default" 
                    :disabled="!script.is_active"
                    @click.stop="handleScriptClick(script)"
                  >
                    运行
                  </el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <div v-if="availableScripts.length === 0" class="no-scripts">
          <el-empty description="暂无可用脚本" />
        </div>
      </div>
    </el-card>
    
    <!-- 脚本参数配置弹窗 -->
    <el-dialog
      v-model="parameterDialog.visible"
      :title="parameterDialog.title"
      width="600px"
      :before-close="handleParameterDialogClose"
    >
      <div v-if="parameterDialog.visible && currentScript">
        <!-- 动态脚本表单组件 -->
        <DynamicScriptForm
          ref="parameterFormRef"
          :script-name="currentScript.name"
          :script-display-name="currentScript.display_name || currentScript.name"
          :script-info="currentScript"
          :show-script-selector="false"
          :show-advanced="false"
          @script-executed="handleParameterScriptExecuted"
        />
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleParameterDialogClose">取消</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Document } from '@element-plus/icons-vue'
import DynamicScriptForm from './DynamicScriptForm.vue'

// 组件props接口定义
interface Props {
  scripts: any[] // 脚本列表
  pageRoute: string // 页面路由
}

// 接收父组件传入的props
const props = defineProps<Props>()

// 脚本列表数据
const availableScripts = ref<any[]>([])

// 监听props变化，更新本地脚本列表
watch(() => props.scripts, (newScripts) => {
  console.log('ScriptButtons 接收到脚本数据:', newScripts)
  availableScripts.value = newScripts || []
}, { immediate: true, deep: true })

// 脚本参数配置弹窗数据
const parameterDialog = reactive({
  visible: false,
  title: '脚本参数配置'
})

// 当前选中的脚本
const currentScript = ref<any>(null)

// 参数表单组件引用
const parameterFormRef = ref()

// 组件挂载时初始化
onMounted(() => {
  // 过滤出当前页面对应的脚本
  if (props.scripts && props.scripts.length > 0) {
    availableScripts.value = props.scripts.filter(script => {
      // 根据新的配置结构，scripts数组中包含脚本名称
      return script.is_active !== false
    })
  }
})

// 脚本点击处理 - 显示参数配置弹窗
const handleScriptClick = (script: any) => {
  console.log('点击脚本:', script)
  
  // 检查脚本是否有可执行的任务
  if (!script.tasks || script.tasks.length === 0) {
    ElMessage.error('脚本没有可执行的任务')
    return
  }
  
  // 设置当前选中的脚本
  currentScript.value = script
  
  // 显示参数配置弹窗
  parameterDialog.visible = true
}

// 处理参数弹窗关闭
const handleParameterDialogClose = () => {
  parameterDialog.visible = false
  currentScript.value = null
}

// 处理参数表单执行完成的回调
const handleParameterScriptExecuted = (result: any) => {
  console.log('参数表单脚本执行完成:', result)
  
  // 关闭参数配置弹窗
  handleParameterDialogClose()
  
  // 根据执行结果显示相应的提示信息
  if (result.success) {
    ElMessage.success('脚本执行成功！')
    
    // 触发父组件刷新数据
    emit('script-executed', result)
  } else {
    ElMessage.error(`脚本执行失败: ${result.error || '未知错误'}`)
  }
}

// 定义事件
const emit = defineEmits(['script-executed'])
</script>

<style scoped lang="less">
.script-list-section {
  margin-bottom: 24px;
}

.script-list-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.script-list-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: #409eff;
  font-size: 18px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.script-count {
  margin-left: auto;
}

.script-list-content {
  padding: 16px 0;
}

.script-item-col {
  margin-bottom: 16px;
}

.script-item-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  height: 150px;
}

.script-item-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.script-item-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 16px 12px 12px 12px;
}

.script-icon-container {
  position: relative;
  flex-shrink: 0;
  margin-right: 16px;
}

.script-icon {
  width: 50px;
  height: 50px;
  background: #f0f9ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.script-icon .el-icon {
  color: #409eff;
  font-size: 24px;
}

.script-status {
  position: absolute;
  top: -8px;
  right: -8px;
  z-index: 1;
}

.script-info {
  flex: 1;
  min-width: 0;
  margin-right: 16px;
}

.script-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.script-description {
  font-size: 14px;
  color: #909399;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.script-buttons {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.no-scripts {
  text-align: center;
  padding: 40px 0;
}
</style>