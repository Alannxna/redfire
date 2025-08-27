import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Theme, ThemeName, themes, defaultTheme } from './theme';

// 主题上下文类型
interface ThemeContextType {
  currentTheme: Theme;
  themeName: ThemeName;
  setTheme: (themeName: ThemeName) => void;
  toggleTheme: () => void;
}

// 创建主题上下文
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// 主题提供者组件属性
interface ThemeProviderProps {
  children: ReactNode;
  defaultThemeName?: ThemeName;
  enableLocalStorage?: boolean;
}

// 本地存储键名
const THEME_STORAGE_KEY = 'redfire_theme';

/**
 * 主题提供者组件
 * 提供全局主题管理功能
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultThemeName = 'light',
  enableLocalStorage = true,
}) => {
  // 从本地存储获取主题
  const getStoredTheme = (): ThemeName => {
    if (!enableLocalStorage) return defaultThemeName;
    
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (stored && stored in themes) {
        return stored as ThemeName;
      }
    } catch (error) {
      console.warn('Failed to read theme from localStorage:', error);
    }
    
    return defaultThemeName;
  };

  const [themeName, setThemeName] = useState<ThemeName>(getStoredTheme);
  const [currentTheme, setCurrentTheme] = useState<Theme>(themes[themeName]);

  // 设置主题
  const setTheme = (newThemeName: ThemeName) => {
    setThemeName(newThemeName);
    setCurrentTheme(themes[newThemeName]);
    
    // 保存到本地存储
    if (enableLocalStorage) {
      try {
        localStorage.setItem(THEME_STORAGE_KEY, newThemeName);
      } catch (error) {
        console.warn('Failed to save theme to localStorage:', error);
      }
    }
    
    // 更新CSS变量
    updateCSSVariables(themes[newThemeName]);
  };

  // 切换主题（在三种主题间循环）
  const toggleTheme = () => {
    const themeOrder: ThemeName[] = ['light', 'gray', 'dark'];
    const currentIndex = themeOrder.indexOf(themeName);
    const nextIndex = (currentIndex + 1) % themeOrder.length;
    setTheme(themeOrder[nextIndex]);
  };

  // 更新CSS变量
  const updateCSSVariables = (theme: Theme) => {
    const root = document.documentElement;
    
    // 设置颜色变量
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    
    // 设置间距变量
    Object.entries(theme.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value);
    });
    
    // 设置字体变量
    Object.entries(theme.typography).forEach(([key, value]) => {
      root.style.setProperty(`--font-size-${key}`, value);
    });
    
    // 设置主题名称
    root.setAttribute('data-theme', theme.name);
  };

  // 初始化CSS变量
  useEffect(() => {
    updateCSSVariables(currentTheme);
  }, [currentTheme]);

  // 监听系统主题变化
  useEffect(() => {
    if (!enableLocalStorage) return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (!stored) {
        // 如果没有存储的主题偏好，跟随系统
        setTheme(e.matches ? 'dark' : 'light');
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [enableLocalStorage]);

  const contextValue: ThemeContextType = {
    currentTheme,
    themeName,
    setTheme,
    toggleTheme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * 使用主题的Hook
 * @returns 主题上下文
 */
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

/**
 * 主题切换按钮组件
 */
export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { themeName, toggleTheme } = useTheme();
  
  const getThemeIcon = () => {
    switch (themeName) {
      case 'light':
        return '☀️';
      case 'dark':
        return '🌙';
      case 'gray':
        return '⚪';
      default:
        return '🎨';
    }
  };
  
  const getThemeLabel = () => {
    switch (themeName) {
      case 'light':
        return '浅色主题';
      case 'dark':
        return '深色主题';
      case 'gray':
        return '灰色主题';
      default:
        return '主题';
    }
  };

  return (
    <button
      onClick={toggleTheme}
      className={`theme-toggle ${className}`}
      title={`当前: ${getThemeLabel()}，点击切换`}
      aria-label={`切换主题，当前为${getThemeLabel()}`}
    >
      <span className="theme-icon">{getThemeIcon()}</span>
      <span className="theme-text">{getThemeLabel()}</span>
    </button>
  );
};

export default ThemeProvider;
