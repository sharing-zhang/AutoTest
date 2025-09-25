<template>
  <!-- 脚本按钮容器 - 根据位置和可用脚本动态渲染按钮 -->
  <div class="script-buttons-container" :class="positionClass">
    <!-- 遍历当前位置的所有可用脚本 -->
    <template v-for="script in availableScripts" :key="script.id">
      
      <!-- 多任务脚本 - 使用下拉菜单显示所有任务选项 -->
      <el-dropdown v-if="script.tasks && script.tasks.length > 1" :class="buttonWrapperClass">
        <!-- 主按钮 - 带有下拉箭头 -->
        <el-button 
          :type="script.button_style?.type || 'primary'" 
          :size="script.button_style?.size || 'default'"
          :loading="script.loading"
          :style="getButtonStyle(script)"
        >
          <!-- 根据加载状态显示不同文本 -->
          {{ script.loading ? '执行中...' : script.button_text }}
          <!-- 下拉箭头图标 -->
          <el-icon><ArrowDown /></el-icon>
        </el-button>
        
        <!-- 下拉菜单内容 -->
        <template #dropdown>
          <el-dropdown-menu>
            <!-- 遍历脚本的所有任务，为每个任务创建一个菜单项 -->
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
      
      <!-- 单任务脚本 - 直接显示为普通按钮 -->
      <el-button 
        v-else-if="script.tasks && script.tasks.length > 0"
        :type="script.button_style?.type || 'primary'"
        :size="script.button_style?.size || 'default'"
        :class="buttonWrapperClass"
        :style="getButtonStyle(script)"
        @click="$emit('execute-script', script, script.tasks[0])" 
        :loading="script.loading"
      >
        <!-- 根据加载状态显示不同文本 -->
        {{ script.loading ? '执行中...' : script.button_text }}
      </el-button>
      
      <!-- 无任务脚本 - 显示为禁用状态的按钮 -->
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

// 脚本任务接口定义
interface ScriptTask {
  name: string        // 任务名称
  full_name: string   // 任务完整名称
  parameters: any     // 任务参数
}

// 脚本对象接口定义
interface Script {
  id: number                    // 脚本唯一标识
  name: string                  // 脚本名称
  description: string           // 脚本描述
  button_text: string           // 按钮显示文本
  button_style: {               // 按钮样式配置
    type?: string               // 按钮类型 (primary, success, warning, danger, info)
    size?: string               // 按钮尺寸 (large, default, small)
    color?: string              // 文字颜色
    backgroundColor?: string    // 背景颜色
    borderColor?: string        // 边框颜色
    borderRadius?: string       // 圆角半径
    padding?: string            // 内边距
    margin?: string             // 外边距
  }
  position: string              // 按钮位置
  customPosition?: {            // 自定义位置配置
    top?: string
    left?: string
    right?: string
    bottom?: string
    position?: 'absolute' | 'fixed' | 'relative'
  }
  display_order: number         // 显示顺序
  loading: boolean              // 是否正在加载
  tasks: ScriptTask[]           // 脚本包含的任务列表
}

// 组件Props接口定义
interface Props {
  scripts: Script[]             // 所有脚本列表
  position: 'top-left' | 'top-right' | 'top-center' | 'bottom-left' | 'bottom-right' | 'bottom-center' | 'sidebar-left' | 'sidebar-right' | 'floating' | 'custom'  // 按钮位置
  customPosition?: {            // 自定义位置配置
    top?: string
    left?: string
    right?: string
    bottom?: string
    position?: 'absolute' | 'fixed' | 'relative'
  }
}

// 设置默认props值
const props = withDefaults(defineProps<Props>(), {
  position: 'top-right'
})

// 定义组件事件
const emit = defineEmits<{
  'execute-script': [script: Script, task: ScriptTask]  // 执行脚本事件
}>()

/**
 * 计算当前位置的可用脚本
 * 过滤出匹配当前位置的脚本并按显示顺序排序
 */
const availableScripts = computed(() => {
  return props.scripts
    .filter(script => script.position === props.position)  // 筛选匹配位置的脚本
    .sort((a, b) => a.display_order - b.display_order)     // 按显示顺序排序
})

/**
 * 计算位置相关的CSS类名
 * 根据不同位置返回对应的样式类
 */
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

/**
 * 计算按钮包装器的CSS类名
 * 侧边栏位置使用垂直布局，其他位置使用水平布局
 */
const buttonWrapperClass = computed(() => {
  if (props.position.includes('sidebar')) {
    return 'button-wrapper button-wrapper--vertical'
  }
  return 'button-wrapper button-wrapper--horizontal'
})

/**
 * 获取按钮的内联样式
 * @param script 脚本对象
 * @returns 返回样式对象
 */
const getButtonStyle = (script: Script) => {
  const baseStyle: any = {}
  
  // 应用脚本配置的按钮样式
  if (script.button_style) {
    if (script.button_style.color) baseStyle.color = script.button_style.color
    if (script.button_style.backgroundColor) baseStyle.backgroundColor = script.button_style.backgroundColor
    if (script.button_style.borderColor) baseStyle.borderColor = script.button_style.borderColor
    if (script.button_style.borderRadius) baseStyle.borderRadius = script.button_style.borderRadius
    if (script.button_style.padding) baseStyle.padding = script.button_style.padding
    if (script.button_style.margin) baseStyle.margin = script.button_style.margin
  }
  
  // 应用自定义位置的额外样式
  if (script.position === 'custom' && script.customPosition) {
    Object.assign(baseStyle, script.customPosition)
  }
  
  return baseStyle
}
</script>

<style scoped lang="less">
/* 脚本按钮容器的基础样式 */
.script-buttons-container {
  display: flex;
  gap: 8px;           /* 按钮之间的间距 */
  z-index: 1000;      /* 确保按钮在其他元素之上 */
  
  &.script-buttons {
    /* 顶部位置样式 */
    &--top-left {
      position: absolute;
      top: 16px;
      left: 16px;
      flex-direction: row;    /* 水平排列 */
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
      transform: translateX(-50%);  /* 水平居中 */
      flex-direction: row;
    }
    
    /* 底部位置样式 */
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
      transform: translateX(-50%);  /* 水平居中 */
      flex-direction: row;
    }
    
    /* 侧边栏位置样式 */
    &--sidebar-left {
      position: fixed;              /* 固定定位，不随页面滚动 */
      top: 50%;
      left: 16px;
      transform: translateY(-50%);  /* 垂直居中 */
      flex-direction: column;       /* 垂直排列 */
      background: rgba(255, 255, 255, 0.9);  /* 半透明背景 */
      padding: 12px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);  /* 阴影效果 */
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
    
    /* 浮动位置样式 - 页面中央悬浮 */
    &--floating {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);  /* 完全居中 */
      flex-direction: row;
      background: rgba(255, 255, 255, 0.95);  /* 更高透明度背景 */
      padding: 16px;
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);  /* 更强阴影效果 */
      backdrop-filter: blur(10px);      /* 背景模糊效果 */
    }
    
    /* 自定义位置 - 样式通过内联方式应用 */
    &--custom {
      /* 样式通过getButtonStyle方法动态应用 */
    }
  }
}

/* 按钮包装器样式 */
.button-wrapper {
  /* 水平布局按钮样式 */
  &--horizontal {
    margin-right: 8px;
    
    &:last-child {
      margin-right: 0;  /* 最后一个按钮不需要右边距 */
    }
  }
  
  /* 垂直布局按钮样式 */
  &--vertical {
    margin-bottom: 8px;
    width: 100%;        /* 垂直布局时按钮占满容器宽度 */
    
    &:last-child {
      margin-bottom: 0; /* 最后一个按钮不需要下边距 */
    }
  }
}

/* 响应式设计 - 移动端适配 */
@media (max-width: 768px) {
  .script-buttons-container {
    /* 在移动端，侧边栏和浮动按钮调整为底部横向排列 */
    &.script-buttons--sidebar-left,
    &.script-buttons--sidebar-right {
      position: fixed;
      bottom: 16px;         /* 移动到底部 */
      top: auto;
      left: 16px;
      right: 16px;
      transform: none;
      flex-direction: row;  /* 改为水平排列 */
      justify-content: space-around;  /* 平均分布 */
    }
    
    &.script-buttons--custom {
      /* 自定义位置样式 - 通过内联样式控制 */
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