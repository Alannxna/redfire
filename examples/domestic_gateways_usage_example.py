"""
国内券商网关集成使用示例
展示如何使用DomesticGatewaysAdapter进行交易操作
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from backend.core.tradingEngine.adapters.domestic_gateways_adapter import (
    DomesticGatewaysAdapter, DomesticGatewayConfig, DomesticGatewayType
)
from backend.core.tradingEngine.config.domestic_gateways_config import (
    load_domestic_config, get_config_manager
)
from backend.core.tradingEngine.monitoring.domestic_gateway_monitor import (
    get_gateway_monitor, get_alert_handler, Alert
)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class DomesticTradingExample:
    """国内券商交易示例"""
    
    def __init__(self):
        self.adapter = DomesticGatewaysAdapter()
        self.monitor = get_gateway_monitor()
        self.config_manager = get_config_manager()
        
        # 注册事件回调
        self._register_callbacks()
    
    def _register_callbacks(self):
        """注册事件回调"""
        # 网关事件回调
        self.adapter.on('on_gateway_connected', self._on_gateway_connected)
        self.adapter.on('on_gateway_disconnected', self._on_gateway_disconnected)
        self.adapter.on('on_order_update', self._on_order_update)
        self.adapter.on('on_trade_update', self._on_trade_update)
        self.adapter.on('on_position_update', self._on_position_update)
        self.adapter.on('on_account_update', self._on_account_update)
        self.adapter.on('on_error', self._on_error)
        
        # 告警回调
        self.monitor.add_alert_callback(self._on_alert)
    
    async def _on_gateway_connected(self, gateway_name: str):
        """网关连接回调"""
        logger.info(f"✅ 网关连接成功: {gateway_name}")
        
        # 记录连接状态
        self.monitor.record_connection_status(gateway_name, True)
        
        # 查询初始数据
        await self._query_initial_data(gateway_name)
    
    async def _on_gateway_disconnected(self, gateway_name: str):
        """网关断开回调"""
        logger.warning(f"❌ 网关断开连接: {gateway_name}")
        
        # 记录断开状态
        self.monitor.record_connection_status(gateway_name, False)
    
    async def _on_order_update(self, order_data: Dict[str, Any]):
        """订单更新回调"""
        order_id = order_data.get('order_id', 'unknown')
        status = order_data.get('status', 'unknown')
        logger.info(f"📋 订单更新: {order_id} -> {status}")
        
        # 记录订单结果
        gateway_name = order_data.get('gateway_name', 'unknown')
        success = status in ['filled', 'partially_filled']
        self.monitor.record_order_result(gateway_name, success)
    
    async def _on_trade_update(self, trade_data: Dict[str, Any]):
        """成交更新回调"""
        trade_id = trade_data.get('trade_id', 'unknown')
        volume = trade_data.get('volume', 0)
        price = trade_data.get('price', 0)
        logger.info(f"💰 成交更新: {trade_id} - {volume}@{price}")
    
    async def _on_position_update(self, position_data: Dict[str, Any]):
        """持仓更新回调"""
        symbol = position_data.get('symbol', 'unknown')
        volume = position_data.get('volume', 0)
        logger.info(f"📊 持仓更新: {symbol} -> {volume}")
    
    async def _on_account_update(self, account_data: Dict[str, Any]):
        """账户更新回调"""
        balance = account_data.get('balance', 0)
        available = account_data.get('available', 0)
        logger.info(f"💳 账户更新: 余额={balance}, 可用={available}")
    
    async def _on_error(self, error_data: Dict[str, Any]):
        """错误回调"""
        gateway_name = error_data.get('gateway', 'unknown')
        error_type = error_data.get('type', 'unknown')
        message = error_data.get('message', 'unknown')
        
        logger.error(f"❌ 网关错误: {gateway_name} - {error_type}: {message}")
        
        # 记录错误
        self.monitor.record_error(gateway_name, error_type, message)
    
    def _on_alert(self, alert: Alert):
        """告警回调"""
        level_icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        
        icon = level_icons.get(alert.level.value, '❓')
        logger.warning(f"{icon} 告警: {alert.message}")
        
        # 在生产环境中，这里可以发送邮件、短信或webhook通知
    
    async def _query_initial_data(self, gateway_name: str):
        """查询初始数据"""
        try:
            logger.info(f"📊 查询初始数据: {gateway_name}")
            
            # 查询账户信息
            accounts = await self.adapter.get_all_accounts()
            if gateway_name in accounts:
                logger.info(f"账户信息: {accounts[gateway_name]}")
            
            # 查询持仓信息
            positions = await self.adapter.get_all_positions()
            if gateway_name in positions:
                logger.info(f"持仓信息: {positions[gateway_name]}")
            
        except Exception as e:
            logger.error(f"查询初始数据失败: {e}")
    
    async def initialize_system(self, environment: str = "development"):
        """初始化系统"""
        try:
            logger.info("🚀 初始化国内券商交易系统...")
            
            # 1. 加载配置
            logger.info(f"📖 加载配置: {environment}")
            config = load_domestic_config(environment)
            
            # 2. 初始化适配器
            logger.info("🔧 初始化适配器...")
            success = await self.adapter.initialize(config)
            if not success:
                raise Exception("适配器初始化失败")
            
            # 3. 启动监控
            logger.info("📊 启动监控系统...")
            await self.monitor.start_monitoring()
            
            # 4. 连接网关
            logger.info("🔗 连接网关...")
            connection_results = await self.adapter.connect_all_gateways()
            
            # 检查连接结果
            successful_connections = [
                name for name, success in connection_results.items() if success
            ]
            failed_connections = [
                name for name, success in connection_results.items() if not success
            ]
            
            if successful_connections:
                logger.info(f"✅ 成功连接网关: {successful_connections}")
            
            if failed_connections:
                logger.warning(f"❌ 连接失败网关: {failed_connections}")
            
            if not successful_connections:
                raise Exception("所有网关连接失败")
            
            logger.info("🎉 系统初始化完成！")
            return True
            
        except Exception as e:
            logger.error(f"💥 系统初始化失败: {e}")
            return False
    
    async def submit_test_order(self, symbol: str = "000001", price: float = 10.0, volume: int = 100):
        """提交测试订单"""
        try:
            logger.info(f"📝 提交测试订单: {symbol} {volume}@{price}")
            
            order_data = {
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'direction': 'BUY',
                'type': 'LIMIT',
                'timestamp': datetime.now()
            }
            
            # 记录提交延迟
            start_time = datetime.now()
            order_id = await self.adapter.submit_order(order_data)
            end_time = datetime.now()
            
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            if order_id:
                logger.info(f"✅ 订单提交成功: {order_id} (延迟: {latency_ms:.2f}ms)")
                
                # 记录延迟
                gateway_name = self.adapter.active_gateways[0] if self.adapter.active_gateways else 'unknown'
                self.monitor.record_latency(gateway_name, latency_ms)
                
                return order_id
            else:
                logger.error("❌ 订单提交失败")
                return None
                
        except Exception as e:
            logger.error(f"💥 提交订单异常: {e}")
            return None
    
    async def cancel_test_order(self, order_id: str):
        """撤销测试订单"""
        try:
            logger.info(f"🚫 撤销订单: {order_id}")
            
            success = await self.adapter.cancel_order(order_id)
            
            if success:
                logger.info(f"✅ 订单撤销成功: {order_id}")
            else:
                logger.error(f"❌ 订单撤销失败: {order_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"💥 撤销订单异常: {e}")
            return False
    
    async def subscribe_test_market_data(self, symbols: list = None):
        """订阅测试行情"""
        try:
            if symbols is None:
                symbols = ["000001", "000002", "600000"]
            
            logger.info(f"📡 订阅行情: {symbols}")
            
            results = await self.adapter.subscribe_market_data(symbols)
            
            successful_subscriptions = [
                gateway for gateway, success in results.items() if success
            ]
            
            if successful_subscriptions:
                logger.info(f"✅ 行情订阅成功: {successful_subscriptions}")
            else:
                logger.warning("❌ 行情订阅失败")
            
            return results
            
        except Exception as e:
            logger.error(f"💥 订阅行情异常: {e}")
            return {}
    
    async def show_system_status(self):
        """显示系统状态"""
        try:
            logger.info("📊 系统状态报告")
            logger.info("=" * 50)
            
            # 网关状态
            gateway_status = self.adapter.get_gateway_status()
            logger.info(f"🔗 活跃网关: {self.adapter.get_active_gateways()}")
            
            for name, status in gateway_status.items():
                status_icon = "✅" if status.connected else "❌"
                logger.info(f"  {status_icon} {name}: 连接={status.connected}, 错误={status.error_count}")
            
            # 性能指标
            all_stats = self.monitor.get_all_statistics()
            for gateway_name, stats in all_stats.items():
                logger.info(f"📈 {gateway_name} 性能指标:")
                logger.info(f"  成功率: {stats.get('success_rate', 0):.2f}%")
                logger.info(f"  错误率: {stats.get('error_rate', 0):.2f}%")
                logger.info(f"  正常运行时间: {stats.get('uptime', 0):.2f}%")
                
                latency_stats = stats.get('latency_statistics', {})
                if latency_stats:
                    logger.info(f"  平均延迟: {latency_stats.get('avg', 0):.2f}ms")
                    logger.info(f"  P95延迟: {latency_stats.get('p95', 0):.2f}ms")
            
            # 活跃告警
            active_alerts = self.monitor.get_active_alerts()
            if active_alerts:
                logger.warning(f"⚠️ 活跃告警数量: {len(active_alerts)}")
                for alert in active_alerts[:5]:  # 显示前5个
                    logger.warning(f"  {alert.level.value}: {alert.message}")
            else:
                logger.info("✅ 无活跃告警")
            
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"💥 获取系统状态异常: {e}")
    
    async def run_demo(self):
        """运行演示"""
        try:
            logger.info("🎬 开始国内券商交易演示")
            
            # 1. 初始化系统
            if not await self.initialize_system("development"):
                return
            
            # 等待连接稳定
            await asyncio.sleep(2)
            
            # 2. 显示初始状态
            await self.show_system_status()
            
            # 3. 订阅行情
            await self.subscribe_test_market_data()
            
            # 4. 提交测试订单
            order_id = await self.submit_test_order("000001", 10.50, 100)
            
            if order_id:
                # 等待一段时间
                await asyncio.sleep(3)
                
                # 5. 撤销订单
                await self.cancel_test_order(order_id)
            
            # 6. 再次显示状态
            await asyncio.sleep(2)
            await self.show_system_status()
            
            logger.info("🎬 演示完成！")
            
        except Exception as e:
            logger.error(f"💥 演示运行异常: {e}")
        
        finally:
            # 清理资源
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        try:
            logger.info("🧹 清理系统资源...")
            
            # 停止监控
            await self.monitor.stop_monitoring()
            
            # 断开网关
            await self.adapter.disconnect_all_gateways()
            
            logger.info("✅ 资源清理完成")
            
        except Exception as e:
            logger.error(f"💥 清理资源异常: {e}")


async def main():
    """主函数"""
    # 创建演示实例
    demo = DomesticTradingExample()
    
    try:
        # 运行演示
        await demo.run_demo()
        
    except KeyboardInterrupt:
        logger.info("👋 用户中断演示")
        
    except Exception as e:
        logger.error(f"💥 演示异常: {e}")
    
    finally:
        # 确保清理
        await demo.cleanup()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
