"""
策略引擎领域服务
提供策略引擎管理、VnPy集成、网关管理等功能
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from ..entities.strategy_config import StrategyConfig
from ..entities.strategy_instance import StrategyInstance
from ..entities.gateway_entity import TradingGateway, GatewayStatus, GatewayType
from ..entities.contract_entity import TradingContract, ContractType, Exchange

logger = logging.getLogger(__name__)


class StrategyEngineService:
    """策略引擎领域服务"""
    
    def __init__(self, storage_path: str = "./strategy_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._configs_cache: Dict[str, StrategyConfig] = {}
        self._instances_cache: Dict[str, StrategyInstance] = {}
        self._gateways_cache: Dict[str, TradingGateway] = {}
        self._contracts_cache: Dict[str, TradingContract] = {}
        
        # 引擎状态
        self._engine_status = {
            "engine_id": str(uuid.uuid4()),
            "status": "stopped",
            "start_time": None,
            "uptime": 0,
            "strategy_count": 0,
            "gateway_count": 0,
            "last_heartbeat": None,
            "version": "1.0.0",
            "is_healthy": False
        }
        
        # VnPy引擎状态
        self._vnpy_engine = None
        self._vnpy_available = False
        
        # 市场数据订阅
        self._market_data_subscriptions: Dict[str, Dict[str, Any]] = {}
        
        # 启动后台任务
        self._background_tasks = []
        self._is_running = False
    
    # ==================== 引擎管理 ====================
    
    async def start_engine(self) -> Dict[str, Any]:
        """启动策略引擎"""
        try:
            if self._engine_status["status"] == "running":
                logger.warning("策略引擎已经在运行")
                return {"success": True, "message": "引擎已在运行"}
            
            logger.info("正在启动策略引擎...")
            
            # 更新状态
            self._engine_status["status"] = "starting"
            self._engine_status["start_time"] = datetime.now()
            self._engine_status["is_healthy"] = True
            
            # 初始化VnPy引擎
            await self._initialize_vnpy_engine()
            
            # 启动后台任务
            await self._start_background_tasks()
            
            # 更新状态
            self._engine_status["status"] = "running"
            self._engine_status["last_heartbeat"] = datetime.now()
            
            logger.info("策略引擎启动成功")
            
            return {
                "success": True,
                "message": "策略引擎启动成功",
                "engine_id": self._engine_status["engine_id"],
                "start_time": self._engine_status["start_time"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"启动策略引擎失败: {e}")
            self._engine_status["status"] = "error"
            self._engine_status["is_healthy"] = False
            raise
    
    async def stop_engine(self) -> Dict[str, Any]:
        """停止策略引擎"""
        try:
            if self._engine_status["status"] == "stopped":
                logger.warning("策略引擎已经停止")
                return {"success": True, "message": "引擎已停止"}
            
            logger.info("正在停止策略引擎...")
            
            # 更新状态
            self._engine_status["status"] = "stopping"
            
            # 停止所有策略
            await self._stop_all_strategies()
            
            # 断开所有网关
            await self._disconnect_all_gateways()
            
            # 停止后台任务
            await self._stop_background_tasks()
            
            # 关闭VnPy引擎
            await self._shutdown_vnpy_engine()
            
            # 更新状态
            self._engine_status["status"] = "stopped"
            self._engine_status["is_healthy"] = False
            
            # 计算运行时间
            if self._engine_status["start_time"]:
                uptime = (datetime.now() - self._engine_status["start_time"]).total_seconds()
                self._engine_status["uptime"] = uptime
            
            logger.info("策略引擎停止成功")
            
            return {
                "success": True,
                "message": "策略引擎停止成功",
                "stop_time": datetime.now().isoformat(),
                "final_status": "stopped",
                "uptime": self._engine_status["uptime"]
            }
            
        except Exception as e:
            logger.error(f"停止策略引擎失败: {e}")
            self._engine_status["status"] = "error"
            raise
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        # 更新运行时间
        if (self._engine_status["status"] == "running" and 
            self._engine_status["start_time"]):
            uptime = (datetime.now() - self._engine_status["start_time"]).total_seconds()
            self._engine_status["uptime"] = uptime
        
        # 更新策略和网关数量
        self._engine_status["strategy_count"] = len(self._instances_cache)
        self._engine_status["gateway_count"] = len(self._gateways_cache)
        
        # 更新最后心跳时间
        self._engine_status["last_heartbeat"] = datetime.now()
        
        return self._engine_status.copy()
    
    # ==================== VnPy引擎管理 ====================
    
    async def _initialize_vnpy_engine(self):
        """初始化VnPy引擎"""
        try:
            # 这里应该集成真正的VnPy引擎
            # 目前使用模拟模式
            logger.info("初始化VnPy引擎...")
            
            # 模拟VnPy引擎初始化
            await asyncio.sleep(1)
            
            self._vnpy_available = True
            self._vnpy_engine = {
                "status": "initialized",
                "version": "2.0.0",
                "modules": ["ctp", "xtp", "ib"],
                "strategies": [],
                "gateways": []
            }
            
            logger.info("VnPy引擎初始化完成")
            
        except Exception as e:
            logger.error(f"VnPy引擎初始化失败: {e}")
            self._vnpy_available = False
            raise
    
    async def _shutdown_vnpy_engine(self):
        """关闭VnPy引擎"""
        try:
            if self._vnpy_engine:
                logger.info("正在关闭VnPy引擎...")
                
                # 模拟关闭过程
                await asyncio.sleep(0.5)
                
                self._vnpy_engine = None
                self._vnpy_available = False
                
                logger.info("VnPy引擎已关闭")
                
        except Exception as e:
            logger.error(f"关闭VnPy引擎失败: {e}")
    
    # ==================== 后台任务管理 ====================
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        try:
            self._is_running = True
            
            # 启动心跳任务
            heartbeat_task = asyncio.create_task(self._heartbeat_task())
            self._background_tasks.append(heartbeat_task)
            
            # 启动健康检查任务
            health_check_task = asyncio.create_task(self._health_check_task())
            self._background_tasks.append(health_check_task)
            
            # 启动市场数据更新任务
            market_data_task = asyncio.create_task(self._market_data_update_task())
            self._background_tasks.append(market_data_task)
            
            logger.info("后台任务启动完成")
            
        except Exception as e:
            logger.error(f"启动后台任务失败: {e}")
            raise
    
    async def _stop_background_tasks(self):
        """停止后台任务"""
        try:
            self._is_running = False
            
            # 取消所有任务
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            
            # 等待任务完成
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            self._background_tasks.clear()
            logger.info("后台任务已停止")
            
        except Exception as e:
            logger.error(f"停止后台任务失败: {e}")
    
    async def _heartbeat_task(self):
        """心跳任务"""
        while self._is_running:
            try:
                # 更新引擎心跳
                self._engine_status["last_heartbeat"] = datetime.now()
                
                # 更新网关心跳
                for gateway in self._gateways_cache.values():
                    if gateway.is_connected:
                        gateway.update_health()
                
                await asyncio.sleep(30)  # 30秒心跳间隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳任务异常: {e}")
                await asyncio.sleep(5)
    
    async def _health_check_task(self):
        """健康检查任务"""
        while self._is_running:
            try:
                # 检查引擎健康状态
                is_healthy = True
                
                # 检查网关健康状态
                for gateway in self._gateways_cache.values():
                    if gateway.is_connected:
                        # 检查最后心跳时间
                        if (gateway.health.last_heartbeat and 
                            (datetime.now() - gateway.health.last_heartbeat).total_seconds() > 60):
                            gateway.record_error("心跳超时")
                            is_healthy = False
                
                self._engine_status["is_healthy"] = is_healthy
                
                await asyncio.sleep(60)  # 60秒检查间隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查任务异常: {e}")
                await asyncio.sleep(10)
    
    async def _market_data_update_task(self):
        """市场数据更新任务"""
        while self._is_running:
            try:
                # 更新订阅的市场数据
                for subscription_id, subscription in self._market_data_subscriptions.items():
                    symbols = subscription.get("symbols", [])
                    for symbol in symbols:
                        # 模拟市场数据更新
                        await self._update_market_data(symbol)
                
                await asyncio.sleep(1)  # 1秒更新间隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"市场数据更新任务异常: {e}")
                await asyncio.sleep(5)
    
    # ==================== 策略管理 ====================
    
    async def _stop_all_strategies(self):
        """停止所有策略"""
        try:
            for instance in self._instances_cache.values():
                if instance.status == "running":
                    await self.stop_strategy(instance.instance_id)
            
            logger.info("所有策略已停止")
            
        except Exception as e:
            logger.error(f"停止所有策略失败: {e}")
    
    # ==================== 网关管理 ====================
    
    async def get_gateway_list(self) -> List[TradingGateway]:
        """获取网关列表"""
        return list(self._gateways_cache.values())
    
    async def connect_gateway(self, gateway_id: str) -> Dict[str, Any]:
        """连接网关"""
        try:
            if gateway_id not in self._gateways_cache:
                raise ValueError(f"网关不存在: {gateway_id}")
            
            gateway = self._gateways_cache[gateway_id]
            
            if gateway.is_connected:
                return {"success": True, "message": "网关已连接"}
            
            # 连接网关
            success = gateway.connect()
            
            if success:
                logger.info(f"网关连接成功: {gateway_id}")
                return {
                    "success": True,
                    "message": "网关连接成功",
                    "connection_time": datetime.now().isoformat()
                }
            else:
                raise Exception("网关连接失败")
                
        except Exception as e:
            logger.error(f"连接网关失败: {e}")
            raise
    
    async def disconnect_gateway(self, gateway_id: str) -> Dict[str, Any]:
        """断开网关连接"""
        try:
            if gateway_id not in self._gateways_cache:
                raise ValueError(f"网关不存在: {gateway_id}")
            
            gateway = self._gateways_cache[gateway_id]
            
            if not gateway.is_connected:
                return {"success": True, "message": "网关已断开"}
            
            # 断开网关
            success = gateway.disconnect()
            
            if success:
                logger.info(f"网关断开成功: {gateway_id}")
                return {
                    "success": True,
                    "message": "网关断开成功",
                    "disconnect_time": datetime.now().isoformat()
                }
            else:
                raise Exception("网关断开失败")
                
        except Exception as e:
            logger.error(f"断开网关失败: {e}")
            raise
    
    async def get_contract_info(self, gateway_id: str) -> List[TradingContract]:
        """获取合约信息"""
        try:
            if gateway_id not in self._gateways_cache:
                raise ValueError(f"网关不存在: {gateway_id}")
            
            # 返回该网关下的所有合约
            contracts = [
                contract for contract in self._contracts_cache.values()
                if contract.exchange.value in gateway_id  # 简化匹配逻辑
            ]
            
            return contracts
            
        except Exception as e:
            logger.error(f"获取合约信息失败: {e}")
            raise
    
    async def _disconnect_all_gateways(self):
        """断开所有网关"""
        try:
            for gateway in self._gateways_cache.values():
                if gateway.is_connected:
                    await self.disconnect_gateway(gateway.gateway_id)
            
            logger.info("所有网关已断开")
            
        except Exception as e:
            logger.error(f"断开所有网关失败: {e}")
    
    # ==================== 市场数据管理 ====================
    
    async def subscribe_market_data(
        self, 
        symbols: List[str], 
        data_type: str = "tick",
        interval: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """订阅市场数据"""
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = {
                "subscription_id": subscription_id,
                "symbols": symbols,
                "data_type": data_type,
                "interval": interval,
                "user_id": user_id,
                "created_at": datetime.now(),
                "is_active": True
            }
            
            self._market_data_subscriptions[subscription_id] = subscription
            
            logger.info(f"市场数据订阅成功: {subscription_id}, 品种: {symbols}")
            
            return {
                "subscription_id": subscription_id,
                "symbols": symbols,
                "data_type": data_type
            }
            
        except Exception as e:
            logger.error(f"订阅市场数据失败: {e}")
            raise
    
    async def get_realtime_data(self, symbols: List[str], user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取实时数据"""
        try:
            data_list = []
            
            for symbol in symbols:
                if symbol in self._contracts_cache:
                    contract = self._contracts_cache[symbol]
                    
                    data = {
                        "symbol": symbol,
                        "data_type": "tick",
                        "timestamp": contract.price_info.timestamp or datetime.now(),
                        "data": {
                            "price": contract.price_info.to_dict(),
                            "volume": contract.volume_info.to_dict(),
                            "contract_info": {
                                "size": contract.size,
                                "price_tick": contract.price_tick,
                                "exchange": contract.exchange.value
                            }
                        }
                    }
                    
                    data_list.append(data)
            
            return data_list
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            raise
    
    async def _update_market_data(self, symbol: str):
        """更新市场数据"""
        try:
            if symbol in self._contracts_cache:
                contract = self._contracts_cache[symbol]
                
                # 模拟价格更新
                import random
                price_change = random.uniform(-0.01, 0.01)
                new_price = max(0.01, contract.price_info.last_price + price_change)
                
                # 更新价格信息
                price_data = {
                    "last_price": new_price,
                    "bid_price": new_price - 0.001,
                    "ask_price": new_price + 0.001,
                    "high_price": max(contract.price_info.high_price, new_price),
                    "low_price": min(contract.price_info.low_price, new_price) if contract.price_info.low_price > 0 else new_price
                }
                
                contract.price_info.update_price(price_data)
                
                # 更新成交量信息
                volume_data = {
                    "volume": contract.volume_info.volume + random.randint(0, 10),
                    "open_interest": contract.volume_info.open_interest + random.randint(-5, 5)
                }
                
                contract.volume_info.update_volume(volume_data)
                
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
    
    # ==================== 策略管理扩展 ====================
    
    async def create_strategy(
        self,
        strategy_name: str,
        strategy_type: str,
        parameters: Dict[str, Any],
        risk_limits: Dict[str, Any],
        description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> StrategyInstance:
        """创建策略"""
        try:
            # 创建策略配置
            config = StrategyConfig(
                strategy_name=strategy_name,
                strategy_type=strategy_type,
                parameters=parameters,
                risk_limits=risk_limits,
                description=description,
                user_id=user_id
            )
            
            # 创建策略实例
            instance = StrategyInstance(
                strategy_name=strategy_name,
                strategy_type=strategy_type,
                parameters=parameters,
                risk_limits=risk_limits,
                description=description,
                user_id=user_id
            )
            
            # 保存到缓存
            self._configs_cache[strategy_name] = config
            self._instances_cache[instance.instance_id] = instance
            
            # 保存到文件
            await self.save_strategy_config(config)
            await self.save_strategy_instance(instance)
            
            logger.info(f"策略创建成功: {strategy_name}")
            
            return instance
            
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            raise
    
    async def get_strategy(self, strategy_id: str, user_id: Optional[str] = None) -> Optional[StrategyInstance]:
        """获取策略"""
        instance = self._instances_cache.get(strategy_id)
        
        if instance and (user_id is None or instance.user_id == user_id):
            return instance
        
        return None
    
    async def get_user_strategies(self, user_id: str) -> List[StrategyInstance]:
        """获取用户策略列表"""
        return [
            instance for instance in self._instances_cache.values()
            if instance.user_id == user_id
        ]
    
    async def start_strategy(self, strategy_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """启动策略"""
        try:
            instance = await self.get_strategy(strategy_id, user_id)
            if not instance:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            if instance.status == "running":
                return {"success": True, "message": "策略已在运行"}
            
            # 启动策略
            instance.status = "running"
            instance.started_at = datetime.now()
            instance.updated_at = datetime.now()
            
            # 保存更新
            await self.save_strategy_instance(instance)
            
            logger.info(f"策略启动成功: {strategy_id}")
            
            return {
                "success": True,
                "message": "策略启动成功",
                "start_time": instance.started_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"启动策略失败: {e}")
            raise
    
    async def stop_strategy(self, strategy_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """停止策略"""
        try:
            instance = await self.get_strategy(strategy_id, user_id)
            if not instance:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            if instance.status == "stopped":
                return {"success": True, "message": "策略已停止"}
            
            # 停止策略
            instance.status = "stopped"
            instance.stopped_at = datetime.now()
            instance.updated_at = datetime.now()
            
            # 保存更新
            await self.save_strategy_instance(instance)
            
            logger.info(f"策略停止成功: {strategy_id}")
            
            return {
                "success": True,
                "message": "策略停止成功",
                "stop_time": instance.stopped_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"停止策略失败: {e}")
            raise
    
    async def get_strategy_performance(self, strategy_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取策略绩效"""
        try:
            instance = await self.get_strategy(strategy_id, user_id)
            if not instance:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            # 返回策略绩效数据
            return {
                "strategy_id": strategy_id,
                "strategy_name": instance.strategy_name,
                "status": instance.status,
                "performance": instance.performance.to_dict() if instance.performance else {},
                "created_at": instance.created_at.isoformat(),
                "started_at": instance.started_at.isoformat() if instance.started_at else None,
                "stopped_at": instance.stopped_at.isoformat() if instance.stopped_at else None
            }
            
        except Exception as e:
            logger.error(f"获取策略绩效失败: {e}")
            raise
    
    async def get_strategy_positions(self, strategy_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取策略持仓"""
        try:
            instance = await self.get_strategy(strategy_id, user_id)
            if not instance:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            # 模拟持仓数据
            positions = [
                {
                    "symbol": "rb2405",
                    "direction": "long",
                    "volume": 10,
                    "avg_price": 3500.0,
                    "current_price": 3520.0,
                    "pnl": 2000.0,
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            return positions
            
        except Exception as e:
            logger.error(f"获取策略持仓失败: {e}")
            raise
    
    # ==================== 原有方法保持不变 ====================
    
    async def save_strategy_config(self, config: StrategyConfig) -> None:
        """保存策略配置"""
        try:
            # 更新缓存
            self._configs_cache[config.strategy_name] = config
            
            # 保存到文件
            config_file = self.storage_path / "strategy_configs.json"
            configs_data = [config.to_dict() for config in self._configs_cache.values()]
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(configs_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"策略配置保存成功: {config.strategy_name}")
            
        except Exception as e:
            logger.error(f"策略配置保存失败: {e}")
            raise
    
    async def get_strategy_config(self, strategy_name: str) -> Optional[StrategyConfig]:
        """获取策略配置"""
        # 首先从缓存获取
        if strategy_name in self._configs_cache:
            return self._configs_cache[strategy_name]
        
        # 如果缓存中没有，尝试从文件加载
        await self._load_strategy_configs()
        return self._configs_cache.get(strategy_name)
    
    async def get_all_strategy_configs(self) -> List[StrategyConfig]:
        """获取所有策略配置"""
        await self._load_strategy_configs()
        return list(self._configs_cache.values())
    
    async def delete_strategy_config(self, strategy_name: str) -> bool:
        """删除策略配置"""
        try:
            if strategy_name in self._configs_cache:
                del self._configs_cache[strategy_name]
                
                # 保存到文件
                config_file = self.storage_path / "strategy_configs.json"
                configs_data = [config.to_dict() for config in self._configs_cache.values()]
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(configs_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"策略配置删除成功: {strategy_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"策略配置删除失败: {e}")
            raise
    
    async def save_strategy_instance(self, instance: StrategyInstance) -> None:
        """保存策略实例"""
        try:
            # 更新缓存
            self._instances_cache[instance.instance_id] = instance
            
            # 保存到文件
            instances_file = self.storage_path / "strategy_instances.json"
            instances_data = [instance.to_dict() for instance in self._instances_cache.values()]
            
            with open(instances_file, 'w', encoding='utf-8') as f:
                json.dump(instances_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"策略实例保存成功: {instance.instance_id}")
            
        except Exception as e:
            logger.error(f"策略实例保存失败: {e}")
            raise
    
    async def get_strategy_instance(self, instance_id: str) -> Optional[StrategyInstance]:
        """获取策略实例"""
        # 首先从缓存获取
        if instance_id in self._instances_cache:
            return self._instances_cache[instance_id]
        
        # 如果缓存中没有，尝试从文件加载
        await self._load_strategy_instances()
        return self._instances_cache.get(instance_id)
    
    async def get_all_strategy_instances(self) -> List[StrategyInstance]:
        """获取所有策略实例"""
        await self._load_strategy_instances()
        return list(self._instances_cache.values())
    
    async def delete_strategy_instance(self, instance_id: str) -> bool:
        """删除策略实例"""
        try:
            if instance_id in self._instances_cache:
                del self._instances_cache[instance_id]
                
                # 保存到文件
                instances_file = self.storage_path / "strategy_instances.json"
                instances_data = [instance.to_dict() for instance in self._instances_cache.values()]
                
                with open(instances_file, 'w', encoding='utf-8') as f:
                    json.dump(instances_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"策略实例删除成功: {instance_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"策略实例删除失败: {e}")
            raise
    
    async def _load_strategy_configs(self) -> None:
        """加载策略配置"""
        config_file = self.storage_path / "strategy_configs.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    configs_data = json.load(f)
                
                self._configs_cache.clear()
                for config_data in configs_data:
                    config = StrategyConfig.from_dict(config_data)
                    self._configs_cache[config.strategy_name] = config
                
                logger.info(f"加载了 {len(self._configs_cache)} 个策略配置")
                
            except Exception as e:
                logger.error(f"策略配置加载失败: {e}")
    
    async def _load_strategy_instances(self) -> None:
        """加载策略实例"""
        instances_file = self.storage_path / "strategy_instances.json"
        if instances_file.exists():
            try:
                with open(instances_file, 'r', encoding='utf-8') as f:
                    instances_data = json.load(f)
                
                self._instances_cache.clear()
                for instance_data in instances_data:
                    instance = StrategyInstance.from_dict(instance_data)
                    self._instances_cache[instance.instance_id] = instance
                
                logger.info(f"加载了 {len(self._instances_cache)} 个策略实例")
                
            except Exception as e:
                logger.error(f"策略实例加载失败: {e}")
