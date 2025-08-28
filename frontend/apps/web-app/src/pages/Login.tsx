import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getAuthEndpoint } from '../config/api';

interface LoginFormData {
  username: string;
  password: string;
  confirmPassword?: string;
  email?: string;
}

const LoginPage: React.FC = () => {
  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
    confirmPassword: '',
    email: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const { login, loginDirect } = useAuth();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 清除错误信息
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      if (isRegisterMode) {
        // 注册逻辑
        if (!formData.username || !formData.password || !formData.email) {
          setError('请填写所有必填字段');
          setIsLoading(false);
          return;
        }
        if (formData.password !== formData.confirmPassword) {
          setError('密码确认不匹配');
          setIsLoading(false);
          return;
        }
        if (formData.password.length < 6) {
          setError('密码至少需要6个字符');
          setIsLoading(false);
          return;
        }

        try {
          const response = await fetch(getAuthEndpoint('REGISTER'), {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username: formData.username,
              email: formData.email,
              password: formData.password,
            }),
          });

          const result = await response.json();

          if (result.success) {
            setError('');
            setIsRegisterMode(false);
            resetForm();
            alert('注册成功！请使用新账户登录。');
          } else {
            setError(result.message || '注册失败');
          }
        } catch {
          setError('注册失败，请检查网络连接');
        }
      } else {
        // 统一登录逻辑
        if (!formData.username || !formData.password) {
          setError('请输入用户名和密码');
          setIsLoading(false);
          return;
        }
        
        try {
          // 先尝试API登录
          const apiSuccess = await login(formData.username, formData.password);
          
          if (apiSuccess) {
            // API登录成功，AuthContext会自动处理状态和路由
            return;
          }
          
          // API登录失败，检查是否为演示账户
          const demoAccounts = [
            { username: 'admin', password: 'admin123' },
            { username: 'trader', password: 'trader123' },
            { username: 'demo', password: 'demo' }
          ];
          
          const isDemoAccount = demoAccounts.some(
            account => account.username === formData.username && account.password === formData.password
          );
          
          if (isDemoAccount) {
            // 使用演示账户登录
            loginDirect(formData.username);
            return;
          }
          
          // 既不是API用户也不是演示账户
          setError('登录失败，请检查用户名和密码');
        } catch (error) {
          console.error('Login error:', error);
          setError('登录失败，请稍后重试');
        }
      }
    } catch {
      setError(isRegisterMode ? '注册失败，请稍后重试' : '登录失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      password: '',
      confirmPassword: '',
      email: ''
    });
  };

  const toggleMode = () => {
    setIsRegisterMode(!isRegisterMode);
    setError('');
    resetForm();
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #2a0000 0%, #1a0000 100%)',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#0d0d0d',
        padding: '32px',
        borderRadius: '6px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        width: '100%',
        maxWidth: '360px',
        border: '1px solid #333'
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <div style={{
            width: '60px',
            height: '60px',
            background: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto',
            fontSize: '32px',
            fontWeight: 'bold',
            color: '#cc3333',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
            border: '2px solid #FFD700'
          }}>
            R
          </div>
        </div>

        {/* 登录/注册表单 */}
        <form onSubmit={handleSubmit}>
          {isRegisterMode && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                color: '#ffffff',
                fontWeight: '500',
                fontSize: '14px'
              }}>
                邮箱
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="请输入邮箱"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  backgroundColor: '#2a2a2a',
                  color: '#ffffff',
                  transition: 'border-color 0.3s'
                }}
                onFocus={(e) => e.target.style.borderColor = '#cc3333'}
                onBlur={(e) => e.target.style.borderColor = '#444'}
              />
            </div>
          )}

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              color: '#ffffff',
              fontWeight: '500',
              fontSize: '14px'
            }}>
              用户名
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="请输入用户名"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #444',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box',
                backgroundColor: '#2a2a2a',
                color: '#ffffff',
                transition: 'border-color 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#ff4444'}
              onBlur={(e) => e.target.style.borderColor = '#444'}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              color: '#ffffff',
              fontWeight: '500',
              fontSize: '14px'
            }}>
              密码
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="请输入密码"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #444',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box',
                backgroundColor: '#2a2a2a',
                color: '#ffffff',
                transition: 'border-color 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#ff4444'}
              onBlur={(e) => e.target.style.borderColor = '#444'}
            />
          </div>

          {isRegisterMode && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                color: '#ffffff',
                fontWeight: '500',
                fontSize: '14px'
              }}>
                确认密码
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="请再次输入密码"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  backgroundColor: '#2a2a2a',
                  color: '#ffffff',
                  transition: 'border-color 0.3s'
                }}
                onFocus={(e) => e.target.style.borderColor = '#cc3333'}
                onBlur={(e) => e.target.style.borderColor = '#444'}
              />
            </div>
          )}

          {error && (
            <div style={{
              color: '#ff6b6b',
              fontSize: '14px',
              marginBottom: '20px',
              padding: '10px',
              backgroundColor: '#2a1a1a',
              border: '1px solid #cc3333',
              borderRadius: '4px',
              textAlign: 'center'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: isLoading ? '#666' : '#cc3333',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.3s',
              marginBottom: '16px'
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                (e.target as HTMLButtonElement).style.backgroundColor = '#dd4444';
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                (e.target as HTMLButtonElement).style.backgroundColor = '#cc3333';
              }
            }}
          >
            {isLoading ? (isRegisterMode ? '注册中...' : '登录中...') : (isRegisterMode ? '注册' : '登录')}
          </button>

          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <button
              type="button"
              onClick={toggleMode}
              style={{
                background: 'none',
                border: 'none',
                color: '#cc3333',
                fontSize: '14px',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              {isRegisterMode ? '已有账户？立即登录' : '没有账户？立即注册'}
            </button>
          </div>
        </form>


      </div>
    </div>
  );
};

export default LoginPage;
