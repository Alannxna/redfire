import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { devtools } from 'zustand/middleware';

// 用户状态接口
interface UserState {
  user: {
    id: string;
    name: string;
    email: string;
    avatar?: string;
    role: string;
  } | null;
  isAuthenticated: boolean;
  login: (user: any) => void;
  logout: () => void;
  updateUser: (userData: Partial<any>) => void;
}

// 应用设置状态接口
interface AppState {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-CN' | 'en-US';
  sidebarCollapsed: boolean;
  notifications: boolean;
  autoSave: boolean;
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  setLanguage: (language: 'zh-CN' | 'en-US') => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setNotifications: (enabled: boolean) => void;
  setAutoSave: (enabled: boolean) => void;
}

// 交易状态接口
interface TradingState {
  positions: any[];
  orders: any[];
  balance: {
    total: number;
    available: number;
    frozen: number;
  };
  selectedSymbol: string | null;
  watchlist: string[];
  addPosition: (position: any) => void;
  removePosition: (positionId: string) => void;
  updatePosition: (positionId: string, updates: any) => void;
  addOrder: (order: any) => void;
  removeOrder: (orderId: string) => void;
  updateOrder: (orderId: string, updates: any) => void;
  setBalance: (balance: any) => void;
  setSelectedSymbol: (symbol: string | null) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
}

// 策略状态接口
interface StrategyState {
  strategies: any[];
  activeStrategies: string[];
  strategyPerformance: Record<string, any>;
  addStrategy: (strategy: any) => void;
  removeStrategy: (strategyId: string) => void;
  updateStrategy: (strategyId: string, updates: any) => void;
  startStrategy: (strategyId: string) => void;
  stopStrategy: (strategyId: string) => void;
  updatePerformance: (strategyId: string, performance: any) => void;
}

// 用户状态管理
export const useUserStore = create<UserState>()(
  devtools(
    persist(
      (set, _get) => ({
        user: null,
        isAuthenticated: false,
        
        login: (user) => {
          set({
            user,
            isAuthenticated: true,
          });
        },
        
        logout: () => {
          set({
            user: null,
            isAuthenticated: false,
          });
        },
        
        updateUser: (userData) => {
          const currentUser = get().user;
          if (currentUser) {
            set({
              user: { ...currentUser, ...userData },
            });
          }
        },
      }),
      {
        name: 'user-storage',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'UserStore' }
  )
);

// 应用设置状态管理
export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, _get) => ({
        theme: 'light',
        language: 'zh-CN',
        sidebarCollapsed: false,
        notifications: true,
        autoSave: true,
        
        setTheme: (theme) => {
          set({ theme });
        },
        
        setLanguage: (language) => {
          set({ language });
        },
        
        toggleSidebar: () => {
          set((state) => ({
            sidebarCollapsed: !state.sidebarCollapsed,
          }));
        },
        
        setSidebarCollapsed: (collapsed) => {
          set({ sidebarCollapsed: collapsed });
        },
        
        setNotifications: (enabled) => {
          set({ notifications: enabled });
        },
        
        setAutoSave: (enabled) => {
          set({ autoSave: enabled });
        },
      }),
      {
        name: 'app-settings',
      }
    ),
    { name: 'AppStore' }
  )
);

// 交易状态管理
export const useTradingStore = create<TradingState>()(
  devtools(
    (set, _get) => ({
      positions: [],
      orders: [],
      balance: {
        total: 0,
        available: 0,
        frozen: 0,
      },
      selectedSymbol: null,
      watchlist: [],
      
      addPosition: (position) => {
        set((state) => ({
          positions: [...state.positions, position],
        }));
      },
      
      removePosition: (positionId) => {
        set((state) => ({
          positions: state.positions.filter((p) => p.id !== positionId),
        }));
      },
      
      updatePosition: (positionId, updates) => {
        set((state) => ({
          positions: state.positions.map((p) =>
            p.id === positionId ? { ...p, ...updates } : p
          ),
        }));
      },
      
      addOrder: (order) => {
        set((state) => ({
          orders: [...state.orders, { ...order, id: Date.now().toString() }],
        }));
      },
      
      removeOrder: (orderId) => {
        set((state) => ({
          orders: state.orders.filter((o) => o.id !== orderId),
        }));
      },
      
      updateOrder: (orderId, updates) => {
        set((state) => ({
          orders: state.orders.map((o) =>
            o.id === orderId ? { ...o, ...updates } : o
          ),
        }));
      },
      
      setBalance: (balance) => {
        set({ balance });
      },
      
      setSelectedSymbol: (symbol) => {
        set({ selectedSymbol: symbol });
      },
      
      addToWatchlist: (symbol) => {
        set((state) => ({
          watchlist: state.watchlist.includes(symbol)
            ? state.watchlist
            : [...state.watchlist, symbol],
        }));
      },
      
      removeFromWatchlist: (symbol) => {
        set((state) => ({
          watchlist: state.watchlist.filter((s) => s !== symbol),
        }));
      },
    }),
    { name: 'TradingStore' }
  )
);

// 策略状态管理
export const useStrategyStore = create<StrategyState>()(
  devtools(
    (set, _get) => ({
      strategies: [],
      activeStrategies: [],
      strategyPerformance: {},
      
      addStrategy: (strategy) => {
        set((state) => ({
          strategies: [
            ...state.strategies,
            { ...strategy, id: Date.now().toString() },
          ],
        }));
      },
      
      removeStrategy: (strategyId) => {
        set((state) => ({
          strategies: state.strategies.filter((s) => s.id !== strategyId),
          activeStrategies: state.activeStrategies.filter((id) => id !== strategyId),
        }));
      },
      
      updateStrategy: (strategyId, updates) => {
        set((state) => ({
          strategies: state.strategies.map((s) =>
            s.id === strategyId ? { ...s, ...updates } : s
          ),
        }));
      },
      
      startStrategy: (strategyId) => {
        set((state) => ({
          activeStrategies: state.activeStrategies.includes(strategyId)
            ? state.activeStrategies
            : [...state.activeStrategies, strategyId],
        }));
      },
      
      stopStrategy: (strategyId) => {
        set((state) => ({
          activeStrategies: state.activeStrategies.filter((id) => id !== strategyId),
        }));
      },
      
      updatePerformance: (strategyId, performance) => {
        set((state) => ({
          strategyPerformance: {
            ...state.strategyPerformance,
            [strategyId]: performance,
          },
        }));
      },
    }),
    { name: 'StrategyStore' }
  )
);

// 导出所有store的类型
export type {
  UserState,
  AppState,
  TradingState,
  StrategyState,
};

// 组合store hook，用于获取所有状态
export const useStores = () => ({
  user: useUserStore(),
  app: useAppStore(),
  trading: useTradingStore(),
  strategy: useStrategyStore(),
});

// 选择器工具函数
export const createSelector = <T, R>(selector: (state: T) => R) => selector;

// 常用选择器
export const userSelectors = {
  isAuthenticated: (state: UserState) => state.isAuthenticated,
  user: (state: UserState) => state.user,
  userName: (state: UserState) => state.user?.name || '',
};

export const appSelectors = {
  theme: (state: AppState) => state.theme,
  language: (state: AppState) => state.language,
  sidebarCollapsed: (state: AppState) => state.sidebarCollapsed,
};

export const tradingSelectors = {
  totalBalance: (state: TradingState) => state.balance.total,
  availableBalance: (state: TradingState) => state.balance.available,
  positionCount: (state: TradingState) => state.positions.length,
  orderCount: (state: TradingState) => state.orders.length,
};

export const strategySelectors = {
  totalStrategies: (state: StrategyState) => state.strategies.length,
  activeStrategyCount: (state: StrategyState) => state.activeStrategies.length,
  runningStrategies: (state: StrategyState) =>
    state.strategies.filter((s) => state.activeStrategies.includes(s.id)),
};
