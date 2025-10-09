<template>
  <a-table
    size="middle"
    rowKey="scanResult_id"
    :loading="loading"
    :columns="columns"
    :data-source="dataSource"
    :scroll="{ x: 'max-content' }"
    :pagination="{
      size: 'small',
      current: current,
      pageSize: pageSize,
      onChange: (page) => emit('page-change', page),
      showSizeChanger: false,
      showTotal: (total) => `共${total}条数据`,
    }"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 组件属性接口
interface Props {
  loading?: boolean
  dataSource?: any[]
  columns?: any[]
  current?: number
  pageSize?: number
}

// 组件事件接口
interface Emits {
  (e: 'page-change', page: number): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  dataSource: () => [],
  columns: () => [],
  current: 1,
  pageSize: 10
})

const emit = defineEmits<Emits>()

// 默认列配置
const defaultColumns = [
  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    align: "center",
    width: 50
  },
  {
    title: '文件名',
    dataIndex: 'scandevresult_filename',
    align: "center",
    key: 'scandevresult_filename',
    width: 200
  },
  {
    title: '时间',
    dataIndex: 'scandevresult_time',
    align: "center",
    key: 'scandevresult_time',
    width: 200
  },
  {
    title: '负责人',
    dataIndex: 'director',
    align: "center",
    key: 'director',
    width: 110
  },
  {
    title: '备注',
    dataIndex: 'remark',
    align: "center",
    key: 'remark',
    width: 120,
    ellipsis: true
  }
]

// 使用传入的列配置或默认配置
const columns = computed(() => {
  return props.columns.length > 0 ? props.columns : defaultColumns
})
</script>

<style scoped lang="less">
// 可以添加自定义样式
</style>
