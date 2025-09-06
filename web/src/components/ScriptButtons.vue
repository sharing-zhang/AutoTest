<template>
  <div class="script-buttons-container" :class="positionClass">
    <!-- 动态生成的脚本按钮 -->
    <template v-for="script in availableScripts" :key="script.id">
      <el-dropdown v-if="script.tasks && script.tasks.length > 1" :class="buttonWrapperClass">
        <el-button 
          :type="script.button_style?.type || 'primary'" 
          :size="script.button_style?.size || 'default'"
          :loading="script.loading"
          :style="getButtonStyle(script)"
        >
          {{ script.loading ? '执行中...' : script.button_text }}
          <el-icon><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item 
              v-for="task in script.tasks" 
              :key="task.name"
              @click="$emit('execute-script', script, task)"
            >
              {{ task.name }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      
      <el-button 
        v-else-if="script.tasks && script.tasks.length > 0"
        :type="script.button_style?.type || 'primary'"
        :size="script.button_style?.size || 'default'"
        :class="buttonWrapperClass"
        :style="getButtonStyle(script)"
        @click="$emit('execute-script', script, script.tasks[0])" 
        :loading="script.loading"
      >
        {{ script.loading ? '执行中...' : script.button_text }}
      </el-button>
      
      <el-button 
        v-else
        type="info" 
        :class="buttonWrapperClass"
        disabled
      >
        {{ script.button_text }} (无可用任务)
      </el-button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

interface ScriptTask {
  name: string
  full_name: string
  parameters: any
}

interface Script {
  id: number
  name: string
  description: string
  button_text: string
  button_style: {
    type?: string
    size?: string
    color?: string
    backgroundColor?: string
    borderColor?: string
    borderRadius?: string
    padding?: string
    margin?: string
  }
  position: string
  display_order: number
  loading: boolean
  tasks: ScriptTask[]
}

interface Props {
  scripts: Script[]
  position: 'top-left' | 'top-right' | 'top-center' | 'bottom-left' | 'bottom-right' | 'bottom-center' | 'sidebar-left' | 'sidebar-right' | 'floating' | 'custom'
  customPosition?: {
    top?: string
    left?: string
    right?: string
    bottom?: string
    position?: 'absolute' | 'fixed' | 'relative'
  }
}

const props = withDefaults(defineProps<Props>(), {
  position: 'top-right'
})

const emit = defineEmits<{
  'execute-script': [script: Script, task: ScriptTask]
}>()

// 过滤当前位置的脚本
const availableScripts = computed(() => {
  return props.scripts
    .filter(script => script.position === props.position)
    .sort((a, b) => a.display_order - b.display_order)
})

// 位置相关的CSS类
const positionClass = computed(() => {
  const baseClass = 'script-buttons'
  
  switch (props.position) {
    case 'top-left':
      return `${baseClass} ${baseClass}--top-left`
    case 'top-right':
      return `${baseClass} ${baseClass}--top-right`
    case 'top-center':
      return `${baseClass} ${baseClass}--top-center`
    case 'bottom-left':
      return `${baseClass} ${baseClass}--bottom-left`
    case 'bottom-right':
      return `${baseClass} ${baseClass}--bottom-right`
    case 'bottom-center':
      return `${baseClass} ${baseClass}--bottom-center`
    case 'sidebar-left':
      return `${baseClass} ${baseClass}--sidebar-left`
    case 'sidebar-right':
      return `${baseClass} ${baseClass}--sidebar-right`
    case 'floating':
      return `${baseClass} ${baseClass}--floating`
    case 'custom':
      return `${baseClass} ${baseClass}--custom`
    default:
      return `${baseClass} ${baseClass}--top-right`
  }
})

// 按钮包装器类
const buttonWrapperClass = computed(() => {
  if (props.position.includes('sidebar')) {
    return 'button-wrapper button-wrapper--vertical'
  }
  return 'button-wrapper button-wrapper--horizontal'
})

// 获取按钮样式
const getButtonStyle = (script: Script) => {
  const baseStyle: any = {}
  
  if (script.button_style) {
    if (script.button_style.color) baseStyle.color = script.button_style.color
    if (script.button_style.backgroundColor) baseStyle.backgroundColor = script.button_style.backgroundColor
    if (script.button_style.borderColor) baseStyle.borderColor = script.button_style.borderColor
    if (script.button_style.borderRadius) baseStyle.borderRadius = script.button_style.borderRadius
    if (script.button_style.padding) baseStyle.padding = script.button_style.padding
    if (script.button_style.margin) baseStyle.margin = script.button_style.margin
  }
  
  // 自定义位置的额外样式
  if (props.position === 'custom' && props.customPosition) {
    Object.assign(baseStyle, props.customPosition)
  }
  
  return baseStyle
}
</script>

<style scoped lang="less">
.script-buttons-container {
  display: flex;
  gap: 8px;
  z-index: 1000;
  
  &.script-buttons {
    // 顶部位置
    &--top-left {
      position: absolute;
      top: 16px;
      left: 16px;
      flex-direction: row;
    }
    
    &--top-right {
      position: absolute;
      top: 16px;
      right: 16px;
      flex-direction: row;
    }
    
    &--top-center {
      position: absolute;
      top: 16px;
      left: 50%;
      transform: translateX(-50%);
      flex-direction: row;
    }
    
    // 底部位置
    &--bottom-left {
      position: absolute;
      bottom: 16px;
      left: 16px;
      flex-direction: row;
    }
    
    &--bottom-right {
      position: absolute;
      bottom: 16px;
      right: 16px;
      flex-direction: row;
    }
    
    &--bottom-center {
      position: absolute;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%);
      flex-direction: row;
    }
    
    // 侧边栏位置
    &--sidebar-left {
      position: fixed;
      top: 50%;
      left: 16px;
      transform: translateY(-50%);
      flex-direction: column;
      background: rgba(255, 255, 255, 0.9);
      padding: 12px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    &--sidebar-right {
      position: fixed;
      top: 50%;
      right: 16px;
      transform: translateY(-50%);
      flex-direction: column;
      background: rgba(255, 255, 255, 0.9);
      padding: 12px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    // 浮动位置
    &--floating {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      flex-direction: row;
      background: rgba(255, 255, 255, 0.95);
      padding: 16px;
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      backdrop-filter: blur(10px);
    }
    
    // 自定义位置
    &--custom {
      /* 样式通过内联方式应用 */
    }
  }
}

.button-wrapper {
  &--horizontal {
    margin-right: 8px;
    
    &:last-child {
      margin-right: 0;
    }
  }
  
  &--vertical {
    margin-bottom: 8px;
    width: 100%;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .script-buttons-container {
    &.script-buttons--sidebar-left,
    &.script-buttons--sidebar-right {
      position: fixed;
      bottom: 16px;
      top: auto;
      left: 16px;
      right: 16px;
      transform: none;
      flex-direction: row;
      justify-content: space-around;
    }
    
    &.script-buttons--floating {
      bottom: 16px;
      top: auto;
      left: 16px;
      right: 16px;
      transform: none;
      flex-direction: row;
      justify-content: space-around;
    }
  }
}
</style>
