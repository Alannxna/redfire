"""
指标计算领域服务
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from decimal import Decimal

from ..entities.bar_data_entity import BarData
from ..entities.indicator_entity import Indicator
from ..value_objects.indicator_type import IndicatorType


class IndicatorCalculationService:
    """
    指标计算领域服务
    
    负责各种技术指标的计算逻辑
    """
    
    def calculate_indicator(self, indicator: Indicator, bars: List[BarData]) -> Dict[str, Any]:
        """计算指标值"""
        if not bars:
            return {"values": [], "error": "没有数据"}
        
        try:
            # 转换数据格式
            df = self._bars_to_dataframe(bars)
            
            # 根据指标类型计算
            if indicator.indicator_type == IndicatorType.MA:
                return self._calculate_ma(df, indicator.parameters)
            elif indicator.indicator_type == IndicatorType.EMA:
                return self._calculate_ema(df, indicator.parameters)
            elif indicator.indicator_type == IndicatorType.RSI:
                return self._calculate_rsi(df, indicator.parameters)
            elif indicator.indicator_type == IndicatorType.MACD:
                return self._calculate_macd(df, indicator.parameters)
            elif indicator.indicator_type == IndicatorType.BOLL:
                return self._calculate_bollinger_bands(df, indicator.parameters)
            elif indicator.indicator_type == IndicatorType.KDJ:
                return self._calculate_kdj(df, indicator.parameters)
            elif indicator.indicator_type == IndicatorType.VOL:
                return self._calculate_volume(df, indicator.parameters)
            else:
                return {"values": [], "error": f"不支持的指标类型: {indicator.indicator_type}"}
        
        except Exception as e:
            return {"values": [], "error": str(e)}
    
    def _bars_to_dataframe(self, bars: List[BarData]) -> pd.DataFrame:
        """将K线数据转换为DataFrame"""
        data = []
        for bar in sorted(bars, key=lambda x: x.datetime):
            data.append({
                'datetime': bar.datetime,
                'open': float(bar.open_price),
                'high': float(bar.high_price),
                'low': float(bar.low_price),
                'close': float(bar.close_price),
                'volume': float(bar.volume)
            })
        
        df = pd.DataFrame(data)
        df.set_index('datetime', inplace=True)
        return df
    
    def _calculate_ma(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算移动平均线"""
        period = params.get('period', 20)
        
        if len(df) < period:
            return {"values": [], "error": f"数据不足，需要至少{period}根K线"}
        
        ma_values = df['close'].rolling(window=period).mean()
        
        return {
            "values": [
                {
                    "datetime": idx,
                    "value": float(val) if not pd.isna(val) else None
                }
                for idx, val in ma_values.items()
            ],
            "error": None
        }
    
    def _calculate_ema(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算指数移动平均线"""
        period = params.get('period', 20)
        
        if len(df) < period:
            return {"values": [], "error": f"数据不足，需要至少{period}根K线"}
        
        ema_values = df['close'].ewm(span=period).mean()
        
        return {
            "values": [
                {
                    "datetime": idx,
                    "value": float(val) if not pd.isna(val) else None
                }
                for idx, val in ema_values.items()
            ],
            "error": None
        }
    
    def _calculate_rsi(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算RSI指标"""
        period = params.get('period', 14)
        
        if len(df) < period + 1:
            return {"values": [], "error": f"数据不足，需要至少{period + 1}根K线"}
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            "values": [
                {
                    "datetime": idx,
                    "value": float(val) if not pd.isna(val) else None
                }
                for idx, val in rsi.items()
            ],
            "error": None
        }
    
    def _calculate_macd(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算MACD指标"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        
        if len(df) < slow + signal:
            return {"values": [], "error": f"数据不足，需要至少{slow + signal}根K线"}
        
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            "values": [
                {
                    "datetime": idx,
                    "macd": float(macd_line[idx]) if not pd.isna(macd_line[idx]) else None,
                    "signal": float(signal_line[idx]) if not pd.isna(signal_line[idx]) else None,
                    "histogram": float(histogram[idx]) if not pd.isna(histogram[idx]) else None
                }
                for idx in df.index
            ],
            "error": None
        }
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算布林带"""
        period = params.get('period', 20)
        std_multiplier = params.get('std', 2)
        
        if len(df) < period:
            return {"values": [], "error": f"数据不足，需要至少{period}根K线"}
        
        ma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper_band = ma + (std * std_multiplier)
        lower_band = ma - (std * std_multiplier)
        
        return {
            "values": [
                {
                    "datetime": idx,
                    "upper": float(upper_band[idx]) if not pd.isna(upper_band[idx]) else None,
                    "middle": float(ma[idx]) if not pd.isna(ma[idx]) else None,
                    "lower": float(lower_band[idx]) if not pd.isna(lower_band[idx]) else None
                }
                for idx in df.index
            ],
            "error": None
        }
    
    def _calculate_kdj(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算KDJ指标"""
        n = params.get('n', 9)
        m1 = params.get('m1', 3)
        m2 = params.get('m2', 3)
        
        if len(df) < n:
            return {"values": [], "error": f"数据不足，需要至少{n}根K线"}
        
        low_min = df['low'].rolling(window=n).min()
        high_max = df['high'].rolling(window=n).max()
        
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        
        k_values = []
        d_values = []
        j_values = []
        
        k = 50.0  # 初始值
        d = 50.0  # 初始值
        
        for rsv_val in rsv:
            if pd.isna(rsv_val):
                k_values.append(None)
                d_values.append(None)
                j_values.append(None)
            else:
                k = (k * (m1 - 1) + rsv_val) / m1
                d = (d * (m2 - 1) + k) / m2
                j = 3 * k - 2 * d
                
                k_values.append(k)
                d_values.append(d)
                j_values.append(j)
        
        return {
            "values": [
                {
                    "datetime": idx,
                    "k": k_values[i] if k_values[i] is not None else None,
                    "d": d_values[i] if d_values[i] is not None else None,
                    "j": j_values[i] if j_values[i] is not None else None
                }
                for i, idx in enumerate(df.index)
            ],
            "error": None
        }
    
    def _calculate_volume(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算成交量"""
        return {
            "values": [
                {
                    "datetime": idx,
                    "volume": float(vol)
                }
                for idx, vol in df['volume'].items()
            ],
            "error": None
        }
