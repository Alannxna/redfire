"""
图表模块依赖注入容器
"""

from dependency_injector import containers, providers

from src.application.services.chart.chart_application_service import ChartApplicationService
from src.infrastructure.repositories.chart_repository_impl import InMemoryChartRepository
from src.infrastructure.repositories.bar_data_repository_impl import InMemoryBarDataRepository
from src.infrastructure.repositories.indicator_repository_impl import InMemoryIndicatorRepository
from src.interfaces.rest.controllers.chart_controller import ChartController
from src.interfaces.websocket.chart_websocket import ChartWebSocketManager


class ChartContainer(containers.DeclarativeContainer):
    """图表模块依赖注入容器"""
    
    # 配置
    config = providers.Configuration()
    
    # 仓储层
    chart_repository = providers.Singleton(InMemoryChartRepository)
    bar_data_repository = providers.Singleton(InMemoryBarDataRepository)
    indicator_repository = providers.Singleton(InMemoryIndicatorRepository)
    
    # 应用服务层
    chart_application_service = providers.Factory(
        ChartApplicationService,
        chart_repository=chart_repository,
        bar_data_repository=bar_data_repository,
        indicator_repository=indicator_repository
    )
    
    # 接口层
    chart_controller = providers.Factory(
        ChartController,
        chart_service=chart_application_service
    )
    
    chart_websocket_manager = providers.Factory(
        ChartWebSocketManager,
        chart_service=chart_application_service
    )



