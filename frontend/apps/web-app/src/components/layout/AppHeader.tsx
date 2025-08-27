import React from 'react';
import { Layout, Button, Dropdown, Avatar, Space, Typography } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { ThemeToggle } from '@redfire/theme-system';

const { Header } = Layout;
const { Text } = Typography;

interface AppHeaderProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

const AppHeader: React.FC<AppHeaderProps> = ({ collapsed, onToggle }) => {
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
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

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    switch (key) {
      case 'profile':
        // 跳转到个人资料页面
        break;
      case 'settings':
        // 跳转到设置页面
        break;
      case 'logout':
        // 执行退出登录
        break;
    }
  };

  return (
    <Header className="app-header">
      <div className="header-left">
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onToggle}
          className="trigger"
        />
        <Text strong className="app-title">
          RedFire 量化交易平台
        </Text>
      </div>
      
      <div className="header-right">
        <Space size="middle">
          <Button
            type="text"
            icon={<BellOutlined />}
            className="notification-btn"
          />
          
          {/* 主题切换按钮 */}
          <ThemeToggle className="theme-toggle-btn" />
          
          <Dropdown
            menu={{
              items: userMenuItems,
              onClick: handleUserMenuClick,
            }}
            placement="bottomRight"
            arrow
          >
            <div className="user-info">
              <Avatar icon={<UserOutlined />} />
              <Text className="username">管理员</Text>
            </div>
          </Dropdown>
        </Space>
      </div>
    </Header>
  );
};

export default AppHeader;
