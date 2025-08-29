"""
技术指标计算器 - 基于vnpy-core技术指标算法

移植vnpy强大的技术指标计算能力到Web图表引擎
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import asyncio

from ..models.chart_models import (
    BarData, IndicatorData, IndicatorType, IndicatorConfig
)
from ..utils.performance import PerformanceMonitor
from ..utils.cache import LRUCache

logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    """计算结果"""
    indicator_name: str
    indicator_type: IndicatorType
    values: Dict[str, List[float]]
    timestamps: List[datetime]
    calculation_time: float
    
    def to_indicator_data(self) -> IndicatorData:
        """转换为指标数据"""
        return IndicatorData(
            name=self.indicator_name,
            type=self.indicator_type,
            values=self.values,
            timestamps=self.timestamps
        )


class TechnicalIndicators:
    """
    技术指标计算核心 - 基于vnpy-core的指标算法
    
    实现常用的技术指标计算，包括：
    - 移动平均线 (MA, EMA)
    - MACD
    - RSI
    - 布林带 (BOLL)
    - KDJ
    - 等等
    """
    
    @staticmethod
    def sma(prices: np.ndarray, period: int) -> np.ndarray:
        """简单移动平均线 - Simple Moving Average"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)
        
        result = np.full(len(prices), np.nan)
        for i in range(period - 1, len(prices)):
            result[i] = np.mean(prices[i - period + 1:i + 1])
        
        return result
    
    @staticmethod
    def ema(prices: np.ndarray, period: int) -> np.ndarray:
        """指数移动平均线 - Exponential Moving Average"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)
        
        result = np.full(len(prices), np.nan)
        multiplier = 2.0 / (period + 1)
        
        # 第一个EMA值使用SMA
        result[period - 1] = np.mean(prices[:period])
        
        # 后续值使用EMA公式
        for i in range(period, len(prices)):
            result[i] = (prices[i] * multiplier) + (result[i - 1] * (1 - multiplier))
        
        return result
    
    @staticmethod
    def macd(
        prices: np.ndarray, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD指标"""
        # 计算快线和慢线EMA
        ema_fast = TechnicalIndicators.ema(prices, fast_period)
        ema_slow = TechnicalIndicators.ema(prices, slow_period)
        
        # MACD线 = 快线EMA - 慢线EMA
        macd_line = ema_fast - ema_slow
        
        # 信号线 = MACD线的EMA
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        
        # 柱状图 = MACD线 - 信号线
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """相对强弱指数 - Relative Strength Index"""
        if len(prices) < period + 1:
            return np.full(len(prices), np.nan)
        
        # 计算价格变化
        deltas = np.diff(prices)
        
        # 分离上涨和下跌
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # 计算平均涨幅和跌幅
        avg_gains = TechnicalIndicators.sma(gains, period)
        avg_losses = TechnicalIndicators.sma(losses, period)
        
        # 计算RSI
        rs = np.divide(avg_gains, avg_losses, out=np.zeros_like(avg_gains), where=avg_losses != 0)
        rsi = 100 - (100 / (1 + rs))
        
        # 在结果前面添加NaN，因为diff减少了一个元素
        result = np.full(len(prices), np.nan)
        result[1:] = rsi
        
        return result
    
    @staticmethod
    def bollinger_bands(
        prices: np.ndarray, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """布林带 - Bollinger Bands"""
        # 计算中轨 (移动平均线)
        middle = TechnicalIndicators.sma(prices, period)
        
        # 计算标准差
        result_upper = np.full(len(prices), np.nan)
        result_lower = np.full(len(prices), np.nan)
        
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            std = np.std(window)
            result_upper[i] = middle[i] + (std_dev * std)
            result_lower[i] = middle[i] - (std_dev * std)
        
        return result_upper, middle, result_lower
    
    @staticmethod
    def kdj(
        highs: np.ndarray, 
        lows: np.ndarray, 
        closes: np.ndarray, 
        period: int = 14,
        k_period: int = 3,
        d_period: int = 3
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """KDJ指标"""
        # 计算RSV (Raw Stochastic Value)
        rsv = np.full(len(closes), np.nan)
        
        for i in range(period - 1, len(closes)):
            highest_high = np.max(highs[i - period + 1:i + 1])
            lowest_low = np.min(lows[i - period + 1:i + 1])
            
            if highest_high != lowest_low:
                rsv[i] = (closes[i] - lowest_low) / (highest_high - lowest_low) * 100
            else:
                rsv[i] = 50
        
        # 计算K值 (RSV的移动平均)
        k_values = np.full(len(closes), np.nan)
        k_values[period - 1] = rsv[period - 1]
        
        for i in range(period, len(closes)):
            if not np.isnan(k_values[i - 1]) and not np.isnan(rsv[i]):
                k_values[i] = (k_values[i - 1] * (k_period - 1) + rsv[i]) / k_period
        
        # 计算D值 (K值的移动平均)
        d_values = np.full(len(closes), np.nan)
        d_values[period - 1] = k_values[period - 1]
        
        for i in range(period, len(closes)):
            if not np.isnan(d_values[i - 1]) and not np.isnan(k_values[i]):
                d_values[i] = (d_values[i - 1] * (d_period - 1) + k_values[i]) / d_period
        
        # 计算J值
        j_values = 3 * k_values - 2 * d_values
        
        return k_values, d_values, j_values
    
    @staticmethod
    def atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
        """平均真实波幅 - Average True Range"""
        if len(closes) < period + 1:
            return np.full(len(closes), np.nan)
        
        # 计算真实波幅 TR
        tr = np.full(len(closes), np.nan)
        
        for i in range(1, len(closes)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i - 1])
            tr3 = abs(lows[i] - closes[i - 1])
            tr[i] = max(tr1, tr2, tr3)
        
        # 计算ATR (TR的移动平均)
        atr_values = TechnicalIndicators.sma(tr, period)
        
        return atr_values


class IndicatorCalculationEngine:
    """
    单个图表的指标计算引擎
    """
    
    def __init__(self, chart_id: str):
        self.chart_id = chart_id
        self.cached_results: Dict[str, CalculationResult] = {}
        self.bars_cache: List[BarData] = []
        self.last_calculation_hash: Optional[str] = None
        
    def calculate_indicators(
        self, 
        bars: List[BarData], 
        indicator_configs: List[IndicatorConfig]
    ) -> Dict[str, IndicatorData]:
        """计算技术指标"""
        if not bars or not indicator_configs:
            return {}
        
        # 检查数据是否有变化
        current_hash = self._calculate_data_hash(bars, indicator_configs)
        if current_hash == self.last_calculation_hash:
            # 返回缓存结果
            return {name: result.to_indicator_data() for name, result in self.cached_results.items()}
        
        results = {}
        
        # 准备价格数组
        opens = np.array([bar.open_price for bar in bars])
        highs = np.array([bar.high_price for bar in bars])
        lows = np.array([bar.low_price for bar in bars])
        closes = np.array([bar.close_price for bar in bars])
        volumes = np.array([bar.volume for bar in bars])
        timestamps = [bar.datetime for bar in bars]
        
        # 计算每个指标
        for config in indicator_configs:
            try:
                start_time = datetime.now()
                
                if config.type == IndicatorType.MA:
                    values = self._calculate_ma(closes, config.parameters)
                elif config.type == IndicatorType.EMA:
                    values = self._calculate_ema(closes, config.parameters)
                elif config.type == IndicatorType.MACD:
                    values = self._calculate_macd(closes, config.parameters)
                elif config.type == IndicatorType.RSI:
                    values = self._calculate_rsi(closes, config.parameters)
                elif config.type == IndicatorType.BOLL:
                    values = self._calculate_bollinger(closes, config.parameters)
                elif config.type == IndicatorType.KDJ:
                    values = self._calculate_kdj(highs, lows, closes, config.parameters)
                elif config.type == IndicatorType.ATR:
                    values = self._calculate_atr(highs, lows, closes, config.parameters)
                else:
                    logger.warning(f"不支持的指标类型: {config.type}")
                    continue
                
                calculation_time = (datetime.now() - start_time).total_seconds()
                
                # 创建计算结果
                result = CalculationResult(
                    indicator_name=config.name,
                    indicator_type=config.type,
                    values=values,
                    timestamps=timestamps,
                    calculation_time=calculation_time
                )
                
                self.cached_results[config.name] = result
                results[config.name] = result.to_indicator_data()
                
            except Exception as e:
                logger.error(f"计算指标 {config.name} 失败: {e}")
        
        # 更新缓存
        self.bars_cache = bars.copy()
        self.last_calculation_hash = current_hash
        
        return results
    
    def _calculate_ma(self, prices: np.ndarray, params: Dict[str, Any]) -> Dict[str, List[float]]:
        """计算移动平均线"""
        period = params.get('period', 20)
        ma_values = TechnicalIndicators.sma(prices, period)
        return {"ma": ma_values.tolist()}
    
    def _calculate_ema(self, prices: np.ndarray, params: Dict[str, Any]) -> Dict[str, List[float]]:
        """计算指数移动平均线"""
        period = params.get('period', 20)
        ema_values = TechnicalIndicators.ema(prices, period)
        return {"ema": ema_values.tolist()}
    
    def _calculate_macd(self, prices: np.ndarray, params: Dict[str, Any]) -> Dict[str, List[float]]:
        """计算MACD"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        
        macd, signal_line, histogram = TechnicalIndicators.macd(prices, fast, slow, signal)
        
        return {
            "macd": macd.tolist(),
            "signal": signal_line.tolist(),
            "histogram": histogram.tolist()
        }
    
    def _calculate_rsi(self, prices: np.ndarray, params: Dict[str, Any]) -> Dict[str, List[float]]:
        """计算RSI"""
        period = params.get('period', 14)
        rsi_values = TechnicalIndicators.rsi(prices, period)
        return {"rsi": rsi_values.tolist()}
    
    def _calculate_bollinger(self, prices: np.ndarray, params: Dict[str, Any]) -> Dict[str, List[float]]:
        """计算布林带"""
        period = params.get('period', 20)
        std_dev = params.get('std', 2.0)
        
        upper, middle, lower = TechnicalIndicators.bollinger_bands(prices, period, std_dev)
        
        return {
            "upper": upper.tolist(),
            "middle": middle.tolist(),
            "lower": lower.tolist()
        }
    
    def _calculate_kdj(
        self, 
        highs: np.ndarray, 
        lows: np.ndarray, 
        closes: np.ndarray, 
        params: Dict[str, Any]
    ) -> Dict[str, List[float]]:
        """计算KDJ"""
        period = params.get('period', 14)
        k_period = params.get('k', 3)
        d_period = params.get('d', 3)
        
        k, d, j = TechnicalIndicators.kdj(highs, lows, closes, period, k_period, d_period)
        
        return {
            "k": k.tolist(),
            "d": d.tolist(),
            "j": j.tolist()
        }
    
    def _calculate_atr(
        self, 
        highs: np.ndarray, 
        lows: np.ndarray, 
        closes: np.ndarray, 
        params: Dict[str, Any]
    ) -> Dict[str, List[float]]:
        """计算ATR"""
        period = params.get('period', 14)
        atr_values = TechnicalIndicators.atr(highs, lows, closes, period)
        return {"atr": atr_values.tolist()}
    
    def _calculate_data_hash(self, bars: List[BarData], configs: List[IndicatorConfig]) -> str:
        """计算数据哈希用于缓存判断"""
        import hashlib
        
        # 组合数据和配置的哈希
        data_str = f"{len(bars)}"
        if bars:
            data_str += f"_{bars[-1].datetime}_{bars[-1].close_price}"
        
        config_str = "_".join([f"{c.type.value}_{c.parameters}" for c in configs])
        
        return hashlib.md5(f"{data_str}_{config_str}".encode()).hexdigest()


class IndicatorCalculator:
    """
    技术指标计算器管理器
    
    管理多个图表的指标计算引擎
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.engines: Dict[str, IndicatorCalculationEngine] = {}
        self.cache = LRUCache(self.config.get('cache_size', 500))
        self.performance_monitor = PerformanceMonitor()
        
        logger.info("技术指标计算器初始化完成")
    
    async def start(self) -> None:
        """启动计算器"""
        logger.info("技术指标计算器启动成功")
    
    async def stop(self) -> None:
        """停止计算器"""
        self.engines.clear()
        self.cache.clear()
        logger.info("技术指标计算器已停止")
    
    async def calculate_indicators(
        self, 
        chart_id: str, 
        bars: List[BarData], 
        indicator_configs: List[IndicatorConfig]
    ) -> Dict[str, IndicatorData]:
        """计算技术指标"""
        try:
            # 获取或创建计算引擎
            if chart_id not in self.engines:
                self.engines[chart_id] = IndicatorCalculationEngine(chart_id)
            
            engine = self.engines[chart_id]
            
            # 异步计算指标
            with self.performance_monitor.timer(f"calculate_indicators_{chart_id}"):
                results = engine.calculate_indicators(bars, indicator_configs)
            
            # 记录性能指标
            self.performance_monitor.increment_counter(f"indicator_calculations_{chart_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {}
    
    async def get_indicators(self, chart_id: str) -> Dict[str, IndicatorData]:
        """获取已计算的指标"""
        if chart_id not in self.engines:
            return {}
        
        engine = self.engines[chart_id]
        return {name: result.to_indicator_data() for name, result in engine.cached_results.items()}
    
    def get_calculator_status(self) -> Dict[str, Any]:
        """获取计算器状态"""
        return {
            "engines_count": len(self.engines),
            "cache_size": self.cache.size(),
            "cache_hit_rate": self.cache.get_hit_rate(),
            "performance": self.performance_monitor.get_metrics(),
            "config": self.config
        }
