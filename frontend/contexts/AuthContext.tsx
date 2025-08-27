import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
  username: string;
  role: string;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // 页面加载时检查本地存储中的登录状态
  useEffect(() => {
    const checkAuthStatus = () => {
      try {
        const savedUser = localStorage.getItem('redfire_user');
        if (savedUser) {
          const userData = JSON.parse(savedUser);
          setUser(userData);
        }
      } catch (error) {
        console.error('Failed to parse saved user data:', error);
        localStorage.removeItem('redfire_user');
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = (username: string) => {
    // 根据用户名确定角色
    let role = 'user';
    if (username === 'admin') {
      role = 'admin';
    } else if (username === 'trader') {
      role = 'trader';
    } else if (username === 'demo') {
      role = 'demo';
    }

    const userData: User = {
      username,
      role,
      avatar: `https://ui-avatars.com/api/?name=${username}&background=1890ff&color=fff`
    };

    setUser(userData);
    localStorage.setItem('redfire_user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('redfire_user');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
