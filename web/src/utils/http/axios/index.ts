import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { showMessage } from './status';
import { IResponse } from './type';
import { getToken } from '/@/utils/auth';
import { TokenPrefix } from '/@/utils/auth';
import {ADMIN_USER_TOKEN, USER_TOKEN, BASE_URL} from '/@/store/constants'
import {message} from "ant-design-vue";
import qs from 'qs'


const service: AxiosInstance = axios.create({
  baseURL: BASE_URL + '',
  timeout: 15000,
});

// axios实例拦截请求
// request 拦截器
// 可以自请求发送前对请求做一些处理
// 比如统一加token，对请求参数统一加密
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    config.headers.ADMINTOKEN = localStorage.getItem(ADMIN_USER_TOKEN)
    config.headers.TOKEN = localStorage.getItem(USER_TOKEN)

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  },
);

// axios实例拦截响应
service.interceptors.response.use(
  (response: AxiosResponse) => {
    if(response.status == 200) {
      // 检查多种成功响应格式
      if(response.data.code == 0 || 
         response.data.code == 200 || 
         response.data.success === true ||
         Array.isArray(response.data) ||
         (typeof response.data === 'object' && response.data !== null && !response.data.error)) {  // 支持直接返回对象的API
        return response
      }else {
        return Promise.reject(response.data)
      }
    } else {
      return Promise.reject(response.data)
    }
  },
  // 请求失败
  (error: any) => {
    console.log('error==>', error)
    if(error.response) {
      //服务器响应了状态码，但不是2x
      message.error('错误状态码：',error.response.status);
      message.error('错误数据：',error.response.data);
    } else if (error.request){
      message.error('请求已发出，但没有收到响应：',error.request)
    } else {
      //其他错误，如网络错误等
      message.error('请求超时、请求被取消或者引起的网络问题导致未发送请求')
    }
    return Promise.reject(error)
  },
);



const request = <T = any>(config: AxiosRequestConfig): Promise<T> => {
  const conf = config;
  //conf.headers["Access-Control-Allow-Origin"] = "*";
  //conf.headers["Access-Control-Allow-Credentials"] = "true";
  //conf.headers["Access-Control-Allow-Methods"] = "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS";
  //conf.headers["Access-Control-Allow-Headers"] = "*"
  //conf.headers["Access-Control-Max-Age"] = "1800";
  return new Promise((resolve, reject) => {
    service.request<any, AxiosResponse<IResponse>>(conf).then((res: AxiosResponse<IResponse>) => {
      const data = res.data
      resolve(data as T);
    }).catch(err => {
      reject(err)
    });
  });
};

export function get<T = any>(config: AxiosRequestConfig): Promise<T> {
  return request({ ...config, method: 'GET' });
}

export function post<T = any>(config: AxiosRequestConfig): Promise<T> {
  return request({ ...config, method: 'POST' });
}

export default request;

export type { AxiosInstance, AxiosResponse };
