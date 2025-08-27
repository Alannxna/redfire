"""
数据库优化器模块
提供数据索引优化、数据导出和清理功能
"""

import sqlite3
import logging
import json
import csv
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import time
import threading
from datetime import datetime, timedelta


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, db_path: str):
        """初始化数据库优化器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self.lock = threading.Lock()
        
    def connect(self):
        """连接数据库"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.logger.info(f"数据库连接成功: {self.db_path}")
            return True
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False
            
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("数据库连接已断开")
            
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        
    def analyze_table_structure(self) -> Dict[str, Any]:
        """分析表结构
        
        Returns:
            表结构分析结果
        """
        if not self.connection:
            return {}
            
        try:
            cursor = self.connection.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            analysis = {}
            for table in tables:
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                # 获取表统计信息
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # 获取索引信息
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = cursor.fetchall()
                
                analysis[table] = {
                    'columns': [{'name': col[1], 'type': col[2], 'notnull': col[3], 'pk': col[5]} for col in columns],
                    'row_count': row_count,
                    'indexes': [idx[1] for idx in indexes],
                    'estimated_size_mb': self._estimate_table_size(table, row_count, columns)
                }
                
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析表结构失败: {e}")
            return {}
            
    def _estimate_table_size(self, table: str, row_count: int, columns: List) -> float:
        """估算表大小
        
        Args:
            table: 表名
            row_count: 行数
            columns: 列信息
            
        Returns:
            估算的表大小(MB)
        """
        try:
            # 简单估算：每行平均100字节
            estimated_bytes = row_count * 100
            return round(estimated_bytes / (1024 * 1024), 2)
        except:
            return 0.0
            
    def optimize_indexes(self) -> Dict[str, List[str]]:
        """优化数据库索引
        
        Returns:
            优化结果
        """
        if not self.connection:
            return {}
            
        try:
            cursor = self.connection.cursor()
            results = {}
            
            # 分析查询性能
            tables = self._get_tables()
            
            for table in tables:
                table_results = []
                
                # 检查是否需要添加索引
                suggested_indexes = self._suggest_indexes(table)
                
                for index_info in suggested_indexes:
                    try:
                        # 创建索引
                        index_name = f"idx_{table}_{index_info['columns']}_{int(time.time())}"
                        columns_str = ', '.join(index_info['columns'])
                        
                        cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns_str})")
                        
                        table_results.append(f"创建索引: {index_name} on ({columns_str})")
                        self.logger.info(f"为表 {table} 创建索引: {index_name}")
                        
                    except Exception as e:
                        table_results.append(f"创建索引失败: {str(e)}")
                        self.logger.error(f"为表 {table} 创建索引失败: {e}")
                        
                # 分析现有索引
                cursor.execute(f"PRAGMA index_list({table})")
                existing_indexes = cursor.fetchall()
                
                for idx in existing_indexes:
                    index_name = idx[1]
                    # 检查索引使用情况
                    usage_info = self._analyze_index_usage(table, index_name)
                    if usage_info['usage_count'] == 0:
                        table_results.append(f"建议删除未使用的索引: {index_name}")
                        
                results[table] = table_results
                
            # 提交更改
            self.connection.commit()
            return results
            
        except Exception as e:
            self.logger.error(f"优化索引失败: {e}")
            return {}
            
    def _suggest_indexes(self, table: str) -> List[Dict[str, Any]]:
        """建议需要创建的索引
        
        Args:
            table: 表名
            
        Returns:
            建议的索引列表
        """
        suggestions = []
        
        try:
            cursor = self.connection.cursor()
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # 为外键列建议索引
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                # 为ID列和常用查询列建议索引
                if col_name.endswith('_id') or col_name in ['symbol', 'datetime', 'status']:
                    suggestions.append({
                        'columns': [col_name],
                        'reason': f'常用查询列: {col_name}'
                    })
                    
            # 为复合查询建议复合索引
            if any(col[1] in ['symbol', 'datetime'] for col in columns):
                suggestions.append({
                    'columns': ['symbol', 'datetime'],
                    'reason': '复合查询优化'
                })
                
        except Exception as e:
            self.logger.error(f"分析表 {table} 索引建议失败: {e}")
            
        return suggestions
        
    def _analyze_index_usage(self, table: str, index_name: str) -> Dict[str, Any]:
        """分析索引使用情况
        
        Args:
            table: 表名
            index_name: 索引名
            
        Returns:
            索引使用情况
        """
        try:
            cursor = self.connection.cursor()
            
            # 这里应该查询SQLite的系统表来获取索引使用统计
            # 由于SQLite的限制，我们使用简单的启发式方法
            
            return {
                'index_name': index_name,
                'usage_count': 0,  # SQLite不提供详细的索引使用统计
                'last_used': None
            }
            
        except Exception as e:
            self.logger.error(f"分析索引 {index_name} 使用情况失败: {e}")
            return {'index_name': index_name, 'usage_count': 0, 'last_used': None}
            
    def _get_tables(self) -> List[str]:
        """获取所有表名
        
        Returns:
            表名列表
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"获取表名失败: {e}")
            return []
            
    def export_data(self, table: str, export_path: str, format: str = 'csv', 
                    filters: Dict[str, Any] = None, limit: int = None) -> bool:
        """导出数据
        
        Args:
            table: 表名
            export_path: 导出文件路径
            format: 导出格式 (csv, json, excel)
            filters: 过滤条件
            limit: 限制导出行数
            
        Returns:
            是否导出成功
        """
        if not self.connection:
            return False
            
        try:
            # 构建查询SQL
            sql = f"SELECT * FROM {table}"
            params = []
            
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    if isinstance(value, (list, tuple)):
                        placeholders = ', '.join(['?' for _ in value])
                        where_clauses.append(f"{key} IN ({placeholders})")
                        params.extend(value)
                    else:
                        where_clauses.append(f"{key} = ?")
                        params.append(value)
                        
                if where_clauses:
                    sql += " WHERE " + " AND ".join(where_clauses)
                    
            if limit:
                sql += f" LIMIT {limit}"
                
            # 执行查询
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            if not rows:
                self.logger.warning(f"表 {table} 没有数据需要导出")
                return True
                
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            # 根据格式导出
            if format.lower() == 'csv':
                return self._export_to_csv(rows, column_names, export_path)
            elif format.lower() == 'json':
                return self._export_to_json(rows, column_names, export_path)
            elif format.lower() == 'excel':
                return self._export_to_excel(rows, column_names, export_path)
            else:
                self.logger.error(f"不支持的导出格式: {format}")
                return False
                
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return False
            
    def _export_to_csv(self, rows: List, column_names: List[str], export_path: str) -> bool:
        """导出为CSV格式
        
        Args:
            rows: 数据行
            column_names: 列名
            export_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)
                
                for row in rows:
                    writer.writerow(row)
                    
            self.logger.info(f"数据已导出到CSV文件: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出CSV失败: {e}")
            return False
            
    def _export_to_json(self, rows: List, column_names: List[str], export_path: str) -> bool:
        """导出为JSON格式
        
        Args:
            rows: 数据行
            column_names: 列名
            export_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            data = []
            for row in rows:
                row_dict = {}
                for i, col_name in enumerate(column_names):
                    row_dict[col_name] = row[i]
                data.append(row_dict)
                
            with open(export_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False, default=str)
                
            self.logger.info(f"数据已导出到JSON文件: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出JSON失败: {e}")
            return False
            
    def _export_to_excel(self, rows: List, column_names: List[str], export_path: str) -> bool:
        """导出为Excel格式
        
        Args:
            rows: 数据行
            column_names: 列名
            export_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            # 创建DataFrame
            df = pd.DataFrame(rows, columns=column_names)
            
            # 导出到Excel
            df.to_excel(export_path, index=False, engine='openpyxl')
            
            self.logger.info(f"数据已导出到Excel文件: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出Excel失败: {e}")
            return False
            
    def cleanup_old_data(self, table: str, date_column: str, days_to_keep: int) -> int:
        """清理旧数据
        
        Args:
            table: 表名
            date_column: 日期列名
            days_to_keep: 保留天数
            
        Returns:
            删除的行数
        """
        if not self.connection:
            return 0
            
        try:
            cursor = self.connection.cursor()
            
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')
            
            # 删除旧数据
            sql = f"DELETE FROM {table} WHERE {date_column} < ?"
            cursor.execute(sql, (cutoff_date_str,))
            
            deleted_rows = cursor.rowcount
            
            # 提交更改
            self.connection.commit()
            
            self.logger.info(f"从表 {table} 删除了 {deleted_rows} 行旧数据")
            return deleted_rows
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return 0
            
    def vacuum_database(self) -> bool:
        """压缩数据库
        
        Returns:
            是否压缩成功
        """
        if not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("VACUUM")
            
            self.logger.info("数据库压缩完成")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库压缩失败: {e}")
            return False
            
    def analyze_database_performance(self) -> Dict[str, Any]:
        """分析数据库性能
        
        Returns:
            性能分析结果
        """
        if not self.connection:
            return {}
            
        try:
            cursor = self.connection.cursor()
            
            # 获取数据库统计信息
            cursor.execute("PRAGMA stats")
            stats = cursor.fetchall()
            
            # 获取表大小信息
            tables = self._get_tables()
            table_sizes = {}
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                table_sizes[table] = row_count
                
            # 获取索引信息
            total_indexes = 0
            for table in tables:
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = cursor.fetchall()
                total_indexes += len(indexes)
                
            return {
                'database_size_mb': self._get_database_size(),
                'table_count': len(tables),
                'total_rows': sum(table_sizes.values()),
                'total_indexes': total_indexes,
                'table_sizes': table_sizes,
                'stats': dict(stats) if stats else {}
            }
            
        except Exception as e:
            self.logger.error(f"分析数据库性能失败: {e}")
            return {}
            
    def _get_database_size(self) -> float:
        """获取数据库文件大小
        
        Returns:
            数据库大小(MB)
        """
        try:
            db_file = Path(self.db_path)
            if db_file.exists():
                size_bytes = db_file.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
            return 0.0
        except:
            return 0.0
            
    def get_optimization_recommendations(self) -> List[str]:
        """获取优化建议
        
        Returns:
            优化建议列表
        """
        recommendations = []
        
        try:
            # 分析表结构
            analysis = self.analyze_table_structure()
            
            for table, info in analysis.items():
                # 检查大表
                if info['row_count'] > 100000:
                    recommendations.append(f"表 {table} 数据量较大({info['row_count']}行)，建议分区或归档")
                    
                # 检查索引数量
                if len(info['indexes']) < 2:
                    recommendations.append(f"表 {table} 索引较少，建议添加常用查询列的索引")
                    
                # 检查表大小
                if info['estimated_size_mb'] > 100:
                    recommendations.append(f"表 {table} 估计大小较大({info['estimated_size_mb']}MB)，建议优化存储")
                    
            # 检查数据库大小
            db_size = self._get_database_size()
            if db_size > 1000:  # 1GB
                recommendations.append(f"数据库总大小较大({db_size}MB)，建议定期清理和压缩")
                
        except Exception as e:
            self.logger.error(f"获取优化建议失败: {e}")
            
        return recommendations
