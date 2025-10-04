/**
 * 请求日志管理 API
 */

import request, { PageResponse } from '@/utils/request';

/**
 * 请求日志数据类型
 */
export interface RequestLog {
  id: number;
  create_time: string;
  update_time: string;
  key_id: number;
  api_key: string | null;
  proxy: string | null;
  model: string;
  res_model: string | null;
  provider: string;
  
  // Token 统计 - OpenAI 格式
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  
  // Token 统计 - Anthropic 格式
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens: number;
  cache_read_input_tokens: number;
  
  // 成本与性能
  cost: number;
  latency_ms: number | null;
  
  // 状态信息
  status: string;
  http_status_code: number | null;
  error_type: string | null;
  error_message: string | null;
  
  // 请求和响应内容
  request_body: string | null;
  response_body: string | null;
}

/**
 * 查询参数
 */
export interface QueryLogsParams {
  page?: number;
  page_size?: number;
  key_id?: number;
  api_key?: string;
  status?: string;
  provider?: string;
  model?: string;
  start_time?: string;
  end_time?: string;
}

/**
 * 请求日志管理 API
 */
export const logsApi = {
  /**
   * 获取请求日志列表
   */
  list: (params: QueryLogsParams = {}) => {
    return request.post<PageResponse<RequestLog>>('/api/logs/list', {
      page: params.page || 1,
      page_size: params.page_size || 10,
      key_id: params.key_id,
      api_key: params.api_key,
      status: params.status,
      provider: params.provider,
      model: params.model,
      start_time: params.start_time,
      end_time: params.end_time,
    });
  },
};

