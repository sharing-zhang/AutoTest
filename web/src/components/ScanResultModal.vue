<template>
  <a-modal
    width="1600px"
    :destroyOnClose="true"
    :body-style="bodystyle"
    :visible="visible"
    :forceRender="true"
    :title="title"
    @cancel="handleCancel"
    cancelText="取消"
  >
    <!-- 根据结果类型显示不同的内容 -->
    <div v-if="resultData.result_type === 'script' || resultData.result_type === 'task'">
      <!-- 脚本执行结果显示 -->
      <el-descriptions title="脚本执行信息" :column="2" border>
        <el-descriptions-item label="脚本名称">
          {{ resultData.scandevresult_filename || '未知' }}
        </el-descriptions-item>
        <el-descriptions-item label="任务ID">
          {{ resultData.task_id || '无' }}
        </el-descriptions-item>
        <el-descriptions-item label="执行时间">
          {{ resultData.scandevresult_time }}
        </el-descriptions-item>
        <el-descriptions-item label="执行耗时">
          {{ resultData.execution_time ? `${resultData.execution_time}秒` : '未知' }}
        </el-descriptions-item>
        <el-descriptions-item label="执行者">
          {{ resultData.director }}
        </el-descriptions-item>
        <el-descriptions-item label="结果类型">
          {{ resultData.result_type === 'script' ? '脚本执行' : '任务执行' }}
        </el-descriptions-item>
        <el-descriptions-item label="所填参数" v-if="resultData.parameters && Object.keys(resultData.parameters).length > 0">
          <div
            style="
              white-space: pre-wrap;
              font-family: 'Courier New', monospace;
              background: #f8f8f8;
              padding: 8px;
              border-radius: 4px;
              max-height: 200px;
              overflow-y: auto;
            "
          >
            {{ formatParametersWithLabels(resultData.parameters, resultData.script_name) }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
      
      <!-- 脚本输出结果 -->
      <el-divider content-position="left">脚本输出结果</el-divider>
      <el-card v-if="resultData.script_output" shadow="never" style="margin-bottom: 16px;">
        <template #header>
          <span style="color: #67C23A;">
            <el-icon><SuccessFilled /></el-icon>
            执行结果
          </span>
        </template>
        <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f5f5f5; padding: 12px; border-radius: 4px;">
          {{ resultData.script_output }}
        </div>
      </el-card>
      
      <!-- 错误信息 -->
      <el-card v-if="resultData.error_message" shadow="never" style="margin-bottom: 16px;">
        <template #header>
          <span style="color: #F56C6C;">
            <el-icon><CircleCloseFilled /></el-icon>
            错误信息
          </span>
        </template>
        <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #fef0f0; padding: 12px; border-radius: 4px; color: #F56C6C;">
          {{ resultData.error_message }}
        </div>
      </el-card>
      
      <!-- 完整JSON结果（折叠显示） -->
      <el-collapse style="margin-top: 16px;">
        <el-collapse-item title="查看完整JSON结果" name="json">
          <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f8f8f8; padding: 12px; border-radius: 4px; max-height: 400px; overflow-y: auto;">
            {{ formatJsonContent(resultData.scandevresult_content) }}
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
    
    <!-- 传统扫描结果显示 -->
    <div v-else style="white-space: pre-wrap">
      {{ resultData.scandevresult_content }}
    </div>
    
    <template #footer="footer">
      <a-button @click="handleCancel">关闭</a-button>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue';

// 定义组件属性
interface Props {
  visible: boolean;
  title?: string;
  resultData: any;
}

// 定义组件事件
interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'cancel'): void;
}

const props = withDefaults(defineProps<Props>(), {
  title: '资源扫描结果',
  resultData: () => ({})
});

const emit = defineEmits<Emits>();

// 弹窗样式
const bodystyle = {
  maxHeight: '70vh',
  overflowY: 'auto',
  padding: '20px'
};

// 关闭弹窗
const handleCancel = () => {
  emit('update:visible', false);
  emit('cancel');
};

// 格式化JSON内容
const formatJsonContent = (jsonStr: string) => {
  if (!jsonStr) return '';
  try {
    const parsed = JSON.parse(jsonStr);
    return JSON.stringify(parsed, null, 2);
  } catch (error) {
    return jsonStr;
  }
};

// 格式化参数显示（带标签）
const formatParametersWithLabels = (parameters: any, scriptName?: string) => {
  if (!parameters) return '';
  
  try {
    let paramObj = parameters;
    
    // 如果是字符串，尝试解析为JSON
    if (typeof parameters === 'string') {
      paramObj = JSON.parse(parameters);
    }
    
    // 如果是对象，转换为键值对格式
    if (typeof paramObj === 'object' && paramObj !== null) {
      // 硬编码的标签映射
      const labelMap: { [key: string]: string } = {
        // check_Reward
        'directory': '目录路径',
        'file_name': '需要检查的文件名',
        'block_name': '配置块名称',
        'rules': '配置项组',
        
        // check_ConfigTime
        'file_names': '需要检查的配置文件',
        'start_time_field': '开始时间对应参数',
        'end_time_field': '结束时间对应参数',
        'recursive': '递归扫描子目录',
        'encoding': '文件编码',
        'expected_days': '正确的活动天数',
        
        // checkConfigExist
        'config_file': '配置文件地址',
        'project_root': '工程文件目录',
        'path_fields_param': '配置参数名',
        'custom_extensions_param': '文件后缀名',
        
        // checkFileName
        'root_path': '目录路径',
        'regex_pattern': '正则表达式',
        'file_extensions': '文件后缀名',
        
        // checkconfigempty
        'file_path': '配置文件地址',
        'parameters_str': '配置参数名',
        
        // check_TextQuality
        't_description': '字段名(可选)',
        
        // find_resource_name
        'resource_name': '资源名称',
        'search_path': '搜索路径',
        
        // 通用参数
        'page': '页码',
        'keyword': '关键词',
        'force': '强制执行',
        'timeout': '超时时间',
        'retry_count': '重试次数'
      };
      
      let formatted = '';
      Object.entries(paramObj).forEach(([key, value]) => {
        const label = labelMap[key] || key;
        const displayValue = value !== null && value !== undefined ? String(value) : '';
        
        if (formatted) {
          formatted += '\n';
        }
        formatted += `${label}: ${displayValue}`;
      });
      
      return formatted;
    }
    
    return String(parameters);
  } catch (error) {
    console.error('参数格式化失败:', error);
    return String(parameters);
  }
};
</script>

<style scoped>
/* 可以添加一些自定义样式 */
</style>
