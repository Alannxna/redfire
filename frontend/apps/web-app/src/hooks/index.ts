import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { message, notification } from 'antd';
import { apiClient } from '@redfire/api-client';
import { debounce, throttle } from '../utils';

// WebSocket Hook
export const useWebSocket = (url: string, options: {
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnect?: boolean;
  reconnectInterval?: number;
} = {}) => {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnect = true,
    reconnectInterval = 3000,
  } = options;

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        onOpen?.();
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (_err) {
          console.error('WebSocket message parse error:', _err);
        }
      };
      
      ws.onerror = (event) => {
        setError('WebSocket连接错误');
        onError?.(event);
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        setSocket(null);
        onClose?.();
        
        if (reconnect) {
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };
      
      setSocket(ws);
    } catch {
      setError('WebSocket连接失败');
    }
  }, [url, onMessage, onError, onOpen, onClose, reconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socket) {
      socket.close();
    }
  }, [socket]);

  const sendMessage = useCallback((data: any) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(data));
    }
  }, [socket, isConnected]);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
};

// 本地存储Hook
export const useLocalStorage = <T>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (_error) {
      console.error('Error reading from localStorage:', _error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (_error) {
      console.error('Error writing to localStorage:', _error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue] as const;
};

// 防抖Hook
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// 防抖回调Hook
export const useDebouncedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
) => {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  return useMemo(
    () => debounce((...args: Parameters<T>) => callbackRef.current(...args), delay),
    [delay]
  );
};

// 节流Hook
export const useThrottle = <T>(value: T, limit: number): T => {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRan = useRef(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        setThrottledValue(value);
        lastRan.current = Date.now();
      }
    }, limit - (Date.now() - lastRan.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, limit]);

  return throttledValue;
};

// 节流回调Hook
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  limit: number
) => {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  return useMemo(
    () => throttle((...args: Parameters<T>) => callbackRef.current(...args), limit),
    [limit]
  );
};

// 页面可见性Hook
export const usePageVisibility = () => {
  const [isVisible, setIsVisible] = useState(!document.hidden);

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return isVisible;
};

// 网络状态Hook
export const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};

// 窗口尺寸Hook
export const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const handleResize = throttle(() => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }, 100);

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
};

// 响应式断点Hook
export const useBreakpoint = () => {
  const { width } = useWindowSize();

  return useMemo(() => ({
    xs: width < 576,
    sm: width >= 576 && width < 768,
    md: width >= 768 && width < 992,
    lg: width >= 992 && width < 1200,
    xl: width >= 1200 && width < 1600,
    xxl: width >= 1600,
    mobile: width < 768,
    tablet: width >= 768 && width < 1200,
    desktop: width >= 1200,
  }), [width]);
};

// 定时器Hook
export const useInterval = (callback: () => void, delay: number | null) => {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay !== null) {
      const id = setInterval(() => savedCallback.current(), delay);
      return () => clearInterval(id);
    }
  }, [delay]);
};

// 超时Hook
export const useTimeout = (callback: () => void, delay: number | null) => {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay !== null) {
      const id = setTimeout(() => savedCallback.current(), delay);
      return () => clearTimeout(id);
    }
  }, [delay]);
};

// 异步状态Hook
export const useAsync = <T, E = Error>(
  asyncFunction: () => Promise<T>,
  immediate = true
) => {
  const [status, setStatus] = useState<'idle' | 'pending' | 'success' | 'error'>('idle');
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<E | null>(null);

  const execute = useCallback(async () => {
    setStatus('pending');
    setData(null);
    setError(null);

    try {
      const response = await asyncFunction();
      setData(response);
      setStatus('success');
      return response;
    } catch (_error) {
      setError(_error as E);
      setStatus('error');
      throw _error;
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return {
    execute,
    status,
    data,
    error,
    isLoading: status === 'pending',
    isError: status === 'error',
    isSuccess: status === 'success',
    isIdle: status === 'idle',
  };
};

// 市场数据Hook
export const useMarketData = (symbols: string[] = []) => {
  return useQuery({
    queryKey: ['marketData', symbols],
    queryFn: () => apiClient.marketData.getMultipleQuotes(symbols),
    enabled: symbols.length > 0,
    refetchInterval: 3000, // 3秒更新一次
    staleTime: 1000, // 1秒内认为数据是新鲜的
  });
};

// 持仓数据Hook
export const usePositions = () => {
  return useQuery({
    queryKey: ['positions'],
    queryFn: () => apiClient.trading.getPositions(),
    refetchInterval: 5000, // 5秒更新一次
  });
};

// 订单数据Hook
export const useOrders = () => {
  return useQuery({
    queryKey: ['orders'],
    queryFn: () => apiClient.trading.getOrders(),
    refetchInterval: 2000, // 2秒更新一次
  });
};

// 策略数据Hook
export const useStrategies = () => {
  return useQuery({
    queryKey: ['strategies'],
    queryFn: () => apiClient.strategy.getStrategies(),
  });
};

// 交易Hook
export const useTrade = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tradeData: any) => apiClient.trading.placeOrder(tradeData),
    onSuccess: () => {
      message.success('交易订单提交成功');
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    },
    onError: (error: any) => {
      message.error(`交易失败: ${error.message}`);
    },
  });
};

// 策略控制Hook
export const useStrategyControl = () => {
  const queryClient = useQueryClient();

  const startStrategy = useMutation({
    mutationFn: (strategyId: string) => apiClient.strategy.startStrategy(strategyId),
    onSuccess: () => {
      message.success('策略启动成功');
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    },
    onError: (error: any) => {
      message.error(`策略启动失败: ${error.message}`);
    },
  });

  const stopStrategy = useMutation({
    mutationFn: (strategyId: string) => apiClient.strategy.stopStrategy(strategyId),
    onSuccess: () => {
      message.success('策略停止成功');
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    },
    onError: (error: any) => {
      message.error(`策略停止失败: ${error.message}`);
    },
  });

  return {
    startStrategy,
    stopStrategy,
  };
};

// 通知Hook
export const useNotification = () => {
  const success = useCallback((message: string, description?: string) => {
    notification.success({
      message,
      description,
      placement: 'topRight',
    });
  }, []);

  const error = useCallback((message: string, description?: string) => {
    notification.error({
      message,
      description,
      placement: 'topRight',
    });
  }, []);

  const warning = useCallback((message: string, description?: string) => {
    notification.warning({
      message,
      description,
      placement: 'topRight',
    });
  }, []);

  const info = useCallback((message: string, description?: string) => {
    notification.info({
      message,
      description,
      placement: 'topRight',
    });
  }, []);

  return {
    success,
    error,
    warning,
    info,
  };
};

// 实时数据Hook
export const useRealtimeData = (endpoint: string) => {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const isPageVisible = usePageVisibility();
  const isOnline = useOnlineStatus();

  const wsUrl = `ws://localhost:8001/${endpoint}`;

  const { isConnected, sendMessage } = useWebSocket(wsUrl, {
    onMessage: setData,
    onError: () => setError('实时数据连接失败'),
    onOpen: () => setError(null),
  });

  // 页面不可见或离线时暂停数据更新
  useEffect(() => {
    if (!isPageVisible || !isOnline) {
      // 可以发送暂停消息给服务器
      sendMessage({ action: 'pause' });
    } else {
      // 恢复数据更新
      sendMessage({ action: 'resume' });
    }
  }, [isPageVisible, isOnline, sendMessage]);

  return {
    data,
    error,
    isConnected: isConnected && isOnline,
  };
};

// 拖拽Hook
export const useDrag = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragData, setDragData] = useState<any>(null);

  const handleDragStart = useCallback((data: any) => {
    setIsDragging(true);
    setDragData(data);
  }, []);

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    setDragData(null);
  }, []);

  return {
    isDragging,
    dragData,
    handleDragStart,
    handleDragEnd,
  };
};

// 剪贴板Hook
export const useClipboard = () => {
  const [text, setText] = useState('');

  const copy = useCallback(async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setText(value);
      message.success('已复制到剪贴板');
      return true;
    } catch {
      message.error('复制失败');
      return false;
    }
  }, []);

  const paste = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      setText(text);
      return text;
    } catch {
      message.error('粘贴失败');
      return '';
    }
  }, []);

  return {
    text,
    copy,
    paste,
  };
};

// 导出所有Hook
export {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
