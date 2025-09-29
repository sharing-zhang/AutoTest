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
            <a-space>
              <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
              <a :href="`${BASE_URL}/myapp/admin/plugin/download?name=${encodeURIComponent(record.name)}`" :download="record.name">下载</a>
            </a-space>
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

    <!-- 编辑插件弹窗 -->
    <a-modal
      :visible="edit.visible"
      title="编辑插件信息"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="edit.loading"
      @ok="confirmEdit"
      @cancel="closeEditModal"
    >
      <a-form :model="edit.form" :label-col="{ style: { width: '100px' } }">
        <a-form-item label="当前文件">
          <a-input :value="edit.form.name" disabled style="color: #666;" />
        </a-form-item>
        <a-form-item label="插件名称">
          <a-input
            v-model:value="edit.form.display_name"
            placeholder="请输入插件名称"
            :maxlength="100"
            show-count
          />
        </a-form-item>
        <a-form-item label="功能描述">
          <a-textarea
            v-model:value="edit.form.description"
            placeholder="请输入功能描述"
            :rows="4"
            :maxlength="200"
            show-count
          />
        </a-form-item>
        <a-form-item label="重新上传文件">
          <a-upload :before-upload="beforeEditFilePick" :show-upload-list="true" :multiple="false" :file-list="edit.fileList">
            <a-button>选择新文件</a-button>
          </a-upload>
          <div v-if="edit.newFileName" style="margin-top: 8px; color: #1890ff">
            将替换为: {{ edit.newFileName }}
          </div>
          <div v-else style="margin-top: 8px; color: #999; font-size: 12px">
            不选择文件则仅更新插件信息
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
  import { message } from 'ant-design-vue';
  import { BASE_URL } from '/@/store/constants';
  import { uploadExeApi, listExeApi, updateExeApi } from '/@/api/plugin'; // 注意这里改为 updateExeApi
  import type { FormInstance } from 'ant-design-vue';
  import { reactive, ref, onMounted, nextTick } from 'vue';

  const columns = reactive([
    { title: '插件名称', dataIndex: 'display_name', key: 'display_name', align: 'left' },
    { title: '文件名', dataIndex: 'name', key: 'name', align: 'left' },
    { title: '插件功能描述', dataIndex: 'description', key: 'desc', align: 'left' },
    { title: '操作', dataIndex: 'action', key: 'action', align: 'center', width: 150 },
  ]);

  // 选中的文件
  const selectedFile = ref<File | null>(null);

  // 上传相关
  const upload = reactive({
    visible: false,
    form: {
      display_name: '',
      description: '',
    },
    file: null as File | null,
    fileName: '',
  });

  // 编辑相关
  const edit = reactive({
    visible: false,
    loading: false,
    form: {
      name: '', // 文件名，不可编辑
      display_name: '', // 插件显示名称
      description: '', // 插件描述
    },
    originalData: {} as any, // 保存原始数据
    newFile: null as File | null, // 新选择的文件
    newFileName: '', // 新文件名
    fileList: [] as any[], // 文件列表
  });

  const openUploadModal = () => {
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

  // 打开编辑弹窗
  const openEditModal = (record: any) => {
    console.log('编辑插件数据:', record);

    edit.originalData = { ...record };
    edit.form.name = record.name || '';
    edit.form.display_name = record.display_name || record.name || '';
    edit.form.description = record.description || '';

    // 重置文件相关
    edit.newFile = null;
    edit.newFileName = '';
    edit.fileList = [];

    edit.visible = true;
    console.log('自动填充后的表单数据:', edit.form);
  };

  // 关闭编辑弹窗
  const closeEditModal = () => {
    edit.visible = false;
    edit.loading = false;
    edit.form.name = '';
    edit.form.display_name = '';
    edit.form.description = '';
    edit.originalData = {};
    edit.newFile = null;
    edit.newFileName = '';
    edit.fileList = [];
  };

  // 编辑时选择文件
  const beforeEditFilePick = async (file: File) => {
    console.log('选择新文件:', file.name);
    edit.newFile = file;
    edit.newFileName = file.name;
    edit.fileList = [{
      uid: '-1',
      name: file.name,
      status: 'done',
    }];
    return false; // 阻止自动上传
  };

  // 确认编辑
  const confirmEdit = async () => {
    if (!edit.form.display_name?.trim()) {
      message.warning('请输入插件名称');
      return;
    }

    try {
      edit.loading = true;

      // 使用 FormData 支持文件上传
      const formData = new FormData();

      // 添加基本信息
      formData.append('original_name', edit.form.name);
      formData.append('display_name', edit.form.display_name.trim());
      formData.append('description', edit.form.description?.trim() || '');

      // 如果有选择新文件，则添加文件
      if (edit.newFile) {
        formData.append('file', edit.newFile);
        console.log('包含新文件:', edit.newFileName);
      }

      console.log('提交更新数据:', {
        original_name: edit.form.name,
        display_name: edit.form.display_name.trim(),
        description: edit.form.description?.trim() || '',
        hasNewFile: !!edit.newFile,
        newFileName: edit.newFileName
      });

      // 调用更新接口
      const response = await updateExeApi(formData);
      console.log('更新接口响应:', response);

      message.success('插件信息更新成功');

      // 关闭弹窗并刷新列表
      closeEditModal();

      // 延迟一下再刷新，确保后端处理完成
      setTimeout(() => {
        reloadList();
      }, 500);

    } catch (e: any) {
      console.error('更新失败:', e);
      message.error(e?.message || e?.msg || '更新失败');
    } finally {
      edit.loading = false;
    }
  };

  const beforeExePick = async (file: File) => {
    upload.file = file;
    upload.fileName = file.name;
    selectedFile.value = file;
    return false;
  };

  // 页面数据
  const data = reactive({
    list: [] as any[],
    loading: false,
  });

  onMounted(() => {
    reloadList();
  });

  // 刷新列表
  const reloadList = async () => {
    console.log('开始刷新列表...');
    data.loading = true;
    try {
      const res: any = await listExeApi();
      console.log('列表API响应:', res);

      if (res && res.code === 0) {
        data.list = res.data || [];
        console.log('更新后的插件列表:', data.list);
      } else {
        console.error('列表API返回错误:', res);
        message.error(res?.msg || '获取列表失败');
      }
    } catch (e: any) {
      console.error('获取列表失败:', e);
      message.error('获取列表失败');
    } finally {
      data.loading = false;
    }
  };

  // 确认上传
  const confirmUpload = async () => {
    if (!upload.file) {
      message.warning('请先选择文件');
      return;
    }

    try {
      const fd = new FormData();
      fd.append('file', upload.file);
      if (upload.form.description) fd.append('description', upload.form.description);
      if (upload.form.display_name) fd.append('display_name', upload.form.display_name);

      await uploadExeApi(fd);
      message.success('上传成功');
      closeUploadModal();
      reloadList();
    } catch (e: any) {
      console.error('上传失败:', e);
      message.error(e?.message || e?.msg || '上传失败');
    }
  };
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