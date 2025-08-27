"""
应用初始化器
============

提供统一的应用层初始化流程，集成CQRS配置管理和依赖注入
"""

# 标准库导入
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# 核心层导入
from ..core.infrastructure.dependency_container import DependencyContainer

# 应用层内部导入
from .cqrs import CQRSConfigurationManager, initialize_cqrs
from .di import DependencyInjectionHelper, create_di_helper, DIConfiguration


logger = logging.getLogger(__name__)


@dataclass
class ApplicationInitializationOptions:
    """应用初始化选项"""
    
    # CQRS配置
    enable_cqrs_auto_discovery: bool = True
    cqrs_base_packages: List[str] = field(default_factory=lambda: ["backend.src.application"])
    
    # 依赖注入配置
    enable_dependency_validation: bool = True
    auto_register_handlers: bool = True
    
    # 模块配置
    enabled_modules: List[str] = field(default_factory=lambda: ["user", "system", "trading", "data", "monitoring"])
    module_configuration: Dict[str, Any] = field(default_factory=dict)
    
    # 性能配置
    parallel_initialization: bool = True
    initialization_timeout: int = 30
    
    # 调试配置
    debug_mode: bool = False
    log_level: str = "INFO"


class ApplicationInitializationResult:
    """应用初始化结果"""
    
    def __init__(self):
        self.success: bool = False
        self.container: Optional[DependencyContainer] = None
        self.cqrs_manager: Optional[CQRSConfigurationManager] = None
        self.di_helper: Optional[DependencyInjectionHelper] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.initialization_time: float = 0.0
        self.registered_services_count: int = 0
        self.registered_handlers_count: int = 0


class ApplicationModuleManager:
    """应用模块管理器"""
    
    def __init__(self, container: DependencyContainer, di_helper: DependencyInjectionHelper):
        self.container = container
        self.di_helper = di_helper
        self.logger = logging.getLogger(self.__class__.__name__)
        self.loaded_modules: Dict[str, Any] = {}
    
    async def load_module(self, module_name: str, configuration: Dict[str, Any] = None) -> None:
        """加载应用模块"""
        self.logger.info(f"加载应用模块: {module_name}")
        
        try:
            # 根据模块名加载对应的配置
            if module_name == "user":
                await self._load_user_module(configuration or {})
            elif module_name == "system":
                await self._load_system_module(configuration or {})
            elif module_name == "trading":
                await self._load_trading_module(configuration or {})
            elif module_name == "data":
                await self._load_data_module(configuration or {})
            elif module_name == "monitoring":
                await self._load_monitoring_module(configuration or {})
            else:
                self.logger.warning(f"未知的应用模块: {module_name}")
                return
            
            self.loaded_modules[module_name] = {
                "name": module_name,
                "configuration": configuration,
                "loaded_at": asyncio.get_event_loop().time()
            }
            
            self.logger.info(f"应用模块 {module_name} 加载完成")
            
        except Exception as e:
            self.logger.error(f"加载应用模块 {module_name} 失败: {e}")
            raise
    
    async def _load_user_module(self, config: Dict[str, Any]) -> None:
        """加载用户模块"""
        self.logger.info("加载用户模块...")
        
        # 创建用户模块的依赖配置文件
        profile = self.di_helper.create_profile("user_module")
        
        # 注册用户相关服务
        from .services.user_application_service import UserApplicationService
        profile.add_scoped(UserApplicationService)
        
        # 应用配置
        await self.di_helper.apply_profile("user_module")
        
        self.logger.info("用户模块加载完成")
    
    async def _load_system_module(self, config: Dict[str, Any]) -> None:
        """加载系统模块"""
        self.logger.info("加载系统模块...")
        
        # 创建系统模块的依赖配置文件
        profile = self.di_helper.create_profile("system_module")
        
        # 注册系统相关服务
        
        # 图表应用服务
        from .services.chart.chart_application_service import ChartApplicationService
        profile.add_scoped(ChartApplicationService)
        
        # 策略应用服务
        from .services.strategy.strategy_application_service import StrategyApplicationService
        profile.add_scoped(StrategyApplicationService)
        
        # 研究应用服务
        from .services.research.research_application_service import ResearchApplicationService
        profile.add_scoped(ResearchApplicationService)
        
        # UI应用服务
        from .services.ui.ui_application_service import UIApplicationService
        profile.add_scoped(UIApplicationService)
        
        # 仪表板应用服务
        from .services.dashboard_application_service import DashboardApplicationService
        profile.add_scoped(DashboardApplicationService)
        
        self.logger.info("系统模块服务注册完成: ChartService, StrategyService, ResearchService, UIService, DashboardService")
        
        # 应用配置
        await self.di_helper.apply_profile("system_module")
        
        self.logger.info("系统模块加载完成")
    
    async def _load_trading_module(self, config: Dict[str, Any]) -> None:
        """加载交易模块"""
        self.logger.info("加载交易模块...")
        
        # 创建交易模块的依赖配置文件
        profile = self.di_helper.create_profile("trading_module")
        
        # 注册交易相关服务
        
        # 交易领域服务
        from ..domain.trading.services.trading_domain_service import TradingDomainService, TradingDomainServiceConfig
        profile.add_singleton(TradingDomainServiceConfig)
        profile.add_scoped(TradingDomainService)
        
        # 如果有交易应用服务也可以在这里注册
        # from .services.trading.trading_application_service import TradingApplicationService
        # profile.add_scoped(TradingApplicationService)
        
        self.logger.info("交易模块服务注册完成: TradingDomainService")
        
        # 应用配置
        await self.di_helper.apply_profile("trading_module")
        
        self.logger.info("交易模块加载完成")
    
    async def _load_data_module(self, config: Dict[str, Any]) -> None:
        """加载数据模块"""
        self.logger.info("加载数据模块...")
        
        # 创建数据模块的依赖配置文件
        profile = self.di_helper.create_profile("data_module")
        
        # 注册数据仓储实现
        from ..infrastructure.data.repositories.market_data_repository_impl import MarketDataRepositoryImpl
        from ..infrastructure.data.repositories.historical_data_repository_impl import HistoricalDataRepositoryImpl
        from ..infrastructure.data.repositories.backtest_repository_impl import BacktestRepositoryImpl
        
        profile.add_singleton(MarketDataRepositoryImpl)
        profile.add_singleton(HistoricalDataRepositoryImpl)
        profile.add_singleton(BacktestRepositoryImpl)
        
        # 注册数据领域服务
        from ..domain.data.services.data_domain_service import DataDomainService, set_data_domain_service
        
        # 注册工厂函数来创建数据领域服务
        def create_data_domain_service() -> DataDomainService:
            market_repo = MarketDataRepositoryImpl()
            historical_repo = HistoricalDataRepositoryImpl()
            backtest_repo = BacktestRepositoryImpl()
            service = DataDomainService(market_repo, historical_repo, backtest_repo)
            set_data_domain_service(service)
            return service
        
        profile.add_singleton_factory(DataDomainService, create_data_domain_service)
        
        # 注册数据应用服务
        from .data.data_application_service import DataApplicationService
        profile.add_scoped(DataApplicationService)
        
        self.logger.info("数据模块服务注册完成: MarketDataRepository, HistoricalDataRepository, BacktestRepository, DataDomainService, DataApplicationService")
        
        # 应用配置
        await self.di_helper.apply_profile("data_module")
        
        self.logger.info("数据模块加载完成")
    
    async def _load_monitoring_module(self, config: Dict[str, Any]) -> None:
        """加载监控模块"""
        self.logger.info("加载监控模块...")
        
        # 创建监控模块的依赖配置文件
        profile = self.di_helper.create_profile("monitoring_module")
        
        # 注册监控仓储实现
        from ..infrastructure.monitoring.repositories import (
            InMemoryHealthCheckRepository,
            InMemorySystemMetricsRepository,
            InMemoryAlertRuleRepository,
            InMemoryServiceStatusRepository
        )
        from ..domain.monitoring.repositories import (
            IHealthCheckRepository,
            ISystemMetricsRepository,
            IAlertRuleRepository,
            IServiceStatusRepository
        )
        
        profile.add_singleton(IHealthCheckRepository, InMemoryHealthCheckRepository)
        profile.add_singleton(ISystemMetricsRepository, InMemorySystemMetricsRepository)
        profile.add_singleton(IAlertRuleRepository, InMemoryAlertRuleRepository)
        profile.add_singleton(IServiceStatusRepository, InMemoryServiceStatusRepository)
        
        # 注册监控领域服务
        from ..domain.monitoring.services import (
            MonitoringDomainService,
            MonitoringDomainServiceConfig,
            HealthCheckService,
            SystemMetricsService,
            AlertRuleService
        )
        
        # 创建监控领域服务配置
        monitoring_config = MonitoringDomainServiceConfig()
        profile.add_singleton(MonitoringDomainServiceConfig, lambda: monitoring_config)
        
        # 注册监控服务
        profile.add_singleton(MonitoringDomainService)
        profile.add_singleton(HealthCheckService)
        profile.add_singleton(SystemMetricsService)
        profile.add_singleton(AlertRuleService)
        
        # 注册监控应用服务
        from ..application.monitoring.monitoring_application_service import MonitoringApplicationService
        profile.add_scoped(MonitoringApplicationService)
        
        self.logger.info("监控模块服务注册完成: MonitoringDomainService, HealthCheckService, SystemMetricsService, AlertRuleService, MonitoringApplicationService")
        
        # 应用配置
        await self.di_helper.apply_profile("monitoring_module")
        
        self.logger.info("监控模块加载完成")
    
    def get_loaded_modules(self) -> Dict[str, Any]:
        """获取已加载的模块"""
        return self.loaded_modules.copy()


class ApplicationInitializer:
    """应用初始化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialized = False
    
    async def initialize(self, 
                        container: DependencyContainer, 
                        options: ApplicationInitializationOptions = None) -> ApplicationInitializationResult:
        """初始化应用层"""
        import time
        start_time = time.time()
        
        options = options or ApplicationInitializationOptions()
        result = ApplicationInitializationResult()
        result.container = container
        
        self.logger.info("开始初始化应用层...")
        
        try:
            # 设置日志级别
            if options.debug_mode:
                logging.getLogger("backend.src.application").setLevel(logging.DEBUG)
            
            # 1. 初始化依赖注入助手
            await self._initialize_dependency_injection(container, options, result)
            
            # 2. 初始化CQRS系统
            await self._initialize_cqrs_system(container, options, result)
            
            # 3. 加载应用模块
            await self._load_application_modules(container, options, result)
            
            # 4. 验证依赖关系
            if options.enable_dependency_validation:
                await self._validate_dependencies(result)
            
            # 5. 收集统计信息
            await self._collect_statistics(result)
            
            result.success = True
            result.initialization_time = time.time() - start_time
            
            self.logger.info(f"应用层初始化成功，耗时: {result.initialization_time:.2f}秒")
            self._initialized = True
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            result.initialization_time = time.time() - start_time
            
            self.logger.error(f"应用层初始化失败: {e}")
            raise
        
        return result
    
    async def _initialize_dependency_injection(self, 
                                             container: DependencyContainer,
                                             options: ApplicationInitializationOptions,
                                             result: ApplicationInitializationResult) -> None:
        """初始化依赖注入"""
        self.logger.info("初始化依赖注入系统...")
        
        # 创建依赖注入助手
        di_helper = create_di_helper(container)
        result.di_helper = di_helper
        
        # 配置应用层依赖注入
        DIConfiguration.configure_application_layer(di_helper)
        
        self.logger.info("依赖注入系统初始化完成")
    
    async def _initialize_cqrs_system(self, 
                                    container: DependencyContainer,
                                    options: ApplicationInitializationOptions,
                                    result: ApplicationInitializationResult) -> None:
        """初始化CQRS系统"""
        self.logger.info("初始化CQRS系统...")
        
        # 初始化CQRS配置管理器
        cqrs_manager = await initialize_cqrs(
            container,
            auto_discover=options.enable_cqrs_auto_discovery
        )
        result.cqrs_manager = cqrs_manager
        
        self.logger.info("CQRS系统初始化完成")
    
    async def _load_application_modules(self, 
                                      container: DependencyContainer,
                                      options: ApplicationInitializationOptions,
                                      result: ApplicationInitializationResult) -> None:
        """加载应用模块"""
        self.logger.info("加载应用模块...")
        
        module_manager = ApplicationModuleManager(container, result.di_helper)
        
        if options.parallel_initialization:
            # 并行加载模块
            tasks = []
            for module_name in options.enabled_modules:
                config = options.module_configuration.get(module_name, {})
                task = module_manager.load_module(module_name, config)
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 串行加载模块
            for module_name in options.enabled_modules:
                config = options.module_configuration.get(module_name, {})
                await module_manager.load_module(module_name, config)
        
        self.logger.info("应用模块加载完成")
    
    async def _validate_dependencies(self, result: ApplicationInitializationResult) -> None:
        """验证依赖关系"""
        self.logger.info("验证依赖关系...")
        
        try:
            issues = result.di_helper.validate_dependencies()
            
            if issues:
                for service, service_issues in issues.items():
                    for issue in service_issues:
                        warning = f"依赖问题 - {service}: {issue}"
                        result.warnings.append(warning)
                        self.logger.warning(warning)
            else:
                self.logger.info("依赖关系验证通过")
        
        except Exception as e:
            warning = f"依赖关系验证失败: {e}"
            result.warnings.append(warning)
            self.logger.warning(warning)
    
    async def _collect_statistics(self, result: ApplicationInitializationResult) -> None:
        """收集统计信息"""
        try:
            # 统计注册的服务数量
            registered_services = result.container.get_registered_services()
            result.registered_services_count = len(registered_services)
            
            # 统计注册的处理器数量
            if result.cqrs_manager:
                registry_info = result.cqrs_manager.get_registry_info()
                result.registered_handlers_count = (
                    len(registry_info.get("command_handlers", {})) +
                    len(registry_info.get("query_handlers", {}))
                )
            
            self.logger.info(f"注册服务数量: {result.registered_services_count}")
            self.logger.info(f"注册处理器数量: {result.registered_handlers_count}")
        
        except Exception as e:
            self.logger.warning(f"统计信息收集失败: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized


# 全局应用初始化器实例
_global_app_initializer: Optional[ApplicationInitializer] = None


def get_app_initializer() -> ApplicationInitializer:
    """获取全局应用初始化器"""
    global _global_app_initializer
    if _global_app_initializer is None:
        _global_app_initializer = ApplicationInitializer()
    return _global_app_initializer


async def initialize_application_layer(container: DependencyContainer,
                                     options: ApplicationInitializationOptions = None) -> ApplicationInitializationResult:
    """初始化应用层"""
    initializer = get_app_initializer()
    return await initializer.initialize(container, options)
