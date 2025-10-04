/* eslint-disable */
import axios, { AxiosResponse } from 'axios';
import { message } from 'antd';
import { history } from 'umi';

// 定义基类
export interface MyResponse {
  code: number;
  msg: string;
  success: boolean;
}

// 定义通用响应类型
export interface BaseResponse<T> extends MyResponse {
  data: T;
}

// 定义列表响应类型
export interface BaseListResponse<T> extends MyResponse {
  data: T[];
}

// 定义分页列表响应类型
export interface PageResponse<T> extends MyResponse {
  data: {
    items: T[];
    total: number;
    page: number;
    page_size: number;
  };
}

// 创建 axios 实例
const requestTool = axios.create({
  baseURL: '', // 不设置 baseURL，API 路径中已包含完整路径
  timeout: 10000,
  withCredentials: true, // 携带 Cookie（JWT token）
});

// 请求拦截器
requestTool.interceptors.request.use(
  (config) => {
    // auth cookie 是 HttpOnly 的，会自动随请求发送
    // 无需手动处理
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
requestTool.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data;

    // 处理业务错误
    if (res.code !== 200 && res.success === false) {
      message.error(res.msg || '请求失败');
      return Promise.reject(new Error(res.msg || '请求失败'));
    }

    return res;
  },
  (error) => {
    // 处理 HTTP 错误
    if (error.response) {
      const { status } = error.response;

      // 处理 401 未授权
      if (status === 401) {
        message.error('登录已过期，请重新登录');
        // 跳转到登录页
        history.push('/login');
        return Promise.reject(new Error('登录已过期'));
      }

      // 处理其他 HTTP 错误
      message.error(error.response.data?.msg || '请求失败');
    } else {
      message.error('网络错误，请稍后重试');
    }

    return Promise.reject(error);
  }
);

export default requestTool;

