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
    // 方案1 Celery任务接口
    executeScript = '/myapp/admin/celery/execute-script',
    scriptTaskResult = '/myapp/admin/celery/script-task-result',
    listScripts = '/myapp/admin/celery/scripts',
    scriptDetail = '/myapp/admin/celery/scripts',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params: params, data: {}, headers: {'Content-Type': 'application/x-www-form-urlencoded'} });
const createApi = async (data: any) =>
    post<any>({ url: URL.create, params: {}, data: data, timeout:20000, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const updateApi = async (params:any, data: any) =>
    post<any>({ url: URL.update, params: params, data: data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params: params, headers: {} });
const detailApi = async (params: any) => get<any>({ url: URL.detail, params: params, headers: {} });

// 方案1任务相关API
const getScriptTaskResultApi = async (taskId: string, executionId?: string) => {
  const params: any = { task_id: taskId };
  if (executionId) {
    params.execution_id = executionId;
  }
  return get<any>({ url: URL.scriptTaskResult, params: params, headers: {} });
};

// 脚本管理API
const listScriptsApi = async (params: any = {}) => get<any>({ url: URL.listScripts, params: params, headers: {} });
const executeScriptApi = async (data: any) => post<any>({ url: URL.executeScript, params: {}, data: data, headers: { 'Content-Type': 'application/json' } });
const getScriptDetailApi = async (scriptId: number) => get<any>({ url: `${URL.scriptDetail}/${scriptId}`, params: {}, headers: {} });

export { 
    listApi, createApi, updateApi, deleteApi, detailApi, 
    getScriptTaskResultApi, listScriptsApi, executeScriptApi, getScriptDetailApi 
};
