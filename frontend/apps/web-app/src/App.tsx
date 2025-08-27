import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from '@redfire/theme-system';
import LoginPage from './pages/Login';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Trading from './pages/Trading';
import Strategy from './pages/Strategy';
import Data from './pages/Data';
import Risk from './pages/Risk';
import Settings from './pages/Settings';

// 导入主题样式
import '@redfire/theme-system/ThemeStyles.css';

// 路由守卫组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '24px',
            marginBottom: '16px'
          }}>🔥</div>
          <div>正在加载...</div>
        </div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// 主应用组件
const AppContent: React.FC = () => {
  const { isAuthenticated, loginDirect } = useAuth();

  return (
    <Routes>
      {/* 登录页面 */}
      <Route 
        path="/login" 
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <LoginPage onLogin={loginDirect} />
          )
        } 
      />
      
      {/* 受保护的路由 */}
      <Route path="/" element={
        <ProtectedRoute>
          <MainLayout />
        </ProtectedRoute>
      }>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="trading" element={<Trading />} />
        <Route path="strategy" element={<Strategy />} />
        <Route path="data" element={<Data />} />
        <Route path="risk" element={<Risk />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      
      {/* 404页面 */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider defaultThemeName="light" enableLocalStorage={true}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
