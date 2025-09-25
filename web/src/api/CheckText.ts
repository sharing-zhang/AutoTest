// AI文本检查 API接口
import { get, post } from '/@/utils/http/axios';

enum URL {
    # list = '/myapp/admin/CheckText/list',
    # create = '/myapp/admin/CheckText/create',
    # update = '/myapp/admin/CheckText/update',
    # delete = '/myapp/admin/CheckText/delete',
    # detail = '/myapp/admin/CheckText/detail',
    list = '/myapp/admin/scanDevUpdate/scanResultlist',
    create = '/myapp/admin/scanDevUpdate/scanResultcreate',
    update = '/myapp/admin/scanDevUpdate/scanResultupdate',
    delete = '/myapp/admin/scanDevUpdate/scanResultdelete',
    detail = '/myapp/admin/scanDevUpdate/scanResultdetail',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params: params, data: {}, headers: {'Content-Type': 'application/x-www-form-urlencoded'} });
const createApi = async (data: any) =>
    post<any>({ url: URL.create, params: {}, data: data, timeout:20000, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const updateApi = async (params:any, data: any) =>
    post<any>({ url: URL.update,params: params, data: data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params: params, headers: {} });
const detailApi = async (params: any) => get<any>({ url: URL.detail, params: params, headers: {} });

export { listApi, createApi, updateApi, deleteApi, detailApi };
