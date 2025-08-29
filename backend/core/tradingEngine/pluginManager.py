"""
插件管理器 (Plugin Manager)

负责管理交易引擎的插件系统，包括：
- 插件动态加载
- 插件依赖管理
- 插件热更新
- 插件生命周期管理
"""

import logging
import os
import sys
import importlib
import importlib.util
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Type
from pathlib import Path


class PluginInfo:
    """插件信息类"""
    
    def __init__(self, name: str, version: str, description: str = "", author: str = ""):
        """
        初始化插件信息
        
        Args:
            name: 插件名称
            version: 插件版本
            description: 插件描述
            author: 插件作者
        """
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.loadTime = time.time()
        self.isLoaded = False
        self.isEnabled = False
        self.errorMessage = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'loadTime': self.loadTime,
            'isLoaded': self.isLoaded,
            'isEnabled': self.isEnabled,
            'errorMessage': self.errorMessage
        }


class PluginManager:
    """
    插件管理器类
    
    负责管理所有插件的生命周期和状态
    """
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        初始化插件管理器
        
        Args:
            plugin_dirs: 插件目录列表
        """
        # 插件目录
        self.pluginDirs = plugin_dirs or []
        
        # 已加载的插件
        self.loadedPlugins: Dict[str, Any] = {}
        
        # 插件信息
        self.pluginInfo: Dict[str, PluginInfo] = {}
        
        # 插件依赖关系
        self.pluginDependencies: Dict[str, List[str]] = {}
        
        # 插件配置
        self.pluginConfigs: Dict[str, Dict[str, Any]] = {}
        
        # 插件状态监控线程
        self.monitorThread: Optional[threading.Thread] = None
        
        # 监控间隔（秒）
        self.monitorInterval = 10.0
        
        # 停止标志
        self.shouldStop = False
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 初始化日志
        self._setup_logging()
        
        # 启动监控线程
        self._start_monitor_thread()
    
    def _setup_logging(self):
        """设置日志记录"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _start_monitor_thread(self):
        """启动监控线程"""
        self.monitorThread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitorThread.start()
        self.logger.info("插件监控线程已启动")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self.shouldStop:
            try:
                self._check_plugin_health()
                time.sleep(self.monitorInterval)
            except Exception as e:
                self.logger.error(f"插件监控循环异常: {e}")
                time.sleep(self.monitorInterval)
    
    def _check_plugin_health(self):
        """检查插件健康状态"""
        for plugin_name, plugin_info in self.pluginInfo.items():
            try:
                if plugin_info.isLoaded and plugin_info.isEnabled:
                    # 检查插件是否仍然可用
                    if plugin_name in self.loadedPlugins:
                        plugin = self.loadedPlugins[plugin_name]
                        # 这里可以添加更详细的健康检查逻辑
                        pass
            except Exception as e:
                self.logger.error(f"插件 {plugin_name} 健康检查失败: {e}")
                plugin_info.errorMessage = str(e)
    
    def addPluginDir(self, plugin_dir: str) -> bool:
        """
        添加插件目录
        
        Args:
            plugin_dir: 插件目录路径
            
        Returns:
            bool: 添加是否成功
        """
        try:
            if not os.path.exists(plugin_dir):
                self.logger.error(f"插件目录不存在: {plugin_dir}")
                return False
            
            if plugin_dir not in self.pluginDirs:
                self.pluginDirs.append(plugin_dir)
                self.logger.info(f"插件目录添加成功: {plugin_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"添加插件目录失败: {e}")
            return False
    
    def removePluginDir(self, plugin_dir: str) -> bool:
        """
        移除插件目录
        
        Args:
            plugin_dir: 插件目录路径
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if plugin_dir in self.pluginDirs:
                self.pluginDirs.remove(plugin_dir)
                self.logger.info(f"插件目录移除成功: {plugin_dir}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"移除插件目录失败: {e}")
            return False
    
    def scanPlugins(self) -> List[str]:
        """
        扫描插件目录中的插件
        
        Returns:
            List[str]: 发现的插件名称列表
        """
        discovered_plugins = []
        
        for plugin_dir in self.pluginDirs:
            try:
                if os.path.exists(plugin_dir):
                    for item in os.listdir(plugin_dir):
                        item_path = os.path.join(plugin_dir, item)
                        
                        # 检查是否是目录
                        if os.path.isdir(item_path):
                            # 检查是否有 __init__.py 文件
                            init_file = os.path.join(item_path, "__init__.py")
                            if os.path.exists(init_file):
                                discovered_plugins.append(item)
                        
                        # 检查是否是 Python 文件
                        elif item.endswith('.py') and not item.startswith('__'):
                            discovered_plugins.append(item[:-3])
            
            except Exception as e:
                self.logger.error(f"扫描插件目录 {plugin_dir} 失败: {e}")
        
        self.logger.info(f"发现 {len(discovered_plugins)} 个插件")
        return discovered_plugins
    
    def loadPlugin(self, plugin_name: str, plugin_dir: Optional[str] = None) -> bool:
        """
        加载插件
        
        Args:
            plugin_name: 插件名称
            plugin_dir: 插件目录，如果为None则从已配置的目录中查找
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if plugin_name in self.loadedPlugins:
                self.logger.warning(f"插件 {plugin_name} 已经加载")
                return True
            
            # 查找插件文件
            plugin_path = self._find_plugin(plugin_name, plugin_dir)
            if not plugin_path:
                self.logger.error(f"找不到插件: {plugin_name}")
                return False
            
            # 加载插件
            plugin_module = self._load_plugin_module(plugin_name, plugin_path)
            if not plugin_module:
                return False
            
            # 创建插件信息
            plugin_info = self._create_plugin_info(plugin_name, plugin_module)
            
            # 检查依赖
            if not self._check_plugin_dependencies(plugin_name):
                self.logger.error(f"插件 {plugin_name} 的依赖未满足")
                return False
            
            # 保存插件
            self.loadedPlugins[plugin_name] = plugin_module
            self.pluginInfo[plugin_name] = plugin_info
            
            # 标记为已加载
            plugin_info.isLoaded = True
            
            self.logger.info(f"插件 {plugin_name} 加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载插件 {plugin_name} 失败: {e}")
            return False
    
    def _find_plugin(self, plugin_name: str, plugin_dir: Optional[str] = None) -> Optional[str]:
        """查找插件文件路径"""
        search_dirs = [plugin_dir] if plugin_dir else self.pluginDirs
        
        for search_dir in search_dirs:
            if not search_dir or not os.path.exists(search_dir):
                continue
            
            # 检查目录形式的插件
            plugin_path = os.path.join(search_dir, plugin_name)
            if os.path.isdir(plugin_path):
                init_file = os.path.join(plugin_path, "__init__.py")
                if os.path.exists(init_file):
                    return plugin_path
            
            # 检查文件形式的插件
            plugin_file = os.path.join(search_dir, f"{plugin_name}.py")
            if os.path.exists(plugin_file):
                return plugin_file
        
        return None
    
    def _load_plugin_module(self, plugin_name: str, plugin_path: str) -> Optional[Any]:
        """加载插件模块"""
        try:
            if os.path.isdir(plugin_path):
                # 目录形式的插件
                spec = importlib.util.spec_from_file_location(
                    plugin_name, 
                    os.path.join(plugin_path, "__init__.py")
                )
            else:
                # 文件形式的插件
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            
            if not spec:
                self.logger.error(f"无法创建插件 {plugin_name} 的模块规范")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            self.logger.error(f"加载插件模块 {plugin_name} 失败: {e}")
            return None
    
    def _create_plugin_info(self, plugin_name: str, plugin_module: Any) -> PluginInfo:
        """创建插件信息"""
        # 尝试从模块中获取插件信息
        version = getattr(plugin_module, '__version__', '1.0.0')
        description = getattr(plugin_module, '__description__', '')
        author = getattr(plugin_module, '__author__', '')
        
        return PluginInfo(plugin_name, version, description, author)
    
    def _check_plugin_dependencies(self, plugin_name: str) -> bool:
        """检查插件依赖"""
        if plugin_name not in self.pluginDependencies:
            return True
        
        dependencies = self.pluginDependencies[plugin_name]
        
        for dep in dependencies:
            if dep not in self.loadedPlugins:
                self.logger.warning(f"插件 {plugin_name} 的依赖 {dep} 未加载")
                return False
        
        return True
    
    def unloadPlugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        try:
            if plugin_name not in self.loadedPlugins:
                self.logger.warning(f"插件 {plugin_name} 未加载")
                return False
            
            # 禁用插件
            if plugin_name in self.pluginInfo:
                self.pluginInfo[plugin_name].isEnabled = False
            
            # 从已加载列表中移除
            del self.loadedPlugins[plugin_name]
            
            # 更新插件信息
            if plugin_name in self.pluginInfo:
                self.pluginInfo[plugin_name].isLoaded = False
            
            self.logger.info(f"插件 {plugin_name} 卸载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"卸载插件 {plugin_name} 失败: {e}")
            return False
    
    def enablePlugin(self, plugin_name: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 启用是否成功
        """
        try:
            if plugin_name not in self.pluginInfo:
                self.logger.error(f"插件 {plugin_name} 不存在")
                return False
            
            plugin_info = self.pluginInfo[plugin_name]
            
            if not plugin_info.isLoaded:
                self.logger.error(f"插件 {plugin_name} 未加载")
                return False
            
            if plugin_info.isEnabled:
                self.logger.warning(f"插件 {plugin_name} 已经启用")
                return True
            
            # 尝试调用插件的启用方法
            if plugin_name in self.loadedPlugins:
                plugin_module = self.loadedPlugins[plugin_name]
                if hasattr(plugin_module, 'enable'):
                    try:
                        plugin_module.enable()
                    except Exception as e:
                        self.logger.error(f"调用插件 {plugin_name} 的启用方法失败: {e}")
                        return False
            
            plugin_info.isEnabled = True
            self.logger.info(f"插件 {plugin_name} 启用成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启用插件 {plugin_name} 失败: {e}")
            return False
    
    def disablePlugin(self, plugin_name: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 禁用是否成功
        """
        try:
            if plugin_name not in self.pluginInfo:
                self.logger.error(f"插件 {plugin_name} 不存在")
                return False
            
            plugin_info = self.pluginInfo[plugin_name]
            
            if not plugin_info.isEnabled:
                self.logger.warning(f"插件 {plugin_name} 已经禁用")
                return True
            
            # 尝试调用插件的禁用方法
            if plugin_name in self.loadedPlugins:
                plugin_module = self.loadedPlugins[plugin_name]
                if hasattr(plugin_module, 'disable'):
                    try:
                        plugin_module.disable()
                    except Exception as e:
                        self.logger.error(f"调用插件 {plugin_name} 的禁用方法失败: {e}")
                        return False
            
            plugin_info.isEnabled = False
            self.logger.info(f"插件 {plugin_name} 禁用成功")
            return True
            
        except Exception as e:
            self.logger.error(f"禁用插件 {plugin_name} 失败: {e}")
            return False
    
    def reloadPlugin(self, plugin_name: str) -> bool:
        """
        重新加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 重新加载是否成功
        """
        try:
            # 先卸载
            if not self.unloadPlugin(plugin_name):
                return False
            
            # 再加载
            return self.loadPlugin(plugin_name)
            
        except Exception as e:
            self.logger.error(f"重新加载插件 {plugin_name} 失败: {e}")
            return False
    
    def getPlugin(self, plugin_name: str) -> Optional[Any]:
        """
        获取指定的插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Any]: 插件模块，如果不存在则返回None
        """
        return self.loadedPlugins.get(plugin_name)
    
    def getAllPlugins(self) -> Dict[str, Any]:
        """
        获取所有已加载的插件
        
        Returns:
            Dict[str, Any]: 所有插件的字典
        """
        return self.loadedPlugins.copy()
    
    def getPluginInfo(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginInfo]: 插件信息，如果不存在则返回None
        """
        return self.pluginInfo.get(plugin_name)
    
    def getAllPluginInfo(self) -> Dict[str, PluginInfo]:
        """
        获取所有插件信息
        
        Returns:
            Dict[str, PluginInfo]: 所有插件信息
        """
        return self.pluginInfo.copy()
    
    def getEnabledPlugins(self) -> List[str]:
        """
        获取所有启用的插件名称
        
        Returns:
            List[str]: 启用的插件名称列表
        """
        enabled_plugins = []
        
        for plugin_name, plugin_info in self.pluginInfo.items():
            if plugin_info.isEnabled:
                enabled_plugins.append(plugin_name)
        
        return enabled_plugins
    
    def getDisabledPlugins(self) -> List[str]:
        """
        获取所有禁用的插件名称
        
        Returns:
            List[str]: 禁用的插件名称列表
        """
        disabled_plugins = []
        
        for plugin_name, plugin_info in self.pluginInfo.items():
            if not plugin_info.isEnabled:
                disabled_plugins.append(plugin_name)
        
        return disabled_plugins
    
    def setPluginConfig(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        设置插件配置
        
        Args:
            plugin_name: 插件名称
            config: 配置字典
            
        Returns:
            bool: 设置是否成功
        """
        try:
            self.pluginConfigs[plugin_name] = config.copy()
            self.logger.info(f"插件 {plugin_name} 配置更新成功")
            return True
            
        except Exception as e:
            self.logger.error(f"设置插件 {plugin_name} 配置失败: {e}")
            return False
    
    def getPluginConfig(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        获取插件配置
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Dict[str, Any]]: 插件配置，如果不存在则返回None
        """
        return self.pluginConfigs.get(plugin_name)
    
    def setPluginDependency(self, plugin_name: str, dependencies: List[str]) -> bool:
        """
        设置插件依赖关系
        
        Args:
            plugin_name: 插件名称
            dependencies: 依赖的插件名称列表
            
        Returns:
            bool: 设置是否成功
        """
        try:
            self.pluginDependencies[plugin_name] = dependencies.copy()
            self.logger.info(f"插件 {plugin_name} 依赖关系设置成功: {dependencies}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置插件 {plugin_name} 依赖关系失败: {e}")
            return False
    
    def getManagerStatus(self) -> Dict[str, Any]:
        """
        获取管理器状态
        
        Returns:
            Dict[str, Any]: 管理器状态信息
        """
        return {
            'totalPlugins': len(self.pluginInfo),
            'loadedPlugins': len(self.loadedPlugins),
            'enabledPlugins': len(self.getEnabledPlugins()),
            'disabledPlugins': len(self.getDisabledPlugins()),
            'pluginDirs': self.pluginDirs,
            'monitorThreadAlive': self.monitorThread.is_alive() if self.monitorThread else False,
            'monitorInterval': self.monitorInterval,
            'loadedPluginNames': list(self.loadedPlugins.keys()),
            'enabledPluginNames': self.getEnabledPlugins(),
            'disabledPluginNames': self.getDisabledPlugins()
        }
    
    def shutdown(self):
        """关闭插件管理器"""
        self.logger.info("正在关闭插件管理器...")
        
        # 禁用所有插件
        for plugin_name in self.getEnabledPlugins():
            self.disablePlugin(plugin_name)
        
        # 卸载所有插件
        for plugin_name in list(self.loadedPlugins.keys()):
            self.unloadPlugin(plugin_name)
        
        # 设置停止标志
        self.shouldStop = True
        
        # 等待监控线程结束
        if self.monitorThread and self.monitorThread.is_alive():
            self.monitorThread.join(timeout=5.0)
        
        self.logger.info("插件管理器已关闭")
