// 数字格式化工具
export const formatNumber = (
  num: number,
  options: {
    decimals?: number;
    thousands?: string;
    decimal?: string;
    prefix?: string;
    suffix?: string;
  } = {}
): string => {
  const {
    decimals = 2,
    thousands = ',',
    decimal = '.',
    prefix = '',
    suffix = '',
  } = options;

  if (isNaN(num) || num === null) return '0';

  const fixedNum = Math.abs(num).toFixed(decimals);
  const [integerPart, decimalPart] = fixedNum.split('.');
  
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, thousands);
  const formattedNumber = decimalPart ? `${formattedInteger}${decimal}${decimalPart}` : formattedInteger;
  
  return `${prefix}${num < 0 ? '-' : ''}${formattedNumber}${suffix}`;
};

// 货币格式化
export const formatCurrency = (
  amount: number,
  currency: string = '¥',
  decimals: number = 2
): string => {
  return formatNumber(amount, {
    decimals,
    thousands: ',',
    prefix: currency,
  });
};

// 百分比格式化
export const formatPercentage = (
  value: number,
  decimals: number = 2
): string => {
  return formatNumber(value, {
    decimals,
    suffix: '%',
  });
};

// 大数字格式化（万、亿）
export const formatLargeNumber = (num: number): string => {
  if (Math.abs(num) >= 100000000) {
    return formatNumber(num / 100000000, { decimals: 2, suffix: '亿' });
  }
  if (Math.abs(num) >= 10000) {
    return formatNumber(num / 10000, { decimals: 2, suffix: '万' });
  }
  return formatNumber(num, { decimals: 2 });
};

// 时间格式化工具
export const formatTime = (
  timestamp: number | string | Date,
  format: string = 'YYYY-MM-DD HH:mm:ss'
): string => {
  const date = new Date(timestamp);
  
  const formatMap: Record<string, () => string> = {
    'YYYY': () => date.getFullYear().toString(),
    'MM': () => (date.getMonth() + 1).toString().padStart(2, '0'),
    'DD': () => date.getDate().toString().padStart(2, '0'),
    'HH': () => date.getHours().toString().padStart(2, '0'),
    'mm': () => date.getMinutes().toString().padStart(2, '0'),
    'ss': () => date.getSeconds().toString().padStart(2, '0'),
  };

  return format.replace(/YYYY|MM|DD|HH|mm|ss/g, (match) => {
    return formatMap[match]?.() || match;
  });
};

// 相对时间格式化
export const formatRelativeTime = (timestamp: number | string | Date): string => {
  const now = new Date().getTime();
  const time = new Date(timestamp).getTime();
  const diff = now - time;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}天前`;
  if (hours > 0) return `${hours}小时前`;
  if (minutes > 0) return `${minutes}分钟前`;
  if (seconds > 0) return `${seconds}秒前`;
  return '刚刚';
};

// 颜色工具
export const getStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    success: '#52c41a',
    error: '#ff4d4f',
    warning: '#faad14',
    info: '#1890ff',
    processing: '#1890ff',
    default: '#d9d9d9',
    // 交易状态
    buy: '#52c41a',
    sell: '#ff4d4f',
    hold: '#faad14',
    // 策略状态
    running: '#52c41a',
    stopped: '#ff4d4f',
    paused: '#faad14',
    // 风险等级
    low: '#52c41a',
    medium: '#faad14',
    high: '#ff4d4f',
  };
  
  return colorMap[status.toLowerCase()] || colorMap.default;
};

// 获取涨跌颜色
export const getPnLColor = (value: number): string => {
  if (value > 0) return '#52c41a';
  if (value < 0) return '#ff4d4f';
  return '#8c8c8c';
};

// 数据验证工具
export const validators = {
  // 邮箱验证
  email: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  // 手机号验证
  phone: (phone: string): boolean => {
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
  },

  // 股票代码验证
  stockCode: (code: string): boolean => {
    const stockRegex = /^[0-9]{6}$/;
    return stockRegex.test(code);
  },

  // 价格验证
  price: (price: number): boolean => {
    return price > 0 && price <= 9999999.99;
  },

  // 数量验证
  quantity: (qty: number): boolean => {
    return Number.isInteger(qty) && qty > 0 && qty % 100 === 0; // 股票以手为单位
  },
};

// 本地存储工具
export const storage = {
  get: <T>(key: string, defaultValue?: T): T | undefined => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('Error getting from localStorage:', error);
      return defaultValue;
    }
  },

  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error setting to localStorage:', error);
    }
  },

  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from localStorage:', error);
    }
  },

  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  },
};

// URL工具
export const urlUtils = {
  // 获取查询参数
  getQueryParam: (param: string): string | null => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  },

  // 设置查询参数
  setQueryParam: (param: string, value: string): void => {
    const url = new URL(window.location.href);
    url.searchParams.set(param, value);
    window.history.replaceState({}, '', url.toString());
  },

  // 移除查询参数
  removeQueryParam: (param: string): void => {
    const url = new URL(window.location.href);
    url.searchParams.delete(param);
    window.history.replaceState({}, '', url.toString());
  },
};

// 防抖函数
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// 节流函数
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// 深拷贝
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;
  if (typeof obj === 'object') {
    const cloned = {} as T;
    Object.keys(obj).forEach(key => {
      (cloned as any)[key] = deepClone((obj as any)[key]);
    });
    return cloned;
  }
  return obj;
};

// 生成唯一ID
export const generateId = (prefix: string = 'id'): string => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// 数组工具
export const arrayUtils = {
  // 数组去重
  unique: <T>(array: T[]): T[] => {
    return Array.from(new Set(array));
  },

  // 数组分组
  groupBy: <T>(array: T[], key: keyof T): Record<string, T[]> => {
    return array.reduce((groups, item) => {
      const group = String(item[key]);
      groups[group] = groups[group] || [];
      groups[group].push(item);
      return groups;
    }, {} as Record<string, T[]>);
  },

  // 数组排序
  sortBy: <T>(array: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] => {
    return [...array].sort((a, b) => {
      const aVal = a[key];
      const bVal = b[key];
      
      if (aVal < bVal) return order === 'asc' ? -1 : 1;
      if (aVal > bVal) return order === 'asc' ? 1 : -1;
      return 0;
    });
  },

  // 数组分页
  paginate: <T>(array: T[], page: number, pageSize: number): T[] => {
    const startIndex = (page - 1) * pageSize;
    return array.slice(startIndex, startIndex + pageSize);
  },
};

// 文件工具
export const fileUtils = {
  // 下载文件
  download: (data: any, filename: string, type: string = 'application/json'): void => {
    const blob = new Blob([data], { type });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // 读取文件
  readFile: (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  },

  // 格式化文件大小
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
};

// 错误处理工具
export const errorUtils = {
  // 解析错误信息
  parseError: (error: any): string => {
    if (typeof error === 'string') return error;
    if (error?.message) return error.message;
    if (error?.response?.data?.message) return error.response.data.message;
    return '未知错误';
  },

  // 错误重试
  retry: async <T>(
    fn: () => Promise<T>,
    retries: number = 3,
    delay: number = 1000
  ): Promise<T> => {
    try {
      return await fn();
    } catch (error) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
        return retry(fn, retries - 1, delay);
      }
      throw error;
    }
  },
};

// 交易相关工具
export const tradingUtils = {
  // 计算盈亏
  calculatePnL: (
    quantity: number,
    buyPrice: number,
    currentPrice: number
  ): number => {
    return (currentPrice - buyPrice) * quantity;
  },

  // 计算盈亏率
  calculatePnLRatio: (
    quantity: number,
    buyPrice: number,
    currentPrice: number
  ): number => {
    const cost = buyPrice * quantity;
    const pnl = tradingUtils.calculatePnL(quantity, buyPrice, currentPrice);
    return cost > 0 ? (pnl / cost) * 100 : 0;
  },

  // 计算手续费
  calculateCommission: (
    amount: number,
    rate: number = 0.0003,
    minCommission: number = 5
  ): number => {
    return Math.max(amount * rate, minCommission);
  },

  // 计算总成本
  calculateTotalCost: (
    quantity: number,
    price: number,
    commissionRate: number = 0.0003
  ): number => {
    const amount = quantity * price;
    const commission = tradingUtils.calculateCommission(amount, commissionRate);
    return amount + commission;
  },

  // 风险计算
  calculateRisk: (
    portfolioValue: number,
    positionValue: number
  ): number => {
    return portfolioValue > 0 ? (positionValue / portfolioValue) * 100 : 0;
  },
};

// 导出所有工具
export default {
  formatNumber,
  formatCurrency,
  formatPercentage,
  formatLargeNumber,
  formatTime,
  formatRelativeTime,
  getStatusColor,
  getPnLColor,
  validators,
  storage,
  urlUtils,
  debounce,
  throttle,
  deepClone,
  generateId,
  arrayUtils,
  fileUtils,
  errorUtils,
  tradingUtils,
};
