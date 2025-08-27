import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// 用户信息接口
interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  role: string;
}

// 认证上下文接口
interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  loginDirect: (username: string) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者组件属性
interface AuthProviderProps {
  children: ReactNode;
}

// 本地存储键名
const TOKEN_KEY = 'redfire_token';
const USER_KEY = 'redfire_user';

// 认证提供者组件
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 计算认证状态
  const isAuthenticated = !!user && !!token;

  // 初始化时从本地存储恢复状态
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY);
    const savedUser = localStorage.getItem(USER_KEY);

    if (savedToken && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(parsedUser);
      } catch (error) {
        console.error('Failed to parse saved user data:', error);
        // 清除无效数据
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
    
    setIsLoading(false);
  }, []);

  // 登录函数
  const login = async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        const { token: newToken, user: newUser } = data;
        
        // 保存到状态
        setToken(newToken);
        setUser(newUser);
        
        // 保存到本地存储
        localStorage.setItem(TOKEN_KEY, newToken);
        localStorage.setItem(USER_KEY, JSON.stringify(newUser));
        
        return true;
      } else {
        console.error('Login failed:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Login error:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // 登出函数
  const logout = () => {
    setUser(null);
    setToken(null);
    
    // 清除本地存储
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  // 直接登录函数（用于演示账户）
  const loginDirect = (_username: string) => {
    // 从本地存储获取已设置的用户信息和token
    const savedToken = localStorage.getItem(TOKEN_KEY);
    const savedUser = localStorage.getItem(USER_KEY);
    
    if (savedToken && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(parsedUser);
      } catch (error) {
        console.error('Failed to parse saved user data:', error);
      }
    }
  };

  // 更新用户信息
  const updateUser = (newUser: User) => {
    setUser(newUser);
    localStorage.setItem(USER_KEY, JSON.stringify(newUser));
  };

  // 提供认证上下文值
  const contextValue: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    loginDirect,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 使用认证上下文的Hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

// 默认导出
export default AuthProvider;