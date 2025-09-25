<template>
  <div>
    <!-- 使用脚本管理布局组件 -->
    <ScriptManagerLayout 
      page-route="/CheckText"
      ref="scriptManager"
    >
      <el-tabs
      v-model="activeName"
      class="el-tabs__content"
      >
        <el-tab-pane label="扫描结果" name="mainContent" >
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

      <!--弹窗区域-->
      <div>
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
        <!-- 根据结果类型显示不同的内容 -->
        <div v-if="scanResultContentDetail.form['result_type'] === 'script' || scanResultContentDetail.form['result_type'] === 'task'">
          <!-- 脚本执行结果显示 -->
          <el-descriptions title="脚本执行信息" :column="2" border>
            <el-descriptions-item label="脚本名称">
              { scanResultContentDetail.form['script_name'] || '未知' }
            </el-descriptions-item>
            <el-descriptions-item label="任务ID">
              { scanResultContentDetail.form['task_id'] || '无' }
            </el-descriptions-item>
            <el-descriptions-item label="执行时间">
              { scanResultContentDetail.form['scandevresult_time'] }
            </el-descriptions-item>
            <el-descriptions-item label="执行耗时">
              { scanResultContentDetail.form['execution_time'] ? `${scanResultContentDetail.form['execution_time']}秒` : '未知' }
            </el-descriptions-item>
            <el-descriptions-item label="执行者">
              { scanResultContentDetail.form['director'] }
            </el-descriptions-item>
            <el-descriptions-item label="结果类型">
              { scanResultContentDetail.form['result_type'] === 'script' ? '脚本执行' : '任务执行' }
            </el-descriptions-item>
          </el-descriptions>
          
          <!-- 脚本输出结果 -->
          <el-divider content-position="left">脚本输出结果</el-divider>
          <el-card v-if="scanResultContentDetail.form['script_output']" shadow="never" style="margin-bottom: 16px;">
            <template #header>
              <span style="color: #67C23A;">
                <el-icon><SuccessFilled /></el-icon>
                执行结果
              </span>
            </template>
            <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f5f5f5; padding: 12px; border-radius: 4px;">
              { scanResultContentDetail.form['script_output'] }
            </div>
          </el-card>
          
          <!-- 错误信息 -->
          <el-card v-if="scanResultContentDetail.form['error_message']" shadow="never" style="margin-bottom: 16px;">
            <template #header>
              <span style="color: #F56C6C;">
                <el-icon><CircleCloseFilled /></el-icon>
                错误信息
              </span>
            </template>
            <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #fef0f0; padding: 12px; border-radius: 4px; color: #F56C6C;">
              { scanResultContentDetail.form['error_message'] }
            </div>
          </el-card>
          
          <!-- 完整JSON结果（折叠显示） -->
          <el-collapse style="margin-top: 16px;">
            <el-collapse-item title="查看完整JSON结果" name="json">
              <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f8f8f8; padding: 12px; border-radius: 4px; max-height: 400px; overflow-y: auto;">
                { formatJsonContent(scanResultContentDetail.form['scandevresult_content']) }
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <!-- 传统扫描结果显示 -->
        <div v-else style="white-space: pre-wrap">
          { scanResultContentDetail.form['scandevresult_content'] }
        </div>
        <template #footer="footer">
          <a-button @click="dataBackup_handleCancel">关闭</a-button>
        </template>
      </a-modal>
      </div>
    </ScriptManagerLayout>
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message } from 'ant-design-vue';
import { createApi, listApi, updateApi, deleteApi } from '/@/api/scanDevUpdate';
import ScriptManagerLayout from '/@/components/ScriptManagerLayout.vue';
import { SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import { ref, reactive, onMounted } from 'vue'

// 进来页面后默认定位到主内容页面
const activeName = ref('mainContent')


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
    title: '文件名',
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
  title: 'AI文本检查结果',
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
  
  // 脚本执行完成后刷新结果列表（确保在ref可用后注册）
  const tryRegister = () => {
    if (scriptManager.value && typeof scriptManager.value.onDataRefresh === 'function') {
      scriptManager.value.onDataRefresh(() => {
        console.log('脚本执行完成，刷新扫描结果数据...')
        getDataList();
        activeName.value = 'mainContent';
      });
      return true;
    }
    return false;
  };
  
  if (!tryRegister()) {
    setTimeout(() => {
      tryRegister();
    }, 0);
  }
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
  modal.title = '编辑AI文本检查信息';
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

// 格式化JSON内容
const formatJsonContent = (jsonStr: string) => {
  if (!jsonStr) return '';
  try {
    const parsed = JSON.parse(jsonStr);
    return JSON.stringify(parsed, null, 2);
  } catch (e) {
    return jsonStr;
  }
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
