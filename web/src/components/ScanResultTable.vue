<template>
  <a-table
    size="middle"
    rowKey="scanResult_id"
    :loading="loading"
    :columns="columns"
    :data-source="dataSource"
    :scroll="{ x: 'max-content' }"
    :pagination="paginationConfig"
  >
    <template #bodyCell="{ text, record, index, column }">
      <template v-if="column.key === 'operation'">
        <span>
          <a @click="handleSend(record)">消息同步</a>
          <a-divider type="vertical" />
          <a @click="handleViewDetail(record)">查看详情</a>
          <a-divider type="vertical" />
          <a @click="handleRerun(record)" v-if="showRerun">重跑</a>
          <a-divider type="vertical" v-if="showRerun" />
          <a @click="handleEdit(record)" v-if="showEdit">编辑</a>
          <a-divider type="vertical" v-if="showEdit" />
          <a-popconfirm
            title="确定要删除这条记录吗？"
            ok-text="确定"
            cancel-text="取消"
            @confirm="handleDelete(record)"
            v-if="showDelete"
          >
            <a style="color: #ff4d4f;">删除</a>
          </a-popconfirm>
        </span>
      </template>
      <template v-else-if="column.key === 'execution_status'">
        <a-tag :color="getStatusColor(record.execution_status)">
          {{ getStatusText(record.execution_status) }}
        </a-tag>
      </template>
      <template v-else-if="column.key === 'result_summary'">
        <span :title="record.result_summary">
          {{ formatSummary(record.result_summary) }}
        </span>
      </template>
    </template>
  </a-table>
</template>

<script setup lang="ts">
import { h, computed } from 'vue';
import { message } from 'ant-design-vue';
import { rerunScriptApi } from '/@/api/scanDevUpdate';

// 定义组件属性
interface Props {
  loading?: boolean;
  dataSource?: any[];
  columns?: any[];
  pagination?: any;
  showRerun?: boolean;
  showEdit?: boolean;
  showDelete?: boolean;
  pageSize?: number;
  current?: number;
  useBuiltinRerun?: boolean; // 是否使用内置的重跑功能
}

// 定义组件事件
interface Emits {
  (e: 'send', record: any): void;
  (e: 'view-detail', record: any): void;
  (e: 'rerun', record: any): void;
  (e: 'edit', record: any): void;
  (e: 'delete', record: any): void;
  (e: 'page-change', current: number): void;
  (e: 'refresh-data'): void;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  dataSource: () => [],
  columns: () => [],
  pagination: () => ({}),
  showRerun: true,
  showEdit: false,
  showDelete: false,
  pageSize: 10,
  current: 1,
  useBuiltinRerun: false
});

const emit = defineEmits<Emits>();

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
    title: '脚本名称',
    dataIndex: 'scandevresult_filename',
    align: "center",
    key: 'scandevresult_filename',
    width: 200
  },
  {
    title: '执行时间',
    dataIndex: 'scandevresult_time',
    align: "center",
    key: 'scandevresult_time',
    width: 200
  },
  {
    title: '执行人',
    dataIndex: 'director',
    align: "center",
    key: 'director',
    width: 110
  },
  {
    title: '执行状态',
    dataIndex: 'execution_status',
    align: "center",
    key: 'execution_status',
    width: 120
  },
  {
    title: '结果摘要',
    dataIndex: 'result_summary',
    align: "center",
    key: 'result_summary',
    width: 120,
    ellipsis: true
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'operation',
    align: 'center',
    fixed: 'right',
    width: 200
  }
];

// 使用传入的列配置或默认配置
const columns = computed(() => {
  return props.columns.length > 0 ? props.columns : defaultColumns;
});

// 分页配置
const paginationConfig = computed(() => {
  const defaultPagination = {
    size: 'small',
    current: props.current,
    pageSize: props.pageSize,
    onChange: (current: number) => emit('page-change', current),
    showSizeChanger: false,
    showTotal: (total: number) => `共${total}条数据`,
  };
  
  return { ...defaultPagination, ...props.pagination };
});

// 状态颜色映射
const getStatusColor = (status: string) => {
  const statusMap = {
    'SUCCESS': 'success',
    'FAILURE': 'error',
    'RUNNING': 'processing',
    'PENDING': 'default',
    'TIMEOUT': 'warning',
    'CANCELLED': 'default'
  };
  return statusMap[status] || 'default';
};

// 状态文本映射
const getStatusText = (status: string) => {
  const statusMap = {
    'SUCCESS': '成功',
    'FAILURE': '失败',
    'RUNNING': '运行中',
    'PENDING': '等待中',
    'TIMEOUT': '超时',
    'CANCELLED': '已取消'
  };
  return statusMap[status] || '未知';
};

// 格式化摘要
const formatSummary = (summary: string) => {
  if (!summary) return '-';
  if (summary.length > 20) {
    return summary.substring(0, 20) + '...';
  }
  return summary;
};

// 事件处理
const handleSend = (record: any) => {
  emit('send', record);
};

const handleViewDetail = (record: any) => {
  emit('view-detail', record);
};

const handleRerun = (record: any) => {
  if (props.useBuiltinRerun) {
    // 使用内置的重跑功能
    handleBuiltinRerun(record);
  } else {
    // 使用外部传入的重跑函数
    emit('rerun', record);
  }
};

// 内置重跑功能
const handleBuiltinRerun = async (record: any) => {
  let loadingMessage: any = null;
  
  try {
    // 检查是否为脚本执行结果
    if (record.result_type !== 'script' && record.result_type !== 'task') {
      message.warning('只有脚本执行结果才能重跑');
      return;
    }

    // 检查是否有task_id
    if (!record.task_id) {
      message.warning('该记录没有关联的任务ID，无法重跑');
      return;
    }

    // 显示加载状态
    loadingMessage = message.loading('正在启动重跑任务...', 0);

    // 调用重跑API
    const response = await rerunScriptApi({ id: record.id });
    
    // 关闭加载状态
    if (loadingMessage) {
      loadingMessage();
      loadingMessage = null;
    }
    
    if (response.code === 0) {
      message.success(response.msg || '重跑任务已启动');
      
      // 发送刷新事件给父组件
      emit('refresh-data');
    } else {
      message.error(response.msg || '重跑失败');
    }
  } catch (error) {
    console.error('重跑脚本失败:', error);
    message.error('重跑失败，请稍后重试');
  } finally {
    // 确保关闭加载状态
    if (loadingMessage) {
      loadingMessage();
    }
  }
};

const handleEdit = (record: any) => {
  emit('edit', record);
};

const handleDelete = (record: any) => {
  emit('delete', record);
};
</script>

<style scoped>
/* 可以添加一些自定义样式 */
</style>
