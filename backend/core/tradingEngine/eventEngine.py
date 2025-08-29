"""
事件交易引擎 (Event Trading Engine)

从 vnpy-core 的 EventEngine 迁移而来，负责处理所有交易相关的事件。
采用更清晰的命名规范和架构设计。
"""

import logging
import threading
import time
from typing import Dict, List, Callable, Any, Optional
from queue import Queue, Empty


class EventTradingEngine:
    """
    事件交易引擎类
    
    负责处理所有交易相关的事件，包括：
    - 事件注册和注销
    - 事件分发
    - 事件队列管理
    """
    
    def __init__(self):
        """初始化事件交易引擎"""
        # 状态标志
        self.isActive = False
        
        # 事件队列
        self.eventQueue = Queue()
        
        # 事件处理器字典
        self.eventHandlers: Dict[str, List[Callable]] = {}
        
        # 事件处理线程
        self.eventThread: Optional[threading.Thread] = None
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 初始化日志
        self._setup_logging()
        
        # 事件统计
        self.eventCount = 0
        self.handlerCount = 0
    
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
    
    def startEngine(self) -> bool:
        """
        启动事件引擎
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.isActive:
                self.logger.warning("事件引擎已经在运行")
                return True
            
            self.logger.info("正在启动事件引擎...")
            
            # 创建事件处理线程
            self.eventThread = threading.Thread(target=self._runEventLoop, daemon=True)
            self.eventThread.start()
            
            self.isActive = True
            self.logger.info("事件引擎启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动事件引擎失败: {e}")
            return False
    
    def stopEngine(self) -> bool:
        """
        停止事件引擎
        
        Returns:
            bool: 停止是否成功
        """
        try:
            if not self.isActive:
                self.logger.warning("事件引擎已经停止")
                return True
            
            self.logger.info("正在停止事件引擎...")
            
            # 设置停止标志
            self.isActive = False
            
            # 等待事件处理线程结束
            if self.eventThread and self.eventThread.is_alive():
                self.eventThread.join(timeout=5.0)
                if self.eventThread.is_alive():
                    self.logger.warning("事件处理线程未能在超时时间内停止")
            
            self.logger.info("事件引擎已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止事件引擎失败: {e}")
            return False
    
    def putEvent(self, event_type: str, data: Any = None) -> bool:
        """
        添加事件到队列
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            bool: 添加是否成功
        """
        try:
            if not self.isActive:
                self.logger.warning("事件引擎未启动，无法添加事件")
                return False
            
            event = {
                'type': event_type,
                'data': data,
                'timestamp': time.time()
            }
            
            self.eventQueue.put(event)
            self.eventCount += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"添加事件失败: {e}")
            return False
    
    def registerHandler(self, event_type: str, handler: Callable) -> bool:
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if event_type not in self.eventHandlers:
                self.eventHandlers[event_type] = []
            
            if handler not in self.eventHandlers[event_type]:
                self.eventHandlers[event_type].append(handler)
                self.handlerCount += 1
                self.logger.debug(f"事件处理器注册成功: {event_type} -> {handler.__name__}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"注册事件处理器失败: {e}")
            return False
    
    def unregisterHandler(self, event_type: str, handler: Callable) -> bool:
        """
        注销事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if event_type in self.eventHandlers:
                if handler in self.eventHandlers[event_type]:
                    self.eventHandlers[event_type].remove(handler)
                    self.handlerCount -= 1
                    self.logger.debug(f"事件处理器注销成功: {event_type} -> {handler.__name__}")
                    
                    # 如果没有处理器了，删除该事件类型
                    if not self.eventHandlers[event_type]:
                        del self.eventHandlers[event_type]
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"注销事件处理器失败: {e}")
            return False
    
    def _runEventLoop(self):
        """事件处理主循环"""
        self.logger.info("事件处理线程已启动")
        
        while self.isActive:
            try:
                # 从队列获取事件，设置超时以便检查停止标志
                try:
                    event = self.eventQueue.get(timeout=1.0)
                except Empty:
                    continue
                
                # 处理事件
                self._processEvent(event)
                
                # 标记任务完成
                self.eventQueue.task_done()
                
            except Exception as e:
                self.logger.error(f"事件处理异常: {e}")
                continue
        
        self.logger.info("事件处理线程已停止")
    
    def _processEvent(self, event: Dict[str, Any]):
        """
        处理单个事件
        
        Args:
            event: 事件字典
        """
        try:
            event_type = event['type']
            event_data = event['data']
            
            # 查找对应的处理器
            if event_type in self.eventHandlers:
                handlers = self.eventHandlers[event_type]
                
                # 调用所有处理器
                for handler in handlers:
                    try:
                        handler(event_data)
                    except Exception as e:
                        self.logger.error(f"事件处理器异常: {event_type} -> {handler.__name__}: {e}")
            else:
                self.logger.debug(f"未找到事件类型 {event_type} 的处理器")
                
        except Exception as e:
            self.logger.error(f"处理事件失败: {e}")
    
    def getEventCount(self) -> int:
        """
        获取已处理的事件数量
        
        Returns:
            int: 事件数量
        """
        return self.eventCount
    
    def getHandlerCount(self) -> int:
        """
        获取已注册的处理器数量
        
        Returns:
            int: 处理器数量
        """
        return self.handlerCount
    
    def getRegisteredEventTypes(self) -> List[str]:
        """
        获取已注册的事件类型列表
        
        Returns:
            List[str]: 事件类型列表
        """
        return list(self.eventHandlers.keys())
    
    def getEventQueueSize(self) -> int:
        """
        获取事件队列当前大小
        
        Returns:
            int: 队列大小
        """
        return self.eventQueue.qsize()
    
    def clearEventQueue(self) -> bool:
        """
        清空事件队列
        
        Returns:
            bool: 清空是否成功
        """
        try:
            while not self.eventQueue.empty():
                self.eventQueue.get()
                self.eventQueue.task_done()
            
            self.logger.info("事件队列已清空")
            return True
            
        except Exception as e:
            self.logger.error(f"清空事件队列失败: {e}")
            return False
    
    def getStatus(self) -> Dict[str, Any]:
        """
        获取引擎状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            'isActive': self.isActive,
            'eventCount': self.eventCount,
            'handlerCount': self.handlerCount,
            'queueSize': self.eventQueue.qsize(),
            'registeredEventTypes': self.getRegisteredEventTypes(),
            'threadAlive': self.eventThread.is_alive() if self.eventThread else False
        }
