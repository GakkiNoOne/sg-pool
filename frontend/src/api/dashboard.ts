/**
 * Dashboard API
 */

import request, { BaseResponse } from '@/utils/request';

/**
 * 今日总览数据
 */
export interface TodayOverview {
  request_count: number;
  success_count: number;
  error_count: number;
  success_rate: number;
  total_cost: number;
  total_tokens: number;
  avg_latency_ms: number;
}

/**
 * 小时趋势数据
 */
export interface HourlyTrend {
  hour: string;
  request_count: number;
  success_count: number;
  error_count: number;
  total_cost: number;
  total_tokens: number;
}

/**
 * 提供商分布数据
 */
export interface ProviderDistribution {
  provider: string;
  request_count: number;
  success_rate: number;
  total_cost: number;
  total_tokens: number;
}

/**
 * 模型分布数据
 */
export interface ModelDistribution {
  model: string;
  provider: string;
  request_count: number;
  total_cost: number;
  total_tokens: number;
  avg_latency_ms: number;
}

/**
 * 错误分布数据
 */
export interface ErrorDistribution {
  error_type: string;
  count: number;
}

/**
 * 错误统计数据
 */
export interface ErrorStats {
  total_errors: number;
  error_distribution: ErrorDistribution[];
}

/**
 * Key 余额统计数据
 */
export interface KeyBalanceStats {
  total_keys: number;
  enabled_keys: number;
  total_balance: number;
  keys_with_balance: number;
}

/**
 * Dashboard API
 */
export const dashboardApi = {
  /**
   * 获取今日总览
   */
  getOverview: () => {
    return request.post<BaseResponse<TodayOverview>>('/api/dashboard/overview', {});
  },

  /**
   * 获取小时趋势
   */
  getHourlyTrend: () => {
    return request.post<BaseResponse<HourlyTrend[]>>('/api/dashboard/hourly-trend', {});
  },

  /**
   * 获取提供商分布
   */
  getProviderDistribution: () => {
    return request.post<BaseResponse<ProviderDistribution[]>>('/api/dashboard/provider-distribution', {});
  },

  /**
   * 获取模型分布
   */
  getModelDistribution: () => {
    return request.post<BaseResponse<ModelDistribution[]>>('/api/dashboard/model-distribution', {});
  },

  /**
   * 获取错误统计
   */
  getErrorStats: () => {
    return request.post<BaseResponse<ErrorStats>>('/api/dashboard/error-stats', {});
  },

  /**
   * 手动触发统计
   */
  triggerStats: () => {
    return request.post<BaseResponse<void>>('/api/dashboard/trigger-stats', {});
  },

  /**
   * 获取 Key 余额统计
   */
  getKeyBalanceStats: () => {
    return request.post<BaseResponse<KeyBalanceStats>>('/api/dashboard/key-balance-stats', {});
  },

  /**
   * 手动更新 Key 余额
   */
  updateKeysBalance: () => {
    return request.post<BaseResponse<{
      total_keys: number;
      updated_keys: number;
      failed_keys: number;
      errors: string[];
    }>>('/api/dashboard/update-keys-balance', {});
  },
};

