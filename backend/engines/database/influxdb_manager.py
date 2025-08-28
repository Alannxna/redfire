"""
InfluxDB时序数据库管理器
=====================

为RedFire量化交易平台提供高性能的时序数据存储和查询功能
支持交易数据、市场数据、性能指标等时序数据的高效管理
"""

import os
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from influxdb_client import InfluxDBClient, Point, QueryApi, WriteApi
    from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
    from influxdb_client.domain.write_precision import WritePrecision
    from influxdb_client import rest
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class InfluxDBConfig:
    """InfluxDB配置"""
    url: str = "http://localhost:8086"
    token: Optional[str] = None
    org: str = "redfire"
    bucket: str = "trading_data"
    
    # 连接配置
    timeout: int = 10000  # 10秒
    verify_ssl: bool = False
    ssl_ca_cert: Optional[str] = None
    
    # 写入配置
    batch_size: int = 1000
    flush_interval: int = 1000  # 毫秒
    jitter_interval: int = 0
    retry_interval: int = 5000
    max_retries: int = 3
    max_retry_delay: int = 30000
    exponential_base: int = 2
    
    # 查询配置
    query_timeout: int = 30000  # 30秒
    
    @classmethod
    def from_env(cls) -> "InfluxDBConfig":
        """从环境变量创建配置"""
        return cls(
            url=os.getenv("INFLUX_URL", "http://localhost:8086"),
            token=os.getenv("INFLUX_TOKEN"),
            org=os.getenv("INFLUX_ORG", "redfire"),
            bucket=os.getenv("INFLUX_BUCKET", "trading_data"),
            timeout=int(os.getenv("INFLUX_TIMEOUT", "10000")),
            batch_size=int(os.getenv("INFLUX_BATCH_SIZE", "1000"))
        )


@dataclass
class TimeSeriesPoint:
    """时序数据点"""
    measurement: str
    fields: Dict[str, Union[float, int, str, bool]]
    tags: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None
    
    def to_influx_point(self) -> Point:
        """转换为InfluxDB Point对象"""
        if not INFLUXDB_AVAILABLE:
            raise RuntimeError("InfluxDB客户端不可用")
        
        point = Point(self.measurement)
        
        # 添加标签
        if self.tags:
            for tag_key, tag_value in self.tags.items():
                point = point.tag(tag_key, str(tag_value))
        
        # 添加字段
        for field_key, field_value in self.fields.items():
            point = point.field(field_key, field_value)
        
        # 设置时间戳
        if self.timestamp:
            point = point.time(self.timestamp, WritePrecision.NS)
        
        return point


class InfluxDBManager:
    """InfluxDB管理器"""
    
    def __init__(self, config: InfluxDBConfig):
        if not INFLUXDB_AVAILABLE:
            raise RuntimeError("InfluxDB不可用，请安装influxdb-client包")
        
        self.config = config
        self._client: Optional[InfluxDBClient] = None
        self._write_api: Optional[WriteApi] = None
        self._query_api: Optional[QueryApi] = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # 统计信息
        self._stats = {
            "points_written": 0,
            "queries_executed": 0,
            "write_errors": 0,
            "query_errors": 0,
            "last_write_time": None,
            "last_query_time": None
        }
    
    @property
    def client(self) -> InfluxDBClient:
        """获取InfluxDB客户端"""
        if self._client is None:
            self._connect()
        return self._client
    
    @property
    def write_api(self) -> WriteApi:
        """获取写入API"""
        if self._write_api is None:
            self._write_api = self.client.write_api(write_options=self._get_write_options())
        return self._write_api
    
    @property
    def query_api(self) -> QueryApi:
        """获取查询API"""
        if self._query_api is None:
            self._query_api = self.client.query_api()
        return self._query_api
    
    def _connect(self):
        """连接到InfluxDB"""
        try:
            self._client = InfluxDBClient(
                url=self.config.url,
                token=self.config.token,
                org=self.config.org,
                timeout=self.config.timeout,
                verify_ssl=self.config.verify_ssl,
                ssl_ca_cert=self.config.ssl_ca_cert
            )
            
            # 测试连接
            self._client.ping()
            logger.info(f"InfluxDB连接成功: {self.config.url}")
            
        except Exception as e:
            logger.error(f"InfluxDB连接失败: {e}")
            raise
    
    def _get_write_options(self):
        """获取写入选项"""
        from influxdb_client.client.write_api import WriteOptions
        
        return WriteOptions(
            batch_size=self.config.batch_size,
            flush_interval=self.config.flush_interval,
            jitter_interval=self.config.jitter_interval,
            retry_interval=self.config.retry_interval,
            max_retries=self.config.max_retries,
            max_retry_delay=self.config.max_retry_delay,
            exponential_base=self.config.exponential_base
        )
    
    def write_point(self, point: TimeSeriesPoint, bucket: Optional[str] = None) -> bool:
        """写入单个数据点"""
        try:
            bucket = bucket or self.config.bucket
            influx_point = point.to_influx_point()
            
            self.write_api.write(bucket=bucket, org=self.config.org, record=influx_point)
            
            self._stats["points_written"] += 1
            self._stats["last_write_time"] = datetime.now()
            
            logger.debug(f"写入数据点成功: {point.measurement}")
            return True
            
        except Exception as e:
            logger.error(f"写入数据点失败: {e}")
            self._stats["write_errors"] += 1
            return False
    
    def write_points(self, points: List[TimeSeriesPoint], bucket: Optional[str] = None) -> bool:
        """批量写入数据点"""
        try:
            bucket = bucket or self.config.bucket
            influx_points = [point.to_influx_point() for point in points]
            
            self.write_api.write(bucket=bucket, org=self.config.org, record=influx_points)
            
            self._stats["points_written"] += len(points)
            self._stats["last_write_time"] = datetime.now()
            
            logger.debug(f"批量写入数据点成功: {len(points)} 个")
            return True
            
        except Exception as e:
            logger.error(f"批量写入数据点失败: {e}")
            self._stats["write_errors"] += 1
            return False
    
    def query(self, flux_query: str, bucket: Optional[str] = None) -> List[Dict[str, Any]]:
        """执行Flux查询"""
        try:
            bucket = bucket or self.config.bucket
            
            # 如果查询中没有指定bucket，则添加默认bucket
            if "from(bucket:" not in flux_query and "from(bucket=" not in flux_query:
                flux_query = f'from(bucket: "{bucket}") |> {flux_query}'
            
            result = self.query_api.query(query=flux_query, org=self.config.org)
            
            # 转换结果为字典列表
            records = []
            for table in result:
                for record in table.records:
                    record_dict = {
                        "measurement": record.get_measurement(),
                        "time": record.get_time(),
                        "field": record.get_field(),
                        "value": record.get_value()
                    }
                    
                    # 添加标签
                    for key, value in record.values.items():
                        if key.startswith("_") or key in ["result", "table"]:
                            continue
                        record_dict[key] = value
                    
                    records.append(record_dict)
            
            self._stats["queries_executed"] += 1
            self._stats["last_query_time"] = datetime.now()
            
            logger.debug(f"查询执行成功，返回 {len(records)} 条记录")
            return records
            
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            self._stats["query_errors"] += 1
            return []
    
    def query_range(self, measurement: str, start_time: datetime, end_time: datetime, 
                   tags: Optional[Dict[str, str]] = None, 
                   fields: Optional[List[str]] = None,
                   bucket: Optional[str] = None) -> List[Dict[str, Any]]:
        """查询时间范围内的数据"""
        bucket = bucket or self.config.bucket
        
        # 构建Flux查询
        query_parts = [
            f'from(bucket: "{bucket}")',
            f'range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)',
            f'filter(fn: (r) => r["_measurement"] == "{measurement}")'
        ]
        
        # 添加标签过滤
        if tags:
            for tag_key, tag_value in tags.items():
                query_parts.append(f'filter(fn: (r) => r["{tag_key}"] == "{tag_value}")')
        
        # 添加字段过滤
        if fields:
            field_filter = " or ".join([f'r["_field"] == "{field}"' for field in fields])
            query_parts.append(f'filter(fn: (r) => {field_filter})')
        
        flux_query = " |> ".join(query_parts)
        
        return self.query(flux_query)
    
    def delete_data(self, measurement: str, start_time: datetime, end_time: datetime,
                   predicate: Optional[str] = None, bucket: Optional[str] = None) -> bool:
        """删除指定时间范围的数据"""
        try:
            bucket = bucket or self.config.bucket
            
            # 构建删除谓词
            if predicate:
                delete_predicate = f'_measurement="{measurement}" AND {predicate}'
            else:
                delete_predicate = f'_measurement="{measurement}"'
            
            delete_api = self.client.delete_api()
            delete_api.delete(
                start=start_time,
                stop=end_time,
                predicate=delete_predicate,
                bucket=bucket,
                org=self.config.org
            )
            
            logger.info(f"删除数据成功: {measurement}, 时间范围: {start_time} - {end_time}")
            return True
            
        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            return False
    
    def get_measurements(self, bucket: Optional[str] = None) -> List[str]:
        """获取所有measurement"""
        bucket = bucket or self.config.bucket
        
        flux_query = f'''
        import "influxdata/influxdb/schema"
        schema.measurements(bucket: "{bucket}")
        '''
        
        try:
            result = self.query_api.query(query=flux_query, org=self.config.org)
            measurements = []
            
            for table in result:
                for record in table.records:
                    measurements.append(record.get_value())
            
            return measurements
            
        except Exception as e:
            logger.error(f"获取measurements失败: {e}")
            return []
    
    def get_tag_keys(self, measurement: str, bucket: Optional[str] = None) -> List[str]:
        """获取measurement的所有tag keys"""
        bucket = bucket or self.config.bucket
        
        flux_query = f'''
        import "influxdata/influxdb/schema"
        schema.tagKeys(
            bucket: "{bucket}",
            predicate: (r) => r["_measurement"] == "{measurement}"
        )
        '''
        
        try:
            result = self.query_api.query(query=flux_query, org=self.config.org)
            tag_keys = []
            
            for table in result:
                for record in table.records:
                    tag_keys.append(record.get_value())
            
            return tag_keys
            
        except Exception as e:
            logger.error(f"获取tag keys失败: {e}")
            return []
    
    def get_field_keys(self, measurement: str, bucket: Optional[str] = None) -> List[str]:
        """获取measurement的所有field keys"""
        bucket = bucket or self.config.bucket
        
        flux_query = f'''
        import "influxdata/influxdb/schema"
        schema.fieldKeys(
            bucket: "{bucket}",
            predicate: (r) => r["_measurement"] == "{measurement}"
        )
        '''
        
        try:
            result = self.query_api.query(query=flux_query, org=self.config.org)
            field_keys = []
            
            for table in result:
                for record in table.records:
                    field_keys.append(record.get_value())
            
            return field_keys
            
        except Exception as e:
            logger.error(f"获取field keys失败: {e}")
            return []
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            self.client.ping()
            logger.info("InfluxDB连接测试成功")
            return True
        except Exception as e:
            logger.error(f"InfluxDB连接测试失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        for key in self._stats:
            if key.endswith("_time"):
                self._stats[key] = None
            else:
                self._stats[key] = 0
    
    def close(self):
        """关闭连接"""
        try:
            if self._write_api:
                self._write_api.close()
            if self._client:
                self._client.close()
            if self._executor:
                self._executor.shutdown(wait=True)
            
            logger.info("InfluxDB连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭InfluxDB连接失败: {e}")


class TradingDataManager:
    """交易数据管理器"""
    
    def __init__(self, influx_manager: InfluxDBManager):
        self.influx = influx_manager
    
    def write_kline_data(self, symbol: str, timeframe: str, 
                        timestamp: datetime, open_price: float, high_price: float,
                        low_price: float, close_price: float, volume: float) -> bool:
        """写入K线数据"""
        point = TimeSeriesPoint(
            measurement="kline",
            tags={
                "symbol": symbol,
                "timeframe": timeframe
            },
            fields={
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume
            },
            timestamp=timestamp
        )
        
        return self.influx.write_point(point)
    
    def write_tick_data(self, symbol: str, timestamp: datetime, 
                       last_price: float, volume: float, bid_price: float, 
                       ask_price: float, bid_volume: float, ask_volume: float) -> bool:
        """写入Tick数据"""
        point = TimeSeriesPoint(
            measurement="tick",
            tags={
                "symbol": symbol
            },
            fields={
                "last_price": last_price,
                "volume": volume,
                "bid_price": bid_price,
                "ask_price": ask_price,
                "bid_volume": bid_volume,
                "ask_volume": ask_volume
            },
            timestamp=timestamp
        )
        
        return self.influx.write_point(point)
    
    def write_order_data(self, order_id: str, symbol: str, side: str, 
                        order_type: str, quantity: float, price: float, 
                        status: str, timestamp: datetime) -> bool:
        """写入订单数据"""
        point = TimeSeriesPoint(
            measurement="order",
            tags={
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "status": status
            },
            fields={
                "quantity": quantity,
                "price": price
            },
            timestamp=timestamp
        )
        
        return self.influx.write_point(point)
    
    def write_trade_data(self, trade_id: str, order_id: str, symbol: str, 
                        side: str, quantity: float, price: float, 
                        commission: float, timestamp: datetime) -> bool:
        """写入成交数据"""
        point = TimeSeriesPoint(
            measurement="trade",
            tags={
                "trade_id": trade_id,
                "order_id": order_id,
                "symbol": symbol,
                "side": side
            },
            fields={
                "quantity": quantity,
                "price": price,
                "commission": commission,
                "amount": quantity * price
            },
            timestamp=timestamp
        )
        
        return self.influx.write_point(point)
    
    def write_portfolio_data(self, account_id: str, timestamp: datetime, 
                           total_value: float, available_cash: float, 
                           position_value: float, pnl: float) -> bool:
        """写入组合数据"""
        point = TimeSeriesPoint(
            measurement="portfolio",
            tags={
                "account_id": account_id
            },
            fields={
                "total_value": total_value,
                "available_cash": available_cash,
                "position_value": position_value,
                "pnl": pnl
            },
            timestamp=timestamp
        )
        
        return self.influx.write_point(point)
    
    def get_kline_data(self, symbol: str, timeframe: str, 
                      start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """获取K线数据"""
        return self.influx.query_range(
            measurement="kline",
            start_time=start_time,
            end_time=end_time,
            tags={"symbol": symbol, "timeframe": timeframe},
            fields=["open", "high", "low", "close", "volume"]
        )
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """获取最新价格"""
        flux_query = f'''
        from(bucket: "{self.influx.config.bucket}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "tick")
        |> filter(fn: (r) => r["symbol"] == "{symbol}")
        |> filter(fn: (r) => r["_field"] == "last_price")
        |> last()
        '''
        
        result = self.influx.query(flux_query)
        if result:
            return result[0].get("value")
        return None


# 全局InfluxDB管理器实例
_influx_manager: Optional[InfluxDBManager] = None
_trading_data_manager: Optional[TradingDataManager] = None


def get_influx_manager() -> InfluxDBManager:
    """获取全局InfluxDB管理器"""
    global _influx_manager
    if _influx_manager is None:
        config = InfluxDBConfig.from_env()
        _influx_manager = InfluxDBManager(config)
    return _influx_manager


def get_trading_data_manager() -> TradingDataManager:
    """获取交易数据管理器"""
    global _trading_data_manager
    if _trading_data_manager is None:
        influx_manager = get_influx_manager()
        _trading_data_manager = TradingDataManager(influx_manager)
    return _trading_data_manager


def init_influx_manager(manager: InfluxDBManager):
    """初始化全局InfluxDB管理器"""
    global _influx_manager
    _influx_manager = manager
