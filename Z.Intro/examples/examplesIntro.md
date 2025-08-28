# Examples 模块介绍

## 🎯 概述

`examples` 是 RedFire 量化交易平台的示例代码模块，提供各种功能的使用示例和最佳实践代码。该模块包含完整的示例项目、代码片段和教程，帮助用户快速上手和理解平台功能。

## 📁 目录结构

```
examples/
└── domestic_gateways_usage_example.py  # 🚪 国内网关使用示例
```

## 💡 示例内容详解

### **国内网关使用示例** (`domestic_gateways_usage_example.py`)

**作用**: 演示如何使用国内交易所网关进行交易

**主要内容**:
- 网关连接示例
- 订单管理示例
- 数据查询示例
- 错误处理示例

**示例代码结构**:
```python
# 国内网关使用示例
import asyncio
from redfire.gateway import DomesticGateway
from redfire.models import Order, Position

class DomesticGatewayExample:
    def __init__(self):
        self.gateway = None
    
    async def setup_gateway(self):
        """设置网关连接"""
        # 配置网关参数
        config = {
            "gateway_name": "HuaxinGateway",
            "username": "your_username",
            "password": "your_password",
            "server": "your_server",
            "port": 12345
        }
        
        # 创建网关实例
        self.gateway = DomesticGateway(config)
        
        # 连接网关
        await self.gateway.connect()
        print("网关连接成功")
    
    async def query_account(self):
        """查询账户信息"""
        try:
            account = await self.gateway.query_account()
            print(f"账户余额: {account.balance}")
            print(f"可用资金: {account.available}")
            print(f"持仓市值: {account.position_value}")
        except Exception as e:
            print(f"查询账户失败: {e}")
    
    async def query_positions(self):
        """查询持仓信息"""
        try:
            positions = await self.gateway.query_positions()
            for position in positions:
                print(f"股票: {position.symbol}")
                print(f"持仓数量: {position.volume}")
                print(f"持仓成本: {position.cost}")
                print(f"当前价格: {position.price}")
                print(f"盈亏: {position.pnl}")
        except Exception as e:
            print(f"查询持仓失败: {e}")
    
    async def place_order(self, symbol, direction, volume, price=None):
        """下单示例"""
        try:
            order = Order(
                symbol=symbol,
                direction=direction,
                volume=volume,
                price=price,
                order_type="LIMIT" if price else "MARKET"
            )
            
            result = await self.gateway.place_order(order)
            print(f"下单成功，订单号: {result.order_id}")
            return result
        except Exception as e:
            print(f"下单失败: {e}")
            return None
    
    async def cancel_order(self, order_id):
        """撤单示例"""
        try:
            result = await self.gateway.cancel_order(order_id)
            print(f"撤单成功: {result}")
            return result
        except Exception as e:
            print(f"撤单失败: {e}")
            return None
    
    async def query_orders(self):
        """查询订单"""
        try:
            orders = await self.gateway.query_orders()
            for order in orders:
                print(f"订单号: {order.order_id}")
                print(f"股票: {order.symbol}")
                print(f"方向: {order.direction}")
                print(f"数量: {order.volume}")
                print(f"价格: {order.price}")
                print(f"状态: {order.status}")
        except Exception as e:
            print(f"查询订单失败: {e}")
    
    async def subscribe_market_data(self, symbols):
        """订阅行情数据"""
        try:
            await self.gateway.subscribe_market_data(symbols)
            
            # 设置回调函数
            def on_market_data(data):
                print(f"收到行情数据: {data}")
            
            self.gateway.set_market_data_callback(on_market_data)
            print("行情订阅成功")
        except Exception as e:
            print(f"订阅行情失败: {e}")
    
    async def run_example(self):
        """运行完整示例"""
        print("开始运行国内网关使用示例...")
        
        # 1. 连接网关
        await self.setup_gateway()
        
        # 2. 查询账户信息
        await self.query_account()
        
        # 3. 查询持仓
        await self.query_positions()
        
        # 4. 订阅行情
        symbols = ["000001.SZ", "000002.SZ"]
        await self.subscribe_market_data(symbols)
        
        # 5. 下单示例（限价单）
        order_result = await self.place_order(
            symbol="000001.SZ",
            direction="BUY",
            volume=100,
            price=15.50
        )
        
        if order_result:
            # 6. 查询订单
            await self.query_orders()
            
            # 7. 撤单示例
            await self.cancel_order(order_result.order_id)
        
        # 8. 等待一段时间观察行情
        await asyncio.sleep(10)
        
        print("示例运行完成")

# 运行示例
if __name__ == "__main__":
    example = DomesticGatewayExample()
    asyncio.run(example.run_example())
```

## 🔧 示例功能特性

### **1. 完整的代码示例**
- 提供完整可运行的代码
- 包含错误处理机制
- 演示最佳实践
- 包含详细注释

### **2. 多种使用场景**
- 基础连接示例
- 交易操作示例
- 数据查询示例
- 实时数据订阅示例

### **3. 错误处理示例**
```python
class ErrorHandlingExample:
    async def robust_order_placement(self, order):
        """健壮的下单示例"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                result = await self.gateway.place_order(order)
                return result
            except ConnectionError as e:
                print(f"连接错误，重试 {retry_count + 1}/{max_retries}: {e}")
                await asyncio.sleep(1)
                retry_count += 1
            except OrderError as e:
                print(f"下单错误: {e}")
                return None
            except Exception as e:
                print(f"未知错误: {e}")
                return None
        
        print("下单失败，已达到最大重试次数")
        return None
```

### **4. 配置管理示例**
```python
class ConfigExample:
    def load_config(self, config_file):
        """加载配置文件"""
        import yaml
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def validate_config(self, config):
        """验证配置"""
        required_fields = ['gateway_name', 'username', 'password', 'server']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必需配置项: {field}")
        
        return True
```

## 📚 示例文档

### **1. 使用说明**
每个示例都包含详细的使用说明：
- 环境要求
- 安装步骤
- 配置说明
- 运行方法
- 预期结果

### **2. 最佳实践**
示例代码展示了最佳实践：
- 异步编程模式
- 错误处理策略
- 资源管理
- 性能优化

### **3. 常见问题**
提供常见问题的解决方案：
- 连接问题
- 认证问题
- 数据格式问题
- 性能问题

## 🚀 扩展示例

### **1. 策略示例**
```python
class StrategyExample:
    def __init__(self, gateway):
        self.gateway = gateway
        self.positions = {}
    
    async def simple_ma_strategy(self, symbol, short_period=5, long_period=20):
        """简单移动平均策略"""
        # 获取历史数据
        data = await self.gateway.get_history_data(symbol, period=long_period)
        
        # 计算移动平均
        short_ma = data['close'].rolling(short_period).mean()
        long_ma = data['close'].rolling(long_period).mean()
        
        # 生成信号
        if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
            # 金叉，买入信号
            await self.place_buy_order(symbol, 100)
        elif short_ma.iloc[-1] < long_ma.iloc[-1] and short_ma.iloc[-2] >= long_ma.iloc[-2]:
            # 死叉，卖出信号
            await self.place_sell_order(symbol, 100)
```

### **2. 风险管理示例**
```python
class RiskManagementExample:
    def __init__(self, gateway, max_position_value=100000):
        self.gateway = gateway
        self.max_position_value = max_position_value
    
    async def check_risk_before_order(self, order):
        """下单前风险检查"""
        # 检查资金余额
        account = await self.gateway.query_account()
        if account.available < order.volume * order.price:
            raise ValueError("资金不足")
        
        # 检查持仓限制
        positions = await self.gateway.query_positions()
        total_position_value = sum(p.volume * p.price for p in positions)
        
        if total_position_value + order.volume * order.price > self.max_position_value:
            raise ValueError("超过最大持仓限制")
        
        return True
```

### **3. 数据同步示例**
```python
class DataSyncExample:
    def __init__(self, gateway, database):
        self.gateway = gateway
        self.database = database
    
    async def sync_market_data(self, symbols):
        """同步市场数据"""
        for symbol in symbols:
            # 获取实时数据
            market_data = await self.gateway.get_market_data(symbol)
            
            # 保存到数据库
            await self.database.save_market_data(market_data)
    
    async def sync_trade_data(self):
        """同步交易数据"""
        # 获取成交记录
        trades = await self.gateway.query_trades()
        
        # 保存到数据库
        for trade in trades:
            await self.database.save_trade(trade)
```

## 📊 示例测试

### **1. 单元测试示例**
```python
import pytest
from examples.domestic_gateways_usage_example import DomesticGatewayExample

class TestDomesticGatewayExample:
    @pytest.fixture
    def example(self):
        return DomesticGatewayExample()
    
    @pytest.mark.asyncio
    async def test_setup_gateway(self, example):
        """测试网关设置"""
        await example.setup_gateway()
        assert example.gateway is not None
        assert example.gateway.is_connected()
    
    @pytest.mark.asyncio
    async def test_query_account(self, example):
        """测试账户查询"""
        await example.setup_gateway()
        account = await example.query_account()
        assert account is not None
        assert hasattr(account, 'balance')
```

### **2. 集成测试示例**
```python
class IntegrationTestExample:
    async def test_full_trading_flow(self):
        """测试完整交易流程"""
        example = DomesticGatewayExample()
        
        # 1. 连接网关
        await example.setup_gateway()
        
        # 2. 查询初始状态
        initial_account = await example.query_account()
        initial_positions = await example.query_positions()
        
        # 3. 下单
        order = await example.place_order("000001.SZ", "BUY", 100, 15.50)
        assert order is not None
        
        # 4. 查询订单状态
        orders = await example.query_orders()
        assert len(orders) > 0
        
        # 5. 撤单
        cancel_result = await example.cancel_order(order.order_id)
        assert cancel_result is True
```

## 🔄 示例维护

### **1. 版本管理**
- 示例代码与平台版本同步
- 定期更新示例内容
- 维护向后兼容性

### **2. 质量保证**
- 代码审查
- 自动化测试
- 用户反馈收集

### **3. 文档更新**
- 及时更新使用说明
- 添加新的示例
- 修复已知问题

---

**总结**: Examples模块提供了丰富的示例代码和最佳实践，帮助用户快速上手RedFire平台。通过完整的代码示例、详细的文档说明和全面的测试覆盖，确保用户能够正确使用平台功能并开发自己的交易策略。
