"""
应用启动生命周期管理

This module handles the startup lifecycle of the RedFire application,
including database initialization, cache setup, and engine initialization.
"""

import logging
import asyncio
from typing import Dict, Any

from app.config.settings import get_settings
from infrastructure.database.connection import database_manager
from infrastructure.cache.redis_client import redis_manager
from infrastructure.vnpy.engine_adapter import vnpy_engine_adapter
from services.monitoring.system_monitor import system_monitor

logger = logging.getLogger(__name__)


class StartupError(Exception):
    """Startup process error."""
    pass


async def startup_handler() -> None:
    """
    Application startup handler.
    
    This function is called when the FastAPI application starts.
    It initializes all necessary components in the correct order.
    """
    logger.info("🚀 Starting RedFire Trading Platform...")
    
    try:
        settings = get_settings()
        startup_tasks = []
        
        # Phase 1: Core Infrastructure
        logger.info("📊 Phase 1: Initializing core infrastructure...")
        startup_tasks.extend([
            init_database(),
            init_cache(),
            init_logging_system()
        ])
        
        # Execute Phase 1 tasks
        await asyncio.gather(*startup_tasks)
        startup_tasks.clear()
        
        # Phase 2: Business Services
        logger.info("🏗️ Phase 2: Initializing business services...")
        startup_tasks.extend([
            init_trading_services(),
            init_data_services(),
            init_strategy_services()
        ])
        
        # Execute Phase 2 tasks
        await asyncio.gather(*startup_tasks)
        startup_tasks.clear()
        
        # Phase 3: External Integrations
        logger.info("🔌 Phase 3: Initializing external integrations...")
        startup_tasks.extend([
            init_vnpy_engine(),
            init_gateway_connections(),
            init_monitoring_system()
        ])
        
        # Execute Phase 3 tasks
        await asyncio.gather(*startup_tasks)
        
        # Phase 4: Final Setup
        logger.info("✅ Phase 4: Finalizing setup...")
        await finalize_startup()
        
        logger.info("🎉 RedFire Trading Platform started successfully!")
        logger.info(f"📈 Environment: {settings.environment}")
        logger.info(f"🚪 API available at: http://{settings.host}:{settings.port}")
        logger.info(f"📚 Documentation: http://{settings.host}:{settings.port}/docs")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise StartupError(f"Failed to start application: {e}")


async def init_database() -> None:
    """Initialize database connections and migrations."""
    try:
        logger.info("🗄️ Initializing database...")
        
        # Initialize database manager
        await database_manager.initialize()
        
        # Run health check
        health_status = await database_manager.health_check()
        if not health_status["healthy"]:
            raise Exception(f"Database health check failed: {health_status['error']}")
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def init_cache() -> None:
    """Initialize Redis cache connections."""
    try:
        logger.info("💾 Initializing cache system...")
        
        # Initialize Redis manager
        await redis_manager.initialize()
        
        # Run health check
        health_status = await redis_manager.health_check()
        if not health_status["healthy"]:
            raise Exception(f"Cache health check failed: {health_status['error']}")
        
        logger.info("✅ Cache system initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Cache initialization failed: {e}")
        raise


async def init_logging_system() -> None:
    """Initialize logging system."""
    try:
        logger.info("📝 Initializing logging system...")
        
        settings = get_settings()
        
        # Configure file logging if specified
        if settings.logging.file_path:
            import logging.handlers
            
            file_handler = logging.handlers.RotatingFileHandler(
                settings.logging.file_path,
                maxBytes=settings.logging.max_file_size,
                backupCount=settings.logging.backup_count
            )
            file_handler.setFormatter(
                logging.Formatter(settings.logging.format)
            )
            
            # Add file handler to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
        
        logger.info("✅ Logging system initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Logging system initialization failed: {e}")
        raise


async def init_trading_services() -> None:
    """Initialize trading services."""
    try:
        logger.info("💼 Initializing trading services...")
        
        # Import and initialize trading services
        from services.trading.order_service import order_service
        from services.trading.position_service import position_service
        from services.trading.trade_service import trade_service
        
        # Initialize services
        await order_service.initialize()
        await position_service.initialize()
        await trade_service.initialize()
        
        logger.info("✅ Trading services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Trading services initialization failed: {e}")
        raise


async def init_data_services() -> None:
    """Initialize data services."""
    try:
        logger.info("📊 Initializing data services...")
        
        # Import and initialize data services
        from services.data.market_data import market_data_service
        from services.data.historical_data import historical_data_service
        
        # Initialize services
        await market_data_service.initialize()
        await historical_data_service.initialize()
        
        logger.info("✅ Data services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Data services initialization failed: {e}")
        raise


async def init_strategy_services() -> None:
    """Initialize strategy services."""
    try:
        logger.info("🧠 Initializing strategy services...")
        
        # Import and initialize strategy services
        from services.strategy.strategy_manager import strategy_manager
        from services.strategy.backtest_service import backtest_service
        
        # Initialize services
        await strategy_manager.initialize()
        await backtest_service.initialize()
        
        logger.info("✅ Strategy services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Strategy services initialization failed: {e}")
        raise


async def init_vnpy_engine() -> None:
    """Initialize VnPy trading engine."""
    try:
        logger.info("⚙️ Initializing VnPy engine...")
        
        # Initialize VnPy engine adapter
        await vnpy_engine_adapter.initialize()
        
        # Load configured gateways
        settings = get_settings()
        for gateway_name in settings.vnpy.gateways:
            await vnpy_engine_adapter.load_gateway(gateway_name)
        
        logger.info("✅ VnPy engine initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ VnPy engine initialization failed: {e}")
        raise


async def init_gateway_connections() -> None:
    """Initialize external gateway connections."""
    try:
        logger.info("🌐 Initializing gateway connections...")
        
        # Import and initialize gateway manager
        from infrastructure.gateway.api_gateway import api_gateway_manager
        
        # Initialize gateway manager
        await api_gateway_manager.initialize()
        
        logger.info("✅ Gateway connections initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Gateway connections initialization failed: {e}")
        raise


async def init_monitoring_system() -> None:
    """Initialize monitoring and health check systems."""
    try:
        logger.info("📊 Initializing monitoring system...")
        
        # Initialize system monitor
        await system_monitor.initialize()
        
        # Start monitoring tasks
        await system_monitor.start_monitoring()
        
        logger.info("✅ Monitoring system initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Monitoring system initialization failed: {e}")
        raise


async def finalize_startup() -> None:
    """Finalize startup process."""
    try:
        logger.info("🎯 Finalizing startup process...")
        
        # Run comprehensive health checks
        health_checks = {
            "database": database_manager.health_check(),
            "cache": redis_manager.health_check(),
            "vnpy": vnpy_engine_adapter.health_check(),
            "monitoring": system_monitor.health_check()
        }
        
        # Execute all health checks
        results = await asyncio.gather(*health_checks.values(), return_exceptions=True)
        
        # Check results
        for service, result in zip(health_checks.keys(), results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ {service} health check failed: {result}")
            elif not result.get("healthy", False):
                logger.warning(f"⚠️ {service} is not healthy: {result.get('error', 'Unknown error')}")
            else:
                logger.info(f"✅ {service} health check passed")
        
        # Log startup completion
        logger.info("🚀 Startup finalization completed")
        
    except Exception as e:
        logger.error(f"❌ Startup finalization failed: {e}")
        raise


# Startup status tracking
startup_status: Dict[str, Any] = {
    "started": False,
    "start_time": None,
    "phases_completed": [],
    "errors": []
}


def get_startup_status() -> Dict[str, Any]:
    """Get current startup status."""
    return startup_status.copy()


# Export key components
__all__ = [
    "startup_handler",
    "StartupError",
    "get_startup_status"
]
