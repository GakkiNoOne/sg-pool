import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import './style.css';

interface LoginForm {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values: LoginForm) => {
    setLoading(true);
    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // 重要：携带 cookie
        body: JSON.stringify(values),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        message.success('登录成功！');
        // 跳转到首页
        navigate('/dashboard');
      } else {
        message.error(data.message || '登录失败，请检查用户名和密码');
      }
    } catch (error) {
      message.error('网络错误，请稍后重试');
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <Card className="login-card" bordered={false}>
        <div className="login-header">
          <div className="logo-container">
            <div className="logo-circle">
              <span className="logo-text">AMP</span>
            </div>
          </div>
          <h1 className="login-title">登录</h1>
          <p className="login-subtitle">使用您的账号登录 AMP Pool 管理后台</p>
        </div>

        <Form
          name="login"
          className="login-form"
          onFinish={handleSubmit}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined style={{ color: 'rgba(0,0,0,.25)' }} />}
              placeholder="用户名"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: 'rgba(0,0,0,.25)' }} />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="login-button"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="login-footer">
          <span className="footer-text">AMP Pool © 2025</span>
        </div>
      </Card>
    </div>
  );
};

export default Login;

