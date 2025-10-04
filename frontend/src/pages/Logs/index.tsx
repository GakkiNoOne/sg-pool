import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Typography, 
  message,
  Form,
  Input,
  Select,
  Tooltip,
  Descriptions,
  Modal,
  DatePicker
} from 'antd';
import { 
  ReloadOutlined,
  SearchOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  CopyOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { logsApi, type RequestLog } from '@/api/logs';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const RequestLogsPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [dataSource, setDataSource] = useState<RequestLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedLog, setSelectedLog] = useState<RequestLog | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // 查询参数
  const [filters, setFilters] = useState<{
    api_key?: string;
    status?: string;
    provider?: string;
    model?: string;
    start_time?: string;
    end_time?: string;
  }>({});

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const response = await logsApi.list({
        page,
        page_size: pageSize,
        ...filters,
      });
      
      if (response.success && response.data) {
        setDataSource(response.data.items);
        setTotal(response.data.total);
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
  }, [page, pageSize, filters]);

  // 搜索
  const handleSearch = () => {
    const values = form.getFieldsValue();
    
    // 处理时间范围
    let start_time: string | undefined;
    let end_time: string | undefined;
    
    if (values.timeRange && values.timeRange.length === 2) {
      start_time = values.timeRange[0].format('YYYY-MM-DD HH:mm:ss');
      end_time = values.timeRange[1].format('YYYY-MM-DD HH:mm:ss');
    }
    
    setFilters({
      api_key: values.api_key,
      status: values.status,
      provider: values.provider,
      model: values.model,
      start_time,
      end_time,
    });
    setPage(1); // 重置到第一页
  };

  // 重置
  const handleReset = () => {
    form.resetFields();
    setFilters({});
    setPage(1);
  };

  // 查看详情
  const handleViewDetail = (record: RequestLog) => {
    setSelectedLog(record);
    setDetailModalVisible(true);
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    switch (status) {
      case 'success':
        return <Tag icon={<CheckCircleOutlined />} color="success">成功</Tag>;
      case 'error':
        return <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>;
      default:
        return <Tag icon={<ClockCircleOutlined />} color="default">{status}</Tag>;
    }
  };

  // 获取提供商标签
  const getProviderTag = (provider: string) => {
    const colors: Record<string, string> = {
      openai: 'blue',
      anthropic: 'purple',
    };
    return <Tag color={colors[provider] || 'default'}>{provider}</Tag>;
  };

  // 格式化延迟
  const formatLatency = (latency: number | null) => {
    if (latency === null) return '-';
    if (latency < 1000) {
      return `${latency}ms`;
    }
    return `${(latency / 1000).toFixed(2)}s`;
  };

  // 格式化 JSON
  const formatJSON = (jsonString: string | null) => {
    if (!jsonString) return null;
    try {
      const obj = JSON.parse(jsonString);
      return JSON.stringify(obj, null, 2);
    } catch {
      return jsonString;
    }
  };

  // 复制内容
  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    message.success('已复制到剪贴板');
  };

  const columns: ColumnsType<RequestLog> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
      fixed: 'left' as const,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 160,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: 'API Key',
      dataIndex: 'api_key',
      key: 'api_key',
      width: 200,
      ellipsis: true,
      render: (apiKey) => {
        if (!apiKey) return '-';
        return (
          <Tooltip title={apiKey}>
            <code style={{ 
              fontSize: '12px',
              background: '#f5f5f5',
              padding: '2px 6px',
              borderRadius: '4px'
            }}>
              {apiKey.substring(0, 20)}...
            </code>
          </Tooltip>
        );
      },
    },
    {
      title: 'Proxy',
      dataIndex: 'proxy',
      key: 'proxy',
      width: 150,
      ellipsis: true,
      render: (proxy) => proxy || '-',
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      width: 100,
      render: (provider) => getProviderTag(provider),
    },
    {
      title: '请求模型',
      dataIndex: 'model',
      key: 'model',
      width: 180,
      ellipsis: true,
      render: (model) => (
        <Tooltip title={model}>
          <code style={{ 
            fontSize: '12px',
            background: '#f5f5f5',
            padding: '2px 6px',
            borderRadius: '4px'
          }}>
            {model}
          </code>
        </Tooltip>
      ),
    },
    {
      title: '响应模型',
      dataIndex: 'res_model',
      key: 'res_model',
      width: 180,
      ellipsis: true,
      render: (resModel) => {
        if (!resModel) return '-';
        return (
          <Tooltip title={resModel}>
            <code style={{ 
              fontSize: '12px',
              background: '#e6f7ff',
              padding: '2px 6px',
              borderRadius: '4px',
              color: '#1890ff'
            }}>
              {resModel}
            </code>
          </Tooltip>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status) => getStatusTag(status),
    },
    {
      title: '延迟',
      dataIndex: 'latency_ms',
      key: 'latency_ms',
      width: 100,
      render: (latency) => {
        const formatted = formatLatency(latency);
        const color = latency !== null && latency > 5000 ? 'warning' : 'default';
        return <Text type={color}>{formatted}</Text>;
      },
    },
    {
      title: 'Total Tokens',
      dataIndex: 'total_tokens',
      key: 'total_tokens',
      width: 120,
      render: (_, record) => {
        const total = record.total_tokens || 
          (record.input_tokens + record.output_tokens) ||
          (record.prompt_tokens + record.completion_tokens);
        return <Text strong>{total.toLocaleString()}</Text>;
      },
    },
    {
      title: '成本',
      dataIndex: 'cost',
      key: 'cost',
      width: 100,
      render: (cost) => (
        <Text type={cost > 0 ? 'warning' : 'secondary'}>
          ${cost.toFixed(6)}
        </Text>
      ),
    },
    {
      title: 'Prompt Tokens',
      dataIndex: 'prompt_tokens',
      key: 'prompt_tokens',
      width: 120,
      render: (value) => value > 0 ? value.toLocaleString() : '-',
    },
    {
      title: 'Completion Tokens',
      dataIndex: 'completion_tokens',
      key: 'completion_tokens',
      width: 140,
      render: (value) => value > 0 ? value.toLocaleString() : '-',
    },
    {
      title: 'Input Tokens',
      dataIndex: 'input_tokens',
      key: 'input_tokens',
      width: 120,
      render: (value) => value > 0 ? value.toLocaleString() : '-',
    },
    {
      title: 'Output Tokens',
      dataIndex: 'output_tokens',
      key: 'output_tokens',
      width: 120,
      render: (value) => value > 0 ? value.toLocaleString() : '-',
    },
    {
      title: 'Cache Create',
      dataIndex: 'cache_creation_input_tokens',
      key: 'cache_creation_input_tokens',
      width: 120,
      render: (value) => value > 0 ? value.toLocaleString() : '-',
    },
    {
      title: 'Cache Read',
      dataIndex: 'cache_read_input_tokens',
      key: 'cache_read_input_tokens',
      width: 110,
      render: (value) => value > 0 ? value.toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 90,
      fixed: 'right' as const,
      render: (_, record) => (
        <Button 
          type="link" 
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24 
      }}>
        <Title level={2}>请求日志</Title>
        <Button 
          icon={<ReloadOutlined />}
          onClick={loadData}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      {/* 搜索表单 */}
      <Card style={{ marginBottom: 16 }} size="small">
        <Form
          form={form}
          layout="inline"
          onFinish={handleSearch}
        >
          <Form.Item name="timeRange" label="时间范围">
            <RangePicker 
              showTime={{ format: 'HH:mm' }}
              format="YYYY-MM-DD HH:mm"
              placeholder={['开始时间', '结束时间']}
              style={{ width: 360 }}
            />
          </Form.Item>
          
          <Form.Item name="api_key" label="API Key">
            <Input 
              placeholder="请输入API Key关键词" 
              style={{ width: 200 }}
            />
          </Form.Item>
          
          <Form.Item name="status" label="状态">
            <Select 
              placeholder="选择状态" 
              style={{ width: 120 }}
              allowClear
            >
              <Option value="success">成功</Option>
              <Option value="error">失败</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="provider" label="提供商">
            <Select 
              placeholder="选择提供商" 
              style={{ width: 120 }}
              allowClear
            >
              <Option value="openai">OpenAI</Option>
              <Option value="anthropic">Anthropic</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="model" label="模型">
            <Input 
              placeholder="请输入模型名称" 
              style={{ width: 200 }}
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit"
                icon={<SearchOutlined />}
              >
                搜索
              </Button>
              <Button onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Table
        columns={columns}
        dataSource={dataSource}
        rowKey="id"
        loading={loading}
        scroll={{ x: 2750 }}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
          onChange: (page, pageSize) => {
            setPage(page);
            setPageSize(pageSize);
          },
        }}
      />

      {/* 详情弹窗 */}
      <Modal
        title="请求日志详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        {selectedLog && (
          <>
            <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="ID" span={1}>
              {selectedLog.id}
            </Descriptions.Item>
            <Descriptions.Item label="状态" span={1}>
              {getStatusTag(selectedLog.status)}
            </Descriptions.Item>
            
            <Descriptions.Item label="创建时间" span={2}>
              {dayjs(selectedLog.create_time).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            
            <Descriptions.Item label="API Key" span={2}>
              {selectedLog.api_key ? (
                <code style={{ fontSize: '12px', wordBreak: 'break-all' }}>
                  {selectedLog.api_key}
                </code>
              ) : '-'}
            </Descriptions.Item>
            
            <Descriptions.Item label="提供商" span={1}>
              {getProviderTag(selectedLog.provider)}
            </Descriptions.Item>
            <Descriptions.Item label="请求模型" span={1}>
              <code style={{ fontSize: '12px' }}>{selectedLog.model}</code>
            </Descriptions.Item>
            
            <Descriptions.Item label="响应模型" span={2}>
              {selectedLog.res_model ? (
                <code style={{ fontSize: '12px', color: '#1890ff' }}>{selectedLog.res_model}</code>
              ) : '-'}
            </Descriptions.Item>
            
            <Descriptions.Item label="代理" span={2}>
              {selectedLog.proxy || '-'}
            </Descriptions.Item>
            
            <Descriptions.Item label="HTTP状态码" span={1}>
              {selectedLog.http_status_code || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="延迟" span={1}>
              {formatLatency(selectedLog.latency_ms)}
            </Descriptions.Item>
            
            <Descriptions.Item label="成本" span={2}>
              <Text strong>${selectedLog.cost.toFixed(6)}</Text>
            </Descriptions.Item>
            
            {/* Token 信息 - OpenAI 格式 */}
            {selectedLog.provider === 'openai' && (
              <>
                <Descriptions.Item label="Prompt Tokens" span={1}>
                  {selectedLog.prompt_tokens.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Completion Tokens" span={1}>
                  {selectedLog.completion_tokens.toLocaleString()}
                </Descriptions.Item>
              </>
            )}
            
            {/* Token 信息 - Anthropic 格式 */}
            {selectedLog.provider === 'anthropic' && (
              <>
                <Descriptions.Item label="Input Tokens" span={1}>
                  {selectedLog.input_tokens.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Output Tokens" span={1}>
                  {selectedLog.output_tokens.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Cache Creation Tokens" span={1}>
                  {selectedLog.cache_creation_input_tokens.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Cache Read Tokens" span={1}>
                  {selectedLog.cache_read_input_tokens.toLocaleString()}
                </Descriptions.Item>
              </>
            )}
            
            <Descriptions.Item label="Total Tokens" span={2}>
              <Text strong>
                {(selectedLog.total_tokens || 
                  selectedLog.input_tokens + selectedLog.output_tokens ||
                  selectedLog.prompt_tokens + selectedLog.completion_tokens
                ).toLocaleString()}
              </Text>
            </Descriptions.Item>
            
            {/* 错误信息 */}
            {selectedLog.status === 'error' && (
              <>
                <Descriptions.Item label="错误类型" span={2}>
                  <Text type="danger">{selectedLog.error_type || '-'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="错误信息" span={2}>
                  <Text type="danger" style={{ wordBreak: 'break-word' }}>
                    {selectedLog.error_message || '-'}
                  </Text>
                </Descriptions.Item>
              </>
            )}
          </Descriptions>
          
          {/* 请求内容 */}
          {selectedLog.request_body && (
            <div style={{ marginTop: 24 }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: 8 
              }}>
                <Text strong>请求内容</Text>
                <Button 
                  size="small" 
                  icon={<CopyOutlined />}
                  onClick={() => handleCopy(formatJSON(selectedLog.request_body) || '')}
                >
                  复制
                </Button>
              </div>
              <pre style={{ 
                background: '#f5f5f5', 
                padding: 12, 
                borderRadius: 4,
                maxHeight: 300,
                overflow: 'auto',
                fontSize: 12
              }}>
                {formatJSON(selectedLog.request_body)}
              </pre>
            </div>
          )}
          
          {/* 响应内容 */}
          {selectedLog.response_body && (
            <div style={{ marginTop: 24 }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: 8 
              }}>
                <Text strong>响应内容</Text>
                <Button 
                  size="small" 
                  icon={<CopyOutlined />}
                  onClick={() => handleCopy(formatJSON(selectedLog.response_body) || '')}
                >
                  复制
                </Button>
              </div>
              <pre style={{ 
                background: '#e6f7ff', 
                padding: 12, 
                borderRadius: 4,
                maxHeight: 300,
                overflow: 'auto',
                fontSize: 12
              }}>
                {formatJSON(selectedLog.response_body)}
              </pre>
            </div>
          )}
          </>
        )}
      </Modal>
    </Card>
  );
};

export default RequestLogsPage;

