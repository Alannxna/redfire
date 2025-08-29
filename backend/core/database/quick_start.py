#!/usr/bin/env python3
"""
RedFire 数据库系统快速启动
========================

一键启动和测试整个数据库系统
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_environment():
    """设置环境变量"""
    # 基于用户提供的配置设置环境变量
    os.environ.update({
        "DB_HOST": "localhost",
        "DB_PORT": "3306", 
        "DB_USER": "root",
        "DB_PASSWORD": "root",
        "DB_NAME": "vnpy",
        
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0",
        
        # 可选组件 - 如果没有安装，系统会优雅降级
        # "INFLUX_HOST": "localhost",
        # "MONGO_HOST": "localhost",
    })
    
    print("✅ 环境变量配置完成")


def test_mysql_connection():
    """测试MySQL连接"""
    try:
        from backend.core.database import get_config_manager
        
        config_manager = get_config_manager()
        if config_manager.test_mysql_connection():
            print("✅ MySQL连接测试成功")
            return True
        else:
            print("❌ MySQL连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ MySQL连接测试异常: {e}")
        return False


def test_redis_connection():
    """测试Redis连接"""
    try:
        from backend.core.database import get_config_manager
        
        config_manager = get_config_manager()
        if config_manager.test_redis_connection():
            print("✅ Redis连接测试成功")
            return True
        else:
            print("❌ Redis连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ Redis连接测试异常: {e}")
        return False


def test_unified_database_manager():
    """测试统一数据库管理器"""
    try:
        from backend.core.database import get_database_manager
        
        db_manager = get_database_manager()
        
        # 测试MySQL连接
        with db_manager.get_session("main") as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            assert test_value == 1
        
        print("✅ 统一数据库管理器测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 统一数据库管理器测试失败: {e}")
        return False


def test_cache_operations():
    """测试缓存操作"""
    try:
        from backend.core.database import get_cache_manager
        
        cache = get_cache_manager("user_data")
        
        # 测试缓存设置和获取
        test_data = {"name": "测试用户", "timestamp": datetime.now().isoformat()}
        cache.set("test", "user_123", test_data)
        
        cached_data = cache.get("test", "user_123")
        assert cached_data is not None
        assert cached_data["name"] == "测试用户"
        
        # 测试缓存删除
        cache.delete("test", "user_123")
        
        print("✅ 缓存操作测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 缓存操作测试失败: {e}")
        return False


def test_read_write_split():
    """测试读写分离"""
    try:
        from backend.core.database import get_read_session, get_write_session
        from sqlalchemy import text
        
        # 测试读操作
        with get_read_session() as session:
            result = session.execute(text("SELECT 'read_test' as test"))
            test_value = result.scalar()
            assert test_value == "read_test"
        
        # 测试写操作
        with get_write_session() as session:
            session.execute(text("SELECT 'write_test' as test"))
        
        print("✅ 读写分离测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 读写分离测试失败: {e}")
        return False


async def test_async_operations():
    """测试异步操作"""
    try:
        from backend.core.database import get_async_read_session, get_async_write_session
        from sqlalchemy import text
        
        # 测试异步读操作
        async with get_async_read_session() as session:
            result = await session.execute(text("SELECT 'async_read' as test"))
            test_value = result.scalar()
            assert test_value == "async_read"
        
        # 测试异步写操作
        async with get_async_write_session() as session:
            await session.execute(text("SELECT 'async_write' as test"))
        
        print("✅ 异步操作测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 异步操作测试失败: {e}")
        return False


def test_optional_components():
    """测试可选组件"""
    # InfluxDB测试
    try:
        from backend.core.database import get_trading_data_manager
        trading_manager = get_trading_data_manager()
        
        # 测试连接
        if trading_manager.influx.test_connection():
            print("✅ InfluxDB连接成功 (可选组件)")
        else:
            print("⚠️ InfluxDB连接失败 (可选组件)")
            
    except Exception as e:
        print(f"⚠️ InfluxDB不可用 (可选组件): {e}")
    
    # MongoDB测试
    try:
        from backend.core.database import get_mongo_manager
        mongo_manager = get_mongo_manager()
        
        if mongo_manager.test_sync_connection():
            print("✅ MongoDB连接成功 (可选组件)")
        else:
            print("⚠️ MongoDB连接失败 (可选组件)")
            
    except Exception as e:
        print(f"⚠️ MongoDB不可用 (可选组件): {e}")


def show_usage_examples():
    """显示使用示例"""
    print("\n" + "="*60)
    print("🚀 RedFire数据库系统使用示例")
    print("="*60)
    
    print("""
1. 基本MySQL操作:
   ```python
   from backend.core.database import get_db_session
   
   with get_db_session() as session:
       result = session.execute("SELECT * FROM users")
       users = result.fetchall()
   ```

2. Redis缓存操作:
   ```python
   from backend.core.database import get_cache_manager
   
   cache = get_cache_manager()
   cache.set("user", "123", {"name": "张三"})
   user_data = cache.get("user", "123")
   ```

3. 读写分离:
   ```python
   from backend.core.database import get_read_session, get_write_session
   
   # 读操作
   with get_read_session() as session:
       users = session.execute("SELECT * FROM users").fetchall()
   
   # 写操作
   with get_write_session() as session:
       session.execute("INSERT INTO users ...")
   ```

4. 异步操作:
   ```python
   from backend.core.database import get_async_read_session
   
   async with get_async_read_session() as session:
       result = await session.execute("SELECT * FROM users")
   ```

5. 缓存装饰器:
   ```python
   from backend.core.database import cache
   
   @cache("api_data", ttl=300)
   def get_user_data(user_id):
       # 自动缓存返回结果
       return fetch_user_from_api(user_id)
   ```
    """)
    
    print("="*60)
    print("📚 更多示例请查看: backend/core/database/usage_examples.py")
    print("📖 详细文档请查看: backend/core/database/README.md")
    print("="*60)


async def main():
    """主函数"""
    print("🚀 RedFire数据库系统快速启动测试")
    print("="*50)
    
    # 1. 设置环境
    setup_environment()
    
    # 2. 基础连接测试
    print("\n📊 基础连接测试...")
    mysql_ok = test_mysql_connection()
    redis_ok = test_redis_connection()
    
    if not mysql_ok:
        print("❌ MySQL连接失败，请检查数据库配置")
        print("💡 提示: 请确保MySQL服务运行在 localhost:3306")
        print("💡 用户名: root, 密码: root, 数据库: vnpy")
        return False
    
    if not redis_ok:
        print("❌ Redis连接失败，请检查Redis配置")
        print("💡 提示: 请确保Redis服务运行在 localhost:6379")
        return False
    
    # 3. 核心功能测试
    print("\n🔧 核心功能测试...")
    
    tests = [
        ("统一数据库管理器", test_unified_database_manager),
        ("缓存操作", test_cache_operations),
        ("读写分离", test_read_write_split),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n测试 {test_name}...")
        if not test_func():
            all_passed = False
    
    # 4. 异步操作测试
    print("\n🔄 异步操作测试...")
    if not await test_async_operations():
        all_passed = False
    
    # 5. 可选组件测试
    print("\n🔌 可选组件测试...")
    test_optional_components()
    
    # 6. 显示结果
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有核心功能测试通过！")
        print("✅ RedFire数据库系统已准备就绪")
        
        # 显示使用示例
        show_usage_examples()
        
        return True
    else:
        print("❌ 部分功能测试失败")
        print("💡 请检查错误信息并修复配置")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
