import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'umi';
import { 
  DashboardOutlined, 
  KeyOutlined, 
  MenuFoldOutlined, 
  MenuUnfoldOutlined,
  UserOutlined,
  SettingOutlined,
  ControlOutlined,
  FileTextOutlined,
  LogoutOutlined
} from '@ant-design/icons';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography, message, Modal } from 'antd';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const AdminLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/keys',
      icon: <KeyOutlined />,
      label: 'Key管理',
    },
    {
      key: '/configs',
      icon: <ControlOutlined />,
      label: '配置管理',
    },
    {
      key: '/logs',
      icon: <FileTextOutlined />,
      label: '请求日志',
    },
  ];

  const userMenuItems = [
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });

      if (response.ok) {
        message.success('已退出登录');
        navigate('/login');
      } else {
        message.error('退出登录失败');
      }
    } catch (error) {
      message.error('网络错误，请稍后重试');
      console.error('Logout error:', error);
    }
  };

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'settings') {
      // 处理设置逻辑
      console.log('打开设置');
    } else if (key === 'logout') {
      Modal.confirm({
        title: '确认退出',
        content: '确定要退出登录吗？',
        okText: '确定',
        cancelText: '取消',
        onOk: handleLogout,
      });
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 顶部导航栏 */}
      <Header 
        style={{ 
          background: '#fff', 
          padding: '0 24px', 
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '16px', width: 64, height: 64 }}
          />
          <div style={{ marginLeft: 16, fontSize: '18px', fontWeight: 'bold', color: '#1890ff' }}>
            AMP Pool 管理系统
          </div>
        </div>
        
        <Dropdown
          menu={{ 
            items: userMenuItems,
            onClick: handleUserMenuClick 
          }}
          placement="bottomRight"
        >
          <Space style={{ cursor: 'pointer' }}>
            <Avatar icon={<UserOutlined />} size="small" />
            <Text>管理员</Text>
          </Space>
        </Dropdown>
      </Header>

      <Layout>
        {/* 左侧菜单 */}
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          style={{ 
            background: '#fff',
            borderRight: '1px solid #f0f0f0'
          }}
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            style={{ 
              height: '100%', 
              borderRight: 0,
              marginTop: 16
            }}
          />
        </Sider>

        {/* 主内容区域 */}
        <Layout>
          <Content
            style={{
              padding: '24px',
              background: '#f0f2f5',
              minHeight: 'calc(100vh - 64px)',
            }}
          >
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default AdminLayout;
