"""
交易引擎使用示例

演示如何使用优化后的交易引擎，包括VnPy集成、独立策略引擎和分布式事件系统。
"""

import asyncio
import logging
from pathlib import Path

# 导入交易引擎组件
from ..mainEngine import MainTradingEngine
from ..adapters import VnPyConfig, VnPyIntegrationMode
from ..strategies import StrategyConfig, StrategyIsolationLevel
from ..strategies.examples import SimpleMAStrategy


async def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("启动交易引擎示例...")
    
    try:
        # 1. 创建VnPy配置（可选）
        vnpy_config = VnPyConfig(
            mode=VnPyIntegrationMode.HYBRID,
            apps=["CtaStrategy", "PortfolioStrategy"],
            gateways=["CTP"],  # 根据实际情况配置
            auto_connect=False
        )
        
        # 2. 创建主交易引擎
        main_engine = MainTradingEngine(
            vnpy_config=vnpy_config,  # 可选：启用VnPy集成
            redis_url="redis://localhost:6379/0",  # 可选：启用分布式事件
            service_name="trading_engine_example"
        )
        
        # 3. 启动主引擎
        logger.info("启动主交易引擎...")
        await main_engine.startEngine()
        
        # 4. 检查引擎状态
        status = main_engine.getStatus()
        logger.info(f"引擎状态: {status}")
        
        # 5. 添加策略示例
        await demo_strategy_engine(main_engine)
        
        # 6. 分布式事件示例
        await demo_distributed_events(main_engine)
        
        # 7. VnPy集成示例
        await demo_vnpy_integration(main_engine)
        
        # 保持运行一段时间观察
        logger.info("运行30秒后停止...")
        await asyncio.sleep(30)
        
    except Exception as e:
        logger.error(f"运行异常: {e}")
    
    finally:
        # 停止引擎
        logger.info("停止主交易引擎...")
        await main_engine.stopEngine()
        logger.info("示例结束")


async def demo_strategy_engine(main_engine: MainTradingEngine):
    """演示独立策略引擎的使用"""
    logger = logging.getLogger("strategy_demo")
    logger.info("=== 独立策略引擎示例 ===")
    
    try:
        # 1. 创建策略配置
        strategy_config = StrategyConfig(
            strategy_id="ma_strategy_001",
            strategy_name="移动平均策略示例",
            strategy_class="SimpleMAStrategy",
            strategy_module="backend.core.tradingEngine.strategies.examples.simple_ma_strategy",
            isolation_level=StrategyIsolationLevel.THREAD,
            config_data={
                'short_window': 5,
                'long_window': 20,
                'symbol': 'BTCUSDT'
            }
        )
        
        # 2. 添加策略
        success = await main_engine.addStrategy(strategy_config)
        if success:
            logger.info(f"策略添加成功: {strategy_config.strategy_id}")
        else:
            logger.error("策略添加失败")
            return
        
        # 3. 启动策略
        success = await main_engine.startStrategy(strategy_config.strategy_id)
        if success:
            logger.info(f"策略启动成功: {strategy_config.strategy_id}")
        else:
            logger.error("策略启动失败")
            return
        
        # 4. 订阅策略事件
        main_engine.subscribeStrategyEvent(strategy_config.strategy_id, "tick_data")
        main_engine.subscribeStrategyEvent(strategy_config.strategy_id, "bar_data")
        
        # 5. 模拟发送一些市场数据
        await simulate_market_data(main_engine)
        
        # 6. 检查策略状态
        strategy_status = main_engine.getStrategyStatus(strategy_config.strategy_id)
        logger.info(f"策略状态: {strategy_status}")
        
        # 7. 停止策略
        await asyncio.sleep(5)
        await main_engine.stopStrategy(strategy_config.strategy_id)
        logger.info(f"策略已停止: {strategy_config.strategy_id}")
        
    except Exception as e:
        logger.error(f"策略引擎示例异常: {e}")


async def demo_distributed_events(main_engine: MainTradingEngine):
    """演示分布式事件系统的使用"""
    logger = logging.getLogger("event_demo")
    logger.info("=== 分布式事件系统示例 ===")
    
    try:
        # 检查分布式事件是否启用
        if not main_engine.isDistributedEventEnabled():
            logger.warning("分布式事件系统未启用，跳过示例")
            return
        
        # 1. 注册分布式事件处理器
        async def order_handler(event):
            logger.info(f"收到订单事件: {event.event_type} - {event.data}")
        
        success = await main_engine.registerDistributedEventHandler(
            "demo_order_handler",
            order_handler,
            ["trading.order_update"]
        )
        
        if success:
            logger.info("分布式事件处理器注册成功")
        
        # 2. 发布分布式事件
        event_id = await main_engine.publishDistributedEvent(
            "trading.order_update",
            {
                "order_id": "demo_order_001",
                "symbol": "BTCUSDT",
                "side": "buy",
                "quantity": 1.0,
                "price": 50000.0,
                "status": "filled"
            }
        )
        
        if event_id:
            logger.info(f"分布式事件发布成功: {event_id}")
        
        # 3. 测试本地到分布式的事件桥接
        main_engine.eventTradingEngine.putEvent("order_update", {
            "order_id": "local_order_001",
            "symbol": "ETHUSDT",
            "side": "sell",
            "quantity": 2.0,
            "price": 3000.0,
            "status": "pending"
        })
        
        logger.info("本地事件已发送，应该会被桥接到分布式事件系统")
        
        # 等待事件处理
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"分布式事件示例异常: {e}")


async def demo_vnpy_integration(main_engine: MainTradingEngine):
    """演示VnPy集成的使用"""
    logger = logging.getLogger("vnpy_demo")
    logger.info("=== VnPy集成示例 ===")
    
    try:
        # 检查VnPy是否启用
        if not main_engine.isVnPyEnabled():
            logger.warning("VnPy集成未启用，跳过示例")
            return
        
        # 1. 获取VnPy主引擎
        vnpy_main_engine = main_engine.getVnPyMainEngine()
        if vnpy_main_engine:
            logger.info("VnPy主引擎获取成功")
            
            # 这里可以使用VnPy的原生API
            # 例如：订阅行情、发送委托等
            
        # 2. 获取VnPy应用
        cta_app = main_engine.getVnPyApp("CtaStrategy")
        if cta_app:
            logger.info("CTA策略应用获取成功")
            
            # 这里可以使用CTA策略应用的功能
            
        # 3. 获取VnPy适配器状态
        adapter = main_engine.getVnPyAdapter()
        if adapter:
            adapter_status = adapter.get_status()
            logger.info(f"VnPy适配器状态: {adapter_status}")
        
    except Exception as e:
        logger.error(f"VnPy集成示例异常: {e}")


async def simulate_market_data(main_engine: MainTradingEngine):
    """模拟市场数据"""
    logger = logging.getLogger("market_sim")
    logger.info("开始模拟市场数据...")
    
    try:
        # 模拟tick数据
        for i in range(10):
            tick_data = {
                "symbol": "BTCUSDT",
                "price": 50000 + i * 10,
                "volume": 100,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # 发送到策略引擎
            await main_engine.broadcastEventToStrategies("tick", tick_data)
            
            # 也发送到本地事件引擎
            main_engine.eventTradingEngine.putEvent("tick_data", tick_data)
            
            await asyncio.sleep(0.5)
        
        # 模拟K线数据
        bar_data = {
            "symbol": "BTCUSDT",
            "open": 50000,
            "high": 50100,
            "low": 49950,
            "close": 50050,
            "volume": 1000,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await main_engine.broadcastEventToStrategies("bar", bar_data)
        main_engine.eventTradingEngine.putEvent("bar_data", bar_data)
        
        logger.info("市场数据模拟完成")
        
    except Exception as e:
        logger.error(f"模拟市场数据异常: {e}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
