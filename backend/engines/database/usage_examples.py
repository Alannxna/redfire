"""
RedFire 数据库使用示例
===================

演示如何使用RedFire统一数据库管理系统的各种功能
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 导入数据库管理模块
from backend.core.database import (
    # 统一数据库管理
    get_database_manager,
    get_db_session,
    get_async_db_session,
    
    # Redis缓存
    get_cache_manager,
    cache,
    
    # InfluxDB时序数据
    get_trading_data_manager,
    TimeSeriesPoint,
    
    # MongoDB日志
    get_log_manager,
    LogEntry,
    LogLevel,
    LogCategory,
    
    # 读写分离
    get_read_session,
    get_write_session,
    get_async_read_session,
    get_async_write_session,
    
    # 数据库初始化
    initialize_databases,
    get_database_status
)

import logging

logger = logging.getLogger(__name__)


class DatabaseUsageExamples:
    """数据库使用示例"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.cache_manager = get_cache_manager("user_data")
        self.trading_manager = get_trading_data_manager()
        self.log_manager = get_log_manager()
    
    def example_mysql_operations(self):
        """MySQL数据库操作示例"""
        print("=== MySQL数据库操作示例 ===")
        
        # 使用统一数据库管理器
        with self.db_manager.get_session("main") as session:
            # 查询用户数据
            result = session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"用户总数: {user_count}")
        
        # 使用读写分离
        with get_read_session() as read_session:
            # 读操作使用从库（如果配置了）
            result = read_session.execute(text("SELECT * FROM users LIMIT 5"))
            users = result.fetchall()
            print(f"查询到 {len(users)} 个用户")
        
        with get_write_session() as write_session:
            # 写操作使用主库
            write_session.execute(text("""
                INSERT INTO users (username, email, password_hash) 
                VALUES ('test_user', 'test@example.com', 'hashed_password')
                ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
            """))
            print("用户数据写入成功")
    
    async def example_async_mysql_operations(self):
        """异步MySQL数据库操作示例"""
        print("=== 异步MySQL数据库操作示例 ===")
        
        # 异步读操作
        async with get_async_read_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM trading_orders"))
            order_count = result.scalar()
            print(f"订单总数: {order_count}")
        
        # 异步写操作
        async with get_async_write_session() as session:
            await session.execute(text("""
                INSERT INTO trading_orders 
                (user_id, symbol, side, order_type, quantity, price, status) 
                VALUES (1, 'AAPL', 'BUY', 'LIMIT', 100, 150.00, 'PENDING')
            """))
            print("订单数据写入成功")
    
    def example_redis_cache_operations(self):
        """Redis缓存操作示例"""
        print("=== Redis缓存操作示例 ===")
        
        # 基本缓存操作
        self.cache_manager.set("user_profile", "user_123", {
            "name": "张三",
            "email": "zhangsan@example.com",
            "last_login": datetime.now().isoformat()
        })
        
        # 获取缓存数据
        user_profile = self.cache_manager.get("user_profile", "user_123")
        print(f"用户资料: {user_profile}")
        
        # 使用缓存装饰器
        @cache("api_data", ttl=300)  # 5分钟缓存
        def get_market_data(symbol: str) -> Dict[str, Any]:
            """模拟获取市场数据"""
            print(f"从API获取 {symbol} 市场数据...")
            return {
                "symbol": symbol,
                "price": 150.25,
                "volume": 1000000,
                "timestamp": datetime.now().isoformat()
            }
        
        # 第一次调用会从API获取
        data1 = get_market_data("AAPL")
        print(f"市场数据 (第一次): {data1}")
        
        # 第二次调用会从缓存获取
        data2 = get_market_data("AAPL")
        print(f"市场数据 (缓存): {data2}")
        
        # 查看缓存统计
        stats = self.cache_manager.get_stats()
        print(f"缓存统计: {stats}")
    
    def example_influxdb_operations(self):
        """InfluxDB时序数据操作示例"""
        print("=== InfluxDB时序数据操作示例 ===")
        
        try:
            # 写入K线数据
            success = self.trading_manager.write_kline_data(
                symbol="AAPL",
                timeframe="1m",
                timestamp=datetime.now(),
                open_price=150.00,
                high_price=151.00,
                low_price=149.50,
                close_price=150.75,
                volume=100000
            )
            print(f"K线数据写入: {'成功' if success else '失败'}")
            
            # 写入Tick数据
            success = self.trading_manager.write_tick_data(
                symbol="AAPL",
                timestamp=datetime.now(),
                last_price=150.75,
                volume=1000,
                bid_price=150.70,
                ask_price=150.80,
                bid_volume=500,
                ask_volume=600
            )
            print(f"Tick数据写入: {'成功' if success else '失败'}")
            
            # 查询历史数据
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            kline_data = self.trading_manager.get_kline_data(
                symbol="AAPL",
                timeframe="1m",
                start_time=start_time,
                end_time=end_time
            )
            print(f"查询到 {len(kline_data)} 条K线数据")
            
            # 获取最新价格
            latest_price = self.trading_manager.get_latest_price("AAPL")
            print(f"AAPL最新价格: {latest_price}")
            
        except Exception as e:
            print(f"InfluxDB操作失败: {e}")
    
    async def example_mongodb_logging(self):
        """MongoDB日志存储示例"""
        print("=== MongoDB日志存储示例 ===")
        
        try:
            # 写入普通日志
            log_entry = LogEntry(
                level=LogLevel.INFO,
                category=LogCategory.TRADING,
                message="用户下单操作",
                source="trading_service",
                user_id="user_123",
                data={
                    "symbol": "AAPL",
                    "quantity": 100,
                    "price": 150.00
                }
            )
            
            log_id = await self.log_manager.write_log(log_entry)
            print(f"日志写入成功，ID: {log_id}")
            
            # 写入审计日志
            audit_id = await self.log_manager.write_audit_log(
                user_id="user_123",
                action="CREATE_ORDER",
                resource="trading_orders",
                details={
                    "order_id": "order_456",
                    "symbol": "AAPL",
                    "side": "BUY"
                },
                ip_address="192.168.1.100"
            )
            print(f"审计日志写入成功，ID: {audit_id}")
            
            # 写入性能指标
            metric_id = await self.log_manager.write_performance_metric(
                metric_type="response_time",
                source="api_gateway",
                value=45.6,
                unit="ms",
                tags={"endpoint": "/api/orders", "method": "POST"}
            )
            print(f"性能指标写入成功，ID: {metric_id}")
            
            # 查询日志
            logs = await self.log_manager.query_logs(
                category=LogCategory.TRADING,
                start_time=datetime.now() - timedelta(hours=1),
                limit=10
            )
            print(f"查询到 {len(logs)} 条交易日志")
            
            # 获取日志统计
            stats = await self.log_manager.get_log_statistics(
                start_time=datetime.now() - timedelta(days=1),
                end_time=datetime.now()
            )
            print(f"日志统计: {stats}")
            
        except Exception as e:
            print(f"MongoDB操作失败: {e}")
    
    def example_database_monitoring(self):
        """数据库监控示例"""
        print("=== 数据库监控示例 ===")
        
        # 获取所有数据库统计
        db_stats = self.db_manager.get_all_stats()
        print("数据库连接统计:")
        for db_name, stats in db_stats.items():
            print(f"  {db_name}: {stats}")
        
        # 测试所有数据库连接
        connection_results = self.db_manager.test_all_connections()
        print("数据库连接测试:")
        for db_name, is_healthy in connection_results.items():
            status = "✅ 正常" if is_healthy else "❌ 异常"
            print(f"  {db_name}: {status}")
        
        # 获取读写分离统计
        from backend.core.database.read_write_split import get_rw_split_manager
        rw_manager = get_rw_split_manager()
        rw_stats = rw_manager.get_all_stats()
        print(f"读写分离统计: {rw_stats}")
    
    def example_batch_operations(self):
        """批量操作示例"""
        print("=== 批量操作示例 ===")
        
        # 批量写入时序数据
        try:
            points = []
            for i in range(10):
                point = TimeSeriesPoint(
                    measurement="test_batch",
                    fields={
                        "value": i * 10,
                        "status": 1
                    },
                    tags={
                        "batch_id": "batch_001",
                        "sequence": str(i)
                    },
                    timestamp=datetime.now()
                )
                points.append(point)
            
            influx_manager = self.trading_manager.influx
            success = influx_manager.write_points(points)
            print(f"批量写入时序数据: {'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"批量操作失败: {e}")
    
    def example_error_handling(self):
        """错误处理示例"""
        print("=== 错误处理示例 ===")
        
        try:
            # 模拟数据库连接错误
            with get_write_session() as session:
                # 执行一个可能失败的操作
                session.execute(text("SELECT * FROM non_existent_table"))
        
        except Exception as e:
            print(f"捕获数据库错误: {e}")
            
            # 记录错误日志
            asyncio.create_task(self._log_error(str(e)))
    
    async def _log_error(self, error_message: str):
        """记录错误日志"""
        try:
            error_log = LogEntry(
                level=LogLevel.ERROR,
                category=LogCategory.DATABASE,
                message="数据库操作错误",
                exception=error_message,
                source="database_examples"
            )
            await self.log_manager.write_log(error_log)
        except Exception:
            pass  # 避免日志记录失败影响主流程


async def run_all_examples():
    """运行所有示例"""
    print("🚀 开始运行RedFire数据库使用示例...")
    
    # 初始化数据库系统
    print("\n📊 初始化数据库系统...")
    init_success = initialize_databases()
    if not init_success:
        print("❌ 数据库初始化失败，部分示例可能无法运行")
    
    # 获取数据库状态
    status = get_database_status()
    print(f"📈 数据库状态: {status}")
    
    # 创建示例实例
    examples = DatabaseUsageExamples()
    
    try:
        # 运行各种示例
        print("\n" + "="*50)
        examples.example_mysql_operations()
        
        print("\n" + "="*50)
        await examples.example_async_mysql_operations()
        
        print("\n" + "="*50)
        examples.example_redis_cache_operations()
        
        print("\n" + "="*50)
        examples.example_influxdb_operations()
        
        print("\n" + "="*50)
        await examples.example_mongodb_logging()
        
        print("\n" + "="*50)
        examples.example_database_monitoring()
        
        print("\n" + "="*50)
        examples.example_batch_operations()
        
        print("\n" + "="*50)
        examples.example_error_handling()
        
        print("\n🎉 所有示例运行完成！")
        
    except Exception as e:
        print(f"\n💥 示例运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("\n🧹 清理数据库资源...")
        examples.db_manager.close_all()


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行示例
    asyncio.run(run_all_examples())
