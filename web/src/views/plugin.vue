<template>
  <div>
    <!--页面区域-->
    <div class="page-view">
      <div class="table-operations">
        <a-space>
          <a-button type="primary" @click="openUploadModal">上传文件</a-button>
          <a-button @click="reloadList">刷新</a-button>
        </a-space>
      </div>
      <a-table size="middle" rowKey="name" :loading="data.loading" :columns="columns" :data-source="data.list" :pagination="false">
          <template #bodyCell="{ text, record, column }">
          <template v-if="column.key === 'action'">
            <a :href="`${BASE_URL}/myapp/admin/plugin/download?name=${encodeURIComponent(record.name)}`" :download="record.name">下载</a>
          </template>
          <template v-else-if="column.key === 'desc'">
            <span :title="record.description">{{ record.description || '暂无描述' }}</span>
          </template>
          <template v-else-if="column.key === 'display_name'">
            <span :title="record.display_name">{{ record.display_name || record.name }}</span>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 上传弹窗 -->
    <a-modal :visible="upload.visible" :title="'上传插件'" ok-text="上传" cancel-text="取消" @ok="confirmUpload" @cancel="closeUploadModal">
      <a-form :model="upload.form" :label-col="{ style: { width: '100px' } }">
        <a-form-item label="插件名称">
          <a-input v-model:value="upload.form.display_name" placeholder="请输入插件名称" />
        </a-form-item>
        <a-form-item label="功能描述">
          <a-input v-model:value="upload.form.description" placeholder="请输入功能描述" />
        </a-form-item>
        <a-form-item label="选择文件">
          <a-upload :before-upload="beforeExePick" :show-upload-list="true" :multiple="false">
            <a-button>选择文件</a-button>
          </a-upload>
          <div v-if="upload.fileName" style="margin-top: 8px; color: #666">已选择: {{ upload.fileName }}</div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
  import { message } from 'ant-design-vue';
  import { BASE_URL } from '/@/store/constants';
  import { uploadExeApi, listExeApi, updateApi } from '/@/api/plugin';
  import type { FormInstance } from 'ant-design-vue';
  import { reactive, ref, onMounted, nextTick } from 'vue';

  const columns = reactive([
    { title: '插件名称', dataIndex: 'display_name', key: 'display_name', align: 'left' },
    { title: '文件名', dataIndex: 'name', key: 'name', align: 'left' },
    { title: '插件功能描述', dataIndex: 'description', key: 'desc', align: 'left' },
    { title: '下载', dataIndex: 'url', key: 'action', align: 'center' },
  ]);

  // 选中的文件
  const selectedFile = ref<File | null>(null);

  const upload = reactive({
    visible: false,
    form: {
      display_name: '',
      description: '',
    },
    file: null as File | null,
    fileName: '',
  });

  const openUploadModal = () => {
    // 重置并打开上传弹窗
    upload.visible = true;
    upload.form.display_name = '';
    upload.form.description = '';
    upload.file = null;
    upload.fileName = '';
  };
  const closeUploadModal = () => {
    upload.visible = false;
    upload.form.display_name = '';
    upload.form.description = '';
    upload.file = null;
    upload.fileName = '';
  };

  const beforeExePick = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    // if (ext !== 'exe') {
    //   message.error('只允许上传 .exe 文件');
    //   return false;
    // }
    upload.file = file;
    upload.fileName = file.name;
    selectedFile.value = file; // 同步更新 selectedFile
    return false;
  };

  // 页面数据
  const data = reactive({
    list: [] as any[],
    loading: false,
  });

  // 弹窗数据源
  const modal = reactive({
    visible: false,
    confirmLoading: false,
    originalFileName: '',
    formData: {
      fileName: '',
      description: '',
    },
    rules: {
      fileName: [
        { required: true, message: '请输入文件名', trigger: 'blur' },
        {
          pattern: /^[^<>:"/\\|?*\x00-\x1f]+$/,
          message: '文件名包含非法字符',
          trigger: 'blur',
        },
        { min: 1, max: 100, message: '文件名长度应在1-100个字符之间', trigger: 'blur' },
      ],
      description: [{ max: 200, message: '描述长度不能超过200个字符', trigger: 'blur' }],
    },
  });

  const uploadForm = ref<FormInstance>();

  onMounted(() => reloadList());


  // 确认上传
  const handleUploadConfirm = async () => {
    if (!selectedFile.value) {
      message.error('请先选择文件');
      return;
    }

    try {
      // 表单验证
      await uploadForm.value?.validate();

      modal.confirmLoading = true;

      const fd = new FormData();
      fd.append('file', selectedFile.value);
      fd.append('fileName', modal.formData.fileName);
      if (modal.formData.description) {
        fd.append('description', modal.formData.description);
      }

      await uploadExeApi(fd);
      message.success('上传成功');

      // 关闭弹窗并刷新列表
      handleUploadCancel();
      reloadList();
    } catch (e: any) {
      message.error(e?.msg || '上传失败');
    } finally {
      modal.confirmLoading = false;
    }
  };

  // 取消上传
  const handleUploadCancel = () => {
    modal.visible = false;
    modal.confirmLoading = false;
    selectedFile.value = null;

    // 重置表单数据
    modal.formData.fileName = '';
    modal.formData.description = '';
    modal.originalFileName = '';

    // 清除表单验证状态
    uploadForm.value?.resetFields();
  };

  const reloadList = async () => {
    data.loading = true;
    try {
      const res: any = await listExeApi();
      data.list = res.data || [];
    } catch (e) {
      message.error('获取列表失败');
    } finally {
      data.loading = false;
    }
  };

  const confirmUpload = async () => {
    if (!upload.file) {
      message.warning('请先选择文件');
      return;
    }
    const fd = new FormData();
    fd.append('file', upload.file);
    if (upload.form.description) fd.append('description', upload.form.description);
    if (upload.form.display_name) fd.append('display_name', upload.form.display_name);
    try {
      await uploadExeApi(fd);
      message.success('上传成功');
      closeUploadModal();
      reloadList();
    } catch (e: any) {
      message.error(e?.msg || '上传失败');
    }
  };

  // 删除不需要的函数
  const rowSelection = ref();
  const handleAdd = () => {};
  const handleEdit = (record: any) => {};
  const confirmDelete = (record: any) => {};
  const handleBatchDelete = () => {};
  const handleOk = () => {};
  const handleCancel = () => {};
  const resetModal = () => {};
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
