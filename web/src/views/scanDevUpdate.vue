<template>
  <div>
    <!-- 国内资源扫描项目-进入项目后实际展示内容 -->
    <div class="page-view">
      <el-tabs
      v-model="activeName"
      class="el-tabs__content"
      >
        <el-tab-pane label="扫描结果" name="scanResult" >
          <a-table
          size="middle"
          rowKey="scanResult_id"
          :loading="data.loading"
          :columns="scanResultcolumns"
          :data-source="data.scanResult_dataList"
          :scroll="{ x: 'max-content' }"
          :pagination="{
            size: 'small',
            current: data.page,
            pageSize: data.pageSize,
            onChange: (current) => (data.page = current),
            showSizeChanger: false,
            showTotal: (total) => `共${total}条数据`,
          }">
            <template #bodyCell="{ text, record, index, column }">
              <template v-if="column.key === 'operation'">
                <span>
                  <a @click="handleEdit(record)">编辑</a>
                  <a-divider type="vertical" />
                  <a @click="handleClick(record)">查看详情</a>
                </span>
              </template>
            </template>
          </a-table>
        </el-tab-pane>
        <el-tab-pane label="数据备份" name="dataBackup" >
          <a-table
          size="middle"
          rowKey="scanResult_id"
          :loading="data.loading"
          :columns="dataBackupcolumns"
          :data-source="data.dataBackup_dataList"
          :scroll="{ x: 'max-content' }"
          :pagination="{
            size: 'small',
            current: data.page,
            pageSize: data.pageSize,
            onChange: (current) => (data.page = current),
            showSizeChanger: false,
            showTotal: (total) => `共${total}条数据`,
          }">
          </a-table>
        </el-tab-pane>
        <el-tab-pane label="操作" name="configuration" >
          功能操作区域 <!-- 补充功能操作区域 -->
        </el-tab-pane>
      </el-tabs>
    </div>

    <!--弹窗区域-->
    <div>
      <!--
         1. <a-modal:创建模态对话框，在不离开当前页面下，创建的一个基于页面图层上的对话框
         2. visible：设置是否可见
         3. title:标题
      -->
      <a-modal
        :visible="modal.scanResult_visile"
        :forceRender="true"
        :title="modal.title"
        ok-text="确认"
        cancel-text="取消"
        @ok="handleOk"
        @cancel="handleCancel"
      >
        <div>
          <!--
            1. a-form: 用于创建表单的组件，提供了一种结构化的方式来收集用户输入;ref‌：用于获取表单实例的引用，方便后续操作‌
            2. label-col‌和‌wrapper-col‌：分别用于设置标签列和包裹列的栅格数
            3. model‌：用于指定表单的绑定数据对象。表单项的值会自动与这个对象进行双向绑定
            4. rules‌：定义表单验证规则，确保用户输入的数据符合预期格式和要求‌
            5. gutter：调整列与列之间的间距
          -->
          <a-form ref="myform" :label-col="{ style: { width: '120px'} }" :model="modal.form" :rules="modal.rules">
            <a-row :gutter="24">
              <a-col span="24">
                <a-form-item label="文件名" name="scandevresult_filename">
                  <a-input placeholder="请输入文件名" v-model:value="modal.form.scandevresult_filename" allowClear />
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="时间" name="scandevresult_time">
                  <a-input placeholder="时间" v-model:value="modal.form.scandevresult_time" allowClear />
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="负责人" name="director">
                  <a-input placeholder="请输入负责人" v-model:value="modal.form.director" allowClear />
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="备注" name="remark">
                  <a-input placeholder="请输入备注" v-model:value="modal.form.remark" allowClear />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </div>
      </a-modal>
      <a-modal
        width="1600px"
        :destroyOnClose="true"
        :body-style="bodystyle"
        :visible="scanResultContentDetail.scanResultContentDetail_visile"
        :forceRender="true"
        :title="scanResultContentDetail.title"
        @cancel="dataBackup_handleCancel"
        cancelText="取消"
      >
        <!-- style="white-space: pre-wrap" 解决div默认不识别换行符的情况 -->
        <div style="white-space: pre-wrap">
          {{ scanResultContentDetail.form['scandevresult_content'] }}
        </div>
        <template #footer="footer">
          <a-button @click="dataBackup_handleCancel">关闭</a-button>
        </template>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message, SelectProps } from 'ant-design-vue';
import { createApi, listApi, updateApi, deleteApi } from '/@/api/scanDevUpdate';
import {BASE_URL} from "/@/store/constants";
import { FileImageOutlined, VideoCameraOutlined } from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import {useRouter} from "vue-router";

import { ref } from 'vue'
import type { TabsPaneContext } from 'element-plus'



// 进来页面后默认定位到扫描结果页面
const activeName = ref('scanResult')


// 扫描结果模块下顶部栏标题
const scanResultcolumns = reactive([

  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    align: "center",
    width: 100
  },
  {
    title: '资源扫描结果文件名',
    dataIndex: 'scandevresult_filename',
    align: "center",
    key: 'scandevresult_filename',
    width: 600
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
    width: 310
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

// 数据备份模块下顶部栏标题
const dataBackupcolumns = reactive([

  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    align: "center",
    width: 100
  },
  {
    title: '数据备份结果文件',
    dataIndex: 'scanDevResult',
    align: "center",
    key: 'scanDevResult',
    width: 800
  },
  {
    title: '时间',
    dataIndex: 'scanDevTime',
    align: "center",
    key: 'scanDevTime',
    width: 200
  },
  {
    title: '负责人',
    dataIndex: 'director',
    align: "center",
    key: 'director',
    width: 100
  },
  {
    title: '备注',
    dataIndex: 'remark',
    align: "center",
    key: 'remark',
    width: 260
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

// 文件列表
const fileList = ref<any[]>([]);

const submitting = ref<boolean>(false);

// 页面数据:一些页面参数比如是否加载、分页参数等通过这里定义，直接调用
// selectedRowKeys: 用于用户勾选内容时，每个勾选内容都会被存在这个数组中
const data = reactive({
  scanResult_dataList: [],
  dataBackup_dataList: [],
  loading: false,
  keyword: '',
  selectedRowKeys: [] as any[],
  pageSize: 10,
  page: 1,
});

// 【编辑】弹窗数据源:编辑信息弹窗
const modal = reactive({
  scanResult_visile: false,
  scanResult_editFlag: false,
  title: '',
  form: {
    id: undefined,
    scandevresult_filename: undefined,
    scandevresult_time: undefined,
    director: undefined,
    remark: undefined,
    status: undefined,
    scandevresult_content: undefined,
  },
  rules: {
    scandevresult_filename: [{ required: true, message: '请输入文件名', trigger: 'change' }],
    scandevresult_time: [{ required: true, message: '请输入时间', trigger: 'change' }],
    director: [{ required: true, message: '请输入负责人', trigger: 'change' }],
    remark: [{ required: false, trigger: 'change' }],
  },
});

// 【查看详情】弹窗，此弹窗只用支持查看即可
const scanResultContentDetail = reactive({
  scanResultContentDetail_visile: false,
  scanResultContentDetail_editFlag: false,
  title: '资源扫描结果',
  form: {
    id: undefined,
    scandevresult_content: undefined,
  },
  rules: {},
});


//获取表单实例后，可以调用其方法进行操作
const myform = ref<FormInstance>();

//onMounted:用于在组件挂载到 DOM 后执行逻辑,当组件挂载时，onMounted 中的代码会执行，初始化要执行的内容
onMounted(() => {
  getDataList();
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
          // 将mysql中"2025-06-13T18:32:49"时间格式去掉中间的T
          item.scandevresult_time = dayjs(item.scandevresult_time).format('YYYY-MM-DD HH:mm:ss');
          item.index = index + 1;
        });
        data.scanResult_dataList = res.data;
        console.log(data.scanResult_dataList);
      })
      .catch((err) => {
        data.loading = false;
        console.log(err);
      });
}

//搜索功能
const onSearchChange = (e: Event) => {
  data.keyword = e?.target?.value;
  console.log(data.keyword);
};

const onSearch = () => {
  getDataList();
};

const handleEdit = (record: any) => {
  resetModal();
  modal.scanResult_visile = true;
  modal.scanResult_editFlag = true;
  modal.title = '编辑资源扫描结果文件信息';
  // 重置
  for (const key in modal.form) {
    modal.form[key] = undefined;
  }
  for (const key in record) {
    if(record[key]) {
      modal.form[key] = record[key];
    }
  }
};

const handleOk = () => {
  myform.value
      ?.validate()
      .then(() => {
        const formData = new FormData();
        formData.append('id', modal.form.id)
        formData.append('scandevresult_filename', modal.form.scandevresult_filename)
        formData.append('scandevresult_time', modal.form.scandevresult_time)
        formData.append('director', modal.form.director)
        formData.append('remark', modal.form.remark)
        formData.append('status', modal.form.status)
        if (modal.scanResult_editFlag) {
          submitting.value = true
          updateApi({
            id: modal.form.id
          },formData)
              .then((res) => {
                submitting.value = false
                handleCancel();
                getDataList();
                message.success('项目信息更新成功')
              })
              .catch((err) => {
                submitting.value = false
                console.log(err);
                message.error(err.msg || '项目信息更新失败');
              });
        } else {
          submitting.value = true
          createApi(formData)
              .then((res) => {
                submitting.value = false
                handleCancel();
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

// 关闭【编辑】弹窗
const handleCancel = () => {
  modal.scanResult_visile = false;
};

// 关闭【查看详情】弹窗
const dataBackup_handleCancel = () => {
  scanResultContentDetail.scanResultContentDetail_visile = false;
};


// 恢复表单初始状态
const resetModal = () => {
  myform.value?.resetFields();
  fileList.value = []
};


// 【查看详情】点击响应
const handleClick = (record: any) => {
  resetModal();
  scanResultContentDetail.scanResultContentDetail_visile = true;
  scanResultContentDetail.scanResultContentDetail_editFlag = true;
  console.log(record )
  // 重置
  for (const key in scanResultContentDetail.form) {
    scanResultContentDetail.form[key] = undefined;
  }
  for (const key in record) {
    if(record[key]) {
      scanResultContentDetail.form[key] = record[key];
    }
  }
  console.log(scanResultContentDetail.form['scandevresult_content'] )
}

const bodystyle = {
  height: '680px',
  overflowY: 'scroll',
  overflowX:'auto',
  width: '1600px',
}


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

.el-tabs__content {
  color: #6b778c;
  font-size: 32px;
  font-weight: 600;

}


::v-deep .el-tabs__item {
  width: 90px !important;
  justify-content: center !important;
  padding: 0;

}

::v-deep .el-tabs__item::after {
  content: "";
  position: absolute;
  align-items: center;
  right: 0;
  height: 35%;
  width: 1px; /* 分割线宽度 */
  background-color: #e4e7ed; /* 分割线颜色 */
  transform: translateX(100%); /* 调整位置使其在标签右侧 */
}

::v-deep .el-tabs__active-bar {
  width: 90px !important;

}

::v-deep .ant-table {
  color: rgb(34 33 33 / 85%);
  font-family: Helvetica, sans-serif;
  font-weight: 520;
}

::v-deep  .ant-modal-body {
  padding: 18px !important;
}


</style>
