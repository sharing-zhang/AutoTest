// 权限问题后期增加
import { get, post } from '/@/utils/http/axios';
import { UserState } from '/@/store/modules/user/types';
// import axios from 'axios';
enum URL {
  delete = '/myapp/admin/plugin/delete',
  upload = '/myapp/admin/plugin/upload',
  listExe = '/myapp/admin/plugin/listExe',
  updateExe = '/myapp/admin/plugin/updateExe',
}



const deleteApi = async (params: any) => post<any>({ url: URL.delete, params: params, headers: {} });

const uploadExeApi = async (data: any) => post<any>({ url: URL.upload, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });

const updateExeApi = async (data: any) => post<any>({ url: URL.updateExe, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const listExeApi = async () => get<any>({ url: URL.listExe });

export { deleteApi, uploadExeApi, listExeApi, updateExeApi };

