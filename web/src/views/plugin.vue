<template>
  <div>
    <!--页面区域-->
    <div class="page-view">
      <div class="table-operations">
        <a-space>
          <a-input v-model:value="uploadDesc" placeholder="插件功能描述" style="width: 260px" />
          <a-upload
            :multiple="false"
            :before-upload="beforeExeUpload"
            :show-upload-list="false"
          >
            <a-button type="primary">上传exe</a-button>
          </a-upload>
          <a-button @click="reloadList">刷新</a-button>
        </a-space>
      </div>
      <a-table
        size="middle"
        rowKey="name"
        :loading="data.loading"
        :columns="columns"
        :data-source="data.list"
        :pagination="false"
      >
        <template #bodyCell="{ text, record, column }">
          <template v-if="column.key === 'action'">
            <a :href="BASE_URL + record.url" target="_blank">下载</a>
          </template>
          <template v-else-if="column.key === 'desc'">
            <span :title="record.description">{{ record.description || '暂无描述' }}</span>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 无弹窗 -->
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue';
import { BASE_URL } from '/@/store/constants';
import { uploadExeApi, listExeApi } from '/@/api/plugin';

const columns = reactive([
  { title: '文件名', dataIndex: 'name', key: 'name', align: 'left' },
  { title: '插件功能描述', dataIndex: 'description', key: 'desc', align: 'left' },
  { title: '下载', dataIndex: 'url', key: 'action', align: 'center' },
]);

const uploadDesc = ref('');

const beforeExeUpload = async (file: File) => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (ext !== 'exe') {
    message.error('只允许上传 .exe 文件');
    return false;
  }
  const fd = new FormData();
  fd.append('file', file);
  if (uploadDesc.value) fd.append('description', uploadDesc.value);
  try {
    await uploadExeApi(fd);
    message.success('上传成功');
    reloadList();
    uploadDesc.value = '';
  } catch (e: any) {
    message.error(e?.msg || '上传失败');
  }
  return false;
};

const fileList = ref([]);

// 页面数据
const data = reactive({
  list: [] as any[],
  loading: false,
});

// 弹窗数据源
const modal = reactive({});

const myform = ref<FormInstance>();

onMounted(() => reloadList());

const reloadList = async () => {
  data.loading = true;
  try {
    const res: any = await listExeApi();
    data.list = res.data || [];
  } catch (e) {
  } finally {
    data.loading = false;
  }
};


const rowSelection = ref();

const handleAdd = () => {};
const handleEdit = (record: any) => {};

const confirmDelete = (record: any) => {};

const handleBatchDelete = () => {};

const handleOk = () => {};

const handleCancel = () => {};

// 恢复表单初始状态
const resetModal = () => {};

// 关闭弹窗
const hideModal = () => {};
</script>

<style scoped lang="less">
.page-view {
  min-height: 100%;
  background: #fff;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.table-operations {
  margin-bottom: 16px;
  text-align: right;
}

.table-operations > button {
  margin-right: 8px;
}
</style>
