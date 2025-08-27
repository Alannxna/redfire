// API配置
export const API_CONFIG = {
  // 开发环境API基础URL
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'https://api.redfire.com' 
    : 'http://localhost:8000',
  
  // API端点
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/api/auth/login',
      REGISTER: '/api/auth/register',
      LOGOUT: '/api/auth/logout',
      VERIFY: '/api/auth/verify-token',
      ME: '/api/auth/me',
    },
    TRADING: {
      ORDERS: '/api/trading/orders',
      POSITIONS: '/api/trading/positions',
      TRADES: '/api/trading/trades',
      ACCOUNT: '/api/trading/account',
    },
    STRATEGY: {
      LIST: '/api/strategy/list',
      CREATE: '/api/strategy/create',
      UPDATE: '/api/strategy/update',
      DELETE: '/api/strategy/delete',
    },
    DATA: {
      MARKET_DATA: '/api/data/market',
      HISTORICAL: '/api/data/historical',
      SYMBOLS: '/api/data/symbols',
    },
  },
  
  // 请求配置
  REQUEST_CONFIG: {
    timeout: 10000, // 10秒超时
    retries: 3,     // 重试3次
  },
} as const;

// 构建完整的API URL
export const buildApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// 获取认证端点
export const getAuthEndpoint = (action: keyof typeof API_CONFIG.ENDPOINTS.AUTH): string => {
  return buildApiUrl(API_CONFIG.ENDPOINTS.AUTH[action]);
};
