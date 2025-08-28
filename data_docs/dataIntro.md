# Data 模块介绍

## 🎯 概述

`data` 是 RedFire 量化交易平台的数据管理模块，负责存储和管理各种类型的交易数据、市场数据、研究数据等。该模块提供数据存储、数据访问、数据同步、数据备份等核心功能，为量化交易策略提供可靠的数据支持。

## 📁 目录结构

```
data/
├── factor-data/             # 📊 因子数据
├── research-data/           # 🔬 研究数据
├── market-data/             # 📈 市场数据
├── market_data/             # 📊 市场数据(备用)
├── databases/               # 🗄️ 数据库文件
├── logs/                    # 📝 数据日志
└── init-db.sql              # 🗃️ 数据库初始化脚本
```

## 📊 数据分类详解

### 1. **因子数据** (`factor-data/`)

**作用**: 存储量化因子数据，用于因子分析和策略开发

**数据类型**:
- **技术因子**: 移动平均、RSI、MACD等
- **基本面因子**: PE、PB、ROE等
- **情绪因子**: 成交量、换手率等
- **宏观因子**: 利率、汇率、GDP等
- **自定义因子**: 用户定义的因子

**数据格式**:
```python
# 因子数据结构
{
    "factor_name": "MA_20",
    "symbol": "000001.SZ",
    "date": "2024-01-01",
    "value": 15.23,
    "source": "calculated",
    "update_time": "2024-01-01 09:30:00"
}
```

**存储方式**:
- Parquet文件 (高效压缩)
- CSV文件 (易读易写)
- HDF5文件 (大文件支持)
- 数据库存储 (实时查询)

### 2. **研究数据** (`research-data/`)

**作用**: 存储研究分析相关的数据

**数据类型**:
- **回测结果**: 策略回测数据
- **研究报告**: 分析报告数据
- **模型数据**: 机器学习模型数据
- **实验数据**: 研究实验数据
- **基准数据**: 基准指数数据

**数据组织**:
```
research-data/
├── backtest/                # 回测结果
│   ├── strategy_001/
│   ├── strategy_002/
│   └── comparison/
├── reports/                 # 研究报告
│   ├── monthly/
│   ├── quarterly/
│   └── annual/
├── models/                  # 模型数据
│   ├── ml_models/
│   ├── deep_learning/
│   └── ensemble/
└── experiments/             # 实验数据
    ├── factor_analysis/
    ├── risk_analysis/
    └── performance_analysis/
```

### 3. **市场数据** (`market-data/`, `market_data/`)

**作用**: 存储实时和历史市场数据

**数据类型**:
- **行情数据**: 开盘价、收盘价、最高价、最低价、成交量
- **分时数据**: 分钟级、秒级行情数据
- **Tick数据**: 逐笔交易数据
- **Level2数据**: 深度行情数据
- **财务数据**: 财务报表数据
- **公告数据**: 公司公告信息

**数据格式**:
```python
# 行情数据结构
{
    "symbol": "000001.SZ",
    "date": "2024-01-01",
    "open": 15.20,
    "high": 15.50,
    "low": 15.10,
    "close": 15.35,
    "volume": 1000000,
    "amount": 15350000,
    "turnover_rate": 0.85
}

# Tick数据结构
{
    "symbol": "000001.SZ",
    "timestamp": "2024-01-01 09:30:00.123",
    "price": 15.23,
    "volume": 100,
    "direction": "buy",
    "order_id": "123456789"
}
```

### 4. **数据库文件** (`databases/`)

**作用**: 存储各种数据库文件

**数据库类型**:
- **SQLite**: 轻量级数据库
- **PostgreSQL**: 关系型数据库
- **MongoDB**: 文档型数据库
- **InfluxDB**: 时序数据库
- **Redis**: 内存数据库

**数据组织**:
```
databases/
├── sqlite/                  # SQLite数据库
│   ├── redfire.db
│   ├── vnpy.db
│   └── backup/
├── postgresql/              # PostgreSQL数据
│   ├── dumps/
│   └── migrations/
├── mongodb/                 # MongoDB数据
│   ├── collections/
│   └── indexes/
├── influxdb/                # InfluxDB数据
│   ├── measurements/
│   └── retention_policies/
└── redis/                   # Redis数据
    ├── rdb/
    └── aof/
```

### 5. **数据日志** (`logs/`)

**作用**: 记录数据操作和处理日志

**日志类型**:
- **数据同步日志**: 数据同步状态
- **数据处理日志**: 数据处理过程
- **错误日志**: 数据错误信息
- **性能日志**: 数据访问性能
- **审计日志**: 数据访问审计

**日志格式**:
```python
# 日志记录结构
{
    "timestamp": "2024-01-01 10:00:00",
    "level": "INFO",
    "module": "data_sync",
    "message": "数据同步完成",
    "details": {
        "symbol": "000001.SZ",
        "records": 1000,
        "duration": 5.2
    }
}
```

## 🔄 数据管理功能

### **1. 数据同步**

```python
class DataSynchronizer:
    def __init__(self, source_config, target_config):
        self.source = DataSource(source_config)
        self.target = DataTarget(target_config)
    
    async def sync_market_data(self, symbols, start_date, end_date):
        """同步市场数据"""
        for symbol in symbols:
            data = await self.source.get_market_data(symbol, start_date, end_date)
            await self.target.save_market_data(data)
    
    async def sync_factor_data(self, factors, symbols, date_range):
        """同步因子数据"""
        for factor in factors:
            data = await self.source.get_factor_data(factor, symbols, date_range)
            await self.target.save_factor_data(data)
```

### **2. 数据验证**

```python
class DataValidator:
    def validate_market_data(self, data):
        """验证市场数据"""
        errors = []
        
        # 检查必要字段
        required_fields = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            if field not in data.columns:
                errors.append(f"Missing required field: {field}")
        
        # 检查数据完整性
        if data['volume'].min() < 0:
            errors.append("Volume cannot be negative")
        
        # 检查价格逻辑
        if (data['high'] < data['low']).any():
            errors.append("High price cannot be lower than low price")
        
        return errors
```

### **3. 数据清洗**

```python
class DataCleaner:
    def clean_market_data(self, data):
        """清洗市场数据"""
        # 去除重复数据
        data = data.drop_duplicates()
        
        # 处理缺失值
        data = data.fillna(method='ffill')
        
        # 异常值处理
        data = self.remove_outliers(data)
        
        # 数据标准化
        data = self.normalize_data(data)
        
        return data
    
    def remove_outliers(self, data, method='iqr'):
        """去除异常值"""
        if method == 'iqr':
            Q1 = data['close'].quantile(0.25)
            Q3 = data['close'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return data[(data['close'] >= lower_bound) & (data['close'] <= upper_bound)]
```

### **4. 数据备份**

```python
class DataBackup:
    def __init__(self, backup_config):
        self.backup_path = backup_config['path']
        self.retention_days = backup_config['retention_days']
    
    async def backup_database(self, database_name):
        """备份数据库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_path}/{database_name}_{timestamp}.sql"
        
        # 执行备份
        await self.execute_backup(database_name, backup_file)
        
        # 清理旧备份
        await self.cleanup_old_backups()
    
    async def restore_database(self, database_name, backup_file):
        """恢复数据库"""
        await self.execute_restore(database_name, backup_file)
```

## 📈 数据访问接口

### **1. 市场数据访问**

```python
class MarketDataAccess:
    def __init__(self, data_source):
        self.data_source = data_source
    
    async def get_daily_data(self, symbol, start_date, end_date):
        """获取日线数据"""
        return await self.data_source.query(
            "SELECT * FROM market_data WHERE symbol = %s AND date BETWEEN %s AND %s",
            (symbol, start_date, end_date)
        )
    
    async def get_realtime_data(self, symbols):
        """获取实时数据"""
        return await self.data_source.query(
            "SELECT * FROM realtime_data WHERE symbol IN %s",
            (tuple(symbols),)
        )
    
    async def get_tick_data(self, symbol, start_time, end_time):
        """获取Tick数据"""
        return await self.data_source.query(
            "SELECT * FROM tick_data WHERE symbol = %s AND timestamp BETWEEN %s AND %s",
            (symbol, start_time, end_time)
        )
```

### **2. 因子数据访问**

```python
class FactorDataAccess:
    def __init__(self, data_source):
        self.data_source = data_source
    
    async def get_factor_data(self, factor_name, symbols, date_range):
        """获取因子数据"""
        return await self.data_source.query(
            "SELECT * FROM factor_data WHERE factor_name = %s AND symbol IN %s AND date BETWEEN %s AND %s",
            (factor_name, tuple(symbols), date_range[0], date_range[1])
        )
    
    async def calculate_factor(self, factor_name, symbols, start_date, end_date):
        """计算因子数据"""
        # 获取基础数据
        market_data = await self.get_market_data(symbols, start_date, end_date)
        
        # 计算因子
        factor_data = self.calculate_factor_value(factor_name, market_data)
        
        # 保存因子数据
        await self.save_factor_data(factor_data)
        
        return factor_data
```

### **3. 研究数据访问**

```python
class ResearchDataAccess:
    def __init__(self, data_source):
        self.data_source = data_source
    
    async def save_backtest_result(self, strategy_name, result_data):
        """保存回测结果"""
        return await self.data_source.insert(
            "backtest_results",
            {
                "strategy_name": strategy_name,
                "result_data": json.dumps(result_data),
                "created_at": datetime.now()
            }
        )
    
    async def get_backtest_results(self, strategy_name):
        """获取回测结果"""
        results = await self.data_source.query(
            "SELECT * FROM backtest_results WHERE strategy_name = %s ORDER BY created_at DESC",
            (strategy_name,)
        )
        return [json.loads(result['result_data']) for result in results]
```

## 🔧 数据工具

### **1. 数据下载工具**

```python
class DataDownloader:
    def __init__(self, api_config):
        self.api = DataAPI(api_config)
    
    async def download_market_data(self, symbols, start_date, end_date):
        """下载市场数据"""
        tasks = []
        for symbol in symbols:
            task = self.download_symbol_data(symbol, start_date, end_date)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def download_symbol_data(self, symbol, start_date, end_date):
        """下载单个股票数据"""
        data = await self.api.get_market_data(symbol, start_date, end_date)
        await self.save_data(symbol, data)
        return data
```

### **2. 数据转换工具**

```python
class DataConverter:
    def convert_to_parquet(self, csv_file, parquet_file):
        """CSV转Parquet"""
        df = pd.read_csv(csv_file)
        df.to_parquet(parquet_file, index=False)
    
    def convert_to_hdf5(self, data, hdf5_file, key):
        """数据转HDF5"""
        df = pd.DataFrame(data)
        df.to_hdf(hdf5_file, key=key, mode='w')
    
    def convert_timezone(self, data, from_tz, to_tz):
        """时区转换"""
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['timestamp'] = data['timestamp'].dt.tz_localize(from_tz).dt.tz_convert(to_tz)
        return data
```

### **3. 数据质量检查**

```python
class DataQualityChecker:
    def check_data_completeness(self, data, expected_fields):
        """检查数据完整性"""
        missing_fields = set(expected_fields) - set(data.columns)
        if missing_fields:
            return False, f"Missing fields: {missing_fields}"
        return True, "Data complete"
    
    def check_data_consistency(self, data):
        """检查数据一致性"""
        errors = []
        
        # 检查数据类型
        for column, expected_type in data.dtypes.items():
            if not pd.api.types.is_dtype_equal(data[column].dtype, expected_type):
                errors.append(f"Type mismatch for column {column}")
        
        # 检查数据范围
        if 'price' in data.columns:
            if (data['price'] <= 0).any():
                errors.append("Price must be positive")
        
        return len(errors) == 0, errors
```

## 📊 数据监控

### **1. 数据质量监控**

```python
class DataQualityMonitor:
    def __init__(self):
        self.quality_metrics = {}
    
    async def monitor_data_quality(self, data_source):
        """监控数据质量"""
        metrics = {
            "completeness": await self.check_completeness(data_source),
            "accuracy": await self.check_accuracy(data_source),
            "timeliness": await self.check_timeliness(data_source),
            "consistency": await self.check_consistency(data_source)
        }
        
        self.quality_metrics[data_source] = metrics
        return metrics
    
    async def generate_quality_report(self):
        """生成质量报告"""
        report = {
            "timestamp": datetime.now(),
            "overall_score": self.calculate_overall_score(),
            "details": self.quality_metrics
        }
        return report
```

### **2. 数据性能监控**

```python
class DataPerformanceMonitor:
    def __init__(self):
        self.performance_metrics = {}
    
    async def monitor_query_performance(self, query_name, query_func):
        """监控查询性能"""
        start_time = time.time()
        result = await query_func()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        self.performance_metrics[query_name] = {
            "execution_time": execution_time,
            "timestamp": datetime.now(),
            "result_size": len(result) if result else 0
        }
        
        return result
```

## 🚀 数据优化

### **1. 数据压缩**

```python
class DataCompressor:
    def compress_parquet(self, input_file, output_file):
        """压缩Parquet文件"""
        df = pd.read_parquet(input_file)
        df.to_parquet(output_file, compression='gzip')
    
    def compress_csv(self, input_file, output_file):
        """压缩CSV文件"""
        df = pd.read_csv(input_file)
        df.to_csv(output_file, compression='gzip', index=False)
```

### **2. 数据索引**

```python
class DataIndexer:
    def create_index(self, table_name, columns):
        """创建数据库索引"""
        for column in columns:
            index_name = f"idx_{table_name}_{column}"
            query = f"CREATE INDEX {index_name} ON {table_name} ({column})"
            await self.execute_query(query)
    
    def optimize_queries(self, query_patterns):
        """优化查询模式"""
        # 分析查询模式并创建合适的索引
        pass
```

---

**总结**: Data模块是RedFire平台的数据管理中心，提供完整的数据存储、管理、访问和监控功能。通过规范化的数据组织、完善的数据质量控制和高效的访问接口，为量化交易策略提供可靠的数据支持。
