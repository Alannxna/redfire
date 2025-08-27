import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface MenuItem {
  key: string;
  icon: string;
  label: string;
  path: string;
  roles?: string[];
}

const menuItems: MenuItem[] = [
  {
    key: 'dashboard',
    icon: '📊',
    label: '仪表盘',
    path: '/dashboard'
  },
  {
    key: 'trading',
    icon: '💹',
    label: '交易中心',
    path: '/trading'
  },
  {
    key: 'strategy',
    icon: '🧠',
    label: '策略管理',
    path: '/strategy'
  },
  {
    key: 'data',
    icon: '📈',
    label: '市场数据',
    path: '/data'
  },
  {
    key: 'risk',
    icon: '🛡️',
    label: '风险控制',
    path: '/risk'
  },
  {
    key: 'settings',
    icon: '⚙️',
    label: '系统设置',
    path: '/settings',
    roles: ['admin'] // 只有管理员可以访问
  }
];

const MainLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  // 过滤菜单项（基于用户角色）
  const filteredMenuItems = menuItems.filter(item => {
    if (!item.roles) return true;
    return item.roles.includes(user?.role || '');
  });

  const handleLogout = () => {
    logout();
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <div style={{
        width: sidebarCollapsed ? '60px' : '240px',
        backgroundColor: '#001529',
        transition: 'width 0.3s',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Logo区域 */}
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
          padding: sidebarCollapsed ? '0' : '0 20px',
          borderBottom: '1px solid #303030'
        }}>
          <div style={{
            color: '#1890ff',
            fontSize: sidebarCollapsed ? '20px' : '24px',
            fontWeight: 'bold'
          }}>
            {sidebarCollapsed ? '🔥' : '🔥 RedFire'}
          </div>
        </div>

        {/* 菜单区域 */}
        <nav style={{ flex: 1, padding: '20px 0' }}>
          {filteredMenuItems.map(item => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.key}
                to={item.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: sidebarCollapsed ? '12px 18px' : '12px 20px',
                  margin: '4px 12px',
                  color: isActive ? '#1890ff' : '#rgba(255, 255, 255, 0.65)',
                  backgroundColor: isActive ? '#111b26' : 'transparent',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  transition: 'all 0.3s',
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    (e.target as HTMLElement).style.backgroundColor = '#1f1f1f';
                    (e.target as HTMLElement).style.color = '#fff';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    (e.target as HTMLElement).style.backgroundColor = 'transparent';
                    (e.target as HTMLElement).style.color = 'rgba(255, 255, 255, 0.65)';
                  }
                }}
              >
                <span style={{ fontSize: '16px', marginRight: sidebarCollapsed ? '0' : '12px' }}>
                  {item.icon}
                </span>
                {!sidebarCollapsed && (
                  <span style={{ fontSize: '14px' }}>{item.label}</span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* 折叠按钮 */}
        <div style={{ padding: '12px', borderTop: '1px solid #303030' }}>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{
              width: '100%',
              padding: '8px',
              backgroundColor: 'transparent',
              border: '1px solid #303030',
              borderRadius: '4px',
              color: 'rgba(255, 255, 255, 0.65)',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {sidebarCollapsed ? '▶' : '◀'}
          </button>
        </div>
      </div>

      {/* 主内容区域 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* 顶部导航栏 */}
        <header style={{
          height: '64px',
          backgroundColor: '#fff',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px'
        }}>
          <div style={{
            fontSize: '16px',
            fontWeight: '500',
            color: '#333'
          }}>
            {filteredMenuItems.find(item => item.path === location.pathname)?.label || '仪表盘'}
          </div>

          {/* 用户信息和操作 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* 当前时间 */}
            <div style={{ fontSize: '14px', color: '#666' }}>
              {new Date().toLocaleString('zh-CN')}
            </div>

            {/* 用户头像和菜单 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <img
                src={user?.avatar}
                alt={user?.username}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  border: '2px solid #f0f0f0'
                }}
              />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '14px', fontWeight: '500' }}>
                  {user?.username}
                </span>
                <span style={{ fontSize: '12px', color: '#666' }}>
                  {user?.role === 'admin' ? '管理员' : 
                   user?.role === 'trader' ? '交易员' : '普通用户'}
                </span>
              </div>
              <button
                onClick={handleLogout}
                style={{
                  padding: '4px 8px',
                  backgroundColor: '#ff4d4f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  marginLeft: '8px'
                }}
                title="退出登录"
              >
                退出
              </button>
            </div>
          </div>
        </header>

        {/* 页面内容 */}
        <main style={{
          flex: 1,
          padding: '24px',
          backgroundColor: '#f5f5f5',
          overflow: 'auto'
        }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
