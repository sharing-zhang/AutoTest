<template>
  <div>
    <!-- 使用脚本管理布局组件 -->
    <ScriptManagerLayout page-route="/scanDevUpdate" ref="scriptManager">
      
      <el-tabs v-model="activeName" class="el-tabs__content">
        <el-tab-pane label="扫描结果" name="scanResult">
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
            @refresh-data="handleRefreshData"
            @page-change="(current) => data.page = current"
          />
        </el-tab-pane>
        <el-tab-pane label="数据备份" name="dataBackup">
          <DataBackupTable
            :loading="data.loading"
            :data-source="data.dataBackup_dataList"
            :columns="dataBackupcolumns"
            :current="data.page"
            :page-size="data.pageSize"
            @page-change="(current) => data.page = current"
          />
        </el-tab-pane>
        <el-tab-pane label="操作" name="configuration">
          功能操作区域
          <!-- 补充功能操作区域 -->
        </el-tab-pane>
      </el-tabs>

      <!--弹窗区域-->
      <div>
        <EditRecordModal
          v-model:visible="modal.scanResult_visile"
          :title="modal.title"
          :form-data="modal.form"
          @ok="handleEditOk"
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
  import { message } from 'ant-design-vue';
  import { createApi, listApi, updateApi, deleteApi } from '/@/api/scanDevUpdate';
  import ScriptManagerLayout from '/@/components/ScriptManagerLayout.vue';
  import ScanResultModal from '/@/components/ScanResultModal.vue';
  import ScanResultTable from '/@/components/ScanResultTable.vue';
  import DataBackupTable from '/@/components/DataBackupTable.vue';
  import EditRecordModal from '/@/components/EditRecordModal.vue';
  import dayjs from 'dayjs';
  import { ref, reactive, onMounted, h } from 'vue';

  // 进来页面后默认定位到扫描结果页面
  const activeName = ref('scanResult');

// 扫描结果表格列配置
const scanResultcolumns = reactive([

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
      if (summary.length > 10) {
        return summary.substring(0, 20) + '...';
      }
      return summary;
    }
  },
  // {
  //   title: '备注',
  //   dataIndex: 'remark',
  //   align: "center",
  //   key: 'remark',
  //   width: 250
  // },
  // {
  //   title: '结果类型',
  //   dataIndex: 'result_type',
  //   align: "center",
  //   key: 'result_type',
  //   width: 100,
  //   customRender: ({ text }) => {
  //     const typeMap = {
  //       'manual': '手动扫描',
  //       'script': '脚本执行',
  //       'task': '任务执行'
  //     };
  //     return typeMap[text] || text || '手动扫描';
  //   }
  // },
  // {
  //   title: '脚本名称',
  //   dataIndex: 'script_name',
  //   align: "center",
  //   key: 'script_name',
  //   width: 120
  // },
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
      align: 'center',
      width: 100,
    },
    {
      title: '数据备份结果文件',
      dataIndex: 'scanDevResult',
      align: 'center',
      key: 'scanDevResult',
      width: 800,
    },
    {
      title: '时间',
      dataIndex: 'scanDevTime',
      align: 'center',
      key: 'scanDevTime',
      width: 200,
    },
    {
      title: '负责人',
      dataIndex: 'director',
      align: 'center',
      key: 'director',
      width: 100,
    },
    {
      title: '备注',
      dataIndex: 'remark',
      align: 'center',
      key: 'remark',
      width: 260,
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

  // 提交状态
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
      console.log('scanDevUpdate页面刷新回调已注册');
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
  };

  // 搜索功能
  const onSearchChange = (e: Event) => {
    data.keyword = (e?.target as HTMLInputElement)?.value || '';
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

  // 重置表单数据
  const resetFormData = (form: any) => {
    for (const key in form) {
      form[key] = undefined;
    }
  };

  // 填充表单数据
  const fillFormData = (form: any, record: any) => {
    for (const key in record) {
      if (record[key]) {
        form[key] = record[key];
      }
    }
  };

  const handleEdit = (record: any) => {
    modal.scanResult_visile = true;
    modal.scanResult_editFlag = true;
    modal.title = '编辑资源扫描结果文件信息';
    resetFormData(modal.form);
    fillFormData(modal.form, record);
  };

  const handleEditOk = (formData: any) => {
    const submitData = new FormData();
    submitData.append('id', formData.id);
    submitData.append('scandevresult_filename', formData.scandevresult_filename);
    submitData.append('scandevresult_time', formData.scandevresult_time);
    submitData.append('director', formData.director);
    submitData.append('remark', formData.remark);
    submitData.append('status', formData.status);
    
    if (modal.scanResult_editFlag) {
      submitting.value = true;
      updateApi(
        {
          id: formData.id,
        },
        submitData,
      )
        .then((res) => {
          submitting.value = false;
          handleCancel();
          getDataList();
          message.success('项目信息更新成功');
        })
        .catch((err) => {
          submitting.value = false;
          console.log(err);
          message.error(err.msg || '项目信息更新失败');
        });
    } else {
      submitting.value = true;
      createApi(submitData)
        .then((res) => {
          submitting.value = false;
          handleCancel();
          getDataList();
        })
        .catch((err) => {
          submitting.value = false;
          console.log(err);
          message.error(err.msg || '操作失败');
        });
    }
  };

  // 关闭编辑弹窗
  const handleCancel = () => {
    modal.scanResult_visile = false;
  };

  // 关闭查看详情弹窗
  const dataBackup_handleCancel = () => {
    scanResultContentDetail.scanResultContentDetail_visile = false;
  };

  // 查看详情点击响应
  const handleClick = (record: any) => {
    scanResultContentDetail.scanResultContentDetail_visile = true;
    scanResultContentDetail.scanResultContentDetail_editFlag = true;
    console.log(record);
    resetFormData(scanResultContentDetail.form);
    fillFormData(scanResultContentDetail.form, record);
    console.log(scanResultContentDetail.form['scandevresult_content']);
  };



  // 重跑脚本功能
  // 刷新数据函数 - 供ScanResultTable组件调用
  const handleRefreshData = () => {
    console.log('收到刷新数据请求，开始刷新扫描结果...');
    getDataList();
  };



  const bodystyle = {
    height: '680px',
    overflowY: 'scroll',
    overflowX: 'auto',
    width: '1600px',
  };

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
    content: '';
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

  ::v-deep .ant-modal-body {
    padding: 18px !important;
  }
</style>
