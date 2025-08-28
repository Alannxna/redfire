# 🔧 RedFire外部配置管理服务 - 配置管理器
# 简单直接的配置管理，舍弃复杂的DDD架构

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime
import weakref
import hashlib

import aiofiles
import yaml
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydantic import ValidationError

from ..models.config_models import (
    AppConfig, 
    create_config_from_file, 
    create_config_from_env,
    create_config_from_dict,
    validate_config
)

# =============================================================================
# 配置变更监听器
# =============================================================================

class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, config_manager: 'ExternalConfigManager'):
        super().__init__()
        self.config_manager = weakref.ref(config_manager)
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        """文件修改时触发"""
        if event.is_directory:
            return
        
        config_manager = self.config_manager()
        if config_manager and event.src_path in config_manager.watched_files:
            self.logger.info(f"配置文件已修改: {event.src_path}")
            asyncio.create_task(config_manager._reload_config_async(event.src_path))

# =============================================================================
# 配置管理器
# =============================================================================

class ExternalConfigManager:
    """
    配置管理器 - 外部微服务架构的核心配置管理组件
    
    特性:
    - 多源配置加载 (文件、环境变量、字典)
    - 热重载支持
    - 配置验证
    - 变更通知
    - 缓存机制
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config: Optional[AppConfig] = None
        self.config_file: Optional[Path] = None
        self.config_hash: Optional[str] = None
        
        # 配置源优先级
        self.config_sources: List[str] = []
        
        # 文件监听
        self.file_observer: Optional[Observer] = None
        self.watched_files: Set[str] = set()
        
        # 变更回调
        self.change_callbacks: List[Callable[[AppConfig], None]] = []
        
        # 缓存
        self.config_cache: Dict[str, Any] = {}
        self.cache_enabled: bool = True
        
        # 状态
        self.is_initialized: bool = False
        self.last_reload_time: Optional[datetime] = None
    
    # =========================================================================
    # 核心配置加载方法
    # =========================================================================
    
    async def initialize(
        self, 
        config_file: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        enable_file_watching: bool = True,
        enable_cache: bool = True
    ) -> AppConfig:
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
            config_dict: 配置字典 (优先级最高)
            enable_file_watching: 是否启用文件监听
            enable_cache: 是否启用缓存
        
        Returns:
            加载的配置对象
        """
        self.logger.info("🚀 初始化配置管理器...")
        
        self.cache_enabled = enable_cache
        
        try:
            # 1. 加载配置
            self.config = await self._load_config(config_file, config_dict)
            
            # 2. 验证配置
            await self._validate_config()
            
            # 3. 设置文件监听
            if enable_file_watching and config_file:
                await self._setup_file_watching(config_file)
            
            # 4. 计算配置哈希
            self._update_config_hash()
            
            self.is_initialized = True
            self.last_reload_time = datetime.now()
            
            self.logger.info("✅ 配置管理器初始化完成")
            self.logger.info(f"📊 配置环境: {self.config.environment}")
            self.logger.info(f"🗂️  配置源: {', '.join(self.config_sources)}")
            
            return self.config
            
        except Exception as e:
            self.logger.error(f"❌ 配置管理器初始化失败: {e}")
            raise
    
    async def _load_config(
        self, 
        config_file: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None
    ) -> AppConfig:
        """加载配置"""
        
        # 配置源优先级: 字典 > 文件 > 环境变量
        
        config = None
        
        # 1. 从字典加载 (最高优先级)
        if config_dict:
            self.logger.info("📋 从配置字典加载配置")
            config = create_config_from_dict(config_dict)
            self.config_sources.append("dict")
        
        # 2. 从文件加载
        elif config_file:
            config_path = Path(config_file)
            if config_path.exists():
                self.logger.info(f"📄 从配置文件加载配置: {config_path}")
                config = create_config_from_file(config_path)
                self.config_file = config_path
                self.config_sources.append(f"file:{config_path}")
            else:
                self.logger.warning(f"⚠️ 配置文件不存在: {config_path}")
        
        # 3. 从环境变量加载 (兜底)
        if config is None:
            self.logger.info("🌍 从环境变量加载配置")
            config = create_config_from_env()
            self.config_sources.append("env")
        
        return config
    
    async def _validate_config(self) -> None:
        """验证配置"""
        if not self.config:
            raise ValueError("配置未加载")
        
        self.logger.info("🔍 验证配置...")
        
        # 使用Pydantic内置验证
        try:
            # 重新创建配置对象以触发所有验证器
            config_dict = self.config.model_dump()
            validated_config = AppConfig(**config_dict)
            self.config = validated_config
        except ValidationError as e:
            self.logger.error(f"❌ Pydantic配置验证失败: {e}")
            raise
        
        # 自定义业务验证
        validation_errors = validate_config(self.config)
        if validation_errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"- {error}" for error in validation_errors)
            self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        self.logger.info("✅ 配置验证通过")
    
    async def _setup_file_watching(self, config_file: str) -> None:
        """设置文件监听"""
        try:
            config_path = Path(config_file).resolve()
            watch_dir = config_path.parent
            
            self.logger.info(f"👀 启用配置文件监听: {config_path}")
            
            # 创建文件观察者
            self.file_observer = Observer()
            event_handler = ConfigChangeHandler(self)
            
            self.file_observer.schedule(event_handler, str(watch_dir), recursive=False)
            self.file_observer.start()
            
            # 记录监听的文件
            self.watched_files.add(str(config_path))
            
            self.logger.info("✅ 文件监听启用成功")
            
        except Exception as e:
            self.logger.error(f"❌ 文件监听启用失败: {e}")
            # 不抛出异常，文件监听失败不应该影响配置加载
    
    def _update_config_hash(self) -> None:
        """更新配置哈希值"""
        if self.config:
            config_str = self.config.model_dump_json()
            self.config_hash = hashlib.md5(config_str.encode()).hexdigest()
    
    # =========================================================================
    # 配置获取方法
    # =========================================================================
    
    def get_config(self) -> AppConfig:
        """获取当前配置"""
        if not self.is_initialized or not self.config:
            raise RuntimeError("配置管理器未初始化，请先调用 initialize()")
        
        return self.config
    
    def get_database_config(self):
        """获取数据库配置"""
        return self.get_config().database
    
    def get_redis_config(self):
        """获取Redis配置"""
        return self.get_config().redis
    
    def get_vnpy_config(self):
        """获取VnPy配置"""
        return self.get_config().vnpy
    
    def get_security_config(self):
        """获取安全配置"""
        return self.get_config().security
    
    def get_monitoring_config(self):
        """获取监控配置"""
        return self.get_config().monitoring
    
    def get_api_gateway_config(self):
        """获取API网关配置"""
        return self.get_config().api_gateway
    
    def get_nested_config(self, key_path: str, default: Any = None) -> Any:
        """
        获取嵌套配置值
        
        Args:
            key_path: 使用点号分隔的配置路径，如 'database.host'
            default: 默认值
        
        Returns:
            配置值
        """
        if not self.config:
            return default
        
        # 缓存检查
        cache_key = f"nested:{key_path}"
        if self.cache_enabled and cache_key in self.config_cache:
            return self.config_cache[cache_key]
        
        try:
            current = self.config.model_dump()
            for key in key_path.split('.'):
                current = current[key]
            
            # 缓存结果
            if self.cache_enabled:
                self.config_cache[cache_key] = current
            
            return current
            
        except (KeyError, TypeError):
            return default
    
    # =========================================================================
    # 配置热重载
    # =========================================================================
    
    async def reload_config(self) -> bool:
        """
        手动重新加载配置
        
        Returns:
            是否成功重新加载
        """
        if not self.config_file:
            self.logger.warning("⚠️ 无配置文件，无法重新加载")
            return False
        
        return await self._reload_config_async(str(self.config_file))
    
    async def _reload_config_async(self, file_path: str) -> bool:
        """异步重新加载配置"""
        try:
            self.logger.info(f"🔄 重新加载配置文件: {file_path}")
            
            # 加载新配置
            new_config = create_config_from_file(file_path)
            
            # 验证新配置
            validation_errors = validate_config(new_config)
            if validation_errors:
                self.logger.error(f"❌ 新配置验证失败: {validation_errors}")
                return False
            
            # 检查配置是否真的有变化
            new_config_str = new_config.model_dump_json()
            new_hash = hashlib.md5(new_config_str.encode()).hexdigest()
            
            if new_hash == self.config_hash:
                self.logger.info("ℹ️ 配置未发生变化，跳过重新加载")
                return True
            
            # 保存旧配置用于回滚
            old_config = self.config
            
            # 应用新配置
            self.config = new_config
            self.config_hash = new_hash
            self.last_reload_time = datetime.now()
            
            # 清空缓存
            if self.cache_enabled:
                self.config_cache.clear()
            
            # 通知变更
            await self._notify_config_change(new_config)
            
            self.logger.info("✅ 配置重新加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置重新加载失败: {e}")
            return False
    
    async def _notify_config_change(self, new_config: AppConfig) -> None:
        """通知配置变更"""
        for callback in self.change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(new_config)
                else:
                    callback(new_config)
            except Exception as e:
                self.logger.error(f"❌ 配置变更回调执行失败: {e}")
    
    def add_change_callback(self, callback: Callable[[AppConfig], None]) -> None:
        """添加配置变更回调"""
        self.change_callbacks.append(callback)
        self.logger.info(f"➕ 添加配置变更回调: {callback.__name__}")
    
    def remove_change_callback(self, callback: Callable[[AppConfig], None]) -> None:
        """移除配置变更回调"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
            self.logger.info(f"➖ 移除配置变更回调: {callback.__name__}")
    
    # =========================================================================
    # 配置管理方法
    # =========================================================================
    
    async def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        更新配置 (仅内存中更新，不保存到文件)
        
        Args:
            updates: 要更新的配置字段
        
        Returns:
            是否更新成功
        """
        try:
            if not self.config:
                raise RuntimeError("配置未初始化")
            
            # 深度合并配置
            current_dict = self.config.model_dump()
            updated_dict = self._deep_merge_dict(current_dict, updates)
            
            # 创建新配置对象并验证
            new_config = AppConfig(**updated_dict)
            validation_errors = validate_config(new_config)
            
            if validation_errors:
                self.logger.error(f"❌ 配置更新验证失败: {validation_errors}")
                return False
            
            # 应用新配置
            old_config = self.config
            self.config = new_config
            self._update_config_hash()
            
            # 清空缓存
            if self.cache_enabled:
                self.config_cache.clear()
            
            # 通知变更
            await self._notify_config_change(new_config)
            
            self.logger.info(f"✅ 配置更新成功: {list(updates.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置更新失败: {e}")
            return False
    
    def _deep_merge_dict(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        
        return result
    
    async def save_config_to_file(self, file_path: Optional[str] = None, format: str = "yaml") -> bool:
        """
        保存配置到文件
        
        Args:
            file_path: 文件路径，默认使用当前配置文件路径
            format: 文件格式 ('yaml' 或 'json')
        
        Returns:
            是否保存成功
        """
        try:
            if not self.config:
                raise RuntimeError("配置未初始化")
            
            target_path = Path(file_path) if file_path else self.config_file
            if not target_path:
                raise ValueError("未指定保存路径")
            
            config_dict = self.config.model_dump()
            
            # 移除敏感信息 (密码等)
            safe_config = self._sanitize_config_for_export(config_dict)
            
            if format.lower() in ['yml', 'yaml']:
                async with aiofiles.open(target_path, 'w', encoding='utf-8') as f:
                    await f.write(yaml.dump(safe_config, default_flow_style=False, allow_unicode=True, indent=2))
            elif format.lower() == 'json':
                async with aiofiles.open(target_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(safe_config, indent=2, ensure_ascii=False))
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            self.logger.info(f"✅ 配置已保存到: {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置保存失败: {e}")
            return False
    
    def _sanitize_config_for_export(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """清理配置用于导出 (移除敏感信息)"""
        # TODO: 实现敏感信息清理逻辑
        # 这里应该递归遍历配置，将密码等敏感字段替换为占位符
        return config_dict
    
    # =========================================================================
    # 工具方法
    # =========================================================================
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置管理器信息"""
        return {
            "initialized": self.is_initialized,
            "config_sources": self.config_sources,
            "config_file": str(self.config_file) if self.config_file else None,
            "config_hash": self.config_hash,
            "last_reload_time": self.last_reload_time.isoformat() if self.last_reload_time else None,
            "file_watching_enabled": self.file_observer is not None,
            "watched_files": list(self.watched_files),
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.config_cache),
            "change_callbacks_count": len(self.change_callbacks)
        }
    
    def clear_cache(self) -> None:
        """清空配置缓存"""
        if self.cache_enabled:
            self.config_cache.clear()
            self.logger.info("🗑️ 配置缓存已清空")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "status": "healthy",
            "initialized": self.is_initialized,
            "config_loaded": self.config is not None,
            "file_watching": self.file_observer is not None and self.file_observer.is_alive(),
            "last_reload": self.last_reload_time.isoformat() if self.last_reload_time else None
        }
        
        # 检查配置文件是否存在
        if self.config_file:
            status["config_file_exists"] = self.config_file.exists()
        
        return status
    
    # =========================================================================
    # 清理方法
    # =========================================================================
    
    async def shutdown(self) -> None:
        """关闭配置管理器"""
        self.logger.info("🛑 关闭配置管理器...")
        
        # 停止文件监听
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join(timeout=5)
            self.file_observer = None
        
        # 清空回调
        self.change_callbacks.clear()
        
        # 清空缓存
        self.config_cache.clear()
        
        # 重置状态
        self.is_initialized = False
        
        self.logger.info("✅ 配置管理器已关闭")

# =============================================================================
# 全局配置管理器实例
# =============================================================================

# 全局配置管理器实例
config_manager = ExternalConfigManager()

# 便捷函数
async def initialize_config(
    config_file: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AppConfig:
    """初始化全局配置管理器"""
    return await config_manager.initialize(config_file, config_dict, **kwargs)

def get_config() -> AppConfig:
    """获取全局配置"""
    return config_manager.get_config()

def get_database_config():
    """获取数据库配置"""
    return config_manager.get_database_config()

def get_redis_config():
    """获取Redis配置"""
    return config_manager.get_redis_config()

def get_vnpy_config():
    """获取VnPy配置"""
    return config_manager.get_vnpy_config()

def get_security_config():
    """获取安全配置"""
    return config_manager.get_security_config()

def get_monitoring_config():
    """获取监控配置"""
    return config_manager.get_monitoring_config()

def get_api_gateway_config():
    """获取API网关配置"""
    return config_manager.get_api_gateway_config()

async def reload_config() -> bool:
    """重新加载全局配置"""
    return await config_manager.reload_config()

if __name__ == "__main__":
    # 示例用法
    import asyncio
    
    async def main():
        print("🔧 RedFire配置管理器示例")
        
        # 初始化配置
        try:
            config = await initialize_config()
            print("✅ 配置初始化成功")
            print(f"📊 环境: {config.environment}")
            print(f"🏠 主机: {config.host}:{config.port}")
            
            # 获取配置信息
            info = config_manager.get_config_info()
            print(f"ℹ️ 配置信息: {info}")
            
            # 健康检查
            health = await config_manager.health_check()
            print(f"🏥 健康状态: {health}")
            
        except Exception as e:
            print(f"❌ 配置初始化失败: {e}")
        
        finally:
            await config_manager.shutdown()
    
    asyncio.run(main())
