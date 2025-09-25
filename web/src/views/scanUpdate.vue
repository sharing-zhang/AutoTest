<template>
  <div>
    <!--页面区域-->
    <div class="page-view">
      <!--
        1. size="middle"：表示字体中型，rowKey="id"：每一行以id作为数据唯一标识符，没有会报错
        2. loading：控制表格在数据加载时的加载状态显示，flase则不显示数据加载动画
        3. columns:用于定义表格的列。每一列是一个对象，包含列的标题、数据索引、宽度等属性.
        4. data-source:表格的数据源，通常是一个数组，包含需要展示的数据对象，每一个对象代表一行数据
        5. scroll="{ x: 'max-content' }"：表格的水平滚动条会根据内容的宽度自适应调整，不会产生多余的滚动空间
        6. row-selection="rowSelection": 控制勾选框，这里不需要勾选框，则去掉
        7. pagination:用于控制分页的配置。可以是一个对象
          7.1 当表格的分页状态发生变化时， onChange 回调函数会被触发。这个回调函数通常接收以下参数：
              current‌：当前页码。
              pageSize‌：每页显示的数量。
          7.2 showSizeChanger：属性用于控制是否显示每页显示条数的选择器

      -->
      
      <!-- 操作按钮区域 -->
      <div style="margin-bottom: 16px;">
        <a-button type="primary" @click="handleAdd">
          <template #icon>
            <PlusOutlined />
          </template>
          新增项目
        </a-button>
      </div>
      
      <a-table
        size="middle"
        rowKey="id"
        :loading="data.loading"
        :columns="columns"
        :data-source="data.dataList"
        :scroll="{ x: 'max-content' }"
        :pagination="{
          size: 'small',
          current: data.page,
          pageSize: data.pageSize,
          onChange: (current) => (data.page = current),
          showSizeChanger: false,
          showTotal: (total) => `共${total}条数据`,
        }"
      >
        <!-- 自定义表头和表体
           1. #bodyCell属性用于定义表格中每个单元格的渲染逻辑。它接收两个参数：column和record。column表示当前列的配置信息，record表示当前行的数据。
           2. v-if="column.key === 'operation'" 检查当前列是否为操作列，如果是，则渲染操作按钮。
           3. <a-popconfirm>: 用于确认删除操作的弹出框，用户在点击删除按钮后会弹出确认框。
           4. <a-divider：创建一个分割线
         -->
        <template #bodyCell="{ text, record, index, column }">
          <template v-if="column.key === 'operation'">
            <span>
              <a @click="handleEdit(record)">编辑</a>
              <a-divider type="vertical" />
              <a @click="handleClick(record)">进入项目</a>
            </span>
          </template>
        </template>
      </a-table>
    </div>

    <!--弹窗区域-->
    <div>
      <!--
         1. <a-modal:创建模态对话框，在不离开当前页面下，创建的一个基于页面图层上的对话框
         2. visible：设置是否可见
         3. title:标题
      -->
      <a-modal
        :visible="modal.visile"
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
                <a-form-item label="项目" name="projectname">
                  <a-input placeholder="请输入项目名" v-model:value="modal.form.projectname" allowClear />
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="说明" name="description">
                  <a-input placeholder="请输入项目说明" v-model:value="modal.form.description" allowClear />
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="版本号" name="versionnumber">
                  <a-input placeholder="请输入版本号" v-model:value="modal.form.versionnumber" allowClear />
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="最新更新日期" name="lastupdatetime">
                  <a-input placeholder="请输入最新更新日期" v-model:value="modal.form.lastupdatetime" allowClear />
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="最新更新内容" name="lastupdates">
                  <a-input placeholder="请输入最新更新内容" v-model:value="modal.form.lastupdates" allowClear />
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
              <a-col span="24">
                <a-form-item label="路由键" name="child_url_key">
                  <a-input placeholder="请输入路由键(如: CheckReward)" v-model:value="modal.form.child_url_key" allowClear />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </div>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message, SelectProps } from 'ant-design-vue';
import { createApi, listApi, updateApi, deleteApi } from '/@/api/scanUpdate';
import {BASE_URL} from "/@/store/constants";
import { FileImageOutlined, VideoCameraOutlined, PlusOutlined } from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import {useRouter} from "vue-router";

const columns = reactive([

  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    align: "center",
    width: 60
  },
  {
    title: '项目',
    dataIndex: 'projectname',
    align: "center",
    key: 'projectname',
    width: 160
  },
  {
    title: '说明',
    dataIndex: 'description',
    align: "center",
    key: 'description',
    width: 300
  },
  {
    title: '版本号',
    dataIndex: 'versionnumber',
    align: "center",
    key: 'versionnumber',
    width: 100
  },
  {
    title: '最近更新日期',
    dataIndex: 'lastupdatetime',
    align: "center",
    key: 'lastupdatetime',
    width: 160
  },
  {
    title: '最新更新内容',
    dataIndex: 'lastupdates',
    align: "center",
    key: 'lastupdates',
    width: 300
  },
  {
    title: '负责人',
    dataIndex: 'director',
    align: "center",
    key: 'director',
    width: 90
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
  dataList: [],
  loading: false,
  keyword: '',
  selectedRowKeys: [] as any[],
  pageSize: 10,
  page: 1,
});

// 弹窗数据源:编辑修改项目信息弹窗
const modal = reactive({
  visile: false,
  editFlag: false,
  title: '',
  form: {
    id: undefined,
    projectname: undefined,
    description: undefined,
    versionnumber: undefined,
    lastupdatetime: undefined,
    lastupdates: undefined,
    director: undefined,
    remark: undefined,
    status: undefined,
    child_url_key: undefined,
  },
  rules: {
    projectname: [{ required: true, message: '请输入项目名', trigger: 'change' }],
    description: [{ required: false, message: '请输入项目说明', trigger: 'change' }],
    versionnumber: [{ required: false, message: '请输入版本号', trigger: 'change' }],
    lastupdatetime: [{ required: true, message: '请输入最近更新日期', trigger: 'change' }],
    lastupdates: [{ required: true, message: '请输入最新更新内容', trigger: 'change' }],
    director: [{ required: true, message: '请输入负责人', trigger: 'change' }],
    remark: [{ required: false, message: '请输入备注', trigger: 'change' }],
    child_url_key: [{ required: true, message: '请输入路由键', trigger: 'change' }]
  },
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
          item.lastupdatetime = dayjs(item.lastupdatetime).format('YYYY-MM-DD HH:mm:ss');
          item.index = index + 1;
        });
        data.dataList = res.data;
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

// 新增项目
const handleAdd = () => {
  resetModal();
  modal.visile = true;
  modal.editFlag = false;
  modal.title = '新增项目';
  // 重置表单
  for (const key in modal.form) {
    modal.form[key] = undefined;
  }
  // 自动填充当前时间
  modal.form.lastupdatetime = dayjs().format('YYYY-MM-DD HH:mm:ss');
  // 自动填充版本号（V + 时间去掉符号）
  modal.form.versionnumber = 'V' + dayjs().format('YYMMDDHHmmss');
};

const handleEdit = (record: any) => {
  resetModal();
  modal.visile = true;
  modal.editFlag = true;
  modal.title = '编辑项目信息';
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
        formData.append('projectname', modal.form.projectname)
        formData.append('description', modal.form.description)
        formData.append('versionnumber', modal.form.versionnumber)
        formData.append('lastupdatetime', modal.form.lastupdatetime)
        formData.append('lastupdates', modal.form.lastupdates)
        formData.append('director', modal.form.director)
        formData.append('remark', modal.form.remark)
        formData.append('child_url_key', modal.form.child_url_key)
        if (modal.editFlag) {
          submitting.value = true
          updateApi({
            id: modal.form.id
          },formData)
              .then((res) => {
                submitting.value = false
                hideModal();
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
              .then(async (res) => {
                submitting.value = false
                hideModal();
                getDataList();
                
                // 如果是新增项目且有路由键，自动创建前端页面
                if (modal.form.child_url_key) {
                  try {
                    await createFrontendPage(modal.form.child_url_key, modal.form.projectname);
                    message.success('项目创建成功，前端页面已自动生成！');
                  } catch (error) {
                    console.error('创建前端页面失败:', error);
                    message.warning('项目创建成功，但前端页面生成失败，请手动创建');
                  }
                } else {
                  message.success('项目创建成功');
                }
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


// 点击【进入项目】实现指定路由跳转
const router = useRouter()
const handleClick = (record: any) => {
  console.log('点击路由===>', record.child_url_key)
  //导航到新的url中
  router.push({
    name: record.child_url_key,
  })
}

// 创建前端页面的函数
const createFrontendPage = async (routeKey: string, projectName: string) => {
  try {
    // 调用后端API创建前端页面
    const response = await fetch(`${BASE_URL}/myapp/api/create-frontend-page/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        route_key: routeKey,
        project_name: projectName,
        page_title: projectName || routeKey
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('前端页面创建成功:', result);
      return result;
    } else {
      throw new Error(result.error || '创建前端页面失败');
    }
  } catch (error) {
    console.error('创建前端页面API调用失败:', error);
    throw error;
  }
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


</style>
