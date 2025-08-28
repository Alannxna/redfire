# 🔧 RedFire外部配置管理服务 - API接口
# 简单直接的REST API，舍弃复杂的DDD架构

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import asyncio
from datetime import datetime
import hashlib
import json

from ..core.config_manager import config_manager, ExternalConfigManager
from ..models.config_models import AppConfig, Environment

# =============================================================================
# API模型定义
# =============================================================================

class ConfigResponse(BaseModel):
    """配置响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    updates: Dict[str, Any] = Field(..., description="要更新的配置字段")
    dry_run: bool = Field(False, description="是否为试运行模式")

class ConfigGetRequest(BaseModel):
    """配置获取请求模型"""
    key_path: Optional[str] = Field(None, description="配置路径，如 'database.host'")
    include_sensitive: bool = Field(False, description="是否包含敏感信息")

class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="健康状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    details: Dict[str, Any] = Field(..., description="详细信息")

class ConfigInfoResponse(BaseModel):
    """配置信息响应模型"""
    config_manager_info: Dict[str, Any] = Field(..., description="配置管理器信息")
    config_summary: Dict[str, Any] = Field(..., description="配置摘要")

# =============================================================================
# 安全认证
# =============================================================================

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """验证访问令牌"""
    # 这里应该实现真正的JWT验证逻辑
    # 为了简化示例，我们只做基本检查
    token = credentials.credentials
    
    if not token or len(token) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

# =============================================================================
# FastAPI应用程序
# =============================================================================

def create_config_app() -> FastAPI:
    """创建配置服务FastAPI应用"""
    
    app = FastAPI(
        title="RedFire配置管理服务",
        description="外部微服务架构的配置管理API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # 添加中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # =========================================================================
    # 工具函数
    # =========================================================================
    
    def create_success_response(message: str, data: Any = None) -> ConfigResponse:
        """创建成功响应"""
        return ConfigResponse(
            success=True,
            message=message,
            data=data
        )
    
    def create_error_response(message: str, data: Any = None) -> ConfigResponse:
        """创建错误响应"""
        return ConfigResponse(
            success=False,
            message=message,
            data=data
        )
    
    def sanitize_config_for_response(config_dict: Dict[str, Any], include_sensitive: bool = False) -> Dict[str, Any]:
        """清理配置用于响应"""
        if include_sensitive:
            return config_dict
        
        # 递归清理敏感信息
        def _sanitize(obj: Any) -> Any:
            if isinstance(obj, dict):
                sanitized = {}
                for key, value in obj.items():
                    # 检查是否为敏感字段
                    if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                        sanitized[key] = "***HIDDEN***"
                    else:
                        sanitized[key] = _sanitize(value)
                return sanitized
            elif isinstance(obj, list):
                return [_sanitize(item) for item in obj]
            else:
                return obj
        
        return _sanitize(config_dict)
    
    # =========================================================================
    # API路由定义
    # =========================================================================
    
    @app.get("/health", response_model=HealthCheckResponse, tags=["健康检查"])
    async def health_check():
        """健康检查接口"""
        try:
            health_details = await config_manager.health_check()
            
            return HealthCheckResponse(
                status="healthy" if health_details.get("config_loaded", False) else "unhealthy",
                details=health_details
            )
        
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return HealthCheckResponse(
                status="unhealthy",
                details={"error": str(e)}
            )
    
    @app.get("/config", response_model=ConfigResponse, tags=["配置管理"])
    async def get_config(
        request: ConfigGetRequest = Depends(),
        token: str = Depends(verify_token)
    ):
        """获取配置"""
        try:
            if not config_manager.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="配置管理器未初始化"
                )
            
            # 获取配置
            if request.key_path:
                # 获取特定路径的配置
                config_value = config_manager.get_nested_config(request.key_path)
                if config_value is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"配置路径不存在: {request.key_path}"
                    )
                
                data = {
                    "key_path": request.key_path,
                    "value": config_value
                }
            else:
                # 获取完整配置
                config = config_manager.get_config()
                config_dict = config.dict()
                data = sanitize_config_for_response(config_dict, request.include_sensitive)
            
            return create_success_response("配置获取成功", data)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置失败: {str(e)}"
            )
    
    @app.put("/config", response_model=ConfigResponse, tags=["配置管理"])
    async def update_config(
        request: ConfigUpdateRequest,
        background_tasks: BackgroundTasks,
        token: str = Depends(verify_token)
    ):
        """更新配置"""
        try:
            if not config_manager.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="配置管理器未初始化"
                )
            
            # 试运行模式
            if request.dry_run:
                # 验证更新是否有效
                current_config = config_manager.get_config()
                current_dict = current_config.dict()
                
                # 模拟更新
                updated_dict = config_manager._deep_merge_dict(current_dict, request.updates)
                
                try:
                    # 尝试创建新配置对象进行验证
                    from ..models.config_models import AppConfig, validate_config
                    test_config = AppConfig(**updated_dict)
                    validation_errors = validate_config(test_config)
                    
                    if validation_errors:
                        return create_error_response(
                            "配置更新验证失败", 
                            {"validation_errors": validation_errors}
                        )
                    
                    return create_success_response(
                        "配置更新验证通过 (试运行模式)", 
                        {"preview": sanitize_config_for_response(updated_dict)}
                    )
                
                except Exception as e:
                    return create_error_response(f"配置验证失败: {str(e)}")
            
            # 实际更新配置
            success = await config_manager.update_config(request.updates)
            
            if success:
                # 后台任务：记录配置变更
                background_tasks.add_task(
                    log_config_change, 
                    request.updates, 
                    config_manager.get_config()
                )
                
                return create_success_response(
                    "配置更新成功", 
                    {"updated_keys": list(request.updates.keys())}
                )
            else:
                return create_error_response("配置更新失败")
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新配置失败: {str(e)}"
            )
    
    @app.post("/config/reload", response_model=ConfigResponse, tags=["配置管理"])
    async def reload_config(token: str = Depends(verify_token)):
        """重新加载配置"""
        try:
            if not config_manager.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="配置管理器未初始化"
                )
            
            success = await config_manager.reload_config()
            
            if success:
                return create_success_response("配置重新加载成功")
            else:
                return create_error_response("配置重新加载失败")
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"重新加载配置失败: {str(e)}"
            )
    
    @app.get("/config/info", response_model=ConfigInfoResponse, tags=["配置管理"])
    async def get_config_info(token: str = Depends(verify_token)):
        """获取配置管理器信息"""
        try:
            manager_info = config_manager.get_config_info()
            
            config_summary = {}
            if config_manager.is_initialized:
                config = config_manager.get_config()
                config_summary = {
                    "app_name": config.app_name,
                    "app_version": config.app_version,
                    "environment": config.environment,
                    "debug": config.debug,
                    "host": config.host,
                    "port": config.port
                }
            
            return ConfigInfoResponse(
                config_manager_info=manager_info,
                config_summary=config_summary
            )
        
        except Exception as e:
            logger.error(f"获取配置信息失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置信息失败: {str(e)}"
            )
    
    @app.post("/config/save", response_model=ConfigResponse, tags=["配置管理"])
    async def save_config(
        file_path: Optional[str] = None,
        format: str = "yaml",
        token: str = Depends(verify_token)
    ):
        """保存配置到文件"""
        try:
            if not config_manager.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="配置管理器未初始化"
                )
            
            if format not in ["yaml", "yml", "json"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不支持的文件格式，支持: yaml, yml, json"
                )
            
            success = await config_manager.save_config_to_file(file_path, format)
            
            if success:
                return create_success_response(
                    "配置保存成功", 
                    {"file_path": file_path, "format": format}
                )
            else:
                return create_error_response("配置保存失败")
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存配置失败: {str(e)}"
            )
    
    @app.delete("/config/cache", response_model=ConfigResponse, tags=["配置管理"])
    async def clear_config_cache(token: str = Depends(verify_token)):
        """清空配置缓存"""
        try:
            config_manager.clear_cache()
            return create_success_response("配置缓存已清空")
        
        except Exception as e:
            logger.error(f"清空配置缓存失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"清空配置缓存失败: {str(e)}"
            )
    
    # =========================================================================
    # 特定配置类型的API
    # =========================================================================
    
    @app.get("/config/database", response_model=ConfigResponse, tags=["特定配置"])
    async def get_database_config(
        include_sensitive: bool = False,
        token: str = Depends(verify_token)
    ):
        """获取数据库配置"""
        try:
            db_config = config_manager.get_database_config()
            config_dict = db_config.dict()
            
            sanitized_config = sanitize_config_for_response(config_dict, include_sensitive)
            
            return create_success_response("数据库配置获取成功", sanitized_config)
        
        except Exception as e:
            logger.error(f"获取数据库配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取数据库配置失败: {str(e)}"
            )
    
    @app.get("/config/redis", response_model=ConfigResponse, tags=["特定配置"])
    async def get_redis_config(
        include_sensitive: bool = False,
        token: str = Depends(verify_token)
    ):
        """获取Redis配置"""
        try:
            redis_config = config_manager.get_redis_config()
            config_dict = redis_config.dict()
            
            sanitized_config = sanitize_config_for_response(config_dict, include_sensitive)
            
            return create_success_response("Redis配置获取成功", sanitized_config)
        
        except Exception as e:
            logger.error(f"获取Redis配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取Redis配置失败: {str(e)}"
            )
    
    @app.get("/config/vnpy", response_model=ConfigResponse, tags=["特定配置"])
    async def get_vnpy_config(token: str = Depends(verify_token)):
        """获取VnPy配置"""
        try:
            vnpy_config = config_manager.get_vnpy_config()
            config_dict = vnpy_config.dict()
            
            return create_success_response("VnPy配置获取成功", config_dict)
        
        except Exception as e:
            logger.error(f"获取VnPy配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取VnPy配置失败: {str(e)}"
            )
    
    @app.get("/config/security", response_model=ConfigResponse, tags=["特定配置"])
    async def get_security_config(
        include_sensitive: bool = False,
        token: str = Depends(verify_token)
    ):
        """获取安全配置"""
        try:
            security_config = config_manager.get_security_config()
            config_dict = security_config.dict()
            
            sanitized_config = sanitize_config_for_response(config_dict, include_sensitive)
            
            return create_success_response("安全配置获取成功", sanitized_config)
        
        except Exception as e:
            logger.error(f"获取安全配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取安全配置失败: {str(e)}"
            )
    
    # =========================================================================
    # 事件处理
    # =========================================================================
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        logger.info("🚀 配置管理服务启动中...")
        
        # 这里可以添加配置初始化逻辑
        # 但通常配置应该在应用启动前就初始化完成
        
        logger.info("✅ 配置管理服务启动完成")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        logger.info("🛑 配置管理服务关闭中...")
        
        # 关闭配置管理器
        await config_manager.shutdown()
        
        logger.info("✅ 配置管理服务已关闭")
    
    return app

# =============================================================================
# 后台任务
# =============================================================================

async def log_config_change(updates: Dict[str, Any], new_config: AppConfig):
    """记录配置变更 (后台任务)"""
    logger = logging.getLogger(__name__)
    
    try:
        # 这里可以将配置变更记录到数据库或日志文件
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "updates": updates,
            "config_hash": hashlib.md5(new_config.json().encode()).hexdigest(),
            "environment": new_config.environment
        }
        
        logger.info(f"📝 配置变更记录: {json.dumps(change_record, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"❌ 记录配置变更失败: {e}")

# =============================================================================
# 应用创建函数
# =============================================================================

def create_app() -> FastAPI:
    """创建并配置FastAPI应用"""
    return create_config_app()

# 默认应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    # 运行应用
    uvicorn.run(
        "backend.config_service.api.config_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
