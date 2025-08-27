// 交易相关类型定义

export type OrderType = 'market' | 'limit' | 'stop';
export type OrderSide = 'buy' | 'sell';
export type OrderStatus = 'pending' | 'filled' | 'cancelled' | 'rejected';

export interface Order {
  id: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  price?: number;
  status: OrderStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  averagePrice: number;
  unrealizedPnL: number;
  realizedPnL: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface Trade {
  id: string;
  orderId: string;
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: number;
  timestamp: Date;
  fee: number;
}

// 图表数据类型
export interface ChartData {
  timestamp: number;
  value: number;
}

export interface CandlestickData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface LineData {
  timestamp: number;
  value: number;
}

export interface BarData {
  timestamp: number;
  value: number;
}

export interface AreaData {
  timestamp: number;
  value: number;
}
