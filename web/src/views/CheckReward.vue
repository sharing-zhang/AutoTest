<template>
  <div>
    <!-- 使用脚本管理布局组件 -->
    <ScriptManagerLayout 
      page-route="/CheckReward"
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
            :show-rerun="true"
            :show-edit="false"
            :use-builtin-rerun="true"
            @send="handleSend"
            @view-detail="handleClick"
            @refresh-data="getDataList"
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
          功能操作区域 <!-- 补充功能操作区域 -->
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
import { createApi, listApi, updateApi, deleteApi } from '/@/api/scanDevUpdate';
import ScriptManagerLayout from '/@/components/ScriptManagerLayout.vue';
import ScanResultModal from '/@/components/ScanResultModal.vue';
import ScanResultTable from '/@/components/ScanResultTable.vue';
import EditRecordModal from '/@/components/EditRecordModal.vue';
import DataBackupTable from '/@/components/DataBackupTable.vue';
import { SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import { ref, reactive, onMounted, h } from 'vue';

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
    title: '脚本名称',
    dataIndex: 'scandevresult_filename',
    align: "center",
    key: 'scandevresult_filename',
    width: 300
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
    width: 120,
    customRender: ({ record }) => {
      const statusMap = {
        'SUCCESS': { text: '成功', type: 'success' },
        'FAILURE': { text: '失败', type: 'error' },
        'RUNNING': { text: '运行中', type: 'processing' },
        'PENDING': { text: '等待中', type: 'default' },
        'TIMEOUT': { text: '超时', type: 'warning' },
        'CANCELLED': { text: '已取消', type: 'default' }
      };
      const status = statusMap[record.execution_status] || { text: '未知', type: 'default' };
      return h('a-tag', { color: status.type }, status.text);
    }
  },
  {
    title: '结果摘要',
    dataIndex: 'result_summary',
    align: "center",
    key: 'result_summary',
    width: 120,
    ellipsis: true,
    customRender: ({ record }) => {
      const summary = record.result_summary || '-';
      if (summary.length > 20) {
        return summary.substring(0, 20) + '...';
      }
      return summary;
    }
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
  
  // 延迟注册脚本执行完成后的数据刷新回调，确保组件已完全挂载
  setTimeout(() => {
    if (scriptManager.value) {
      scriptManager.value.onDataRefresh(() => {
        console.log('脚本执行完成，刷新扫描结果数据...')
        getDataList();
      });
      console.log('CheckReward页面刷新回调已注册');
    } else {
      console.error('scriptManager组件引用未找到');
    }
  }, 100);
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

// 搜索功能
const onSearchChange = (e: Event) => {
  data.keyword = (e.target as HTMLInputElement)?.value;
  console.log(data.keyword);
};

const onSearch = () => {
  getDataList();
};

const handleSend = (record: any) => {
  // 调用 ScriptManagerLayout 的钉钉机器人弹窗方法
  if (scriptManager.value) {
    scriptManager.value.openDingtalkDialog(record);
  }
};

const handleEdit = (record: any) => {
  resetModal();
  modal.scanResult_visile = true;
  modal.scanResult_editFlag = true;
  modal.title = '编辑CheckReward信息';
  for (const key in modal.form) {
    modal.form[key] = undefined;
  }
  for (const key in record) {
    if(record[key]) {
      modal.form[key] = record[key];
    }
  }
};

const handleOk = (formData: any) => {
  if (modal.scanResult_editFlag) {
    submitting.value = true
    updateApi({
      id: modal.form.id
    }, formData)
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
        message.success('操作成功')
      })
      .catch((err) => {
        submitting.value = false
        console.log(err);
        message.error(err.msg || '操作失败');
      });
  }
}

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
  console.log(scanResultContentDetail.form.scandevresult_content )
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


</style>
