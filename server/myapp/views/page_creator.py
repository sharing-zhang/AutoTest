"""
页面创建器视图
专门用于动态创建前端页面的功能
"""
import json
import os
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
import logging

# 获取日志器
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_frontend_page(request):
    """动态创建前端页面"""
    try:
        print(f"收到创建前端页面请求: {request.body}")
        data = json.loads(request.body) if request.body else {}
        print(f"解析后的数据: {data}")
        route_key = data.get('route_key')
        # 所有页面都复用scanDevUpdate的路由
        api_route_key = 'scanDevUpdate'
        project_name = data.get('project_name', '')
        page_title = data.get('page_title', route_key)
        print(f"路由键: {route_key}, 项目名: {project_name}, 页面标题: {page_title}")
        
        if not route_key:
            return JsonResponse({
                'success': False,
                'error': '缺少route_key参数'
            }, status=400)
        
        # 验证路由键格式（只允许字母、数字、下划线）
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', route_key):
            return JsonResponse({
                'success': False,
                'error': '路由键格式不正确，只能包含字母、数字、下划线，且必须以字母开头'
            }, status=400)
        
        # 检查路由键是否已存在
        if check_route_exists(route_key):
            return JsonResponse({
          
                'success': True,
                'message': f'路由键 "{route_key}" 已存在，直接进入已有页面',
                'route_key': route_key,
                'existing': True,
                'api_endpoints': {
                    'list': '/myapp/admin/scanDevUpdate/scanResultlist',
                    'create': '/myapp/admin/scanDevUpdate/scanResultcreate',
                    'update': '/myapp/admin/scanDevUpdate/scanResultupdate',
                    'delete': '/myapp/admin/scanDevUpdate/scanResultdelete',
                    'detail': '/myapp/admin/scanDevUpdate/scanResultdetail'
                }
            })
        
        # 创建Vue组件文件
        vue_file_path = create_vue_component(route_key, project_name, page_title)
        
        # 更新路由配置
        update_router_config(route_key)
        
        # 创建对应的API接口
        create_api_endpoints(route_key, project_name)
        
        return JsonResponse({
            'success': True,
            'message': f'前端页面 "{route_key}" 创建成功',
            'route_key': route_key,
            'vue_file': vue_file_path,
            'api_endpoints': {
                # 'list': f'/myapp/admin/{route_key}/list',
                # 'create': f'/myapp/admin/{route_key}/create',
                # 'update': f'/myapp/admin/{route_key}/update',
                # 'delete': f'/myapp/admin/{route_key}/delete',
                # 'detail': f'/myapp/admin/{route_key}/detail'
                'list': '/myapp/admin/scanDevUpdate/scanResultlist',
                'create': '/myapp/admin/scanDevUpdate/scanResultcreate',
                'update': '/myapp/admin/scanDevUpdate/scanResultupdate',
                'delete': '/myapp/admin/scanDevUpdate/scanResultdelete',
                'detail': '/myapp/admin/scanDevUpdate/scanResultdetail'
            }
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return JsonResponse({
            'success': False,
            'error': f'请求数据格式错误: {str(e)}'
        }, status=400)
    except Exception as e:
        print(f"创建前端页面异常: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '创建前端页面失败'
        }, status=500)

def check_route_exists(route_key):
    """检查路由键是否已存在"""
    try:
        # 检查Vue路由配置
        base_dir = os.path.dirname(settings.BASE_DIR)  # 获取server目录的父目录
        router_file = os.path.join(base_dir, 'web', 'src', 'router', 'root.js')
        if os.path.exists(router_file):
            with open(router_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if f"name: '{route_key}'" in content:
                    return True
        
        # 检查Vue组件文件
        vue_file = os.path.join(base_dir, 'web', 'src', 'views', f'{route_key}.vue')
        if os.path.exists(vue_file):
            return True
            
        return False
    except Exception as e:
        logger.error(f"检查路由存在性失败: {e}")
        return False

def create_vue_component(route_key, project_name, page_title):
    """创建Vue组件文件"""
    try:
        # 直接嵌入scanDevUpdate.vue的完整内容作为模板
        vue_template = get_scan_dev_template(route_key, page_title)
        
        # 创建Vue文件
        print(f"BASE_DIR: {settings.BASE_DIR}")
        # 修复路径问题 - 使用绝对路径
        base_dir = os.path.dirname(settings.BASE_DIR)  # 获取server目录的父目录
        vue_file_path = os.path.join(base_dir, 'web', 'src', 'views', f'{route_key}.vue')
        print(f"Vue文件路径: {vue_file_path}")
        os.makedirs(os.path.dirname(vue_file_path), exist_ok=True)
        
        with open(vue_file_path, 'w', encoding='utf-8') as f:
            f.write(vue_template)
        
        logger.info(f"Vue组件文件创建成功: {vue_file_path}")
        return vue_file_path
        
    except Exception as e:
        logger.error(f"创建Vue组件失败: {e}")
        raise e

def update_router_config(route_key):
    """更新路由配置"""
    try:
        base_dir = os.path.dirname(settings.BASE_DIR)  # 获取server目录的父目录
        router_file = os.path.join(base_dir, 'web', 'src', 'router', 'root.js')
        print(f"路由文件路径: {router_file}")
        
        if not os.path.exists(router_file):
            logger.error(f"路由文件不存在: {router_file}")
            return
        
        # 读取现有路由配置
        with open(router_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已存在该路由
        if f"name: '{route_key}'" in content:
            logger.info(f"路由 {route_key} 已存在，跳过添加")
            return
        
        # 在children数组中添加新路由
        new_route = f"      {{ path: '{route_key}', name: '{route_key}', component: () => import('/@/views/{route_key}.vue') }},\n"
        
        # 使用更简单的方法：在最后一个路由项后添加新路由
        # 查找最后一个路由项的位置
        lines = content.split('\n')
        last_route_line = -1
        
        for i, line in enumerate(lines):
            if 'component: () => import' in line and 'views/' in line:
                last_route_line = i
        
        if last_route_line != -1:
            # 在最后一个路由项后添加新路由
            new_route = f"      {{ path: '{route_key}', name: '{route_key}', component: () => import('/@/views/{route_key}.vue') }},"
            lines.insert(last_route_line + 1, new_route)
            content = '\n'.join(lines)
            logger.info(f"在行 {last_route_line + 1} 后添加新路由: {route_key}")
        else:
            logger.error("无法找到现有路由项，无法添加新路由")
            return
        
        # 写回文件
        with open(router_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"路由配置更新成功: {route_key}")
        
    except Exception as e:
        logger.error(f"更新路由配置失败: {e}")
        raise e

def create_api_endpoints(route_key, project_name):
    """创建API接口文件"""
    try:
        # 创建API文件
        base_dir = os.path.dirname(settings.BASE_DIR)  # 获取server目录的父目录
        api_file_path = os.path.join(base_dir, 'web', 'src', 'api', f'{route_key}.ts')
        print(f"API文件路径: {api_file_path}")
        os.makedirs(os.path.dirname(api_file_path), exist_ok=True)
        
        api_template = f"""// {project_name} API接口
import {{ get, post }} from '/@/utils/http/axios';

enum URL {{
    # list = '/myapp/admin/{route_key}/list',
    # create = '/myapp/admin/{route_key}/create',
    # update = '/myapp/admin/{route_key}/update',
    # delete = '/myapp/admin/{route_key}/delete',
    # detail = '/myapp/admin/{route_key}/detail',
    list = '/myapp/admin/scanDevUpdate/scanResultlist',
    create = '/myapp/admin/scanDevUpdate/scanResultcreate',
    update = '/myapp/admin/scanDevUpdate/scanResultupdate',
    delete = '/myapp/admin/scanDevUpdate/scanResultdelete',
    detail = '/myapp/admin/scanDevUpdate/scanResultdetail',
}}

const listApi = async (params: any) => get<any>({{ url: URL.list, params: params, data: {{}}, headers: {{'Content-Type': 'application/x-www-form-urlencoded'}} }});
const createApi = async (data: any) =>
    post<any>({{ url: URL.create, params: {{}}, data: data, timeout:20000, headers: {{ 'Content-Type': 'multipart/form-data;charset=utf-8' }} }});
const updateApi = async (params:any, data: any) =>
    post<any>({{ url: URL.update,params: params, data: data, headers: {{ 'Content-Type': 'multipart/form-data;charset=utf-8' }} }});
const deleteApi = async (params: any) => post<any>({{ url: URL.delete, params: params, headers: {{}} }});
const detailApi = async (params: any) => get<any>({{ url: URL.detail, params: params, headers: {{}} }});

export {{ listApi, createApi, updateApi, deleteApi, detailApi }};
"""
        
        with open(api_file_path, 'w', encoding='utf-8') as f:
            f.write(api_template)
        
        logger.info(f"API文件创建成功: {api_file_path}")
        
        #  # 创建后端API接口
        # create_backend_api_endpoints(route_key, project_name)

        # 复用scanDevUpdate的后端API接口，不需要创建新的路由
        logger.info(f"页面 {route_key} 将复用 scanDevUpdate 的后端API接口")
        
    except Exception as e:
        logger.error(f"创建API接口失败: {e}")
        raise e

def create_backend_api_endpoints(route_key, project_name):
    """创建后端API接口"""
    try:
        # 在urls.py中添加路由
        urls_file = os.path.join(settings.BASE_DIR, 'myapp', 'urls.py')
        
        if os.path.exists(urls_file):
            with open(urls_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已存在该路由
            if f"path('admin/{route_key}/" in content:
                logger.info(f"后端路由 {route_key} 已存在，跳过添加")
                return
            
            # 添加新的路由配置
            new_routes = f'''    # {project_name}相关接口
    path('admin/{route_key}/list', views.admin.{route_key}.list_api),
    path('admin/{route_key}/detail', views.admin.{route_key}.detail),
    path('admin/{route_key}/create', views.admin.{route_key}.create),
    path('admin/{route_key}/update', views.admin.{route_key}.update),
    path('admin/{route_key}/delete', views.admin.{route_key}.delete),
    
'''
            
            # 在适当位置插入新路由
            content = content.replace(
                '    path(\'admin/plugin/list\', views.admin.thing.list_api),',
                f'{new_routes}    path(\'admin/plugin/list\', views.admin.thing.list_api),'
            )
            
            with open(urls_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"后端路由配置更新成功: {route_key}")
        
    except Exception as e:
        logger.error(f"创建后端API接口失败: {e}")
        raise e

def get_scan_dev_template(route_key, page_title):
    """获取scanDevUpdate.vue的完整模板内容"""
    return f"""<template>
  <div>
    <!-- 使用脚本管理布局组件 -->
    <ScriptManagerLayout 
      page-route="/{route_key}"
      ref="scriptManager"
    >
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
          :scroll="{{ x: 'max-content' }}"
          :pagination="{{
            size: 'small',
            current: data.page,
            pageSize: data.pageSize,
            onChange: (current) => (data.page = current),
            showSizeChanger: false,
            showTotal: (total) => `共${{total}}条数据`,
          }}">
            <template #bodyCell="{{ text, record, index, column }}">
              <template v-if="column.key === 'operation'">
                <span>
                  <a @click="handleSend(record)">消息同步</a>
                  <a-divider type="vertical" />
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
          :scroll="{{ x: 'max-content' }}"
          :pagination="{{
            size: 'small',
            current: data.page,
            pageSize: data.pageSize,
            onChange: (current) => (data.page = current),
            showSizeChanger: false,
            showTotal: (total) => `共${{total}}条数据`,
          }}">
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
            <a-form ref="myform" :label-col="{{ style: {{ width: '120px'}} }}" :model="modal.form" :rules="modal.rules">
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
        <div v-if="scanResultContentDetail.form.result_type === 'script' || scanResultContentDetail.form.result_type === 'task'">
          <!-- 脚本执行结果显示 -->
          <el-descriptions title="脚本执行信息" :column="2" border>
            <el-descriptions-item label="脚本名称">
              {{{{ scanResultContentDetail.form.script_name || '未知' }}}}
            </el-descriptions-item>
            <el-descriptions-item label="任务ID">
              {{{{ scanResultContentDetail.form.task_id || '无' }}}}
            </el-descriptions-item>
            <el-descriptions-item label="执行时间">
              {{{{ scanResultContentDetail.form.scandevresult_time }}}}
            </el-descriptions-item>
            <el-descriptions-item label="执行耗时">
              {{{{ scanResultContentDetail.form.execution_time ? scanResultContentDetail.form.execution_time + '秒' : '未知' }}}}
            </el-descriptions-item>
            <el-descriptions-item label="执行者">
              {{{{ scanResultContentDetail.form.director }}}}
            </el-descriptions-item>
            <el-descriptions-item label="结果类型">
              {{{{ scanResultContentDetail.form.result_type === 'script' ? '脚本执行' : '任务执行' }}}}
            </el-descriptions-item>
          </el-descriptions>
          
          <!-- 脚本输出结果 -->
          <el-divider content-position="left">脚本输出结果</el-divider>
          <el-card v-if="scanResultContentDetail.form.script_output" shadow="never" style="margin-bottom: 16px;">
            <template #header>
              <span style="color: #67C23A;">
                <el-icon><SuccessFilled /></el-icon>
                执行结果
              </span>
            </template>
            <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f5f5f5; padding: 12px; border-radius: 4px;">
              {{{{ scanResultContentDetail.form.script_output }}}}
            </div>
          </el-card>
          
          <!-- 错误信息 -->
          <el-card v-if="scanResultContentDetail.form.error_message" shadow="never" style="margin-bottom: 16px;">
            <template #header>
              <span style="color: #F56C6C;">
                <el-icon><CircleCloseFilled /></el-icon>
                错误信息
              </span>
            </template>
            <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #fef0f0; padding: 12px; border-radius: 4px; color: #F56C6C;">
              {{{{ scanResultContentDetail.form.error_message }}}}
            </div>
          </el-card>
          
          <!-- 完整JSON结果（折叠显示） -->
          <el-collapse style="margin-top: 16px;">
            <el-collapse-item title="查看完整JSON结果" name="json">
              <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f8f8f8; padding: 12px; border-radius: 4px; max-height: 400px; overflow-y: auto;">
                {{{{ formatJsonContent(scanResultContentDetail.form.scandevresult_content) }}}}
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <!-- 传统扫描结果显示 -->
        <div v-else style="white-space: pre-wrap">
          {{{{ scanResultContentDetail.form.scandevresult_content }}}}
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
import {{ FormInstance, message }} from 'ant-design-vue';
import {{ createApi, listApi, updateApi, deleteApi }} from '/@/api/scanDevUpdate';
import ScriptManagerLayout from '/@/components/ScriptManagerLayout.vue';
import {{ SuccessFilled, CircleCloseFilled }} from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import {{ ref, reactive, onMounted, h}} from 'vue'

// 进来页面后默认定位到扫描结果页面
const activeName = ref('scanResult')


// 扫描结果表格列配置
const scanResultcolumns = reactive([

  {{
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    align: "center",
    width: 100
  }},
  {{
    title: '脚本名称',
    dataIndex: 'scandevresult_filename',
    align: "center",
    key: 'scandevresult_filename',
    width: 300
  }},
  {{
    title: '执行时间',
    dataIndex: 'scandevresult_time',
    align: "center",
    key: 'scandevresult_time',
    width: 200
  }},
  {{
    title: '执行人',
    dataIndex: 'director',
    align: "center",
    key: 'director',
    width: 110
  }},
  {{
    title: '执行状态',
    dataIndex: 'execution_status',
    align: "center",
    key: 'execution_status',
    width: 120,
  }},
  {{
    title: '结果摘要',
    dataIndex: 'result_summary',
    align: "center",
    key: 'result_summary',
    width: 120,
    ellipsis: true,
    customRender: ({{ record }}) => {{
      const summary = record.result_summary || '-';
      if (summary.length > 20) {{
        return summary.substring(0, 20) + '...';
      }}
      return summary;
    }}
  }},
  {{
    title: '操作',
    dataIndex: 'action',
    key: 'operation',
    align: 'center',
    fixed: 'right',
    width: 140,
  }},
]);

// 数据备份表格列配置
const dataBackupcolumns = reactive([

  {{
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    align: "center",
    width: 100
  }},
  {{
    title: '数据备份结果文件',
    dataIndex: 'scanDevResult',
    align: "center",
    key: 'scanDevResult',
    width: 800
  }},
  {{
    title: '时间',
    dataIndex: 'scanDevTime',
    align: "center",
    key: 'scanDevTime',
    width: 200
  }},
  {{
    title: '负责人',
    dataIndex: 'director',
    align: "center",
    key: 'director',
    width: 100
  }},
  {{
    title: '备注',
    dataIndex: 'remark',
    align: "center",
    key: 'remark',
    width: 260
  }},
  {{
    title: '操作',
    dataIndex: 'action',
    key: 'operation',
    align: 'center',
    fixed: 'right',
    width: 140,
  }},
]);

// 文件列表和提交状态
const fileList = ref<any[]>([]);
const submitting = ref<boolean>(false);

// 页面数据状态
const data = reactive({{
  scanResult_dataList: [],
  dataBackup_dataList: [],
  loading: false,
  keyword: '',
  selectedRowKeys: [] as any[],
  pageSize: 10,
  page: 1,
}});

// 编辑弹窗数据
const modal = reactive({{
  scanResult_visile: false,
  scanResult_editFlag: false,
  title: '',
  form: {{
    id: undefined,
    scandevresult_filename: undefined,
    scandevresult_time: undefined,
    director: undefined,
    remark: undefined,
    status: undefined,
    scandevresult_content: undefined,
  }},
  rules: {{
    scandevresult_filename: [{{ required: true, message: '请输入文件名', trigger: 'change' }}],
    scandevresult_time: [{{ required: true, message: '请输入时间', trigger: 'change' }}],
    director: [{{ required: true, message: '请输入负责人', trigger: 'change' }}],
    remark: [{{ required: false, trigger: 'change' }}],
  }},
}});

// 查看详情弹窗数据
const scanResultContentDetail = reactive({{
  scanResultContentDetail_visile: false,
  scanResultContentDetail_editFlag: false,
  title: '{page_title}结果',
  form: {{
    id: undefined,
    scandevresult_content: undefined,
  }},
  rules: {{}},
}});


// 表单实例引用
const myform = ref<FormInstance>();

// 组件引用
const scriptManager = ref();

onMounted(() => {{
  getDataList();
  
  // 延迟注册脚本执行完成后的数据刷新回调，确保组件已完全挂载
  setTimeout(() => {{
    if (scriptManager.value) {{
      scriptManager.value.onDataRefresh(() => {{
        console.log('脚本执行完成，刷新扫描结果数据...')
        getDataList();
      }});
      console.log('{route_key}页面刷新回调已注册');
    }} else {{
      console.error('scriptManager组件引用未找到');
    }}
  }}, 100);
}});

const getDataList = () => {{
  data.loading = true;
  listApi({{
    keyword: data.keyword,
  }})
      .then((res) => {{
        data.loading = false;
        console.log(res);
        res.data.forEach((item: any, index: any) => {{
          item.scandevresult_time = dayjs(item.scandevresult_time).format('YYYY-MM-DD HH:mm:ss');
          item.index = index + 1;
        }});
        data.scanResult_dataList = res.data;
        console.log(data.scanResult_dataList);
      }})
      .catch((err) => {{
        data.loading = false;
        console.log(err);
      }});
}}

// 搜索功能
const onSearchChange = (e: Event) => {{
  data.keyword = e?.target?.value;
  console.log(data.keyword);
}};

const onSearch = () => {{
  getDataList();
}};

const handleSend = (record: any) => {{
  // 调用 ScriptManagerLayout 的钉钉机器人弹窗方法
  if (scriptManager.value) {{
    scriptManager.value.openDingtalkDialog(record);
  }}
}};

const handleEdit = (record: any) => {{
  resetModal();
  modal.scanResult_visile = true;
  modal.scanResult_editFlag = true;
  modal.title = '编辑{page_title}信息';
  for (const key in modal.form) {{
    modal.form[key] = undefined;
  }}
  for (const key in record) {{
    if(record[key]) {{
      modal.form[key] = record[key];
    }}
  }}
}};

const handleOk = () => {{
  myform.value
      ?.validate()
      .then(() => {{
        const formData = new FormData();
        formData.append('id', modal.form.id)
        formData.append('scandevresult_filename', modal.form.scandevresult_filename)
        formData.append('scandevresult_time', modal.form.scandevresult_time)
        formData.append('director', modal.form.director)
        formData.append('remark', modal.form.remark)
        formData.append('status', modal.form.status)
        if (modal.scanResult_editFlag) {{
          submitting.value = true
          updateApi({{
            id: modal.form.id
          }},formData)
              .then((res) => {{
                submitting.value = false
                handleCancel();
                getDataList();
                message.success('项目信息更新成功')
              }})
              .catch((err) => {{
                submitting.value = false
                console.log(err);
                message.error(err.msg || '项目信息更新失败');
              }});
        }} else {{
          submitting.value = true
          createApi(formData)
              .then((res) => {{
                submitting.value = false
                handleCancel();
                getDataList();
              }})
              .catch((err) => {{
                submitting.value = false
                console.log(err);
                message.error(err.msg || '操作失败');
              }});
        }}
      }})
      .catch((err) => {{
        console.log('不能为空');
      }});
}};

// 关闭编辑弹窗
const handleCancel = () => {{
  modal.scanResult_visile = false;
}};

// 关闭查看详情弹窗
const dataBackup_handleCancel = () => {{
  scanResultContentDetail.scanResultContentDetail_visile = false;
}};


// 恢复表单初始状态
const resetModal = () => {{
  myform.value?.resetFields();
  fileList.value = []
}};


// 查看详情点击响应
const handleClick = (record: any) => {{
  resetModal();
  scanResultContentDetail.scanResultContentDetail_visile = true;
  scanResultContentDetail.scanResultContentDetail_editFlag = true;
  console.log(record )
  for (const key in scanResultContentDetail.form) {{
    scanResultContentDetail.form[key] = undefined;
  }}
  for (const key in record) {{
    if(record[key]) {{
      scanResultContentDetail.form[key] = record[key];
    }}
  }}
  console.log(scanResultContentDetail.form.scandevresult_content )
}}

// 格式化JSON内容
const formatJsonContent = (jsonStr: string) => {{
  if (!jsonStr) return '';
  try {{
    const parsed = JSON.parse(jsonStr);
    return JSON.stringify(parsed, null, 2);
  }} catch (e) {{
    return jsonStr;
  }}
}}

const bodystyle = {{
  height: '680px',
  overflowY: 'scroll',
  overflowX:'auto',
  width: '1600px',
}}


</script>

<style scoped lang="less">
.page-view {{
  min-height: 100%;
  background: #fff;
  padding: 24px;
  display: flex;
  flex-direction: column;
  position: relative; /* 为绝对定位的按钮提供定位上下文 */
}}


.table-operations {{
  margin-bottom: 16px;
  text-align: right;
}}

.table-operations > button {{
  margin-right: 8px;
}}

.el-tabs__content {{
  color: #6b778c;
  font-size: 32px;
  font-weight: 600;

}}


::v-deep .el-tabs__item {{
  width: 90px !important;
  justify-content: center !important;
  padding: 0;

}}

::v-deep .el-tabs__item::after {{
  content: "";
  position: absolute;
  align-items: center;
  right: 0;
  height: 35%;
  width: 1px; /* 分割线宽度 */
  background-color: #e4e7ed; /* 分割线颜色 */
  transform: translateX(100%); /* 调整位置使其在标签右侧 */
}}

::v-deep .el-tabs__active-bar {{
  width: 90px !important;

}}

::v-deep .ant-table {{
  color: rgb(34 33 33 / 85%);
  font-family: Helvetica, sans-serif;
  font-weight: 520;
}}

::v-deep  .ant-modal-body {{
  padding: 18px !important;
}}


</style>
"""
