"""
国内券商网关集成测试
测试vnpy_ctptest、vnpy_xtp、vnpy_oes三个接口的完整功能
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.core.tradingEngine.adapters.domestic_gateways_adapter import (
    DomesticGatewaysAdapter, DomesticGatewayConfig, DomesticGatewayType, GatewayStatus
)
from backend.core.tradingEngine.config.domestic_gateways_config import (
    DomesticGatewaysConfigManager, CtptestConfig, XtpConfig, OesConfig
)
from backend.core.tradingEngine.monitoring.domestic_gateway_monitor import (
    DomesticGatewayMonitor, AlertRule, AlertLevel, MetricType
)
from backend.core.tradingEngine.gateways.ctptest_gateway import CtptestGateway
from backend.core.tradingEngine.gateways.xtp_gateway import XtpGateway
from backend.core.tradingEngine.gateways.oes_gateway import OesGateway


class TestDomesticGatewaysAdapter:
    """国内券商适配器测试"""
    
    @pytest.fixture
    def mock_main_engine(self):
        """模拟主引擎"""
        return Mock()
    
    @pytest.fixture
    def test_config(self):
        """测试配置"""
        return DomesticGatewayConfig(
            enabled_gateways=[DomesticGatewayType.CTPTEST],
            ctptest_config={
                'userid': 'test_user',
                'password': 'test_pass',
                'brokerid': '9999',
                'td_address': 'tcp://180.168.146.187:10101',
                'md_address': 'tcp://180.168.146.187:10111'
            },
            xtp_config={'enabled': False},
            oes_config={'enabled': False},
            enable_auto_reconnect=True,
            reconnect_interval=1,
            max_reconnect_attempts=3
        )
    
    @pytest.fixture
    def adapter(self, mock_main_engine):
        """适配器实例"""
        return DomesticGatewaysAdapter(mock_main_engine)
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter, test_config):
        """测试适配器初始化"""
        # 测试初始化
        result = await adapter.initialize(test_config)
        
        assert result is True
        assert adapter.is_initialized is True
        assert adapter.config == test_config
        assert len(adapter.gateways) == 1  # 只启用了CTPTEST
        assert "CTPTEST" in adapter.gateways
    
    @pytest.mark.asyncio
    async def test_gateway_connection(self, adapter, test_config):
        """测试网关连接"""
        await adapter.initialize(test_config)
        
        # 模拟网关连接成功
        with patch.object(adapter.gateways["CTPTEST"], 'connect', new_callable=AsyncMock, return_value=True):
            results = await adapter.connect_all_gateways()
            
            assert results["CTPTEST"] is True
            assert "CTPTEST" in adapter.active_gateways
            assert adapter.gateway_status["CTPTEST"].connected is True
    
    @pytest.mark.asyncio
    async def test_gateway_disconnection(self, adapter, test_config):
        """测试网关断开连接"""
        await adapter.initialize(test_config)
        
        # 先连接
        with patch.object(adapter.gateways["CTPTEST"], 'connect', new_callable=AsyncMock, return_value=True):
            await adapter.connect_all_gateways()
        
        # 再断开
        with patch.object(adapter.gateways["CTPTEST"], 'disconnect', new_callable=AsyncMock, return_value=True):
            results = await adapter.disconnect_all_gateways()
            
            assert results["CTPTEST"] is True
            assert "CTPTEST" not in adapter.active_gateways
    
    @pytest.mark.asyncio
    async def test_order_submission(self, adapter, test_config):
        """测试订单提交"""
        await adapter.initialize(test_config)
        
        # 设置为已连接状态
        adapter.active_gateways = ["CTPTEST"]
        
        order_data = {
            'symbol': '000001',
            'price': 10.0,
            'volume': 100,
            'direction': 'BUY'
        }
        
        expected_order_id = "test_order_123"
        
        with patch.object(adapter.gateways["CTPTEST"], 'submit_order', 
                         new_callable=AsyncMock, return_value=expected_order_id):
            order_id = await adapter.submit_order(order_data)
            
            assert order_id == expected_order_id
            assert adapter.gateway_status["CTPTEST"].orders_count == 1
    
    @pytest.mark.asyncio
    async def test_order_cancellation(self, adapter, test_config):
        """测试订单撤销"""
        await adapter.initialize(test_config)
        adapter.active_gateways = ["CTPTEST"]
        
        order_id = "test_order_123"
        
        with patch.object(adapter.gateways["CTPTEST"], 'cancel_order', 
                         new_callable=AsyncMock, return_value=True):
            result = await adapter.cancel_order(order_id, "CTPTEST")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_market_data_subscription(self, adapter, test_config):
        """测试行情订阅"""
        await adapter.initialize(test_config)
        adapter.active_gateways = ["CTPTEST"]
        
        symbols = ["000001", "000002"]
        
        with patch.object(adapter.gateways["CTPTEST"], 'subscribe_market_data', 
                         new_callable=AsyncMock, return_value=True):
            results = await adapter.subscribe_market_data(symbols)
            
            assert results["CTPTEST"] is True
    
    @pytest.mark.asyncio
    async def test_auto_reconnection(self, adapter, test_config):
        """测试自动重连功能"""
        test_config.enable_auto_reconnect = True
        test_config.reconnect_interval = 0.1  # 快速测试
        
        await adapter.initialize(test_config)
        
        # 模拟连接失败然后成功
        connect_calls = [False, True]  # 第一次失败，第二次成功
        
        with patch.object(adapter, '_connect_single_gateway', 
                         new_callable=AsyncMock, side_effect=connect_calls):
            await adapter._start_reconnection_monitoring()
            
            # 等待重连尝试
            await asyncio.sleep(0.2)
            
            await adapter._stop_reconnection_monitoring()
    
    @pytest.mark.asyncio
    async def test_event_callbacks(self, adapter, test_config):
        """测试事件回调"""
        await adapter.initialize(test_config)
        
        # 注册回调
        connected_called = False
        disconnected_called = False
        
        async def on_connected(gateway_name):
            nonlocal connected_called
            connected_called = True
        
        async def on_disconnected(gateway_name):
            nonlocal disconnected_called
            disconnected_called = True
        
        adapter.on('on_gateway_connected', on_connected)
        adapter.on('on_gateway_disconnected', on_disconnected)
        
        # 触发事件
        await adapter._on_gateway_connected("CTPTEST")
        await adapter._on_gateway_disconnected("CTPTEST")
        
        assert connected_called is True
        assert disconnected_called is True


class TestDomesticGatewaysConfigManager:
    """配置管理器测试"""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """配置管理器实例"""
        return DomesticGatewaysConfigManager(str(tmp_path))
    
    def test_config_manager_initialization(self, config_manager):
        """测试配置管理器初始化"""
        assert config_manager.current_environment == "development"
        assert len(config_manager.default_configs) == 4
        assert len(config_manager.config_files) == 4
    
    def test_load_default_config(self, config_manager):
        """测试加载默认配置"""
        config = config_manager.load_config("development")
        
        assert isinstance(config, DomesticGatewayConfig)
        assert DomesticGatewayType.CTPTEST in config.enabled_gateways
        assert config.enable_auto_reconnect is True
    
    def test_save_and_load_config(self, config_manager):
        """测试保存和加载配置"""
        # 创建测试配置
        test_config = DomesticGatewayConfig(
            enabled_gateways=[DomesticGatewayType.XTP],
            xtp_config={
                'userid': 'test_xtp_user',
                'password': 'test_xtp_pass',
                'client_id': 2
            },
            enable_auto_reconnect=False
        )
        
        # 保存配置
        result = config_manager.save_config(test_config, "testing")
        assert result is True
        
        # 重新加载配置
        loaded_config = config_manager.reload_config("testing")
        assert loaded_config.enable_auto_reconnect is False
        assert DomesticGatewayType.XTP in loaded_config.enabled_gateways
    
    def test_config_validation(self, config_manager):
        """测试配置验证"""
        # 有效配置
        valid_config = DomesticGatewayConfig(
            enabled_gateways=[DomesticGatewayType.CTPTEST],
            ctptest_config={
                'userid': 'test',
                'password': 'test',
                'brokerid': '9999',
                'td_address': 'tcp://test:10101',
                'md_address': 'tcp://test:10111'
            }
        )
        
        assert config_manager.validate_config(valid_config) is True
        
        # 无效配置 (缺少必要字段)
        invalid_config = DomesticGatewayConfig(
            enabled_gateways=[DomesticGatewayType.CTPTEST],
            ctptest_config={}  # 缺少必要字段
        )
        
        assert config_manager.validate_config(invalid_config) is False
    
    def test_export_import_config(self, config_manager, tmp_path):
        """测试配置导出和导入"""
        # 创建测试配置
        test_config = config_manager.load_config("development")
        
        # 导出配置
        export_file = str(tmp_path / "test_export.yaml")
        result = config_manager.export_config(test_config, export_file)
        assert result is True
        
        # 导入配置
        imported_config = config_manager.import_config(export_file)
        assert imported_config is not None
        assert isinstance(imported_config, DomesticGatewayConfig)


class TestDomesticGatewayMonitor:
    """网关监控系统测试"""
    
    @pytest.fixture
    def monitor(self):
        """监控系统实例"""
        return DomesticGatewayMonitor(monitor_interval=0.1)  # 快速测试
    
    def test_monitor_initialization(self, monitor):
        """测试监控系统初始化"""
        assert monitor.is_monitoring is False
        assert len(monitor.alert_rules) > 0  # 有默认规则
        assert len(monitor.alert_callbacks) == 0
    
    @pytest.mark.asyncio
    async def test_monitoring_start_stop(self, monitor):
        """测试监控启动和停止"""
        # 启动监控
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True
        assert monitor.monitor_task is not None
        
        # 停止监控
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False
    
    def test_latency_recording(self, monitor):
        """测试延迟记录"""
        gateway_name = "CTPTEST"
        
        # 记录延迟数据
        monitor.record_latency(gateway_name, 50.0)
        monitor.record_latency(gateway_name, 75.0)
        monitor.record_latency(gateway_name, 100.0)
        
        assert len(monitor.latency_data[gateway_name]) == 3
        
        # 计算延迟统计
        stats = monitor._calculate_latency_statistics(gateway_name)
        assert stats['avg'] > 0
        assert stats['max'] == 100.0
        assert stats['min'] == 50.0
    
    def test_order_result_recording(self, monitor):
        """测试订单结果记录"""
        gateway_name = "CTPTEST"
        
        # 记录订单结果
        monitor.record_order_result(gateway_name, True)   # 成功
        monitor.record_order_result(gateway_name, True)   # 成功
        monitor.record_order_result(gateway_name, False)  # 失败
        
        # 检查统计
        stats = monitor.stats[gateway_name]
        assert stats['total_orders'] == 3
        assert stats['successful_orders'] == 2
        assert stats['failed_orders'] == 1
        
        # 检查成功率
        success_rate = monitor._calculate_success_rate(gateway_name)
        assert abs(success_rate - 66.67) < 0.1  # 约66.67%
    
    def test_error_recording(self, monitor):
        """测试错误记录"""
        gateway_name = "CTPTEST"
        
        # 记录错误
        monitor.record_error(gateway_name, "CONNECTION_ERROR", "Connection timeout")
        monitor.record_error(gateway_name, "ORDER_ERROR", "Invalid order")
        
        # 检查错误统计
        errors = monitor.stats[gateway_name]['errors']
        assert len(errors) == 2
        assert errors[0]['type'] == "CONNECTION_ERROR"
        assert errors[1]['type'] == "ORDER_ERROR"
    
    def test_alert_rules(self, monitor):
        """测试告警规则"""
        # 添加自定义规则
        custom_rule = AlertRule(
            name="test_rule",
            metric_type=MetricType.LATENCY,
            condition=">=",
            threshold=200.0,
            level=AlertLevel.WARNING
        )
        
        monitor.add_alert_rule(custom_rule)
        assert "test_rule" in monitor.alert_rules
        
        # 启用/禁用规则
        monitor.disable_alert_rule("test_rule")
        assert monitor.alert_rules["test_rule"].enabled is False
        
        monitor.enable_alert_rule("test_rule")
        assert monitor.alert_rules["test_rule"].enabled is True
        
        # 移除规则
        monitor.remove_alert_rule("test_rule")
        assert "test_rule" not in monitor.alert_rules
    
    def test_alert_triggering(self, monitor):
        """测试告警触发"""
        gateway_name = "CTPTEST"
        
        # 添加告警回调
        alerts_received = []
        
        def alert_callback(alert):
            alerts_received.append(alert)
        
        monitor.add_alert_callback(alert_callback)
        
        # 触发高延迟告警 (需要连续3次违规)
        for _ in range(3):
            monitor.record_latency(gateway_name, 150.0)  # 超过100ms阈值
        
        # 检查是否触发告警
        assert len(alerts_received) > 0
        alert = alerts_received[0]
        assert alert.rule_name == "high_latency"
        assert alert.gateway_name == gateway_name
        assert alert.level == AlertLevel.WARNING
    
    def test_performance_metrics_update(self, monitor):
        """测试性能指标更新"""
        gateway_name = "CTPTEST"
        
        # 创建模拟状态
        status = GatewayStatus(
            name=gateway_name,
            type=DomesticGatewayType.CTPTEST,
            connected=True,
            error_count=2
        )
        
        # 添加一些测试数据
        monitor.record_latency(gateway_name, 50.0)
        monitor.record_latency(gateway_name, 75.0)
        monitor.record_order_result(gateway_name, True)
        
        # 更新性能指标
        monitor.update_performance_metrics(gateway_name, status)
        
        # 检查指标历史
        metrics_history = monitor.get_performance_metrics(gateway_name)
        assert len(metrics_history) > 0
        
        latest_metrics = metrics_history[-1]
        assert latest_metrics.gateway_name == gateway_name
        assert latest_metrics.avg_latency > 0
        assert latest_metrics.error_count == 2
    
    def test_statistics_retrieval(self, monitor):
        """测试统计信息获取"""
        gateway_name = "CTPTEST"
        
        # 添加测试数据
        monitor.record_latency(gateway_name, 100.0)
        monitor.record_order_result(gateway_name, True)
        monitor.record_error(gateway_name, "TEST_ERROR", "Test error message")
        
        # 获取统计信息
        stats = monitor.get_gateway_statistics(gateway_name)
        
        assert 'success_rate' in stats
        assert 'error_rate' in stats
        assert 'uptime' in stats
        assert 'latency_statistics' in stats
        
        # 获取所有统计信息
        all_stats = monitor.get_all_statistics()
        assert gateway_name in all_stats


class TestGatewayImplementations:
    """网关实现测试"""
    
    @pytest.fixture
    def mock_main_engine(self):
        return Mock()
    
    @pytest.mark.asyncio
    async def test_ctptest_gateway(self, mock_main_engine):
        """测试CTP测试网关"""
        gateway = CtptestGateway(mock_main_engine)
        
        assert gateway.gatewayName == "CTPTEST"
        assert gateway.isConnected is False
        
        # 测试配置验证
        valid_config = {
            'userid': 'test',
            'password': 'test',
            'brokerid': '9999',
            'td_address': 'tcp://test:10101',
            'md_address': 'tcp://test:10111'
        }
        
        assert gateway._validate_config_with_dict(valid_config) is True
        
        # 测试无效配置
        invalid_config = {'userid': 'test'}  # 缺少必要字段
        assert gateway._validate_config_with_dict(invalid_config) is False
    
    def _validate_config_with_dict(self, gateway, config):
        """辅助方法：使用字典验证配置"""
        gateway.gatewayConfig = config
        return gateway._validate_config()
    
    @pytest.mark.asyncio
    async def test_xtp_gateway(self, mock_main_engine):
        """测试XTP网关"""
        gateway = XtpGateway(mock_main_engine)
        
        assert gateway.gatewayName == "XTP"
        assert gateway.trade_connected is False
        assert gateway.quote_connected is False
        
        # 测试网关信息
        info = gateway.get_gateway_info()
        assert info['type'] == 'XTP'
        assert '中泰证券' in info['description']
        assert '极速交易' in info['features']
    
    @pytest.mark.asyncio
    async def test_oes_gateway(self, mock_main_engine):
        """测试OES网关"""
        gateway = OesGateway(mock_main_engine)
        
        assert gateway.gatewayName == "OES"
        assert gateway.ord_connected is False
        assert gateway.rpt_connected is False
        assert gateway.qry_connected is False
        
        # 测试网关信息
        info = gateway.get_gateway_info()
        assert info['type'] == 'OES'
        assert '宽睿OES' in info['description']
        assert '多通道架构' in info['features']


@pytest.mark.integration
class TestIntegrationScenarios:
    """集成测试场景"""
    
    @pytest.fixture
    def complete_system(self, tmp_path):
        """完整系统设置"""
        # 配置管理器
        config_manager = DomesticGatewaysConfigManager(str(tmp_path))
        
        # 监控系统
        monitor = DomesticGatewayMonitor(monitor_interval=0.1)
        
        # 适配器
        adapter = DomesticGatewaysAdapter()
        
        return {
            'config_manager': config_manager,
            'monitor': monitor,
            'adapter': adapter
        }
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, complete_system):
        """测试完整工作流程"""
        config_manager = complete_system['config_manager']
        monitor = complete_system['monitor']
        adapter = complete_system['adapter']
        
        # 1. 加载配置
        config = config_manager.load_config("development")
        assert config is not None
        
        # 2. 初始化适配器
        result = await adapter.initialize(config)
        assert result is True
        
        # 3. 启动监控
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True
        
        # 4. 模拟网关连接
        with patch.object(adapter.gateways["CTPTEST"], 'connect', 
                         new_callable=AsyncMock, return_value=True):
            connection_results = await adapter.connect_all_gateways()
            assert connection_results["CTPTEST"] is True
        
        # 5. 模拟交易操作
        order_data = {
            'symbol': '000001',
            'price': 10.0,
            'volume': 100,
            'direction': 'BUY'
        }
        
        with patch.object(adapter.gateways["CTPTEST"], 'submit_order', 
                         new_callable=AsyncMock, return_value="order_123"):
            order_id = await adapter.submit_order(order_data)
            assert order_id == "order_123"
        
        # 6. 记录性能数据
        monitor.record_latency("CTPTEST", 50.0)
        monitor.record_order_result("CTPTEST", True)
        
        # 7. 检查统计信息
        stats = monitor.get_gateway_statistics("CTPTEST")
        assert stats['success_rate'] == 100.0
        
        # 8. 清理
        await monitor.stop_monitoring()
        await adapter.disconnect_all_gateways()
    
    @pytest.mark.asyncio
    async def test_error_handling_scenario(self, complete_system):
        """测试错误处理场景"""
        monitor = complete_system['monitor']
        adapter = complete_system['adapter']
        
        # 初始化
        config = DomesticGatewayConfig(
            enabled_gateways=[DomesticGatewayType.CTPTEST],
            ctptest_config={'userid': 'test', 'password': 'test', 'brokerid': '9999'}
        )
        
        await adapter.initialize(config)
        await monitor.start_monitoring()
        
        # 模拟连接失败
        with patch.object(adapter.gateways["CTPTEST"], 'connect', 
                         new_callable=AsyncMock, return_value=False):
            connection_results = await adapter.connect_all_gateways()
            assert connection_results["CTPTEST"] is False
        
        # 模拟错误记录
        monitor.record_error("CTPTEST", "CONNECTION_ERROR", "Failed to connect")
        
        # 检查错误统计
        stats = monitor.get_gateway_statistics("CTPTEST")
        assert len(stats.get('errors', [])) > 0
        
        # 清理
        await monitor.stop_monitoring()
    
    @pytest.mark.asyncio 
    async def test_multi_gateway_scenario(self, complete_system):
        """测试多网关场景"""
        adapter = complete_system['adapter']
        
        # 配置多个网关
        config = DomesticGatewayConfig(
            enabled_gateways=[
                DomesticGatewayType.CTPTEST,
                DomesticGatewayType.XTP,
                DomesticGatewayType.OES
            ],
            ctptest_config={'userid': 'test', 'password': 'test', 'brokerid': '9999'},
            xtp_config={'userid': 'test', 'password': 'test', 'client_id': 1},
            oes_config={'username': 'test', 'password': 'test'}
        )
        
        await adapter.initialize(config)
        
        # 检查所有网关都已创建
        assert len(adapter.gateways) == 3
        assert "CTPTEST" in adapter.gateways
        assert "XTP" in adapter.gateways
        assert "OES" in adapter.gateways
        
        # 模拟部分网关连接成功
        with patch.object(adapter.gateways["CTPTEST"], 'connect', 
                         new_callable=AsyncMock, return_value=True), \
             patch.object(adapter.gateways["XTP"], 'connect', 
                         new_callable=AsyncMock, return_value=True), \
             patch.object(adapter.gateways["OES"], 'connect', 
                         new_callable=AsyncMock, return_value=False):
            
            connection_results = await adapter.connect_all_gateways()
            
            assert connection_results["CTPTEST"] is True
            assert connection_results["XTP"] is True
            assert connection_results["OES"] is False
            
            # 检查活跃网关
            assert len(adapter.active_gateways) == 2
            assert "CTPTEST" in adapter.active_gateways
            assert "XTP" in adapter.active_gateways
            assert "OES" not in adapter.active_gateways


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
