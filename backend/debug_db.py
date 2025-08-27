#!/usr/bin/env python3
"""
调试数据库连接
"""

import os
from pathlib import Path

# 加载.env文件
def load_env_file():
    """加载.env文件"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# 加载环境变量
load_env_file()

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "vnpy")

print(f"DB_HOST: '{DB_HOST}'")
print(f"DB_PORT: '{DB_PORT}'")
print(f"DB_USER: '{DB_USER}'")
print(f"DB_PASSWORD: '{DB_PASSWORD}'")
print(f"DB_NAME: '{DB_NAME}'")

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

print(f"DATABASE_URL: '{DATABASE_URL}'")
print(f"DATABASE_URL type: {type(DATABASE_URL)}")
print(f"DATABASE_URL length: {len(DATABASE_URL)}")

# 测试SQLAlchemy URL解析
try:
    from sqlalchemy.engine import make_url
    url = make_url(DATABASE_URL)
    print(f"✅ SQLAlchemy URL解析成功: {url}")
except Exception as e:
    print(f"❌ SQLAlchemy URL解析失败: {e}")
