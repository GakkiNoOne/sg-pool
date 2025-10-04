import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  Tag, 
  Typography, 
  Popconfirm,
  message,
  Switch,
  Upload,
  Select,
  DatePicker,
  InputNumber,
  Row,
  Col
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  KeyOutlined,
  CopyOutlined,
  ReloadOutlined,
  UploadOutlined,
  SearchOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile } from 'antd/es/upload/interface';
import dayjs from 'dayjs';
import { keysApi, type APIKey, type CreateAPIKeyRequest, type UpdateAPIKeyRequest, type BatchCheckResult } from '@/api/keys';
import { configsApi } from '@/api/configs';

const { Title } = Typography;

const KeyManagement: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isBatchModalVisible, setIsBatchModalVisible] = useState(false);
  const [editingKey, setEditingKey] = useState<APIKey | null>(null);
  const [form] = Form.useForm();
  const [batchForm] = Form.useForm();
  const [searchForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [dataSource, setDataSource] = useState<APIKey[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [uaList, setUaList] = useState<string[]>([]);
  const [proxyList, setProxyList] = useState<string[]>([]);
  const [loadingUA, setLoadingUA] = useState(false);
  const [loadingProxy, setLoadingProxy] = useState(false);
  // 搜索条件 - 默认只显示启用的 key
  const [searchParams, setSearchParams] = useState<{
    name?: string;
    enabled?: boolean;
    create_date?: string;
  }>({
    enabled: true
  });

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const response = await keysApi.list({
        page,
        page_size: pageSize,
        ...searchParams,
      });
      
      // 响应拦截器已经返回了 response.data，所以这里 response 就是后端的 JSON
      if (response.success && response.data) {
        setDataSource(response.data.items);
        setTotal(response.data.total);
      }
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载UA列表
  const loadUAList = async () => {
    setLoadingUA(true);
    try {
      const response = await configsApi.getUAList();
      if (response.success && response.data) {
        setUaList(response.data);
      }
    } catch (error) {
      console.error('加载UA列表失败:', error);
    } finally {
      setLoadingUA(false);
    }
  };

  // 加载Proxy列表
  const loadProxyList = async () => {
    setLoadingProxy(true);
    try {
      const response = await configsApi.getProxyList();
      if (response.success && response.data) {
        setProxyList(response.data);
      }
    } catch (error) {
      console.error('加载代理列表失败:', error);
    } finally {
      setLoadingProxy(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, pageSize, searchParams]);

  // 处理搜索
  const handleSearch = () => {
    const values = searchForm.getFieldsValue();
    const params: any = {};
    
    if (values.name) params.name = values.name;
    if (values.enabled !== undefined) params.enabled = values.enabled;
    if (values.create_date) {
      params.create_date = values.create_date.format('YYYY-MM-DD');
    }
    
    setSearchParams(params);
    setPage(1); // 重置到第一页
  };

  // 重置搜索
  const handleReset = () => {
    searchForm.resetFields();
    // 重置后也默认显示启用的 key
    searchForm.setFieldsValue({ enabled: true });
    setSearchParams({ enabled: true });
    setPage(1);
  };

  useEffect(() => {
    loadUAList();
    loadProxyList();
    // 设置搜索表单的初始值
    searchForm.setFieldsValue({ enabled: true });
  }, []);

  const handleAdd = () => {
    setEditingKey(null);
    form.resetFields();
    form.setFieldsValue({
      enabled: true,
    });
    setIsModalVisible(true);
  };

  const handleEdit = (record: APIKey) => {
    setEditingKey(record);
    form.setFieldsValue({
      name: record.name,
      api_key: record.api_key,
      ua: record.ua,
      proxy: record.proxy,
      enabled: record.enabled,
      memo: record.memo,
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      const response = await keysApi.delete(id);
      if (response.success) {
        message.success('删除成功');
        loadData();
      }
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();

      if (editingKey) {
        // 编辑 - 只更新允许编辑的字段
        const updateData: UpdateAPIKeyRequest = {
          name: values.name,
          ua: values.ua,
          proxy: values.proxy,
          enabled: values.enabled,
          memo: values.memo,
        };
        const response = await keysApi.update(editingKey.id, updateData);
        if (response.success) {
          message.success('更新成功');
        }
      } else {
        // 新增
        const createData: CreateAPIKeyRequest = {
          name: values.name,
          api_key: values.api_key,
          ua: values.ua,
          proxy: values.proxy,
          enabled: values.enabled,
          memo: values.memo,
        };
        const response = await keysApi.create(createData);
        if (response.success) {
          message.success('创建成功');
        }
      }
      
      setIsModalVisible(false);
      form.resetFields();
      loadData();
    } catch (error) {
      console.error('操作失败:', error);
    }
  };

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    message.success('密钥已复制到剪贴板');
  };

  // 批量导入
  const handleBatchImport = () => {
    batchForm.resetFields();
    setIsBatchModalVisible(true);
  };

  // 批量测活
  const handleBatchCheck = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择需要测活的密钥');
      return;
    }

    Modal.confirm({
      title: '确认批量测活',
      content: `确定要测活选中的 ${selectedRowKeys.length} 个密钥吗？测活失败的密钥将被自动禁用。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        const hide = message.loading('正在测活中...', 0);
        try {
          const response = await keysApi.batchCheck(selectedRowKeys as number[]);
          hide();
          
          if (response.success && response.data) {
            const result = response.data;
            
            // 显示详细结果
            Modal.info({
              title: '批量测活结果',
              width: 600,
              content: (
                <div>
                  <p>总数量：{result.total_count}</p>
                  <p style={{ color: '#52c41a' }}>成功：{result.success_count}</p>
                  <p style={{ color: '#ff4d4f' }}>失败：{result.fail_count}</p>
                  <div style={{ marginTop: 16, maxHeight: 300, overflow: 'auto' }}>
                    {result.results.map((item, index) => (
                      <div key={index} style={{ marginBottom: 8 }}>
                        <Tag color={item.success ? 'green' : 'red'}>
                          {item.success ? '成功' : '失败'}
                        </Tag>
                        <span>{item.key_name}: {item.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ),
            });
            
            // 清空选中项并刷新列表
            setSelectedRowKeys([]);
            loadData();
          }
        } catch (error) {
          hide();
          console.error('批量测活失败:', error);
        }
      },
    });
  };

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择需要删除的密钥');
      return;
    }

    Modal.confirm({
      title: '确认批量删除',
      content: (
        <div>
          <p style={{ color: '#ff4d4f', marginBottom: 8 }}>
            ⚠️ 警告：此操作不可恢复！
          </p>
          <p>确定要删除选中的 {selectedRowKeys.length} 个密钥吗？</p>
        </div>
      ),
      okText: '确定删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        const hide = message.loading('正在删除中...', 0);
        try {
          const response = await keysApi.batchDelete(selectedRowKeys as number[]);
          hide();
          
          if (response.success && response.data) {
            const result = response.data;
            
            if (result.fail_count > 0) {
              message.warning(`删除完成：成功 ${result.success_count} 个，失败 ${result.fail_count} 个`);
            } else {
              message.success(`成功删除 ${result.success_count} 个密钥`);
            }
            
            // 清空选中
            setSelectedRowKeys([]);
            // 刷新列表
            loadData();
          }
        } catch (error) {
          hide();
          console.error('批量删除失败:', error);
          message.error('批量删除失败');
        }
      },
    });
  };

  // 处理批量导入
  const handleBatchModalOk = async () => {
    try {
      const values = await batchForm.validateFields();
      const batchName = values.batchName;
      const keysText = values.keysText;
      
      // 按行分割，过滤空行
      const apiKeys = keysText
        .split('\n')
        .map((line: string) => line.trim())
        .filter((line: string) => line !== '');
      
      if (apiKeys.length === 0) {
        message.error('请输入至少一个API密钥');
        return;
      }
      
      setBatchLoading(true);
      const response = await keysApi.batchCreate(batchName, apiKeys);
      
      if (response.success && response.data) {
        const result = response.data;
        message.success(response.msg);
        
        // 显示详细结果
        Modal.info({
          title: '批量导入结果',
          content: (
            <div>
              <p>总数量：{result.total_count}</p>
              <p style={{ color: '#52c41a' }}>✅ 成功导入：{result.success_count}</p>
              {result.fail_count > 0 && (
                <p style={{ color: '#faad14' }}>
                  ⚠️ 跳过：{result.fail_count}（重复或已存在）
                </p>
              )}
            </div>
          ),
        });
        
        setIsBatchModalVisible(false);
        batchForm.resetFields();
        loadData();
      }
    } catch (error) {
      console.error('批量导入失败:', error);
    } finally {
      setBatchLoading(false);
    }
  };

  // 切换状态
  const handleToggleStatus = (record: APIKey) => {
    const newStatus = !record.enabled;
    const statusText = newStatus ? '启用' : '禁用';
    
    Modal.confirm({
      title: `确认${statusText}`,
      content: `确定要${statusText}密钥 "${record.name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await keysApi.update(record.id, {
            enabled: newStatus,
          });
          if (response.success) {
            message.success(`${statusText}成功`);
            loadData();
          }
        } catch (error) {
          console.error(`${statusText}失败:`, error);
        }
      },
    });
  };

  const getStatusTag = (enabled: boolean, record: APIKey) => {
    return (
      <Tag 
        color={enabled ? "green" : "red"}
        style={{ cursor: 'pointer' }}
        onClick={() => handleToggleStatus(record)}
      >
        {enabled ? '启用' : '禁用'}
      </Tag>
    );
  };

  const columns: ColumnsType<APIKey> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      fixed: 'left' as const,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '密钥名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text) => (
        <Space>
          <KeyOutlined />
          <span style={{ fontWeight: 'bold' }}>{text}</span>
        </Space>
      ),
    },
    {
      title: '密钥',
      dataIndex: 'api_key',
      key: 'api_key',
      width: 200,
      ellipsis: true,
      render: (key) => (
        <Space>
          <code style={{ 
            background: '#f5f5f5', 
            padding: '2px 6px', 
            borderRadius: '4px',
            fontSize: '12px'
          }}>
            {key.substring(0, 20)}...
          </code>
          <Button 
            type="text" 
            size="small" 
            icon={<CopyOutlined />}
            onClick={() => handleCopyKey(key)}
          />
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled, record) => getStatusTag(enabled, record),
    },
    {
      title: '错误代码',
      dataIndex: 'error_code',
      key: 'error_code',
      width: 120,
      render: (errorCode) => {
        if (!errorCode) {
          return <span style={{ color: '#999' }}>-</span>;
        }
        return (
          <Tag color="red" style={{ fontFamily: 'monospace' }}>
            {errorCode}
          </Tag>
        );
      },
    },
    {
      title: 'UA',
      dataIndex: 'ua',
      key: 'ua',
      width: 150,
      ellipsis: true,
    },
    {
      title: '代理',
      dataIndex: 'proxy',
      key: 'proxy',
      width: 150,
    },
    {
      title: '当前余额',
      dataIndex: 'balance',
      key: 'balance',
      width: 100,
      render: (balance) => balance !== null ? `$${balance}` : '-',
    },
    {
      title: '总额度',
      dataIndex: 'total_balance',
      key: 'total_balance',
      width: 100,
      render: (total) => total !== null ? `$${total}` : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个密钥吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              size="small"
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      {/* 搜索表单 */}
      <Card 
        size="small" 
        style={{ marginBottom: 16, background: '#fafafa' }}
        title={
          <Space>
            <SearchOutlined />
            <span>搜索筛选</span>
          </Space>
        }
      >
        <Form form={searchForm} layout="inline">
          <Row gutter={16} style={{ width: '100%' }}>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="name" label="名称" style={{ marginBottom: 8 }}>
                <Input placeholder="输入密钥名称" allowClear />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="enabled" label="状态" style={{ marginBottom: 8 }}>
                <Select placeholder="选择状态" allowClear style={{ width: '100%' }}>
                  <Select.Option value={true}>启用</Select.Option>
                  <Select.Option value={false}>禁用</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="create_date" label="创建日期" style={{ marginBottom: 8 }}>
                <DatePicker 
                  placeholder="选择日期" 
                  style={{ width: '100%' }}
                  format="YYYY-MM-DD"
                  allowClear
                />
              </Form.Item>
            </Col>
          </Row>
          <Row style={{ marginTop: 8 }}>
            <Col span={24}>
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                  搜索
                </Button>
                <Button onClick={handleReset}>
                  重置
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>
      </Card>

      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24 
      }}>
        <div>
          <Title level={2} style={{ marginBottom: 8 }}>Key管理</Title>
          {selectedRowKeys.length > 0 && (
            <div style={{ fontSize: 14, color: '#666' }}>
              已选择 {selectedRowKeys.length} 项
            </div>
          )}
        </div>
        <Space>
          <Button 
            icon={<ReloadOutlined />}
            onClick={loadData}
          >
            刷新
          </Button>
          <Button 
            icon={<UploadOutlined />}
            onClick={handleBatchImport}
          >
            批量导入
          </Button>
          <Button
            type="default"
            disabled={selectedRowKeys.length === 0}
            onClick={handleBatchCheck}
          >
            批量测活 ({selectedRowKeys.length})
          </Button>
          <Button
            type="default"
            danger
            disabled={selectedRowKeys.length === 0}
            onClick={handleBatchDelete}
          >
            批量删除 ({selectedRowKeys.length})
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            创建密钥
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={dataSource}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1620 }}
        rowSelection={{
          selectedRowKeys,
          onChange: (selectedRowKeys) => {
            setSelectedRowKeys(selectedRowKeys);
          },
          preserveSelectedRowKeys: true,
        }}
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

      <Modal
        title={editingKey ? '编辑密钥' : '创建密钥'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        width={600}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            enabled: true,
          }}
        >
          <Form.Item
            name="name"
            label="密钥名称"
            rules={[{ required: true, message: '请输入密钥名称' }]}
          >
            <Input placeholder="请输入密钥名称" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API密钥"
            rules={[{ required: !editingKey, message: '请输入API密钥' }]}
          >
            <Input.TextArea 
              rows={3} 
              placeholder={editingKey ? '只读显示' : '请输入API密钥'}
              disabled={!!editingKey}
              style={editingKey ? { color: '#666', cursor: 'not-allowed' } : {}}
            />
          </Form.Item>

          <Form.Item
            name="ua"
            label="User Agent"
            rules={[{ required: true, message: '请选择User Agent' }]}
          >
            <Select
              placeholder="请选择User Agent"
              loading={loadingUA}
              showSearch
              optionFilterProp="children"
              allowClear
            >
              {uaList.map((ua, index) => (
                <Select.Option key={index} value={ua}>
                  {ua}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="proxy"
            label="代理"
          >
            <Select
              placeholder="代理可选，不配置则使用本机ip去请求"
              loading={loadingProxy}
              showSearch
              optionFilterProp="children"
              allowClear
            >
              {proxyList.map((proxy, index) => (
                <Select.Option key={index} value={proxy}>
                  {proxy}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="enabled"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item
            name="memo"
            label="备注说明"
          >
            <Input.TextArea 
              rows={3} 
              placeholder="请输入备注说明" 
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量导入弹窗 */}
      <Modal
        title="批量导入密钥"
        open={isBatchModalVisible}
        onOk={handleBatchModalOk}
        onCancel={() => {
          setIsBatchModalVisible(false);
          batchForm.resetFields();
        }}
        width={800}
        okText="导入"
        cancelText="取消"
        confirmLoading={batchLoading}
      >
        <Form
          form={batchForm}
          layout="vertical"
        >
          <Form.Item
            name="batchName"
            label="批次名称"
            rules={[{ required: true, message: '请输入批次名称' }]}
            extra="为这一批密钥设置统一的名称前缀，例如：test-key，系统会自动生成 test-key-1, test-key-2..."
          >
            <Input placeholder="例如：test-key" />
          </Form.Item>

          <Form.Item
            name="keysText"
            label="API 密钥列表"
            rules={[{ required: true, message: '请输入 API 密钥' }]}
            extra={
              <div style={{ marginTop: 8 }}>
                <div style={{ color: '#666', fontSize: 12 }}>
                  每行一个 API 密钥，系统会自动：<br />
                  • <strong style={{ color: '#52c41a' }}>自动去重</strong>（跳过已存在和重复的密钥）<br />
                  • 使用批次名称 + 序号作为密钥名称<br />
                  • 默认余额：10，默认总额：10<br />
                  • 默认状态：启用<br />
                  • 从配置中随机选择 UA 和代理
                </div>
                <div style={{ marginTop: 8 }}>格式示例：</div>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  fontSize: 12,
                  marginTop: 8 
                }}>
{`sk-ant-api03-xxx
sk-ant-api03-yyy
sk-ant-api03-zzz`}
                </pre>
              </div>
            }
          >
            <Input.TextArea 
              rows={12} 
              placeholder="每行粘贴一个 API 密钥&#10;例如：&#10;sk-ant-api03-xxx&#10;sk-ant-api03-yyy&#10;sk-ant-api03-zzz"
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default KeyManagement;
