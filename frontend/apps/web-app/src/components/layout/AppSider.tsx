import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  StockOutlined,
  RobotOutlined,
  SafetyOutlined,
  DatabaseOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { Sider } = Layout;

type MenuItem = Required<MenuProps>['items'][number];

const AppSider: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems: MenuItem[] = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/trading',
      icon: <StockOutlined />,
      label: '交易中心',
    },
    {
      key: '/strategy',
      icon: <RobotOutlined />,
      label: '策略管理',
    },
    {
      key: '/risk',
      icon: <SafetyOutlined />,
      label: '风险控制',
    },
    {
      key: '/data',
      icon: <DatabaseOutlined />,
      label: '数据中心',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key);
  };

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      className="app-sider"
      theme="dark"
      width={220}
    >
      <div className="logo">
        <div className="logo-icon">🔥</div>
        {!collapsed && <span className="logo-text">RedFire</span>}
      </div>
      
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        className="sidebar-menu"
      />
    </Sider>
  );
};

export default AppSider;
