"""
交易所枚举
"""

from enum import Enum
from typing import Dict


class Exchange(Enum):
    """交易所枚举"""
    
    # 中国股票交易所
    SSE = "SSE"                    # 上海证券交易所
    SZSE = "SZSE"                  # 深圳证券交易所
    BSE = "BSE"                    # 北京证券交易所
    
    # 中国期货交易所
    CFFEX = "CFFEX"                # 中国金融期货交易所
    SHFE = "SHFE"                  # 上海期货交易所
    DCE = "DCE"                    # 大连商品交易所
    CZCE = "CZCE"                  # 郑州商品交易所
    INE = "INE"                    # 上海国际能源交易中心
    GFEX = "GFEX"                  # 广州期货交易所
    
    # 其他中国交易所
    SGE = "SGE"                    # 上海黄金交易所
    WXE = "WXE"                    # 无锡不锈钢交易所
    CFETS = "CFETS"                # 中国外汇交易中心
    
    # 国际交易所
    NYSE = "NYSE"                  # 纽约证券交易所
    NASDAQ = "NASDAQ"              # 纳斯达克
    CME = "CME"                    # 芝加哥商业交易所
    CBOT = "CBOT"                  # 芝加哥期货交易所
    NYMEX = "NYMEX"                # 纽约商业交易所
    COMEX = "COMEX"                # 纽约商品交易所
    ICE = "ICE"                    # 洲际交易所
    EUREX = "EUREX"                # 欧洲期货交易所
    LSE = "LSE"                    # 伦敦证券交易所
    TSE = "TSE"                    # 东京证券交易所
    HKEX = "HKEX"                  # 香港交易所
    SGX = "SGX"                    # 新加坡交易所
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["Exchange", str]:
        """中文名称映射"""
        return {
            # 中国股票交易所
            cls.SSE: "上海证券交易所",
            cls.SZSE: "深圳证券交易所", 
            cls.BSE: "北京证券交易所",
            
            # 中国期货交易所
            cls.CFFEX: "中国金融期货交易所",
            cls.SHFE: "上海期货交易所",
            cls.DCE: "大连商品交易所",
            cls.CZCE: "郑州商品交易所",
            cls.INE: "上海国际能源交易中心",
            cls.GFEX: "广州期货交易所",
            
            # 其他中国交易所
            cls.SGE: "上海黄金交易所",
            cls.WXE: "无锡不锈钢交易所",
            cls.CFETS: "中国外汇交易中心",
            
            # 国际交易所
            cls.NYSE: "纽约证券交易所",
            cls.NASDAQ: "纳斯达克",
            cls.CME: "芝加哥商业交易所",
            cls.CBOT: "芝加哥期货交易所", 
            cls.NYMEX: "纽约商业交易所",
            cls.COMEX: "纽约商品交易所",
            cls.ICE: "洲际交易所",
            cls.EUREX: "欧洲期货交易所",
            cls.LSE: "伦敦证券交易所",
            cls.TSE: "东京证券交易所",
            cls.HKEX: "香港交易所",
            cls.SGX: "新加坡交易所",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "Exchange":
        """从字符串创建Exchange对象"""
        value = value.upper()
        for exchange in cls:
            if exchange.value == value:
                return exchange
        raise ValueError(f"Invalid exchange: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Exchange.{self.name}"
    
    @property
    def is_chinese(self) -> bool:
        """是否为中国交易所"""
        chinese_exchanges = {
            Exchange.SSE, Exchange.SZSE, Exchange.BSE,
            Exchange.CFFEX, Exchange.SHFE, Exchange.DCE, 
            Exchange.CZCE, Exchange.INE, Exchange.GFEX,
            Exchange.SGE, Exchange.WXE, Exchange.CFETS
        }
        return self in chinese_exchanges
    
    @property
    def is_stock_exchange(self) -> bool:
        """是否为股票交易所"""
        stock_exchanges = {
            Exchange.SSE, Exchange.SZSE, Exchange.BSE,
            Exchange.NYSE, Exchange.NASDAQ, Exchange.LSE,
            Exchange.TSE, Exchange.HKEX
        }
        return self in stock_exchanges
    
    @property
    def is_futures_exchange(self) -> bool:
        """是否为期货交易所"""
        futures_exchanges = {
            Exchange.CFFEX, Exchange.SHFE, Exchange.DCE,
            Exchange.CZCE, Exchange.INE, Exchange.GFEX,
            Exchange.CME, Exchange.CBOT, Exchange.NYMEX,
            Exchange.COMEX, Exchange.ICE, Exchange.EUREX
        }
        return self in futures_exchanges
    
    @property
    def timezone(self) -> str:
        """获取交易所时区"""
        timezone_mapping = {
            # 中国交易所
            Exchange.SSE: "Asia/Shanghai",
            Exchange.SZSE: "Asia/Shanghai",
            Exchange.BSE: "Asia/Shanghai",
            Exchange.CFFEX: "Asia/Shanghai",
            Exchange.SHFE: "Asia/Shanghai", 
            Exchange.DCE: "Asia/Shanghai",
            Exchange.CZCE: "Asia/Shanghai",
            Exchange.INE: "Asia/Shanghai",
            Exchange.GFEX: "Asia/Shanghai",
            Exchange.SGE: "Asia/Shanghai",
            Exchange.WXE: "Asia/Shanghai",
            Exchange.CFETS: "Asia/Shanghai",
            
            # 美国交易所
            Exchange.NYSE: "America/New_York",
            Exchange.NASDAQ: "America/New_York",
            Exchange.CME: "America/Chicago",
            Exchange.CBOT: "America/Chicago",
            Exchange.NYMEX: "America/New_York",
            Exchange.COMEX: "America/New_York",
            
            # 其他国际交易所
            Exchange.ICE: "America/New_York",
            Exchange.EUREX: "Europe/Berlin",
            Exchange.LSE: "Europe/London",
            Exchange.TSE: "Asia/Tokyo",
            Exchange.HKEX: "Asia/Hong_Kong",
            Exchange.SGX: "Asia/Singapore",
        }
        return timezone_mapping.get(self, "UTC")
