// 权限问题后期增加
import { get, post } from '/@/utils/http/axios';
import { UserState } from '/@/store/modules/user/types';
// import axios from 'axios';
//每个新的URL路径都需要到server/myapp/urls.py中声明当前url对应具体哪个请求方法
enum URL {
    list = '/myapp/admin/scanUpdate/list',
    create = '/myapp/admin/scanUpdate/create',
    update = '/myapp/admin/scanUpdate/update',
    delete = '/myapp/admin/scanUpdate/delete',
    detail = '/myapp/admin/scanUpdate/detail',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params: params, data: {}, headers: {'Content-Type': 'application/x-www-form-urlencoded'} });
const createApi = async (data: any) =>
    post<any>({ url: URL.create, params: {}, data: data, timeout:20000, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const updateApi = async (params:any, data: any) =>
    post<any>({ url: URL.update,params: params, data: data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params: params, headers: {} });
const detailApi = async (params: any) => get<any>({ url: URL.detail, params: params, headers: {} });

export { listApi, createApi, updateApi, deleteApi, detailApi };
