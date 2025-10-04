import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Form,
  Input,
  InputNumber,
  Typography,
  message,
  Divider,
  Alert,
  Spin,
  Select,
  Switch,
  Modal,
  Row,
  Col
} from 'antd';
import {
  SaveOutlined,
  SettingOutlined,
  LockOutlined
} from '@ant-design/icons';
import { configsApi, SystemConfigsResponse } from '@/api/configs';

const { Title, Text } = Typography;
const { TextArea } = Input;

const ConfigManagement: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [systemConfig, setSystemConfig] = useState<any>(null); // 存储系统核心配置

  // 加载配置
  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await configsApi.getSystemConfigs();

      if (response.success && response.data) {
        const { configs } = response.data;
        
        // 提取系统核心配置
        if (configs.system_config) {
          try {
            const sysConfig = JSON.parse(configs.system_config);
            setSystemConfig(sysConfig);
          } catch (e) {
            console.error('解析系统配置失败:', e);
          }
        }
        
        // 解析 JSON 字段
        const uaList = configs.ua_list ? JSON.parse(configs.ua_list) : [];
        const proxyList = configs.proxy_list ? JSON.parse(configs.proxy_list) : [];
        const openaiModels = configs.openai_models ? JSON.parse(configs.openai_models) : [];
        const anthropicModels = configs.anthropic_models ? JSON.parse(configs.anthropic_models) : [];
        
        form.setFieldsValue({
          key_pool_size: parseInt(configs.key_pool_size) || 5,
          key_selection_strategy: configs.key_selection_strategy || '0',
          ua_list: uaList.join('\n'),
          proxy_list: proxyList.join('\n'),
          log_conversation_content: configs.log_conversation_content === 'true',
          openai_models: openaiModels,  // 直接使用数组
          anthropic_models: anthropicModels,  // 直接使用数组
        });
      }
    } catch (error) {
      console.error('加载配置失败:', error);
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      // 显示确认对话框
      Modal.confirm({
        title: '确认保存配置',
        content: (
          <div>
            <p>保存配置后，系统将自动检查所有启用的 API Key：</p>
            <ul style={{ marginTop: 8, paddingLeft: 20 }}>
              <li>如果 Key 的 UA 不在新配置中，将随机选择一个新的 UA</li>
              <li>如果 Key 的代理不在新配置中，将随机选择一个新的代理</li>
            </ul>
            <p style={{ marginTop: 8, color: '#ff4d4f' }}>
              此操作将影响所有启用的 Key，确定要继续吗？
            </p>
          </div>
        ),
        okText: '确定保存',
        cancelText: '取消',
        onOk: async () => {
          setSaving(true);
          try {
            // 处理 UA 列表和代理列表
            const uaList = values.ua_list
              .split('\n')
              .map((line: string) => line.trim())
              .filter((line: string) => line !== '');
            
            const proxyList = values.proxy_list
              ? values.proxy_list
                  .split('\n')
                  .map((line: string) => line.trim())
                  .filter((line: string) => line !== '')
              : [];
            
            // 模型列表已经是数组格式，直接使用
            const openaiModels = values.openai_models || [];
            const anthropicModels = values.anthropic_models || [];

            // 构建配置对象
            const configs: Record<string, string> = {
              key_pool_size: values.key_pool_size.toString(),
              key_selection_strategy: values.key_selection_strategy,
              ua_list: JSON.stringify(uaList),
              proxy_list: JSON.stringify(proxyList),
              log_conversation_content: values.log_conversation_content ? 'true' : 'false',
              openai_models: JSON.stringify(openaiModels),
              anthropic_models: JSON.stringify(anthropicModels),
            };

            const response = await configsApi.saveSystemConfigs(configs);

            if (response.success) {
              message.success('保存成功，已自动更新相关 Key 配置');
            }
          } catch (error) {
            console.error('保存失败:', error);
            message.error('保存失败');
          } finally {
            setSaving(false);
          }
        },
      });
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };


  return (
    <Card>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24
      }}>
        <Space align="center">
          <SettingOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <Title level={2} style={{ margin: 0 }}>系统配置</Title>
        </Space>
      </div>

      {/* 系统核心配置（只读） */}
      {systemConfig && (
        <Alert
          message={
            <Space>
              <LockOutlined />
              <Text strong>系统核心配置（只读）</Text>
            </Space>
          }
          description={
            <div>
              <Text type="secondary">API 前缀：</Text>
              <Text strong style={{ marginLeft: 8, fontSize: 16 }}>
                {systemConfig.API_PREFIX || '（无）'}
              </Text>
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                其他敏感配置（API 密钥、管理员密码等）不在此显示，如需修改请联系系统管理员。
              </div>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Spin spinning={loading}>
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={24}>
            {/* 左侧列 - 基础配置 */}
            <Col xs={24} lg={12}>
              {/* Key 池配置 */}
              <Card 
                title={<Text strong style={{ fontSize: 16 }}>⚙️ Key 池配置</Text>}
                size="small"
                style={{ marginBottom: 24 }}
              >
                <Form.Item
                  name="key_pool_size"
                  label={<Text strong>轮询 Key 池大小</Text>}
                  rules={[
                    { required: true, message: '请输入 Key 池大小' },
                    { type: 'number', min: 1, max: 100, message: 'Key 池大小必须在 1-100 之间' }
                  ]}
                  style={{ marginBottom: 16 }}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={1}
                    max={100}
                    placeholder="请输入 Key 池大小"
                  />
                </Form.Item>
                <Alert
                  message="控制同时活跃的 API Key 数量。系统会从所有启用的 Key 中随机选择指定数量的 Key 用于请求轮询。"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Form.Item
                  name="key_selection_strategy"
                  label={<Text strong>Key 选择策略</Text>}
                  rules={[{ required: true, message: '请选择 Key 选择策略' }]}
                  style={{ marginBottom: 16 }}
                >
                  <Select
                    style={{ width: '100%' }}
                    disabled
                    options={[
                      { value: '0', label: '随机选择' },
                    ]}
                  />
                </Form.Item>
                <Alert
                  message="选择如何从 Key 池中选择 API Key。当前仅支持随机选择策略。"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Form.Item
                  name="log_conversation_content"
                  label={<Text strong>记录对话内容</Text>}
                  valuePropName="checked"
                  initialValue={false}
                  style={{ marginBottom: 16 }}
                >
                  <Switch 
                    checkedChildren="开启" 
                    unCheckedChildren="关闭"
                  />
                </Form.Item>
                <Alert
                  message="是否在日志中记录请求和响应的完整内容（request_body 和 response_body）。"
                  description={
                    <div style={{ marginTop: 4 }}>
                      <Text type="warning">⚠️ 注意：开启后会增加数据库存储空间</Text>
                    </div>
                  }
                  type="info"
                  showIcon
                />
              </Card>

              {/* UA 配置 */}
              <Card 
                title={<Text strong style={{ fontSize: 16 }}>🌐 User Agent 配置</Text>}
                size="small"
                style={{ marginBottom: 24 }}
              >
                <Alert
                  message="配置说明"
                  description={
                    <div>
                      <div>• 请求时会从列表中<Text strong>随机选择</Text>一个 UA</div>
                      <div>• <Text strong type="danger">每行一个</Text>，支持配置<Text strong>多个</Text> UA</div>
                      <div>• 至少需要配置一个 UA</div>
                    </div>
                  }
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Form.Item
                  name="ua_list"
                  label={<Text strong>UA 列表（每行一个）</Text>}
                  rules={[
                    { required: true, message: '请输入 UA 列表' },
                    {
                      validator: (_, value) => {
                        const lines = value.split('\n').filter((line: string) => line.trim() !== '');
                        if (lines.length === 0) {
                          return Promise.reject(new Error('至少需要一个 UA'));
                        }
                        return Promise.resolve();
                      }
                    }
                  ]}
                  style={{ marginBottom: 0 }}
                >
                  <TextArea
                    rows={6}
                    placeholder="每行一个 User Agent，例如：&#10;Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36&#10;Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    style={{ fontFamily: 'monospace', fontSize: '12px' }}
                  />
                </Form.Item>
              </Card>

              {/* 代理配置 */}
              <Card 
                title={<Text strong style={{ fontSize: 16 }}>🔌 代理服务器配置</Text>}
                size="small"
                style={{ marginBottom: 24 }}
              >
                <Alert
                  message="配置说明"
                  description={
                    <div>
                      <div>• 代理<Text strong>可选</Text>，不配置则使用本机 IP 发送请求</div>
                      <div>• 请求时会从列表中<Text strong>随机选择</Text>一个代理</div>
                      <div>• <Text strong type="danger">每行一个</Text>，支持配置<Text strong>多个</Text>代理</div>
                      <div>• 支持协议：<Text code>http://</Text>、<Text code>https://</Text>、<Text code>socks5://</Text></div>
                    </div>
                  }
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Form.Item
                  name="proxy_list"
                  label={<Text strong>代理列表（每行一个，可选）</Text>}
                  rules={[
                    {
                      validator: (_, value) => {
                        if (!value || value.trim() === '') {
                          return Promise.resolve();
                        }
                        const lines = value.split('\n').filter((line: string) => line.trim() !== '');
                        if (lines.length === 0) {
                          return Promise.resolve();
                        }
                        for (const line of lines) {
                          if (!line.match(/^(https?|socks5):\/\/.+/)) {
                            return Promise.reject(new Error(`代理地址格式错误: ${line}`));
                          }
                        }
                        return Promise.resolve();
                      }
                    }
                  ]}
                  style={{ marginBottom: 0 }}
                >
                  <TextArea
                    rows={6}
                    placeholder="每行一个代理地址（可选），格式示例：&#10;http://127.0.0.1:7890&#10;https://proxy.example.com:8080&#10;socks5://user:pass@host:port"
                    style={{ fontFamily: 'monospace', fontSize: '12px' }}
                  />
                </Form.Item>
              </Card>
            </Col>

            {/* 右侧列 - 模型配置 */}
            <Col xs={24} lg={12}>
              {/* 模型列表配置 */}
              <Card 
                title={<Text strong style={{ fontSize: 16 }}>🤖 模型列表配置</Text>}
                size="small"
                style={{ marginBottom: 24 }}
              >
                <Alert
                  message="配置说明"
                  description={
                    <div>
                      <div>• 选择系统支持的模型列表，只有在列表中的模型才能被使用</div>
                      <div>• 支持<Text strong>多选</Text>和<Text strong>自定义输入</Text>（输入后按回车添加）</div>
                      <div>• 至少需要选择一个模型</div>
                    </div>
                  }
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                {/* OpenAI 模型列表 */}
                <Form.Item
                  name="openai_models"
                  label={<Text strong>OpenAI 支持的模型</Text>}
                  rules={[
                    { required: true, message: '请选择至少一个 OpenAI 模型' },
                    {
                      validator: (_, value) => {
                        if (!value || value.length === 0) {
                          return Promise.reject(new Error('至少需要一个模型'));
                        }
                        return Promise.resolve();
                      }
                    }
                  ]}
                  style={{ marginBottom: 16 }}
                >
                <Select
                  mode="tags"
                  allowClear
                  showSearch
                  placeholder="请选择或输入 OpenAI 模型名称（按回车添加）"
                  style={{ width: '100%' }}
                  maxTagCount="responsive"
                  optionFilterProp="label"
                  options={[
                    { label: 'GPT-4o 系列', options: [
                      { value: 'gpt-4o', label: 'gpt-4o' },
                      { value: 'gpt-4o-mini', label: 'gpt-4o-mini' },
                      { value: 'gpt-4o-2024-05-13', label: 'gpt-4o-2024-05-13' },
                      { value: 'gpt-4o-2024-08-06', label: 'gpt-4o-2024-08-06' },
                    ]},
                    { label: 'GPT-4 系列', options: [
                      { value: 'gpt-4', label: 'gpt-4' },
                      { value: 'gpt-4-turbo', label: 'gpt-4-turbo' },
                      { value: 'gpt-4-turbo-preview', label: 'gpt-4-turbo-preview' },
                      { value: 'gpt-4-0125-preview', label: 'gpt-4-0125-preview' },
                      { value: 'gpt-4-1106-preview', label: 'gpt-4-1106-preview' },
                      { value: 'gpt-4-vision-preview', label: 'gpt-4-vision-preview' },
                      { value: 'gpt-4-32k', label: 'gpt-4-32k' },
                      { value: 'gpt-4-0613', label: 'gpt-4-0613' },
                      { value: 'gpt-4-32k-0613', label: 'gpt-4-32k-0613' },
                    ]},
                    { label: 'GPT-3.5 系列', options: [
                      { value: 'gpt-3.5-turbo', label: 'gpt-3.5-turbo' },
                      { value: 'gpt-3.5-turbo-16k', label: 'gpt-3.5-turbo-16k' },
                      { value: 'gpt-3.5-turbo-0125', label: 'gpt-3.5-turbo-0125' },
                      { value: 'gpt-3.5-turbo-1106', label: 'gpt-3.5-turbo-1106' },
                      { value: 'gpt-3.5-turbo-0613', label: 'gpt-3.5-turbo-0613' },
                    ]},
                    { label: 'O1 系列', options: [
                      { value: 'o1', label: 'o1' },
                      { value: 'o1-mini', label: 'o1-mini' },
                      { value: 'o1-preview', label: 'o1-preview' },
                    ]},
                  ]}
                />
              </Form.Item>

              {/* Anthropic 模型列表 */}
              <Form.Item
                name="anthropic_models"
                label={<Text strong>Anthropic (Claude) 支持的模型</Text>}
                rules={[
                  { required: true, message: '请选择至少一个 Anthropic 模型' },
                  {
                    validator: (_, value) => {
                      if (!value || value.length === 0) {
                        return Promise.reject(new Error('至少需要一个模型'));
                      }
                      return Promise.resolve();
                    }
                  }
                ]}
                style={{ marginBottom: 0 }}
              >
                <Select
                  mode="tags"
                  allowClear
                  showSearch
                  placeholder="请选择或输入 Anthropic 模型名称（按回车添加）"
                  style={{ width: '100%' }}
                  maxTagCount="responsive"
                  optionFilterProp="label"
                  options={[
                    { label: 'Claude Sonnet 4', options: [
                      { value: 'claude-sonnet-4-20250514', label: 'claude-sonnet-4-20250514' },
                      { value: 'claude-sonnet-4', label: 'claude-sonnet-4 (别名)' },
                    ]},
                    { label: 'Claude 3.5 系列', options: [
                      { value: 'claude-3-5-sonnet-20241022', label: 'claude-3-5-sonnet-20241022' },
                      { value: 'claude-3-5-sonnet-20240620', label: 'claude-3-5-sonnet-20240620' },
                      { value: 'claude-3.5-sonnet', label: 'claude-3.5-sonnet (别名)' },
                    ]},
                    { label: 'Claude 3 系列', options: [
                      { value: 'claude-3-opus-20240229', label: 'claude-3-opus-20240229' },
                      { value: 'claude-3-sonnet-20240229', label: 'claude-3-sonnet-20240229' },
                      { value: 'claude-3-haiku-20240307', label: 'claude-3-haiku-20240307' },
                      { value: 'claude-3-opus', label: 'claude-3-opus (别名)' },
                      { value: 'claude-3-sonnet', label: 'claude-3-sonnet (别名)' },
                      { value: 'claude-3-haiku', label: 'claude-3-haiku (别名)' },
                    ]},
                  ]}
                />
              </Form.Item>
              </Card>
            </Col>
          </Row>

          {/* 底部操作按钮 */}
          <Form.Item style={{ marginTop: 32 }}>
            <Space>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={saving}
                size="large"
              >
                保存配置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Spin>
    </Card>
  );
};

export default ConfigManagement;

