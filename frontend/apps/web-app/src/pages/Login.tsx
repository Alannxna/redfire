import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getAuthEndpoint } from '../config/api';

interface LoginFormData {
  username: string;
  password: string;
  confirmPassword?: string;
  email?: string;
}

interface LoginPageProps {
  onLogin: (username: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
    confirmPassword: '',
    email: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  // const navigate = useNavigate(); // 不再需要手动导航，AuthContext会自动处理
  const { login: authLogin } = useAuth();

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
        // 登录逻辑
        if (!formData.username || !formData.password) {
          setError('请输入用户名和密码');
          setIsLoading(false);
          return;
        }
        
        try {
          // 使用AuthContext的统一登录方法
          const success = await authLogin(formData.username, formData.password);
          
          if (success) {
            // AuthContext会自动设置认证状态，路由会自动重定向
            return;
          } else {
            // 如果API调用失败，回退到演示账户验证
            if (formData.username === 'admin' && formData.password === 'admin123') {
              // 手动设置演示用户状态
              const demoUser = { id: '1', username: 'admin', email: 'admin@demo.com', role: 'admin' };
              localStorage.setItem('redfire_token', 'demo-token-admin');
              localStorage.setItem('redfire_user', JSON.stringify(demoUser));
              onLogin(formData.username);
            } else if (formData.username === 'trader' && formData.password === 'trader123') {
              const demoUser = { id: '2', username: 'trader', email: 'trader@demo.com', role: 'trader' };
              localStorage.setItem('redfire_token', 'demo-token-trader');
              localStorage.setItem('redfire_user', JSON.stringify(demoUser));
              onLogin(formData.username);
            } else if (formData.username === 'demo' && formData.password === 'demo') {
              const demoUser = { id: '3', username: 'demo', email: 'demo@demo.com', role: 'user' };
              localStorage.setItem('redfire_token', 'demo-token-demo');
              localStorage.setItem('redfire_user', JSON.stringify(demoUser));
              onLogin(formData.username);
            } else {
              setError('登录失败，请检查用户名和密码');
            }
          }
        } catch (error) {
          // eslint-disable-next-line no-console
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
