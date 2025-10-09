<template>
  <div>
    <!-- 使用脚本管理布局组件 -->
    <ScriptManagerLayout 
      page-route="/thing"
      ref="scriptManager"
    >
      <el-tabs
      v-model="activeName"
      class="el-tabs__content"
      >
        <el-tab-pane label="扫描结果" name="scanResult" >
          <ScanResultTable
            :loading="data.loading"
            :data-source="data.scanResult_dataList"
            :columns="scanResultcolumns"
            :current="data.page"
            :page-size="data.pageSize"
            :show-rerun="false"
            :show-edit="true"
            :show-delete="true"
            @send="handleSend"
            @view-detail="handleClick"
            @edit="handleEdit"
            @delete="handleDelete"
            @page-change="(current) => data.page = current"
          />
        </el-tab-pane>
        <el-tab-pane label="数据备份" name="dataBackup" >
          <DataBackupTable
            :loading="data.loading"
            :data-source="data.dataBackup_dataList"
            :current="data.page"
            :page-size="data.pageSize"
            @page-change="(current) => data.page = current"
          />
        </el-tab-pane>
        <el-tab-pane label="操作" name="configuration" >
          <!-- 脚本执行说明 -->
          <div class="operation-section">
            <el-card shadow="never">
              <template #header>
                <div class="card-header">
                  <span>脚本执行</span>
                  <el-text type="info" size="small">点击页面右上角的脚本按钮执行自动化处理</el-text>
                </div>
              </template>
              
              <el-empty description="点击页面右上角的脚本按钮开始执行自动化任务">
                <template #image>
                  <el-icon size="60" color="#909399">
                    <Document />
                  </el-icon>
                </template>
                
                <div class="operation-tips">
                  <h4>使用说明：</h4>
                  <ol>
                    <li>在页面右上角找到脚本执行按钮</li>
                    <li>点击按钮后，如果脚本需要参数会自动弹出参数配置界面</li>
                    <li>填写必要的参数后点击执行</li>
                    <li>执行完成后结果会自动显示在"扫描结果"标签页中</li>
                  </ol>
                </div>
              </el-empty>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!--弹窗区域-->
      <div>
        <EditRecordModal
          v-model:visible="modal.scanResult_visile"
          :title="modal.title"
          :form-data="modal.form"
          @ok="handleOk"
          @cancel="handleCancel"
        />
      <!-- 使用通用扫描结果弹窗组件 -->
      <ScanResultModal
        v-model:visible="scanResultContentDetail.scanResultContentDetail_visile"
        :resultData="scanResultContentDetail.form"
        @cancel="dataBackup_handleCancel"
      />
      </div>
    </ScriptManagerLayout>
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message } from 'ant-design-vue';
import { createApi, listApi, updateApi, deleteApi } from '/@/api/thing';
import ScriptManagerLayout from '/@/components/ScriptManagerLayout.vue';
import ScanResultModal from '/@/components/ScanResultModal.vue';
import EditRecordModal from '/@/components/EditRecordModal.vue';
import DataBackupTable from '/@/components/DataBackupTable.vue';
import { SuccessFilled, CircleCloseFilled, Document } from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import { ref, reactive, onMounted } from 'vue'

// 进来页面后默认定位到扫描结果页面
const activeName = ref('scanResult')


// 扫描结果表格列配置
const scanResultcolumns = reactive([

  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    align: "center",
    width: 100
  },
  {
    title: '资源扫描结果',
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
    width: 250
  },
  {
    title: '结果类型',
    dataIndex: 'result_type',
    align: "center",
    key: 'result_type',
    width: 100,
    customRender: ({ text }) => {
      const typeMap = {
        'manual': '手动扫描',
        'script': '脚本执行', 
        'task': '任务执行'
      };
      return typeMap[text] || text || '手动扫描';
    }
  },
  {
    title: '脚本名称',
    dataIndex: 'script_name',
    align: "center",
    key: 'script_name',
    width: 120
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

// 数据备份表格列配置
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

// 文件列表和提交状态
const fileList = ref<any[]>([]);
const submitting = ref<boolean>(false);

// 页面数据状态
const data = reactive({
  scanResult_dataList: [],
  dataBackup_dataList: [],
  loading: false,
  keyword: '',
  selectedRowKeys: [] as any[],
  pageSize: 10,
  page: 1,
});



// 编辑弹窗数据
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

// 查看详情弹窗数据
const scanResultContentDetail = reactive({
  scanResultContentDetail_visile: false,
  scanResultContentDetail_editFlag: false,
  form: {
    id: undefined,
    scandevresult_content: undefined,
  },
  rules: {},
});


// 表单实例引用
const myform = ref<FormInstance>();

// 组件引用
const scriptManager = ref();

onMounted(() => {
  getDataList();
});

const getDataList = () => {
  data.loading = true;
  console.log('正在调用API获取数据...');
  listApi({
    keyword: data.keyword,
  })
      .then((res) => {
        data.loading = false;
        console.log('API响应:', res);
        console.log('返回的数据条数:', res.data ? res.data.length : 0);
        res.data.forEach((item: any, index: any) => {
          item.scandevresult_time = dayjs(item.scandevresult_time).format('YYYY-MM-DD HH:mm:ss');
          item.index = index + 1;
        });
        data.scanResult_dataList = res.data;
        console.log('处理后的数据:', data.scanResult_dataList);
      })
      .catch((err) => {
        data.loading = false;
        console.log('API调用错误:', err);
      });
}

// 搜索功能
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

// 关闭编辑弹窗
const handleCancel = () => {
  modal.scanResult_visile = false;
};

// 关闭查看详情弹窗
const dataBackup_handleCancel = () => {
  scanResultContentDetail.scanResultContentDetail_visile = false;
};


// 恢复表单初始状态
const resetModal = () => {
  myform.value?.resetFields();
  fileList.value = []
};


// 查看详情点击响应
const handleClick = (record: any) => {
  resetModal();
  scanResultContentDetail.scanResultContentDetail_visile = true;
  scanResultContentDetail.scanResultContentDetail_editFlag = true;
  console.log(record )
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

// 删除记录
const handleDelete = (record: any) => {
  deleteApi({
    ids: record.id
  })
    .then((res) => {
      message.success('删除成功');
      getDataList(); // 刷新数据列表
    })
    .catch((err) => {
      console.log(err);
      message.error(err.msg || '删除失败');
    });
};


const bodystyle = {
  height: '680px',
  overflowY: 'scroll',
  overflowX:'auto',
  width: '1600px',
}

// 脚本执行成功后的回调处理
// 注册数据刷新回调
onMounted(() => {
  // 当ScriptManagerLayout组件可用时注册回调
  scriptManager.value?.onDataRefresh(() => {
    getDataList(); // 刷新扫描结果数据
    activeName.value = 'scanResult'; // 切换到扫描结果标签页
  });
});


</script>

<style scoped lang="less">
.page-view {
  min-height: 100%;
  background: #fff;
  padding: 24px;
  display: flex;
  flex-direction: column;
  position: relative; /* 为绝对定位的按钮提供定位上下文 */
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

// 操作区域样式
.operation-section {
  padding: 16px;
  
  .card-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    span:first-child {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

// 确保标签页内容区域有合适的内边距
:deep(.el-tab-pane) {
  min-height: 400px;
}

// 操作说明样式
.operation-tips {
  text-align: left;
  max-width: 400px;
  margin: 20px auto 0;
  
  h4 {
    color: #303133;
    margin-bottom: 12px;
  }
  
  ol {
    padding-left: 20px;
    
    li {
      margin-bottom: 8px;
      color: #606266;
      line-height: 1.6;
    }
  }
}


</style>
