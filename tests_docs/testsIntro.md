# Tests 模块介绍

## 🎯 概述

`tests` 是 RedFire 量化交易平台的测试模块，提供完整的测试框架和测试用例，确保系统的质量、稳定性和可靠性。该模块包含单元测试、集成测试、性能测试和端到端测试等多种测试类型。

## 📁 目录结构

```
tests/
└── test_domestic_gateways.py  # 🚪 国内网关测试
```

## 🧪 测试内容详解

### **国内网关测试** (`test_domestic_gateways.py`)

**作用**: 测试国内交易所网关的功能和性能

**测试内容**:
- 网关连接测试
- 订单管理测试
- 数据查询测试
- 错误处理测试
- 性能压力测试

**测试框架**: pytest + pytest-asyncio

## 🔧 测试框架

### **1. 测试配置**

```python
# tests/conftest.py
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_gateway_config():
    """模拟网关配置"""
    return {
        "gateway_name": "TestGateway",
        "username": "test_user",
        "password": "test_password",
        "server": "test.server.com",
        "port": 12345
    }

@pytest.fixture
def mock_market_data():
    """模拟市场数据"""
    return {
        "symbol": "000001.SZ",
        "timestamp": "2024-01-01T10:00:00Z",
        "open": 15.20,
        "high": 15.50,
        "low": 15.10,
        "close": 15.35,
        "volume": 1000000,
        "amount": 15350000
    }

@pytest.fixture
def mock_order_data():
    """模拟订单数据"""
    return {
        "symbol": "000001.SZ",
        "direction": "BUY",
        "quantity": 100,
        "price": 15.50,
        "order_type": "LIMIT"
    }
```

### **2. 测试用例结构**

```python
# tests/test_domestic_gateways.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from redfire.gateway import DomesticGateway
from redfire.models import Order, Position, Account

class TestDomesticGateway:
    """国内网关测试类"""
    
    @pytest.fixture
    async def gateway(self, mock_gateway_config):
        """创建测试网关实例"""
        gateway = DomesticGateway(mock_gateway_config)
        yield gateway
        await gateway.disconnect()
    
    @pytest.mark.asyncio
    async def test_gateway_connection(self, gateway):
        """测试网关连接"""
        # 模拟连接成功
        with patch.object(gateway, '_connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            
            result = await gateway.connect()
            
            assert result is True
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_gateway_connection_failure(self, gateway):
        """测试网关连接失败"""
        # 模拟连接失败
        with patch.object(gateway, '_connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = ConnectionError("Connection failed")
            
            with pytest.raises(ConnectionError):
                await gateway.connect()
    
    @pytest.mark.asyncio
    async def test_query_account(self, gateway, mock_gateway_config):
        """测试账户查询"""
        # 模拟账户数据
        mock_account_data = {
            "balance": 100000.00,
            "available": 95000.00,
            "position_value": 5000.00,
            "frozen": 5000.00
        }
        
        with patch.object(gateway, '_query_account', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_account_data
            
            account = await gateway.query_account()
            
            assert account is not None
            assert account.balance == 100000.00
            assert account.available == 95000.00
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_positions(self, gateway):
        """测试持仓查询"""
        # 模拟持仓数据
        mock_positions_data = [
            {
                "symbol": "000001.SZ",
                "quantity": 1000,
                "cost": 15.20,
                "price": 15.35,
                "pnl": 150.00
            },
            {
                "symbol": "000002.SZ",
                "quantity": 500,
                "cost": 20.10,
                "price": 20.50,
                "pnl": 200.00
            }
        ]
        
        with patch.object(gateway, '_query_positions', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_positions_data
            
            positions = await gateway.query_positions()
            
            assert len(positions) == 2
            assert positions[0].symbol == "000001.SZ"
            assert positions[0].quantity == 1000
            assert positions[1].symbol == "000002.SZ"
            assert positions[1].quantity == 500
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_place_order(self, gateway, mock_order_data):
        """测试下单"""
        # 模拟下单结果
        mock_order_result = {
            "order_id": "order123",
            "status": "PENDING",
            "message": "Order placed successfully"
        }
        
        with patch.object(gateway, '_place_order', new_callable=AsyncMock) as mock_place:
            mock_place.return_value = mock_order_result
            
            order = Order(**mock_order_data)
            result = await gateway.place_order(order)
            
            assert result is not None
            assert result.order_id == "order123"
            assert result.status == "PENDING"
            mock_place.assert_called_once_with(order)
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, gateway):
        """测试撤单"""
        order_id = "order123"
        
        with patch.object(gateway, '_cancel_order', new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = True
            
            result = await gateway.cancel_order(order_id)
            
            assert result is True
            mock_cancel.assert_called_once_with(order_id)
    
    @pytest.mark.asyncio
    async def test_query_orders(self, gateway):
        """测试订单查询"""
        # 模拟订单数据
        mock_orders_data = [
            {
                "order_id": "order123",
                "symbol": "000001.SZ",
                "direction": "BUY",
                "quantity": 100,
                "price": 15.50,
                "status": "FILLED"
            },
            {
                "order_id": "order124",
                "symbol": "000002.SZ",
                "direction": "SELL",
                "quantity": 200,
                "price": 20.00,
                "status": "PENDING"
            }
        ]
        
        with patch.object(gateway, '_query_orders', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_orders_data
            
            orders = await gateway.query_orders()
            
            assert len(orders) == 2
            assert orders[0].order_id == "order123"
            assert orders[0].status == "FILLED"
            assert orders[1].order_id == "order124"
            assert orders[1].status == "PENDING"
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_market_data(self, gateway):
        """测试行情订阅"""
        symbols = ["000001.SZ", "000002.SZ"]
        
        with patch.object(gateway, '_subscribe_market_data', new_callable=AsyncMock) as mock_subscribe:
            mock_subscribe.return_value = True
            
            result = await gateway.subscribe_market_data(symbols)
            
            assert result is True
            mock_subscribe.assert_called_once_with(symbols)
    
    @pytest.mark.asyncio
    async def test_market_data_callback(self, gateway, mock_market_data):
        """测试行情数据回调"""
        callback_called = False
        received_data = None
        
        def test_callback(data):
            nonlocal callback_called, received_data
            callback_called = True
            received_data = data
        
        # 设置回调函数
        gateway.set_market_data_callback(test_callback)
        
        # 模拟收到行情数据
        await gateway._handle_market_data(mock_market_data)
        
        assert callback_called is True
        assert received_data is not None
        assert received_data["symbol"] == "000001.SZ"
        assert received_data["close"] == 15.35
```

## 📊 性能测试

### **1. 压力测试**

```python
# tests/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from redfire.gateway import DomesticGateway

class TestGatewayPerformance:
    """网关性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_orders(self, gateway):
        """测试并发下单性能"""
        num_orders = 100
        orders = []
        
        # 创建测试订单
        for i in range(num_orders):
            order = Order(
                symbol=f"00000{i%10}.SZ",
                direction="BUY" if i % 2 == 0 else "SELL",
                quantity=100,
                price=15.50 + i * 0.01
            )
            orders.append(order)
        
        # 并发下单
        start_time = time.time()
        tasks = [gateway.place_order(order) for order in orders]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 统计结果
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        failure_count = len(results) - success_count
        execution_time = end_time - start_time
        
        # 性能断言
        assert success_count >= num_orders * 0.95  # 95%成功率
        assert execution_time < 30  # 30秒内完成
        assert failure_count <= num_orders * 0.05  # 失败率不超过5%
    
    @pytest.mark.asyncio
    async def test_market_data_throughput(self, gateway):
        """测试行情数据吞吐量"""
        num_messages = 1000
        received_count = 0
        
        def data_callback(data):
            nonlocal received_count
            received_count += 1
        
        gateway.set_market_data_callback(data_callback)
        
        # 模拟大量行情数据
        start_time = time.time()
        tasks = []
        for i in range(num_messages):
            data = {
                "symbol": f"00000{i%10}.SZ",
                "timestamp": time.time(),
                "price": 15.50 + i * 0.01,
                "volume": 1000 + i
            }
            task = gateway._handle_market_data(data)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 统计结果
        execution_time = end_time - start_time
        throughput = num_messages / execution_time
        
        # 性能断言
        assert received_count == num_messages
        assert throughput > 100  # 每秒处理100条消息
        assert execution_time < 10  # 10秒内完成
```

### **2. 负载测试**

```python
# tests/test_load.py
import pytest
import asyncio
import aiohttp
import time
from typing import List

class TestLoadTesting:
    """负载测试"""
    
    @pytest.mark.asyncio
    async def test_api_load(self):
        """测试API负载"""
        base_url = "http://localhost:8000"
        num_requests = 1000
        concurrent_users = 50
        
        async def make_request(session, url):
            async with session.get(url) as response:
                return await response.json()
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            # 创建并发任务
            tasks = []
            for i in range(num_requests):
                url = f"{base_url}/api/health"
                task = make_request(session, url)
                tasks.append(task)
            
            # 限制并发数
            semaphore = asyncio.Semaphore(concurrent_users)
            
            async def limited_request(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(*[limited_request(task) for task in tasks])
            end_time = time.time()
            
            # 统计结果
            success_count = sum(1 for r in results if r.get("success"))
            execution_time = end_time - start_time
            requests_per_second = num_requests / execution_time
            
            # 性能断言
            assert success_count >= num_requests * 0.99  # 99%成功率
            assert requests_per_second > 50  # 每秒50个请求
            assert execution_time < 20  # 20秒内完成
```

## 🔍 集成测试

### **1. 端到端测试**

```python
# tests/test_e2e.py
import pytest
import asyncio
from redfire.gateway import DomesticGateway
from redfire.models import Order

class TestEndToEnd:
    """端到端测试"""
    
    @pytest.mark.asyncio
    async def test_complete_trading_flow(self, gateway):
        """测试完整交易流程"""
        # 1. 连接网关
        await gateway.connect()
        assert gateway.is_connected()
        
        # 2. 查询账户
        account = await gateway.query_account()
        assert account is not None
        assert account.balance > 0
        
        # 3. 查询持仓
        positions = await gateway.query_positions()
        assert isinstance(positions, list)
        
        # 4. 订阅行情
        symbols = ["000001.SZ"]
        await gateway.subscribe_market_data(symbols)
        
        # 5. 下单
        order = Order(
            symbol="000001.SZ",
            direction="BUY",
            quantity=100,
            price=15.50
        )
        result = await gateway.place_order(order)
        assert result is not None
        assert result.order_id is not None
        
        # 6. 查询订单
        orders = await gateway.query_orders()
        assert len(orders) > 0
        
        # 7. 撤单
        if result.status == "PENDING":
            cancel_result = await gateway.cancel_order(result.order_id)
            assert cancel_result is True
        
        # 8. 断开连接
        await gateway.disconnect()
        assert not gateway.is_connected()
```

### **2. 数据库集成测试**

```python
# tests/test_database_integration.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from redfire.database import get_database
from redfire.models import User, Order

class TestDatabaseIntegration:
    """数据库集成测试"""
    
    @pytest.fixture
    async def db_session(self):
        """数据库会话"""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            yield session
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_user_creation(self, db_session):
        """测试用户创建"""
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "test_user"
        assert user.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_order_creation(self, db_session):
        """测试订单创建"""
        # 创建用户
        user = User(username="test_user", email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        
        # 创建订单
        order = Order(
            user_id=user.id,
            symbol="000001.SZ",
            direction="BUY",
            quantity=100,
            price=15.50
        )
        
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        
        assert order.id is not None
        assert order.user_id == user.id
        assert order.symbol == "000001.SZ"
        assert order.direction == "BUY"
```

## 🚀 测试运行

### **1. 运行所有测试**

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_domestic_gateways.py

# 运行特定测试类
pytest tests/test_domestic_gateways.py::TestDomesticGateway

# 运行特定测试方法
pytest tests/test_domestic_gateways.py::TestDomesticGateway::test_gateway_connection
```

### **2. 测试配置**

```python
# pytest.ini
[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    e2e: marks tests as end-to-end tests
```

### **3. 测试覆盖率**

```bash
# 运行测试并生成覆盖率报告
pytest --cov=redfire --cov-report=html --cov-report=term

# 运行测试并生成XML覆盖率报告
pytest --cov=redfire --cov-report=xml

# 检查覆盖率阈值
pytest --cov=redfire --cov-fail-under=80
```

## 📊 测试报告

### **1. 测试结果分析**

```python
# tests/report_analyzer.py
import json
import statistics
from typing import Dict, List

class TestReportAnalyzer:
    """测试报告分析器"""
    
    def __init__(self, report_file: str):
        self.report_file = report_file
        self.report_data = self.load_report()
    
    def load_report(self) -> Dict:
        """加载测试报告"""
        with open(self.report_file, 'r') as f:
            return json.load(f)
    
    def get_test_summary(self) -> Dict:
        """获取测试摘要"""
        return {
            "total_tests": self.report_data.get("total", 0),
            "passed": self.report_data.get("passed", 0),
            "failed": self.report_data.get("failed", 0),
            "skipped": self.report_data.get("skipped", 0),
            "success_rate": self.calculate_success_rate()
        }
    
    def calculate_success_rate(self) -> float:
        """计算成功率"""
        total = self.report_data.get("total", 0)
        passed = self.report_data.get("passed", 0)
        return (passed / total * 100) if total > 0 else 0
    
    def get_performance_metrics(self) -> Dict:
        """获取性能指标"""
        test_times = self.report_data.get("test_times", [])
        return {
            "average_time": statistics.mean(test_times) if test_times else 0,
            "median_time": statistics.median(test_times) if test_times else 0,
            "min_time": min(test_times) if test_times else 0,
            "max_time": max(test_times) if test_times else 0
        }
    
    def generate_report(self) -> str:
        """生成测试报告"""
        summary = self.get_test_summary()
        performance = self.get_performance_metrics()
        
        report = f"""
测试报告
========

测试摘要:
- 总测试数: {summary['total_tests']}
- 通过: {summary['passed']}
- 失败: {summary['failed']}
- 跳过: {summary['skipped']}
- 成功率: {summary['success_rate']:.2f}%

性能指标:
- 平均执行时间: {performance['average_time']:.3f}秒
- 中位数执行时间: {performance['median_time']:.3f}秒
- 最短执行时间: {performance['min_time']:.3f}秒
- 最长执行时间: {performance['max_time']:.3f}秒
        """
        
        return report
```

---

**总结**: Tests模块提供了完整的测试框架和测试用例，包括单元测试、集成测试、性能测试和端到端测试。通过全面的测试覆盖和自动化测试流程，确保系统的质量、稳定性和可靠性，为持续集成和部署提供重要支持。
