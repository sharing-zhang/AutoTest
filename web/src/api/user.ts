// 权限问题后期增加
import { get, post } from '/@/utils/http/axios';
import { UserState } from '/@/store/modules/user/types';
// import axios from 'axios';
enum URL {
    login = '/myapp/admin/adminLogin',
    userList = '/myapp/admin/user/list',
    detail = '/api/user/detail',
    create = '/myapp/admin/user/create',
    update = '/myapp/admin/user/update',
    delete = '/myapp/admin/user/delete',
    userLogin = '/myapp/api/user/userLogin',
    userRegister = '/myapp/api/user/userRegister',
    updateUserPwd = '/api/user/updatePwd',
    updateUserInfo = '/api/user/updateUserInfo'
}
interface LoginRes {
    token: string;
}

export interface LoginData {
    username: string;
    password: string;
}


const loginApi = async (data: LoginData) => post<any>({ url: URL.login, data, headers: { 'Content-Type': 'application/x-www-form-urlencoded' }});
const listApi = async (params: any) => get<any>({ url: URL.userList, params: params, data: {}, headers: {'Content-Type': 'application/x-www-form-urlencoded'} });
const detailApi = async (params: any) => get<any>({ url: URL.detail, params: params, data: {}, headers: {'Content-Type': 'application/x-www-form-urlencoded'} });
const createApi = async (data: any) => post<any>({ url: URL.create, params: {}, data: data, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
const updateApi = async (params: any, data: any) => post<any>({ url: URL.update,params: params, data: data, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params: params, headers: {'Content-Type': 'application/x-www-form-urlencoded'} });
const userLoginApi = async (data: LoginData) => post<any>({ url: URL.userLogin, data, headers: { 'Content-Type': 'application/x-www-form-urlencoded'} });
const userRegisterApi = async (data: any) => post<any>({ url: URL.userRegister, params: {}, data: data, headers: {'Content-Type': 'application/x-www-form-urlencoded' } });
const updateUserPwdApi = async (params: any) => post<any>({ url: URL.updateUserPwd, params: params });
const updateUserInfoApi = async (data: any) => post<any>({ url: URL.updateUserInfo, data: data, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });

export { loginApi, listApi, detailApi, createApi, updateApi, deleteApi, userLoginApi, userRegisterApi, updateUserPwdApi, updateUserInfoApi};
