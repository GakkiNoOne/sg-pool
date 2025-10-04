import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Table,
  Button,
  message,
  Spin,
  Tag,
  Space,
  Divider
} from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DollarOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { dashboardApi, type TodayOverview, type ModelDistribution, type ProviderDistribution, type ErrorStats, type KeyBalanceStats } from '@/api/dashboard';

const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<TodayOverview | null>(null);
  const [modelDistribution, setModelDistribution] = useState<ModelDistribution[]>([]);
  const [providerDistribution, setProviderDistribution] = useState<ProviderDistribution[]>([]);
  const [errorStats, setErrorStats] = useState<ErrorStats | null>(null);
  const [keyBalanceStats, setKeyBalanceStats] = useState<KeyBalanceStats | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // 加载所有数据
  const loadData = async () => {
    setLoading(true);
    try {
      const [overviewRes, modelRes, providerRes, errorRes, keyBalanceRes] = await Promise.all([
        dashboardApi.getOverview(),
        dashboardApi.getModelDistribution(),
        dashboardApi.getProviderDistribution(),
        dashboardApi.getErrorStats(),
        dashboardApi.getKeyBalanceStats(),
      ]);

      if (overviewRes.success) {
        setOverview(overviewRes.data);
      }
      if (modelRes.success) {
        setModelDistribution(modelRes.data || []);
      }
      if (providerRes.success) {
        setProviderDistribution(providerRes.data || []);
      }
      if (errorRes.success) {
        setErrorStats(errorRes.data);
      }
      if (keyBalanceRes.success) {
        setKeyBalanceStats(keyBalanceRes.data);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // 每30秒自动刷新
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // 手动触发统计
  const handleTriggerStats = async () => {
    setRefreshing(true);
    try {
      const response = await dashboardApi.triggerStats();
      if (response.success) {
        message.success('统计任务已触发，请稍后刷新查看');
        // 5秒后自动刷新数据
        setTimeout(loadData, 5000);
      }
    } catch (error) {
      console.error('触发统计失败:', error);
      message.error('触发统计失败');
    } finally {
      setRefreshing(false);
    }
  };

  // 手动更新 Key 余额
  const handleUpdateBalance = async () => {
    setRefreshing(true);
    try {
      const response = await dashboardApi.updateKeysBalance();
      if (response.success) {
        const { updated_keys, failed_keys } = response.data;
        if (failed_keys > 0) {
          message.warning(`余额更新完成，成功 ${updated_keys} 个，失败 ${failed_keys} 个`);
        } else {
          message.success(`余额更新成功，共更新 ${updated_keys} 个 Key`);
        }
        // 立即刷新数据
        loadData();
      }
    } catch (error) {
      console.error('更新余额失败:', error);
      message.error('更新余额失败');
    } finally {
      setRefreshing(false);
    }
  };

  // 模型分布表格列
  const modelColumns: ColumnsType<ModelDistribution> = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_, __, index) => index + 1,
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      width: 200,
      render: (model) => (
        <code style={{ 
          fontSize: '12px',
          background: '#f5f5f5',
          padding: '2px 6px',
          borderRadius: '4px'
        }}>
          {model}
        </code>
      ),
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      width: 100,
      render: (provider) => {
        const colors: Record<string, string> = {
          openai: 'blue',
          anthropic: 'purple',
        };
        return <Tag color={colors[provider] || 'default'}>{provider}</Tag>;
      },
    },
    {
      title: '请求数',
      dataIndex: 'request_count',
      key: 'request_count',
      width: 100,
      render: (count) => count.toLocaleString(),
    },
    {
      title: '总成本',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 100,
      render: (cost) => `$${cost.toFixed(4)}`,
    },
    {
      title: '总Token',
      dataIndex: 'total_tokens',
      key: 'total_tokens',
      width: 120,
      render: (tokens) => tokens.toLocaleString(),
    },
    {
      title: '平均延迟',
      dataIndex: 'avg_latency_ms',
      key: 'avg_latency_ms',
      width: 100,
      render: (latency) => latency ? `${latency}ms` : '-',
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24 
      }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
          📊 Dashboard
        </h1>
        <Space>
          <Button 
            icon={<ThunderboltOutlined />}
            onClick={handleTriggerStats}
            loading={refreshing}
          >
            立即统计
          </Button>
          <Button 
            type="primary"
            icon={<ReloadOutlined />}
            onClick={loadData}
            loading={loading}
          >
            刷新数据
          </Button>
        </Space>
      </div>

      <Spin spinning={loading}>
        {/* 今日总览 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总请求数"
                value={overview?.request_count || 0}
                prefix={<ApiOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="成功率"
                value={overview?.success_rate || 0}
                suffix="%"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
                precision={2}
              />
              <div style={{ marginTop: 8, fontSize: '12px', color: '#999' }}>
                成功: {overview?.success_count || 0} / 失败: {overview?.error_count || 0}
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总成本"
                value={overview?.total_cost || 0}
                prefix={<DollarOutlined />}
                precision={4}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="平均延迟"
                value={overview?.avg_latency_ms || 0}
                suffix="ms"
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
              <div style={{ marginTop: 8, fontSize: '12px', color: '#999' }}>
                总Token: {(overview?.total_tokens || 0).toLocaleString()}
              </div>
            </Card>
          </Col>
        </Row>

        {/* Key 余额统计 */}
        <Card 
          title="💳 API Key 余额统计" 
          style={{ marginBottom: 24 }}
          extra={
            <Space>
              <Tag color="green">实时数据</Tag>
              <Button 
                size="small"
                icon={<ReloadOutlined />}
                onClick={handleUpdateBalance}
                loading={refreshing}
              >
                更新余额
              </Button>
            </Space>
          }
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card size="small" style={{ textAlign: 'center', background: '#f0f5ff' }}>
                <Statistic
                  title="总 Key 数量"
                  value={keyBalanceStats?.total_keys || 0}
                  valueStyle={{ color: '#1890ff', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card size="small" style={{ textAlign: 'center', background: '#f6ffed' }}>
                <Statistic
                  title="可用 Key 数量"
                  value={keyBalanceStats?.enabled_keys || 0}
                  valueStyle={{ color: '#52c41a', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card size="small" style={{ textAlign: 'center', background: '#fffbe6' }}>
                <Statistic
                  title="可用 Key 总余额"
                  value={keyBalanceStats?.total_balance || 0}
                  prefix={<DollarOutlined />}
                  precision={2}
                  valueStyle={{ color: '#faad14', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card size="small" style={{ textAlign: 'center', background: '#fff7e6' }}>
                <Statistic
                  title="有余额的 Key"
                  value={keyBalanceStats?.keys_with_balance || 0}
                  valueStyle={{ color: '#fa8c16', fontSize: '28px', fontWeight: 'bold' }}
                />
                <div style={{ marginTop: 8, fontSize: '12px', color: '#999' }}>
                  占可用 Key: {keyBalanceStats?.enabled_keys && keyBalanceStats?.keys_with_balance 
                    ? `${((keyBalanceStats.keys_with_balance / keyBalanceStats.enabled_keys) * 100).toFixed(1)}%` 
                    : '0%'}
                </div>
              </Card>
            </Col>
          </Row>
        </Card>

        {/* 提供商分布 */}
        <Card 
          title="提供商分布" 
          style={{ marginBottom: 24 }}
          extra={<Tag color="blue">今日数据</Tag>}
        >
          <Row gutter={[16, 16]}>
            {providerDistribution.map((item) => (
              <Col xs={24} sm={12} lg={8} key={item.provider}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: 8 }}>
                    <Tag color={item.provider === 'openai' ? 'blue' : 'purple'} style={{ fontSize: '14px' }}>
                      {item.provider.toUpperCase()}
                    </Tag>
                  </div>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic
                        title="请求数"
                        value={item.request_count}
                        valueStyle={{ fontSize: '18px' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="成功率"
                        value={item.success_rate}
                        suffix="%"
                        precision={1}
                        valueStyle={{ fontSize: '18px', color: '#52c41a' }}
                      />
                    </Col>
                  </Row>
                  <Divider style={{ margin: '12px 0' }} />
                  <Row gutter={16}>
                    <Col span={12}>
                      <div style={{ fontSize: '12px', color: '#999' }}>总成本</div>
                      <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                        ${item.total_cost.toFixed(4)}
                      </div>
                    </Col>
                    <Col span={12}>
                      <div style={{ fontSize: '12px', color: '#999' }}>总Token</div>
                      <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                        {item.total_tokens.toLocaleString()}
                      </div>
                    </Col>
                  </Row>
                </Card>
              </Col>
            ))}
            {providerDistribution.length === 0 && (
              <Col span={24}>
                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                  暂无数据
                </div>
              </Col>
            )}
          </Row>
        </Card>

        {/* 模型使用排行 */}
        <Card 
          title="模型使用排行 Top 10" 
          style={{ marginBottom: 24 }}
          extra={<Tag color="green">今日数据</Tag>}
        >
          <Table
            columns={modelColumns}
            dataSource={modelDistribution}
            rowKey="model"
            pagination={false}
            size="small"
            locale={{ emptyText: '暂无数据' }}
          />
        </Card>

        {/* 错误统计 */}
        <Card 
          title={
            <Space>
              错误统计
              {errorStats && errorStats.total_errors > 0 && (
                <Tag color="red" icon={<CloseCircleOutlined />}>
                  {errorStats.total_errors} 个错误
                </Tag>
              )}
            </Space>
          }
          extra={<Tag color="orange">今日数据</Tag>}
        >
          {errorStats && errorStats.total_errors > 0 ? (
            <Row gutter={[16, 16]}>
              {errorStats.error_distribution.map((item) => (
                <Col xs={24} sm={12} lg={8} key={item.error_type}>
                  <Card size="small" hoverable>
                    <Statistic
                      title={
                        <div style={{ 
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {item.error_type}
                        </div>
                      }
                      value={item.count}
                      valueStyle={{ color: '#ff4d4f', fontSize: '20px' }}
                      suffix="次"
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <CheckCircleOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
              <div style={{ marginTop: 16, fontSize: '16px', color: '#52c41a' }}>
                太棒了！今日暂无错误
              </div>
            </div>
          )}
        </Card>

        {/* 页面底部说明 */}
        <Card size="small" style={{ background: '#fafafa', marginTop: 24 }}>
          <div style={{ fontSize: '12px', color: '#999', textAlign: 'center' }}>
            📌 数据每5分钟自动统计一次，页面每30秒自动刷新 | 点击"立即统计"可手动触发统计任务
          </div>
        </Card>
      </Spin>
    </div>
  );
};

export default DashboardPage;
