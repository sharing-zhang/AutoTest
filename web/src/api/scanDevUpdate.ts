// 权限问题后期增加
import { get, post } from '/@/utils/http/axios';
import { UserState } from '/@/store/modules/user/types';
// import axios from 'axios';
//每个新的URL路径都需要到server/myapp/urls.py中声明当前url对应具体哪个请求方法
enum URL {
    list = '/myapp/admin/scanDevUpdate/scanResultlist',
    create = '/myapp/admin/scanDevUpdate/scanResultcreate',
    update = '/myapp/admin/scanDevUpdate/scanResultupdate',
    delete = '/myapp/admin/scanDevUpdate/scanResultdelete',
    detail = '/myapp/admin/scanDevUpdate/scanResultdetail',
    // 钉钉机器人发送消息接口
    sendmessage = '/myapp/admin/scanDevUpdate/scanResultsendmessage',
    // ViewSet API 路由
    listScripts = '/myapp/api/scripts/',
    scriptDetail = '/myapp/api/scripts/',
    pageConfigs = '/myapp/api/page-configs/',
    taskExecutions = '/myapp/api/task-executions/',
    // ScriptExecutionViewSet - 独立的脚本执行ViewSet
    executeScript = '/myapp/api/script-executions/execute/',
    scriptStatus = '/myapp/api/script-executions/status/',
    // TaskExecutionViewSet - 任务记录管理
    cancelTask = '/myapp/api/task-executions/',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params: params, data: {}, headers: {'Content-Type': 'application/x-www-form-urlencoded'} });
const createApi = async (data: any) =>
    post<any>({ url: URL.create, params: {}, data: data, timeout:20000, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const updateApi = async (params:any, data: any) =>
    post<any>({ url: URL.update, params: params, data: data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params: params, headers: {} });
const detailApi = async (params: any) => get<any>({ url: URL.detail, params: params, headers: {} });

//钉钉机器人发送消息接口
const sendmessageApi = async (params:any, data: any) =>
    post<any>({ url: URL.sendmessage, params: params, data: data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });

// ViewSet API 函数
const listScriptsApi = async (params: any = {}) => get<any>({ url: URL.listScripts, params: params, headers: {} });
const getScriptDetailApi = async (scriptId: number) => get<any>({ url: `${URL.scriptDetail}/${scriptId}`, params: {}, headers: {} });

// 页面配置API
const getPageConfigsApi = async (pageRoute?: string) => {
  const params = pageRoute ? { page_route: pageRoute } : {};
  return get<any>({ url: URL.pageConfigs, params: params, headers: {} });
};

// ScriptExecutionViewSet API - 脚本执行相关
const executeScriptApi = async (data: any) => post<any>({ url: URL.executeScript, params: {}, data: data, headers: { 'Content-Type': 'application/json' } });
const getScriptTaskResultApi = async (taskId?: string, executionId?: string) => {
  const params: any = {};
  if (taskId) params.task_id = taskId;
  if (executionId) params.execution_id = executionId;
  return get<any>({ url: URL.scriptStatus, params: params, headers: {} });
};

// TaskExecutionViewSet API - 任务记录管理
const cancelTaskApi = async (executionId: number) => post<any>({ url: `${URL.cancelTask}${executionId}/cancel_task/`, params: {}, data: {}, headers: {} });

export { 
    listApi, createApi, updateApi, deleteApi, detailApi, sendmessageApi,
    listScriptsApi, getScriptDetailApi, getPageConfigsApi,
    executeScriptApi, getScriptTaskResultApi, cancelTaskApi
};
