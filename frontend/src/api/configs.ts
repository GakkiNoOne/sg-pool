/**
 * 配置管理 API
 */

import request, { BaseResponse } from '@/utils/request';

/**
 * 系统配置响应类型
 */
export interface SystemConfigsResponse {
  configs: Record<string, string>;
  readonly_keys: string[];
}

/**
 * 配置管理 API
 */
export const configsApi = {
  /**
   * 获取所有系统配置
   */
  getSystemConfigs: () => {
    return request.post<BaseResponse<SystemConfigsResponse>>('/api/configs/system/get', {});
  },

  /**
   * 保存系统配置
   */
  saveSystemConfigs: (configs: Record<string, string>) => {
    return request.post<BaseResponse<void>>('/api/configs/system/save', {
      configs,
    });
  },

  /**
   * 获取UA列表
   */
  getUAList: () => {
    return request.post<BaseResponse<string[]>>('/api/configs/ua/list', {});
  },

  /**
   * 获取代理列表
   */
  getProxyList: () => {
    return request.post<BaseResponse<string[]>>('/api/configs/proxy/list', {});
  },
};

