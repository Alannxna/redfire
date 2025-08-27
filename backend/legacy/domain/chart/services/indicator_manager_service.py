"""
指标管理器领域服务
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np

from ..entities.bar_data_entity import BarData
from ..entities.indicator_entity import Indicator
from ..value_objects.indicator_type import IndicatorType

logger = logging.getLogger(__name__)


@dataclass
class IndicatorCalculationResult:
    """指标计算结果"""
    indicator_id: str
    success: bool
    values: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    calculation_time: datetime = field(default_factory=datetime.now)


class IndicatorManagerService:
    """
    指标管理器领域服务
    
    负责管理和计算各种技术指标
    """
    
    def __init__(self):
        self.symbol_indicators: Dict[str, List[Indicator]] = {}
        self.calculation_cache: Dict[str, IndicatorCalculationResult] = {}
        
    def add_indicator(
        self, 
        symbol: str, 
        indicator: Indicator
    ) -> bool:
        """
        为指定品种添加技术指标
        
        Args:
            symbol: 交易品种
            indicator: 指标实例
            
        Returns:
            bool: 是否添加成功
        """
        try:
            if symbol not in self.symbol_indicators:
                self.symbol_indicators[symbol] = []
            
            # 检查是否已存在相同的指标
            existing_indicator = self._find_indicator(symbol, indicator.name)
            if existing_indicator:
                logger.warning(f"指标 {indicator.name} 已存在于品种 {symbol}")
                return False
            
            self.symbol_indicators[symbol].append(indicator)
            logger.info(f"成功添加指标 {indicator.name} 到品种 {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"添加指标失败: {e}")
            return False
    
    def remove_indicator(self, symbol: str, indicator_name: str) -> bool:
        """
        移除指定的技术指标
        
        Args:
            symbol: 交易品种
            indicator_name: 指标名称
            
        Returns:
            bool: 是否移除成功
        """
        try:
            if symbol not in self.symbol_indicators:
                return False
            
            indicators = self.symbol_indicators[symbol]
            for i, indicator in enumerate(indicators):
                if indicator.name == indicator_name:
                    indicators.pop(i)
                    # 清理缓存
                    cache_key = f"{symbol}_{indicator_name}"
                    if cache_key in self.calculation_cache:
                        del self.calculation_cache[cache_key]
                    logger.info(f"成功移除指标 {indicator_name} 从品种 {symbol}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"移除指标失败: {e}")
            return False
    
    def calculate_all(self, symbol: str, bars: List[BarData]) -> Dict[str, Any]:
        """
        计算指定品种的所有指标
        
        Args:
            symbol: 交易品种
            bars: K线数据
            
        Returns:
            Dict[str, Any]: 指标计算结果
        """
        if symbol not in self.symbol_indicators:
            return {}
        
        if not bars:
            return {}
        
        # 转换为DataFrame
        df = self._bars_to_dataframe(bars)
        
        results = {}
        for indicator in self.symbol_indicators[symbol]:
            try:
                if indicator.is_active():
                    calculation_result = self._calculate_indicator(indicator, df)
                    results[indicator.name] = calculation_result.values
                    
                    # 更新缓存
                    cache_key = f"{symbol}_{indicator.name}"
                    self.calculation_cache[cache_key] = calculation_result
                    
            except Exception as e:
                logger.error(f"计算指标 {indicator.name} 失败: {e}")
                results[indicator.name] = {"error": str(e)}
        
        return results
    
    def calculate_single(
        self, 
        symbol: str, 
        indicator_name: str, 
        bars: List[BarData]
    ) -> IndicatorCalculationResult:
        """
        计算单个指标
        
        Args:
            symbol: 交易品种
            indicator_name: 指标名称
            bars: K线数据
            
        Returns:
            IndicatorCalculationResult: 计算结果
        """
        indicator = self._find_indicator(symbol, indicator_name)
        if not indicator:
            return IndicatorCalculationResult(
                indicator_id=indicator_name,
                success=False,
                error="指标未找到"
            )
        
        if not bars:
            return IndicatorCalculationResult(
                indicator_id=indicator.indicator_id,
                success=False,
                error="K线数据为空"
            )
        
        df = self._bars_to_dataframe(bars)
        return self._calculate_indicator(indicator, df)
    
    def get_indicators(self, symbol: str) -> List[Indicator]:
        """获取指定品种的所有指标"""
        return self.symbol_indicators.get(symbol, [])
    
    def get_indicator(self, symbol: str, indicator_name: str) -> Optional[Indicator]:
        """获取指定指标"""
        return self._find_indicator(symbol, indicator_name)
    
    def _find_indicator(self, symbol: str, indicator_name: str) -> Optional[Indicator]:
        """查找指标"""
        if symbol not in self.symbol_indicators:
            return None
        
        for indicator in self.symbol_indicators[symbol]:
            if indicator.name == indicator_name:
                return indicator
        
        return None
    
    def _bars_to_dataframe(self, bars: List[BarData]) -> pd.DataFrame:
        """将K线数据转换为DataFrame"""
        data = []
        for bar in bars:
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
    
    def _calculate_indicator(
        self, 
        indicator: Indicator, 
        df: pd.DataFrame
    ) -> IndicatorCalculationResult:
        """
        计算指标值
        
        Args:
            indicator: 指标实例
            df: 价格数据DataFrame
            
        Returns:
            IndicatorCalculationResult: 计算结果
        """
        try:
            indicator_type = indicator.indicator_type
            parameters = indicator.parameters
            
            # 根据指标类型计算
            if indicator_type == IndicatorType.SMA:
                values = self._calculate_sma(df, parameters)
            elif indicator_type == IndicatorType.EMA:
                values = self._calculate_ema(df, parameters)
            elif indicator_type == IndicatorType.MACD:
                values = self._calculate_macd(df, parameters)
            elif indicator_type == IndicatorType.RSI:
                values = self._calculate_rsi(df, parameters)
            elif indicator_type == IndicatorType.BOLLINGER_BANDS:
                values = self._calculate_bollinger_bands(df, parameters)
            elif indicator_type == IndicatorType.KDJ:
                values = self._calculate_kdj(df, parameters)
            elif indicator_type == IndicatorType.VOLUME:
                values = self._calculate_volume(df, parameters)
            else:
                raise ValueError(f"不支持的指标类型: {indicator_type}")
            
            return IndicatorCalculationResult(
                indicator_id=indicator.indicator_id,
                success=True,
                values=values
            )
            
        except Exception as e:
            logger.error(f"计算指标失败: {e}")
            return IndicatorCalculationResult(
                indicator_id=indicator.indicator_id,
                success=False,
                error=str(e)
            )
    
    def _calculate_sma(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算简单移动平均线"""
        period = params.get('period', 20)
        price_type = params.get('price_type', 'close')
        
        sma_values = df[price_type].rolling(window=period).mean()
        
        return {
            'values': sma_values.dropna().tolist(),
            'timestamps': sma_values.dropna().index.tolist(),
            'period': period,
            'price_type': price_type
        }
    
    def _calculate_ema(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算指数移动平均线"""
        period = params.get('period', 12)
        price_type = params.get('price_type', 'close')
        
        ema_values = df[price_type].ewm(span=period).mean()
        
        return {
            'values': ema_values.dropna().tolist(),
            'timestamps': ema_values.dropna().index.tolist(),
            'period': period,
            'price_type': price_type
        }
    
    def _calculate_macd(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算MACD指标"""
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        signal_period = params.get('signal_period', 9)
        price_type = params.get('price_type', 'close')
        
        prices = df[price_type]
        
        # 计算快线和慢线EMA
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        
        # MACD线 = 快线EMA - 慢线EMA
        macd_line = ema_fast - ema_slow
        
        # 信号线 = MACD线的EMA
        signal_line = macd_line.ewm(span=signal_period).mean()
        
        # 柱状图 = MACD线 - 信号线
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.dropna().tolist(),
            'signal': signal_line.dropna().tolist(),
            'histogram': histogram.dropna().tolist(),
            'timestamps': macd_line.dropna().index.tolist(),
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period
        }
    
    def _calculate_rsi(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算RSI指标"""
        period = params.get('period', 14)
        price_type = params.get('price_type', 'close')
        
        prices = df[price_type]
        delta = prices.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            'values': rsi.dropna().tolist(),
            'timestamps': rsi.dropna().index.tolist(),
            'period': period,
            'overbought_level': 70,
            'oversold_level': 30
        }
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算布林带指标"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)
        price_type = params.get('price_type', 'close')
        
        prices = df[price_type]
        
        # 中轨线（移动平均）
        middle_band = prices.rolling(window=period).mean()
        
        # 标准差
        std = prices.rolling(window=period).std()
        
        # 上轨线和下轨线
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return {
            'upper': upper_band.dropna().tolist(),
            'middle': middle_band.dropna().tolist(),
            'lower': lower_band.dropna().tolist(),
            'timestamps': middle_band.dropna().index.tolist(),
            'period': period,
            'std_dev': std_dev
        }
    
    def _calculate_kdj(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算KDJ指标"""
        period = params.get('period', 9)
        k_period = params.get('k_period', 3)
        d_period = params.get('d_period', 3)
        
        # 计算RSV (Raw Stochastic Value)
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        
        # 计算K值
        k_values = rsv.ewm(alpha=1/k_period).mean()
        
        # 计算D值
        d_values = k_values.ewm(alpha=1/d_period).mean()
        
        # 计算J值
        j_values = 3 * k_values - 2 * d_values
        
        return {
            'k': k_values.dropna().tolist(),
            'd': d_values.dropna().tolist(),
            'j': j_values.dropna().tolist(),
            'timestamps': k_values.dropna().index.tolist(),
            'period': period,
            'k_period': k_period,
            'd_period': d_period
        }
    
    def _calculate_volume(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算成交量相关指标"""
        volume_type = params.get('volume_type', 'volume')
        ma_period = params.get('ma_period', 20)
        
        volume = df['volume']
        volume_ma = volume.rolling(window=ma_period).mean()
        
        return {
            'volume': volume.tolist(),
            'volume_ma': volume_ma.dropna().tolist(),
            'timestamps': volume.index.tolist(),
            'ma_period': ma_period
        }
