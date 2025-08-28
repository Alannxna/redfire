#!/usr/bin/env python3
"""
RedFire 量化交易平台 - 统一应用入口点

This is the main entry point for the RedFire quantitative trading platform.
Integrates all services, engines, and components into a unified FastAPI application.

Version: 2.0.0
Author: RedFire Team
Last Updated: 2025-08-28
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import application components
from app.config.settings import get_settings
from app.lifecycle.startup import startup_handler
from app.lifecycle.shutdown import shutdown_handler
from app.lifecycle.health import health_router
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import error_handler

# Import API routers
from api.v1.routes.trading import router as trading_router
from api.v1.routes.strategy import router as strategy_router
from api.v1.routes.data import router as data_router
from api.v1.routes.monitoring import router as monitoring_router
from api.v1.routes.admin import router as admin_router
from api.auth.login import router as auth_router
from api.websocket.trading_ws import router as trading_ws_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="RedFire 量化交易平台",
        description="A comprehensive quantitative trading platform with VnPy integration",
        version="2.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)
    
    # Add exception handler
    app.add_exception_handler(Exception, error_handler)
    
    # Add event handlers
    app.add_event_handler("startup", startup_handler)
    app.add_event_handler("shutdown", shutdown_handler)
    
    # Add health check router
    app.include_router(health_router, prefix="/health", tags=["Health"])
    
    # Add API routers
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(trading_router, prefix="/api/v1/trading", tags=["Trading"])
    app.include_router(strategy_router, prefix="/api/v1/strategy", tags=["Strategy"])
    app.include_router(data_router, prefix="/api/v1/data", tags=["Data"])
    app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["Monitoring"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    
    # Add WebSocket routers
    app.include_router(trading_ws_router, prefix="/ws")
    
    # Add root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "RedFire 量化交易平台 API",
            "version": "2.0.0",
            "status": "active",
            "docs": "/docs" if settings.debug else "disabled"
        }
    
    # Add system info endpoint
    @app.get("/system/info")
    async def system_info():
        """Get system information."""
        return {
            "platform": "RedFire Quantitative Trading Platform",
            "version": "2.0.0",
            "environment": settings.environment,
            "debug": settings.debug,
            "features": {
                "trading": True,
                "strategy": True,
                "data": True,
                "monitoring": True,
                "vnpy_integration": True,
                "websocket": True
            }
        }
    
    logger.info(f"FastAPI application created successfully")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    return app

# Create the FastAPI application instance
app = create_application()

async def main():
    """Main application entry point."""
    try:
        settings = get_settings()
        
        logger.info("Starting RedFire Quantitative Trading Platform...")
        logger.info(f"Version: 2.0.0")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Host: {settings.host}")
        logger.info(f"Port: {settings.port}")
        
        # Configure uvicorn
        config = uvicorn.Config(
            app,
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower(),
            reload=settings.debug and settings.environment == "development",
            workers=1 if settings.debug else settings.workers
        )
        
        # Create and run server
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
