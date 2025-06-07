<template>
  <div>
    <!--页面区域-->
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message, SelectProps } from 'ant-design-vue';
import { createApi, listApi, updateApi, deleteApi } from '/@/api/thing';
import {listApi as listClassificationApi} from '/@/api/classification'
import {listApi as listTagApi} from '/@/api/tag'
import {BASE_URL} from "/@/store/constants";
import { FileImageOutlined, VideoCameraOutlined } from '@ant-design/icons-vue';

const columns = reactive([

  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    width: 60
  },
  {
    title: '学号',
    dataIndex: 'xuehao',
    key: 'xuehao'
  },
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '性别',
    dataIndex: 'sex',
    key: 'sex'
  },
  {
    title: '出生日期',
    dataIndex: 'birthday',
    key: 'birthday'
  },
  {
    title: '身份证号',
    dataIndex: 'sfz',
    key: 'sfz'
  },
  {
    title: '民族',
    dataIndex: 'minzu',
    key: 'minzu'
  },
  {
    title: '班级',
    dataIndex: 'classification_title',
    key: 'classification_title'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    customRender: ({ text, record, index, column }) => text === '0' ? '在读' : '毕业'
  },
  {
    title: '备注',
    dataIndex: 'remark',
    key: 'remark'
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'operation',
    align: 'center',
    fixed: 'right',
    width: 140,
  },
]);

const beforeUpload = (file: File) => {
  // 改封面文件名
  const fileName = new Date().getTime().toString() + '.' + file.type.substring(6);
  const copyFile = new File([file], fileName);
  console.log(copyFile);
  modal.form.imageFile = copyFile;
  return false;
};

// 文件列表
const fileList = ref<any[]>([]);

const submitting = ref<boolean>(false);

// 页面数据
const data = reactive({
  dataList: [],
  loading: false,
  keyword: '',
  selectedRowKeys: [] as any[],
  pageSize: 10,
  page: 1,
});

// 弹窗数据源
const modal = reactive({
  visile: false,
  editFlag: false,
  title: '',
  cData: [],
  tagData: [{}],
  form: {
    id: undefined,
    name: undefined,
    classification: undefined,
    xuehao: undefined,
    sfz: undefined,
    minzu: undefined,
    tag: [],
    sex: undefined,
    birthday: undefined,
    remark: undefined,
    status: undefined,
    cover: undefined,
    coverUrl: undefined,
    imageFile: undefined
  },
  rules: {
    xuehao: [{ required: true, message: '请输入学号', trigger: 'change' }],
    sfz: [{ required: true, message: '请输入身份证', trigger: 'change' }],
    name: [{ required: true, message: '请输入姓名', trigger: 'change' }],
    classification: [{ required: true, message: '请选择班级', trigger: 'change' }],
    sex: [{ required: true, message: '请输入性别', trigger: 'change' }],
    status: [{ required: true, message: '请选择状态', trigger: 'change' }]
  },
});

const myform = ref<FormInstance>();

onMounted(() => {
  getDataList();
  getCDataList();
  getTagDataList();
});

const getDataList = () => {
  data.loading = true;
  listApi({
    keyword: data.keyword,
  })
      .then((res) => {
        data.loading = false;
        console.log(res);
        res.data.forEach((item: any, index: any) => {
          item.index = index + 1;
        });
        data.dataList = res.data;
      })
      .catch((err) => {
        data.loading = false;
        console.log(err);
      });
}

const getCDataList = () => {
  listClassificationApi({}).then(res => {
    modal.cData = res.data
  })
}
const getTagDataList = ()=> {
  listTagApi({}).then(res => {
    res.data.forEach((item, index) => {
      item.index = index + 1
    })
    modal.tagData = res.data
  })
}

const onSearchChange = (e: Event) => {
  data.keyword = e?.target?.value;
  console.log(data.keyword);
};

const onSearch = () => {
  getDataList();
};

const rowSelection = ref({
  onChange: (selectedRowKeys: (string | number)[], selectedRows: DataItem[]) => {
    console.log(`selectedRowKeys: ${selectedRowKeys}`, 'selectedRows: ', selectedRows);
    data.selectedRowKeys = selectedRowKeys;
  },
});

const handleAdd = () => {
  resetModal();
  modal.visile = true;
  modal.editFlag = false;
  modal.title = '新增';
  // 重置
  for (const key in modal.form) {
    modal.form[key] = undefined;
  }
  modal.form.cover = undefined
};
const handleEdit = (record: any) => {
  resetModal();
  modal.visile = true;
  modal.editFlag = true;
  modal.title = '编辑';
  // 重置
  for (const key in modal.form) {
    modal.form[key] = undefined;
  }
  for (const key in record) {
    if(record[key]) {
      modal.form[key] = record[key];
    }
  }
  if(modal.form.cover) {
    modal.form.coverUrl = BASE_URL + modal.form.cover
    modal.form.cover = undefined
  }
};

const confirmDelete = (record: any) => {
  console.log('delete', record);
  deleteApi({ ids: record.id })
      .then((res) => {
        getDataList();
      })
      .catch((err) => {
        message.error(err.msg || '操作失败');
      });
};

const handleBatchDelete = () => {
  console.log(data.selectedRowKeys);
  if (data.selectedRowKeys.length <= 0) {
    console.log('hello');
    message.warn('请勾选删除项');
    return;
  }
  deleteApi({ ids: data.selectedRowKeys.join(',') })
      .then((res) => {
        message.success('删除成功');
        data.selectedRowKeys = [];
        getDataList();
      })
      .catch((err) => {
        message.error(err.msg || '操作失败');
      });
};

const handleOk = () => {
  myform.value
      ?.validate()
      .then(() => {
        const formData = new FormData();
        if(modal.editFlag) {
          formData.append('id', modal.form.id)
        }
        formData.append('xuehao', modal.form.xuehao || '')
        formData.append('name', modal.form.name || '')
        formData.append('sex', modal.form.sex || '')
        formData.append('birthday', modal.form.birthday || '')
        formData.append('minzu', modal.form.minzu || '')
        formData.append('sfz', modal.form.sfz || '')
        formData.append('remark', modal.form.remark || '')
        if (modal.form.classification) {
          formData.append('classification', modal.form.classification)
        }
        if (modal.form.imageFile) {
          formData.append('cover', modal.form.imageFile)
        }
        if (modal.form.status) {
          formData.append('status', modal.form.status)
        }
        if (modal.editFlag) {
          submitting.value = true
          updateApi({
            id: modal.form.id
          },formData)
              .then((res) => {
                submitting.value = false
                hideModal();
                getDataList();
              })
              .catch((err) => {
                submitting.value = false
                console.log(err);
                message.error(err.msg || '操作失败');
              });
        } else {
          submitting.value = true
          createApi(formData)
              .then((res) => {
                submitting.value = false
                hideModal();
                getDataList();
              })
              .catch((err) => {
                submitting.value = false
                console.log(err);
                message.error(err.msg || '操作失败');
              });
        }
      })
      .catch((err) => {
        console.log('不能为空');
      });
};

const handleCancel = () => {
  hideModal();
};

// 恢复表单初始状态
const resetModal = () => {
  myform.value?.resetFields();
  fileList.value = []
};

// 关闭弹窗
const hideModal = () => {
  modal.visile = false;
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
