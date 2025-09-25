<template>
  <!-- 钉钉机器人消息同步弹窗 -->
  <a-modal
    :visible="visible"
    :forceRender="true"
    :title="title"
    ok-text="确认发送"
    cancel-text="取消"
    @ok="handleSend"
    @cancel="handleCancel"
  >
    <div>
      <a-form
        ref="formRef"
        :label-col="{ style: { width: '180px' } }"
        :model="form"
        :rules="rules"
      >
        <a-row :gutter="24">
          <a-col span="24">
            <a-form-item label="群机器人Webhook" name="webhook">
              <a-input 
                placeholder="请输入群机器人的Webhook" 
                v-model:value="form.webhook" 
                allowClear 
              />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="群机器人加签密钥" name="secret">
              <a-input 
                placeholder="请输入群机器人加签密钥" 
                v-model:value="form.secret" 
                allowClear 
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { FormInstance, message } from 'ant-design-vue'
import { sendmessageApi } from '/@/api/scanDevUpdate'

// 组件属性接口
interface Props {
  visible: boolean
  title?: string
  recordData?: any
  apiEndpoint?: string
}

// 组件事件接口
interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
  (e: 'error', error: any): void
}

// 接收属性
const props = withDefaults(defineProps<Props>(), {
  title: '扫描结果同步钉钉机器人',
  apiEndpoint: '/myapp/admin/scanDevUpdate/sendmessage'
})

// 定义事件
const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive({
  id: undefined,
  webhook: undefined,
  secret: undefined,
})

// 表单验证规则
const rules = reactive({
  webhook: [{ required: true, message: '请输入群机器人的Webhook', trigger: 'change' }],
  secret: [{ required: true, message: '请输入群机器人加签密钥', trigger: 'change' }],
})

// 发送消息
const handleSend = () => {
  formRef.value
    ?.validate()
    .then(() => {
      const formData = new FormData()
      formData.append('id', form.id)
      formData.append('resultSendDingDingRobot_webhook', form.webhook)
      formData.append('resultSendDingDingRobot_secret', form.secret)
      
      sendmessageApi(
        {
          id: form.id,
        },
        formData,
      )
        .then((res) => {
          message.success('钉钉群机器人消息发送成功')
          emit('success')
          handleCancel()
        })
        .catch((err) => {
          console.log(err)
          message.error(err.msg || '钉钉群机器人消息发送失败')
          emit('error', err)
        })
    })
    .catch((err) => {
      console.log('表单验证失败:', err)
    })
}

// 关闭弹窗
const handleCancel = () => {
  emit('update:visible', false)
  // 重置表单
  formRef.value?.resetFields()
  form.id = undefined
  form.webhook = undefined
  form.secret = undefined
}

// 监听 visible 变化，当弹窗打开时填充数据
watch(() => props.visible, (newVisible) => {
  if (newVisible && props.recordData) {
    // 填充记录数据
    form.id = props.recordData.id
    // 可以在这里设置默认的 webhook 和 secret，或者从配置中读取
  }
})

// 暴露方法给父组件
defineExpose({
  open: (recordData: any) => {
    form.id = recordData.id
    emit('update:visible', true)
  }
})
</script>

<style scoped>
/* 可以添加一些自定义样式 */
</style>
