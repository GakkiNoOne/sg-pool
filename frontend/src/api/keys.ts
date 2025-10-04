/**
 * Key 管理 API
 */

import request, { BaseResponse, PageResponse } from '@/utils/request';

/**
 * API Key 数据类型
 */
export interface APIKey {
  id: number;
  create_time: string;
  update_time: string;
  name: string;
  api_key: string;
  ua: string;
  proxy: string;
  enabled: boolean;
  balance: number | null;
  total_balance: number | null;
  balance_last_update: string | null;
  error_code: string | null;
  memo: string | null;
}

/**
 * 创建 API Key 请求
 */
export interface CreateAPIKeyRequest {
  name: string;
  api_key: string;
  ua: string;
  proxy?: string;
  enabled: boolean;
  memo?: string;
}

/**
 * 更新 API Key 请求
 */
export interface UpdateAPIKeyRequest {
  key_id: number;
  name?: string;
  ua?: string;
  proxy?: string;
  enabled?: boolean;
  memo?: string;
}

/**
 * 查询参数
 */
export interface QueryKeysParams {
  page?: number;
  page_size?: number;
  name?: string;
  enabled?: boolean;
  create_date?: string;  // 创建日期（格式：YYYY-MM-DD）
  min_balance?: number;  // 最小余额
}

/**
 * 批量创建结果
 */
export interface BatchCreateResult {
  success_count: number;
  fail_count: number;
  total_count: number;
  success_keys: APIKey[];
}

/**
 * 单个密钥测活结果
 */
export interface KeyCheckResult {
  key_id: number;
  key_name: string;
  success: boolean;
  message: string;
}

/**
 * 批量测活结果
 */
export interface BatchCheckResult {
  success_count: number;
  fail_count: number;
  total_count: number;
  results: KeyCheckResult[];
}

/**
 * Key 管理 API
 */
export const keysApi = {
  /**
   * 获取 API Key 列表
   */
  list: (params: QueryKeysParams = {}) => {
    return request.post<PageResponse<APIKey>>('/api/keys/list', {
      page: params.page || 1,
      page_size: params.page_size || 10,
      name: params.name,
      enabled: params.enabled,
    });
  },

  /**
   * 获取 API Key 详情
   */
  get: (id: number) => {
    return request.post<BaseResponse<APIKey>>('/api/keys/get', {
      key_id: id,
    });
  },

  /**
   * 创建 API Key
   */
  create: (data: CreateAPIKeyRequest) => {
    return request.post<BaseResponse<APIKey>>('/api/keys/create', data);
  },

  /**
   * 批量创建 API Keys
   */
  batchCreate: (batchName: string, apiKeys: string[]) => {
    return request.post<BaseResponse<BatchCreateResult>>('/api/keys/batchCreate', {
      batch_name: batchName,
      api_keys: apiKeys,
    });
  },

  /**
   * 更新 API Key
   */
  update: (id: number, data: Omit<UpdateAPIKeyRequest, 'key_id'>) => {
    return request.post<BaseResponse<APIKey>>('/api/keys/update', {
      key_id: id,
      ...data,
    });
  },

  /**
   * 删除 API Key
   */
  delete: (id: number) => {
    return request.post<BaseResponse<void>>('/api/keys/delete', {
      key_id: id,
    });
  },

  /**
   * 批量测活 API Keys
   */
  batchCheck: (keyIds: number[]) => {
    return request.post<BaseResponse<BatchCheckResult>>(
      '/api/keys/batchCheck',
      {
        key_ids: keyIds,
      },
      {
        timeout: 3600000, // 3600秒 = 1小时
      }
    );
  },

  /**
   * 批量删除 API Keys
   */
  batchDelete: (keyIds: number[]) => {
    return request.post<BaseResponse<{
      success_count: number;
      fail_count: number;
      total_count: number;
    }>>('/api/keys/batchDelete', {
      key_ids: keyIds,
    });
  },
};
