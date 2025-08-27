"""
产品类型枚举
"""

from enum import Enum
from typing import Dict


class Product(Enum):
    """产品类型枚举"""
    
    EQUITY = "EQUITY"              # 股票
    FUTURES = "FUTURES"            # 期货
    OPTION = "OPTION"              # 期权
    SPREAD = "SPREAD"              # 价差
    FOREX = "FOREX"                # 外汇
    SPOT = "SPOT"                  # 现货
    ETF = "ETF"                    # ETF基金
    BOND = "BOND"                  # 债券
    WARRANT = "WARRANT"            # 权证
    INDEX = "INDEX"                # 指数
    FUND = "FUND"                  # 基金
    CRYPTO = "CRYPTO"              # 数字货币
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["Product", str]:
        """中文名称映射"""
        return {
            cls.EQUITY: "股票",
            cls.FUTURES: "期货",
            cls.OPTION: "期权",
            cls.SPREAD: "价差",
            cls.FOREX: "外汇",
            cls.SPOT: "现货",
            cls.ETF: "ETF基金",
            cls.BOND: "债券",
            cls.WARRANT: "权证",
            cls.INDEX: "指数",
            cls.FUND: "基金",
            cls.CRYPTO: "数字货币",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "Product":
        """从字符串创建Product对象"""
        value = value.upper()
        for product in cls:
            if product.value == value:
                return product
        raise ValueError(f"Invalid product: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Product.{self.name}"
    
    @property
    def is_derivative(self) -> bool:
        """是否为衍生品"""
        return self in (Product.FUTURES, Product.OPTION, Product.WARRANT)
    
    @property
    def is_spot_market(self) -> bool:
        """是否为现货市场产品"""
        return self in (Product.EQUITY, Product.SPOT, Product.ETF, Product.BOND, Product.FUND)
    
    @property
    def supports_margin(self) -> bool:
        """是否支持保证金交易"""
        return self in (Product.FUTURES, Product.FOREX, Product.CRYPTO)
    
    @property
    def has_expiry(self) -> bool:
        """是否有到期日"""
        return self in (Product.FUTURES, Product.OPTION, Product.WARRANT)
