<template>
  <a-modal
    :visible="visible"
    :forceRender="true"
    :title="title"
    ok-text="确认"
    cancel-text="取消"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <div>
      <a-form ref="formRef" :label-col="{ style: { width: '120px'} }" :model="form" :rules="rules">
        <a-row :gutter="24">
          <a-col span="24">
            <a-form-item label="文件名" name="scandevresult_filename">
              <a-input placeholder="请输入文件名" v-model:value="form.scandevresult_filename" allowClear />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="时间" name="scandevresult_time">
              <a-input placeholder="时间" v-model:value="form.scandevresult_time" allowClear />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="负责人" name="director">
              <a-input placeholder="请输入负责人" v-model:value="form.director" allowClear />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="备注" name="remark">
              <a-input placeholder="请输入备注" v-model:value="form.remark" allowClear />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { FormInstance } from 'ant-design-vue'

// 组件属性接口
interface Props {
  visible: boolean
  title?: string
  formData?: any
}

// 组件事件接口
interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'ok', formData: any): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '编辑记录',
  formData: () => ({})
})

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive({
  id: undefined,
  scandevresult_filename: '',
  scandevresult_time: '',
  director: '',
  remark: ''
})

// 表单验证规则
const rules = reactive({
  scandevresult_filename: [{ required: true, message: '请输入文件名', trigger: 'change' }],
  scandevresult_time: [{ required: true, message: '请输入时间', trigger: 'change' }],
  director: [{ required: true, message: '请输入负责人', trigger: 'change' }],
  remark: [{ required: false, trigger: 'change' }],
})

// 监听props变化，更新表单数据
watch(() => props.formData, (newData) => {
  if (newData) {
    Object.assign(form, newData)
  }
}, { immediate: true, deep: true })

// 监听visible变化，重置表单
watch(() => props.visible, (newVisible) => {
  if (newVisible && props.formData) {
    Object.assign(form, props.formData)
  }
})

// 确认处理
const handleOk = async () => {
  try {
    await formRef.value?.validate()
    emit('ok', { ...form })
    emit('update:visible', false)
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 取消处理
const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
}
</script>

<style scoped lang="less">
// 可以添加自定义样式
</style>
