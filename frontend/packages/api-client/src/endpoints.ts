// API 端点定义
export const API_ENDPOINTS = {
  // 用户相关
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
  },
  
  // 交易相关
  TRADING: {
    ORDERS: '/trading/orders',
    POSITIONS: '/trading/positions',
    TRADES: '/trading/trades',
    ACCOUNT: '/trading/account',
  },
  
  // 用户管理
  USER: {
    PROFILE: '/user/profile',
    PREFERENCES: '/user/preferences',
    SETTINGS: '/user/settings',
  },
} as const;
