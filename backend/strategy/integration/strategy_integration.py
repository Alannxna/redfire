"""
量化策略系统集成模块

提供一键式策略系统集成功能，包括：
- 策略引擎初始化和配置
- 回测引擎集成
- 风险管理集成
- 绩效分析集成
- FastAPI接口集成
- 数据源配置
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd

from ..core.strategy_base import BaseStrategy, StrategyConfig, StrategyType, MarketData
from ..core.strategy_engine import StrategyEngine, StrategyManager, EngineConfig
from ..core.backtest_engine import BacktestEngine, BacktestConfig
from ..core.risk_manager import RiskManager, RiskConfig
from ..core.performance_analyzer import PerformanceAnalyzer, PerformanceConfig


class StrategySystem:
    """
    统一策略系统
    
    集成所有策略相关组件，提供统一的管理接口。
    """
    
    def __init__(self, 
                 engine_config: Optional[EngineConfig] = None,
                 risk_config: Optional[RiskConfig] = None,
                 performance_config: Optional[PerformanceConfig] = None):
        """
        初始化策略系统
        
        Args:
            engine_config: 引擎配置
            risk_config: 风险管理配置
            performance_config: 绩效分析配置
        """
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self.engine = StrategyEngine(engine_config)
        self.manager = StrategyManager(self.engine)
        self.risk_manager = RiskManager(risk_config)
        self.performance_analyzer = PerformanceAnalyzer(performance_config)
        
        # 回测引擎（按需创建）
        self.backtest_engine: Optional[BacktestEngine] = None
        
        # 系统状态
        self._is_running = False
        self._strategies: Dict[str, BaseStrategy] = {}
        
        # 数据提供器
        self._data_provider: Optional[Callable] = None
        
        self.logger.info("策略系统初始化完成")
    
    async def start(self) -> bool:
        """启动策略系统"""
        try:
            if self._is_running:
                self.logger.warning("策略系统已在运行")
                return True
            
            self.logger.info("启动策略系统...")
            
            # 启动引擎
            if not await self.engine.start():
                return False
            
            # 启动风险管理
            if not await self.risk_manager.start_monitoring():
                return False
            
            # 启动绩效分析
            if not await self.performance_analyzer.start_monitoring():
                return False
            
            self._is_running = True
            self.logger.info("策略系统启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动策略系统失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止策略系统"""
        try:
            if not self._is_running:
                self.logger.warning("策略系统未运行")
                return True
            
            self.logger.info("停止策略系统...")
            
            # 停止绩效分析
            await self.performance_analyzer.stop_monitoring()
            
            # 停止风险管理
            await self.risk_manager.stop_monitoring()
            
            # 停止引擎
            await self.engine.stop()
            
            self._is_running = False
            self.logger.info("策略系统停止成功")
            return True
            
        except Exception as e:
            self.logger.error(f"停止策略系统失败: {e}")
            return False
    
    async def add_strategy(self, strategy: BaseStrategy) -> bool:
        """添加策略"""
        try:
            strategy_id = strategy.strategy_id
            
            # 添加到引擎
            if not await self.engine.add_strategy(strategy):
                return False
            
            # 添加到风险管理
            if not self.risk_manager.add_strategy(strategy):
                return False
            
            # 添加到绩效分析
            if not self.performance_analyzer.add_strategy(strategy):
                return False
            
            self._strategies[strategy_id] = strategy
            self.logger.info(f"策略添加成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    async def remove_strategy(self, strategy_id: str) -> bool:
        """移除策略"""
        try:
            # 从各组件移除
            await self.engine.remove_strategy(strategy_id)
            self.risk_manager.remove_strategy(strategy_id)
            self.performance_analyzer.remove_strategy(strategy_id)
            
            if strategy_id in self._strategies:
                del self._strategies[strategy_id]
            
            self.logger.info(f"策略移除成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除策略失败: {e}")
            return False
    
    async def start_strategy(self, strategy_id: str) -> bool:
        """启动策略"""
        return await self.engine.start_strategy(strategy_id)
    
    async def stop_strategy(self, strategy_id: str) -> bool:
        """停止策略"""
        return await self.engine.stop_strategy(strategy_id)
    
    async def feed_market_data(self, data: MarketData):
        """推送市场数据"""
        try:
            # 推送到引擎
            await self.engine.feed_data(data)
            
            # 推送到风险管理
            await self.risk_manager.update_market_data(data)
            
            # 推送到绩效分析
            await self.performance_analyzer.update_market_data(data)
            
        except Exception as e:
            self.logger.error(f"推送市场数据失败: {e}")
    
    def set_data_provider(self, provider: Callable[[str, datetime, datetime], pd.DataFrame]):
        """设置数据提供器"""
        self._data_provider = provider
    
    async def run_backtest(self, strategy: BaseStrategy, 
                          backtest_config: BacktestConfig) -> Dict[str, Any]:
        """运行回测"""
        try:
            if not self._data_provider:
                raise ValueError("未设置数据提供器")
            
            # 创建回测引擎
            self.backtest_engine = BacktestEngine(backtest_config)
            self.backtest_engine.set_data_provider(self._data_provider)
            
            # 加载数据
            if not self.backtest_engine.load_data(strategy.config.symbols):
                raise ValueError("加载回测数据失败")
            
            # 运行回测
            result = await self.backtest_engine.run_backtest(strategy)
            
            return {
                'success': True,
                'result': {
                    'total_return': result.total_return,
                    'annual_return': result.annual_return,
                    'volatility': result.volatility,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'total_trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'profit_factor': result.profit_factor
                }
            }
            
        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'is_running': self._is_running,
            'engine_status': self.engine.state.value,
            'strategies_count': len(self._strategies),
            'running_strategies': len([s for s in self._strategies.values() if s.is_running]),
            'engine_stats': self.engine.stats.__dict__,
            'risk_monitoring': self.risk_manager._is_monitoring,
            'performance_monitoring': self.performance_analyzer._is_monitoring
        }
    
    def get_strategy_list(self) -> List[Dict[str, Any]]:
        """获取策略列表"""
        return [
            {
                'strategy_id': strategy.strategy_id,
                'strategy_name': strategy.strategy_name,
                'strategy_type': strategy.strategy_type.value,
                'state': strategy.state.value,
                'symbols': strategy.config.symbols,
                'initial_capital': float(strategy.config.initial_capital),
                'current_balance': float(strategy.account_balance)
            }
            for strategy in self._strategies.values()
        ]


def setup_strategy_system(app: FastAPI, 
                         engine_config: Optional[EngineConfig] = None,
                         risk_config: Optional[RiskConfig] = None,
                         performance_config: Optional[PerformanceConfig] = None) -> StrategySystem:
    """
    设置策略系统并集成到FastAPI应用
    
    Args:
        app: FastAPI应用实例
        engine_config: 引擎配置
        risk_config: 风险管理配置
        performance_config: 绩效分析配置
        
    Returns:
        StrategySystem: 策略系统实例
    """
    
    # 创建策略系统
    strategy_system = StrategySystem(engine_config, risk_config, performance_config)
    
    # 添加系统管理接口
    @app.get("/api/strategy/system/status")
    async def get_system_status():
        """获取系统状态"""
        try:
            return strategy_system.get_system_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/strategy/system/start")
    async def start_system():
        """启动系统"""
        try:
            success = await strategy_system.start()
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/strategy/system/stop")
    async def stop_system():
        """停止系统"""
        try:
            success = await strategy_system.stop()
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 添加策略管理接口
    @app.get("/api/strategy/list")
    async def get_strategies():
        """获取策略列表"""
        try:
            return strategy_system.get_strategy_list()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/strategy/{strategy_id}/start")
    async def start_strategy(strategy_id: str):
        """启动策略"""
        try:
            success = await strategy_system.start_strategy(strategy_id)
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/strategy/{strategy_id}/stop")
    async def stop_strategy(strategy_id: str):
        """停止策略"""
        try:
            success = await strategy_system.stop_strategy(strategy_id)
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/strategy/{strategy_id}")
    async def remove_strategy(strategy_id: str):
        """移除策略"""
        try:
            success = await strategy_system.remove_strategy(strategy_id)
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 添加绩效分析接口
    @app.get("/api/strategy/{strategy_id}/performance")
    async def get_strategy_performance(strategy_id: str):
        """获取策略绩效"""
        try:
            metrics = strategy_system.performance_analyzer.get_strategy_metrics(strategy_id)
            if metrics is None:
                raise HTTPException(status_code=404, detail="策略不存在")
            
            return metrics.__dict__
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/strategy/{strategy_id}/equity-curve")
    async def get_equity_curve(strategy_id: str):
        """获取权益曲线"""
        try:
            equity_curve = strategy_system.performance_analyzer.get_equity_curve(strategy_id)
            if equity_curve is None:
                raise HTTPException(status_code=404, detail="策略不存在")
            
            return equity_curve.to_dict('records')
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/strategy/{strategy_id}/report")
    async def get_performance_report(strategy_id: str):
        """获取绩效报告"""
        try:
            report = strategy_system.performance_analyzer.generate_performance_report(strategy_id)
            if not report:
                raise HTTPException(status_code=404, detail="策略不存在")
            
            return report
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 添加风险管理接口
    @app.get("/api/strategy/risk/status")
    async def get_risk_status():
        """获取风险状态"""
        try:
            return strategy_system.risk_manager.get_current_risks()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/strategy/risk/events")
    async def get_risk_events(active_only: bool = False):
        """获取风险事件"""
        try:
            events = strategy_system.risk_manager.get_risk_events(active_only)
            return [
                {
                    'event_id': event.event_id,
                    'timestamp': event.timestamp,
                    'risk_type': event.risk_type.value,
                    'risk_level': event.risk_level.value,
                    'strategy_id': event.strategy_id,
                    'description': event.description,
                    'resolved': event.resolved
                }
                for event in events
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/strategy/risk/report")
    async def get_risk_report():
        """获取风险报告"""
        try:
            return strategy_system.risk_manager.generate_risk_report()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 添加回测接口
    @app.post("/api/strategy/backtest")
    async def run_backtest(request: Dict[str, Any]):
        """运行回测"""
        try:
            # 这里需要根据请求创建策略和配置
            # 暂时返回示例响应
            return {"message": "回测功能需要具体实现"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 添加数据推送接口
    @app.post("/api/strategy/data/feed")
    async def feed_market_data(data: Dict[str, Any]):
        """推送市场数据"""
        try:
            market_data = MarketData(
                symbol=data['symbol'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume']
            )
            
            await strategy_system.feed_market_data(market_data)
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 添加策略比较接口
    @app.post("/api/strategy/compare")
    async def compare_strategies(request: Dict[str, List[str]]):
        """比较策略"""
        try:
            strategy_ids = request.get('strategy_ids', [])
            if len(strategy_ids) < 2:
                raise HTTPException(status_code=400, detail="至少需要2个策略进行比较")
            
            comparison = strategy_system.performance_analyzer.compare_strategies(strategy_ids)
            return comparison
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 添加策略组合管理接口
    @app.post("/api/strategy/group")
    async def create_strategy_group(request: Dict[str, Any]):
        """创建策略组合"""
        try:
            group_name = request['group_name']
            strategy_ids = request['strategy_ids']
            capital_allocation = request.get('capital_allocation', 1.0)
            config = request.get('config', {})
            
            success = strategy_system.manager.create_strategy_group(
                group_name, strategy_ids, capital_allocation, config
            )
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/strategy/group/{group_name}/start")
    async def start_strategy_group(group_name: str):
        """启动策略组合"""
        try:
            success = await strategy_system.manager.start_strategy_group(group_name)
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/strategy/group/{group_name}/stop")
    async def stop_strategy_group(group_name: str):
        """停止策略组合"""
        try:
            success = await strategy_system.manager.stop_strategy_group(group_name)
            return {"success": success}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/strategy/groups")
    async def get_strategy_groups():
        """获取策略组合列表"""
        try:
            return strategy_system.manager.get_all_groups()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/strategy/group/{group_name}/performance")
    async def get_group_performance(group_name: str):
        """获取组合绩效"""
        try:
            performance = await strategy_system.manager.update_group_performance(group_name)
            return performance
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 健康检查接口
    @app.get("/api/strategy/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "system_running": strategy_system._is_running
        }
    
    return strategy_system


# 示例策略创建函数
def create_sample_strategy(strategy_id: str, symbols: List[str]) -> BaseStrategy:
    """创建示例策略"""
    
    class SampleStrategy(BaseStrategy):
        """示例策略"""
        
        async def on_start(self):
            self.log_info("示例策略启动")
        
        async def on_stop(self):
            self.log_info("示例策略停止")
        
        async def on_tick(self, data: MarketData):
            # 简单的交易逻辑
            if len(self._market_data) > 1:
                # 获取前一个价格
                prev_price = list(self._market_data.values())[-2].close
                current_price = data.close
                
                # 简单的趋势跟随
                if current_price > prev_price * 1.01:  # 上涨1%
                    if not self.get_position(data.symbol):
                        await self.buy(data.symbol, 100)
                elif current_price < prev_price * 0.99:  # 下跌1%
                    position = self.get_position(data.symbol)
                    if position:
                        await self.sell(data.symbol, position.quantity)
        
        async def on_bar(self, data: MarketData):
            await self.on_tick(data)
    
    config = StrategyConfig(
        strategy_id=strategy_id,
        strategy_name=f"示例策略_{strategy_id}",
        strategy_type=StrategyType.MOMENTUM,
        symbols=symbols
    )
    
    return SampleStrategy(config)
