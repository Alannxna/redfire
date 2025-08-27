# 🎨 RedFire前端架构设计

## 📋 概述

RedFire前端采用现代化的React技术栈，基于TypeScript构建，使用Monorepo架构管理多个应用和共享包，提供一致的用户体验和高效的开发效率。

## 🏗️ 架构层次

### 1. 应用层 (Application Layer)
- **Web应用**: 主要的Web交易界面
- **移动应用**: React Native移动端应用
- **管理后台**: 系统管理和监控界面
- **专业交易界面**: 高级交易功能界面

### 2. 共享包层 (Shared Packages Layer)
- **UI组件库**: 可复用的UI组件
- **业务组件库**: 业务逻辑组件
- **类型定义**: 共享的TypeScript类型
- **API客户端**: HTTP请求和WebSocket客户端
- **主题系统**: 统一的主题和样式管理

### 3. 构建工具层 (Build Tools Layer)
- **Turborepo**: Monorepo管理工具
- **Vite**: 快速构建工具
- **TypeScript**: 类型安全的JavaScript
- **ESLint + Prettier**: 代码质量和格式化

### 4. 测试体系层 (Testing Layer)
- **Jest**: 单元测试框架
- **React Testing Library**: React组件测试
- **Cypress**: 端到端测试
- **Storybook**: 组件文档和测试

## 📦 Monorepo结构

```
frontend/
├── apps/                           # 应用目录
│   ├── web-app/                    # Web应用
│   ├── mobile-app/                 # 移动应用
│   ├── admin-panel/                # 管理后台
│   └── trading-terminal/           # 专业交易终端
├── packages/                       # 共享包目录
│   ├── ui-components/              # UI组件库
│   ├── business-components/        # 业务组件库
│   ├── shared-types/               # 共享类型定义
│   ├── api-client/                 # API客户端
│   ├── theme-system/               # 主题系统
│   └── utils/                      # 工具库
├── tools/                          # 开发工具
├── scripts/                        # 构建脚本
└── package.json                    # 根包配置
```

## 🔧 核心技术栈

### React生态系统
```typescript
// React 18 + TypeScript
import React, { useState, useEffect, useCallback } from 'react';
import { createRoot } from 'react-dom/client';

// 函数组件示例
interface TradingPanelProps {
  symbol: string;
  onOrderSubmit: (order: Order) => void;
}

const TradingPanel: React.FC<TradingPanelProps> = ({ symbol, onOrderSubmit }) => {
  const [orderType, setOrderType] = useState<OrderType>('market');
  const [volume, setVolume] = useState<number>(0);
  const [price, setPrice] = useState<number>(0);

  const handleSubmit = useCallback(() => {
    const order: Order = {
      symbol,
      orderType,
      volume,
      price,
      timestamp: Date.now()
    };
    onOrderSubmit(order);
  }, [symbol, orderType, volume, price, onOrderSubmit]);

  return (
    <div className="trading-panel">
      <h3>交易面板 - {symbol}</h3>
      {/* 交易表单 */}
    </div>
  );
};
```

### 状态管理
```typescript
// Redux Toolkit状态管理
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// 异步Action
export const fetchMarketData = createAsyncThunk(
  'market/fetchData',
  async (symbol: string) => {
    const response = await api.getMarketData(symbol);
    return response.data;
  }
);

// Slice定义
const marketSlice = createSlice({
  name: 'market',
  initialState: {
    data: {},
    loading: false,
    error: null
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchMarketData.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchMarketData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchMarketData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});
```

### 路由管理
```typescript
// React Router v6路由配置
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trading" element={<Trading />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
};
```

## 🎨 UI组件系统

### 组件库架构
```typescript
// UI组件库结构
export interface ComponentProps {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

// 基础按钮组件
export interface ButtonProps extends ComponentProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  onClick?: () => void;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  disabled = false,
  onClick,
  children,
  ...props
}) => {
  const buttonClass = classNames(
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    { disabled }
  );

  return (
    <button
      className={buttonClass}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};
```

### 主题系统
```typescript
// 主题配置
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    danger: string;
    background: string;
    surface: string;
    text: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      small: string;
      medium: string;
      large: string;
    };
  };
}

// 主题上下文
const ThemeContext = React.createContext<Theme | null>(null);

export const ThemeProvider: React.FC<{ theme: Theme; children: React.ReactNode }> = ({
  theme,
  children
}) => {
  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): Theme => {
  const theme = useContext(ThemeContext);
  if (!theme) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return theme;
};
```

## 📡 API集成

### HTTP客户端
```typescript
// API客户端配置
export class ApiClient {
  private baseURL: string;
  private token: string | null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // 获取市场数据
  async getMarketData(symbol: string): Promise<MarketData> {
    return this.request<MarketData>(`/market/data/${symbol}`);
  }

  // 提交订单
  async submitOrder(order: Order): Promise<OrderResponse> {
    return this.request<OrderResponse>('/orders', {
      method: 'POST',
      body: JSON.stringify(order)
    });
  }
}
```

### WebSocket客户端
```typescript
// WebSocket客户端
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(private url: string, private onMessage: (data: any) => void) {}

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
    } catch (error) {
      console.error('WebSocket连接失败:', error);
    }
  }

  private handleOpen(): void {
    console.log('WebSocket连接已建立');
    this.reconnectAttempts = 0;
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      this.onMessage(data);
    } catch (error) {
      console.error('消息解析失败:', error);
    }
  }

  private handleClose(): void {
    console.log('WebSocket连接已关闭');
    this.attemptReconnect();
  }

  private handleError(error: Event): void {
    console.error('WebSocket错误:', error);
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`尝试重新连接... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

## 🧪 测试策略

### 单元测试
```typescript
// Jest + React Testing Library测试示例
import { render, screen, fireEvent } from '@testing-library/react';
import { TradingPanel } from './TradingPanel';

describe('TradingPanel', () => {
  const mockOnOrderSubmit = jest.fn();

  beforeEach(() => {
    mockOnOrderSubmit.mockClear();
  });

  it('应该渲染交易面板', () => {
    render(<TradingPanel symbol="BTCUSDT" onOrderSubmit={mockOnOrderSubmit} />);
    
    expect(screen.getByText('交易面板 - BTCUSDT')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '提交订单' })).toBeInTheDocument();
  });

  it('应该处理订单提交', () => {
    render(<TradingPanel symbol="BTCUSDT" onOrderSubmit={mockOnOrderSubmit} />);
    
    const submitButton = screen.getByRole('button', { name: '提交订单' });
    fireEvent.click(submitButton);
    
    expect(mockOnOrderSubmit).toHaveBeenCalledTimes(1);
  });
});
```

### 端到端测试
```typescript
// Cypress E2E测试示例
describe('交易功能测试', () => {
  beforeEach(() => {
    cy.visit('/trading');
    cy.login('testuser', 'password');
  });

  it('应该能够提交市价订单', () => {
    cy.get('[data-testid="symbol-input"]').type('BTCUSDT');
    cy.get('[data-testid="volume-input"]').type('0.1');
    cy.get('[data-testid="order-type-select"]').select('market');
    cy.get('[data-testid="submit-order-btn"]').click();
    
    cy.get('[data-testid="order-success-message"]').should('be.visible');
  });

  it('应该显示实时价格更新', () => {
    cy.get('[data-testid="price-display"]').should('be.visible');
    cy.wait(5000); // 等待5秒
    cy.get('[data-testid="price-display"]').should('not.have.text', '0.00');
  });
});
```

## 🚀 性能优化

### 代码分割
```typescript
// 路由级别的代码分割
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Trading = lazy(() => import('./pages/Trading'));
const Portfolio = lazy(() => import('./pages/Portfolio'));

const App: React.FC = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trading" element={<Trading />} />
        <Route path="/portfolio" element={<Portfolio />} />
      </Routes>
    </Suspense>
  );
};
```

### 虚拟化列表
```typescript
// 虚拟化长列表
import { FixedSizeList as List } from 'react-window';

interface OrderListProps {
  orders: Order[];
}

const OrderList: React.FC<OrderListProps> = ({ orders }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style} className="order-row">
      <span>{orders[index].symbol}</span>
      <span>{orders[index].volume}</span>
      <span>{orders[index].price}</span>
      <span>{orders[index].status}</span>
    </div>
  );

  return (
    <List
      height={400}
      itemCount={orders.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

## 📱 响应式设计

### 媒体查询
```typescript
// 响应式Hook
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }

    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
};

// 使用示例
const TradingPanel: React.FC = () => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');

  return (
    <div className={`trading-panel ${isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop'}`}>
      {/* 响应式内容 */}
    </div>
  );
};
```

## 🔧 构建配置

### Vite配置
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types')
    }
  },
  build: {
    target: 'es2015',
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['antd', '@ant-design/icons'],
          utils: ['lodash', 'dayjs']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

### Turborepo配置
```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "build/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "dependsOn": ["^build"]
    }
  }
}
```

---

*RedFire前端架构设计 - 构建现代化、高性能的交易系统前端* 🔥
