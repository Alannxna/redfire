"""
数据管理应用 (Data Manager App)

负责管理交易数据，包括：
- 市场数据存储
- 交易记录管理
- 历史数据查询
- 数据导出功能
"""

import logging
import time
import json
import sqlite3
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from ..appBase import BaseTradingApp


class DataManagerApp(BaseTradingApp):
    """
    数据管理应用类
    
    负责管理所有交易相关的数据
    """
    
    def __init__(self, main_engine=None, app_name: str = "DataManager"):
        """
        初始化数据管理应用
        
        Args:
            main_engine: 主交易引擎实例
            app_name: 应用名称
        """
        super().__init__(main_engine, app_name)
        
        # 数据配置
        self.dataConfig = {
            'dataDir': './data',
            'dbPath': './data/trading.db',
            'backupInterval': 3600,  # 备份间隔（秒）
            'maxDataAge': 30 * 24 * 3600,  # 最大数据保留时间（30天）
            'compressionEnabled': True
        }
        
        # 数据库连接
        self.dbConnection: Optional[sqlite3.Connection] = None
        
        # 数据表结构
        self.tableSchemas = {
            'market_data': '''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    source TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''',
            'trades': '''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    engine_name TEXT,
                    status TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                ''',
            'orders': '''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    price REAL,
                    quantity REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    engine_name TEXT,
                    status TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                ''',
            'positions': '''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    engine_name TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                '''
            }
        
        # 初始化数据目录和数据库
        self._init_data_storage()
    
    def _init_data_storage(self):
        """初始化数据存储"""
        try:
            # 创建数据目录
            data_dir = Path(self.dataConfig['dataDir'])
            data_dir.mkdir(exist_ok=True)
            
            # 初始化数据库
            self._init_database()
            
            self.logger.info("数据存储初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化数据存储失败: {e}")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            # 创建数据库连接
            self.dbConnection = sqlite3.connect(self.dataConfig['dbPath'])
            self.dbConnection.row_factory = sqlite3.Row
            
            # 创建表
            cursor = self.dbConnection.cursor()
            for table_name, schema in self.tableSchemas.items():
                cursor.execute(schema)
            
            # 创建索引
            self._create_indexes(cursor)
            
            # 提交更改
            self.dbConnection.commit()
            
            self.logger.info("数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
            raise
    
    def _create_indexes(self, cursor):
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time ON market_data(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_orders_symbol_time ON orders(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def startApp(self) -> bool:
        """
        启动数据管理应用
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.isActive:
                self.logger.warning("数据管理应用已经在运行")
                return True
            
            self.logger.info("正在启动数据管理应用...")
            
            # 启动数据监控
            self._start_data_monitoring()
            
            self.isActive = True
            self.logger.info("数据管理应用启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动数据管理应用失败: {e}")
            return False
    
    def stopApp(self) -> bool:
        """
        停止数据管理应用
        
        Returns:
            bool: 停止是否成功
        """
        try:
            if not self.isActive:
                self.logger.warning("数据管理应用已经停止")
                return True
            
            self.logger.info("正在停止数据管理应用...")
            
            # 停止数据监控
            self._stop_data_monitoring()
            
            self.isActive = False
            self.logger.info("数据管理应用已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止数据管理应用失败: {e}")
            return False
    
    def closeApp(self) -> bool:
        """
        关闭数据管理应用
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            if self.isActive:
                self.stopApp()
            
            # 关闭数据库连接
            if self.dbConnection:
                self.dbConnection.close()
            
            self.logger.info("数据管理应用已关闭")
            return True
            
        except Exception as e:
            self.logger.error(f"关闭数据管理应用失败: {e}")
            return False
    
    def _start_data_monitoring(self):
        """启动数据监控"""
        self.logger.info("数据监控已启动")
    
    def _stop_data_monitoring(self):
        """停止数据监控"""
        self.logger.info("数据监控已停止")
    
    def saveMarketData(self, symbol: str, data: Dict[str, Any], source: str = "unknown") -> bool:
        """
        保存市场数据
        
        Args:
            symbol: 交易品种
            data: 市场数据
            source: 数据源
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return False
            
            cursor = self.dbConnection.cursor()
            
            # 插入市场数据
            cursor.execute('''
                INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                data.get('timestamp', time.time()),
                data.get('open'),
                data.get('high'),
                data.get('low'),
                data.get('close'),
                data.get('volume'),
                source
            ))
            
            self.dbConnection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"保存市场数据失败: {e}")
            return False
    
    def saveTrade(self, trade_data: Dict[str, Any]) -> bool:
        """
        保存交易记录
        
        Args:
            trade_data: 交易数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return False
            
            cursor = self.dbConnection.cursor()
            
            # 插入交易记录
            cursor.execute('''
                INSERT INTO trades (order_id, symbol, side, price, quantity, timestamp, engine_name, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('order_id'),
                trade_data.get('symbol'),
                trade_data.get('side'),
                trade_data.get('price'),
                trade_data.get('quantity'),
                trade_data.get('timestamp', time.time()),
                trade_data.get('engine_name'),
                trade_data.get('status')
            ))
            
            self.dbConnection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"保存交易记录失败: {e}")
            return False
    
    def saveOrder(self, order_data: Dict[str, Any]) -> bool:
        """
        保存订单记录
        
        Args:
            order_data: 订单数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return False
            
            cursor = self.dbConnection.cursor()
            
            # 插入或更新订单记录
            cursor.execute('''
                INSERT OR REPLACE INTO orders (order_id, symbol, side, order_type, price, quantity, timestamp, engine_name, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_data.get('order_id'),
                order_data.get('symbol'),
                order_data.get('side'),
                order_data.get('order_type'),
                order_data.get('price'),
                order_data.get('quantity'),
                order_data.get('timestamp', time.time()),
                order_data.get('engine_name'),
                order_data.get('status')
            ))
            
            self.dbConnection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"保存订单记录失败: {e}")
            return False
    
    def savePosition(self, position_data: Dict[str, Any]) -> bool:
        """
        保存仓位记录
        
        Args:
            position_data: 仓位数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return False
            
            cursor = self.dbConnection.cursor()
            
            # 插入仓位记录
            cursor.execute('''
                INSERT INTO positions (symbol, side, quantity, avg_price, timestamp, engine_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                position_data.get('symbol'),
                position_data.get('side'),
                position_data.get('quantity'),
                position_data.get('avg_price'),
                position_data.get('timestamp', time.time()),
                position_data.get('engine_name')
            ))
            
            self.dbConnection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"保存仓位记录失败: {e}")
            return False
    
    def queryMarketData(self, symbol: str, start_time: float = None, end_time: float = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        查询市场数据
        
        Args:
            symbol: 交易品种
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 市场数据列表
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return []
            
            cursor = self.dbConnection.cursor()
            
            # 构建查询条件
            where_conditions = ["symbol = ?"]
            query_params = [symbol]
            
            if start_time:
                where_conditions.append("timestamp >= ?")
                query_params.append(start_time)
            
            if end_time:
                where_conditions.append("timestamp <= ?")
                query_params.append(end_time)
            
            where_clause = " AND ".join(where_conditions)
            
            # 执行查询
            cursor.execute(f'''
                SELECT * FROM market_data 
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            ''', query_params + [limit])
            
            # 转换为字典列表
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self.logger.error(f"查询市场数据失败: {e}")
            return []
    
    def queryTrades(self, symbol: str = None, start_time: float = None, end_time: float = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        查询交易记录
        
        Args:
            symbol: 交易品种
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 交易记录列表
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return []
            
            cursor = self.dbConnection.cursor()
            
            # 构建查询条件
            where_conditions = []
            query_params = []
            
            if symbol:
                where_conditions.append("symbol = ?")
                query_params.append(symbol)
            
            if start_time:
                where_conditions.append("timestamp >= ?")
                query_params.append(start_time)
            
            if end_time:
                where_conditions.append("timestamp <= ?")
                query_params.append(end_time)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # 执行查询
            cursor.execute(f'''
                SELECT * FROM trades 
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            ''', query_params + [limit])
            
            # 转换为字典列表
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self.logger.error(f"查询交易记录失败: {e}")
            return []
    
    def exportData(self, table_name: str, file_path: str, format: str = "csv") -> bool:
        """
        导出数据
        
        Args:
            table_name: 表名
            file_path: 导出文件路径
            format: 导出格式（csv, json）
            
        Returns:
            bool: 导出是否成功
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return False
            
            cursor = self.dbConnection.cursor()
            
            # 查询数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if format.lower() == "csv":
                return self._export_to_csv(rows, file_path)
            elif format.lower() == "json":
                return self._export_to_json(rows, file_path)
            else:
                self.logger.error(f"不支持的导出格式: {format}")
                return False
                
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return False
    
    def _export_to_csv(self, rows, file_path: str) -> bool:
        """导出为CSV格式"""
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                if rows:
                    fieldnames = rows[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            
            self.logger.info(f"数据已导出到CSV文件: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出CSV失败: {e}")
            return False
    
    def _export_to_json(self, rows, file_path: str) -> bool:
        """导出为JSON格式"""
        try:
            data = [dict(row) for row in rows]
            
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            
            self.logger.info(f"数据已导出到JSON文件: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出JSON失败: {e}")
            return False
    
    def getDataStats(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            if not self.dbConnection:
                return {}
            
            cursor = self.dbConnection.cursor()
            stats = {}
            
            # 统计各表记录数
            for table_name in self.tableSchemas.keys():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats[f"{table_name}_count"] = count
            
            # 统计数据大小
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats['database_size_mb'] = (page_count * page_size) / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取数据统计失败: {e}")
            return {}
    
    def cleanupOldData(self, days: int = 30) -> bool:
        """
        清理旧数据
        
        Args:
            days: 保留天数
            
        Returns:
            bool: 清理是否成功
        """
        try:
            if not self.dbConnection:
                self.logger.error("数据库连接未建立")
                return False
            
            cutoff_time = time.time() - (days * 24 * 3600)
            cursor = self.dbConnection.cursor()
            
            # 清理各表旧数据
            tables = ['market_data', 'trades', 'orders', 'positions']
            total_deleted = 0
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff_time,))
                deleted_count = cursor.rowcount
                total_deleted += deleted_count
                self.logger.info(f"表 {table} 删除了 {deleted_count} 条旧记录")
            
            self.dbConnection.commit()
            self.logger.info(f"总共清理了 {total_deleted} 条旧记录")
            return True
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return False
    
    def getStatus(self) -> Dict[str, Any]:
        """
        获取应用状态
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            'appName': self.appName,
            'isActive': self.isActive,
            'dataConfig': self.dataConfig.copy(),
            'databaseConnected': self.dbConnection is not None,
            'dataStats': self.getDataStats()
        }
