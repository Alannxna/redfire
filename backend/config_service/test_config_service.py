#!/usr/bin/env python3
# 🧪 RedFire配置管理服务测试

"""
配置管理服务基础测试

这个测试文件用于验证配置服务的基本功能是否正常工作。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

async def test_config_models():
    """测试配置模型"""
    print("🧪 测试配置模型...")
    
    try:
        from backend.config_service.models.config_models import (
            AppConfig, DatabaseConfig, RedisConfig, 
            Environment, create_config_from_dict
        )
        
        # 测试基本配置创建
        config_dict = {
            "app_name": "Test App",
            "environment": Environment.DEVELOPMENT,
            "debug": True,
            "database": {
                "engine": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "test_user",
                "password": "test_pass"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "security": {
                "secret_key": "test-secret-key-must-be-at-least-32-characters-long",
                "algorithm": "HS256"
            }
        }
        
        config = create_config_from_dict(config_dict)
        
        assert config.app_name == "Test App"
        assert config.environment == Environment.DEVELOPMENT
        assert config.database.host == "localhost"
        assert config.redis.port == 6379
        
        print("✅ 配置模型测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置模型测试失败: {e}")
        return False

async def test_config_manager():
    """测试配置管理器"""
    print("🧪 测试配置管理器...")
    
    try:
        from backend.config_service.core.config_manager import ExternalConfigManager
        
        # 创建配置管理器实例
        manager = ExternalConfigManager()
        
        # 测试配置字典
        config_dict = {
            "app_name": "Test Manager App",
            "environment": "testing",
            "debug": True,
            "database": {
                "engine": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "test_user", 
                "password": "test_pass"
            },
            "security": {
                "secret_key": "test-secret-key-must-be-at-least-32-characters-long"
            }
        }
        
        # 初始化配置
        config = await manager.initialize(
            config_dict=config_dict,
            enable_file_watching=False,
            enable_cache=True
        )
        
        assert config.app_name == "Test Manager App"
        assert manager.is_initialized == True
        
        # 测试配置获取
        db_config = manager.get_database_config()
        assert db_config.host == "localhost"
        
        # 测试嵌套配置获取
        host = manager.get_nested_config("database.host")
        assert host == "localhost"
        
        # 测试配置更新
        success = await manager.update_config({
            "debug": False,
            "database": {"pool_size": 30}
        })
        assert success == True
        
        updated_config = manager.get_config()
        assert updated_config.debug == False
        assert updated_config.database.pool_size == 30
        
        # 清理
        await manager.shutdown()
        
        print("✅ 配置管理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False

async def test_config_api():
    """测试配置API"""
    print("🧪 测试配置API...")
    
    try:
        from backend.config_service.api.config_api import create_config_app
        from backend.config_service.core.config_manager import initialize_config
        
        # 初始化配置
        config_dict = {
            "app_name": "Test API App",
            "environment": "testing",
            "debug": True,
            "database": {
                "engine": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "test_user",
                "password": "test_pass"
            },
            "security": {
                "secret_key": "test-secret-key-must-be-at-least-32-characters-long"
            }
        }
        
        await initialize_config(config_dict=config_dict, enable_file_watching=False)
        
        # 创建FastAPI应用
        app = create_config_app()
        
        assert app is not None
        assert app.title == "RedFire配置管理服务"
        
        print("✅ 配置API测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置API测试失败: {e}")
        return False

async def test_config_file_loading():
    """测试配置文件加载"""
    print("🧪 测试配置文件加载...")
    
    try:
        from backend.config_service.models.config_models import create_config_from_file
        
        # 测试加载开发环境配置
        config_file = "backend/config_service/config/development.yaml"
        config_path = Path(config_file)
        
        if config_path.exists():
            config = create_config_from_file(config_file)
            
            assert config.app_name == "RedFire Config Service"
            assert config.environment.value == "development"
            assert config.database.engine.value == "postgresql"
            
            print("✅ 配置文件加载测试通过")
            return True
        else:
            print("⚠️ 开发配置文件不存在，跳过测试")
            return True
            
    except Exception as e:
        print(f"❌ 配置文件加载测试失败: {e}")
        return False

async def test_package_import():
    """测试包导入"""
    print("🧪 测试包导入...")
    
    try:
        # 测试主包导入
        import backend.config_service
        
        # 测试版本信息
        version = backend.config_service.get_version()
        assert version == "1.0.0"
        
        # 测试包信息
        info = backend.config_service.get_package_info()
        assert "name" in info
        assert "version" in info
        
        # 测试便捷函数导入
        from backend.config_service import (
            AppConfig, DatabaseConfig, Environment,
            initialize_config, get_config
        )
        
        print("✅ 包导入测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 包导入测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行RedFire配置管理服务测试...")
    print("=" * 60)
    
    tests = [
        test_package_import,
        test_config_models,
        test_config_manager,
        test_config_file_loading,
        test_config_api,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            success = await test()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {test.__name__} - {e}")
            failed += 1
        
        print("-" * 40)
    
    print("📊 测试结果:")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 所有测试通过！配置服务可以正常使用")
        return True
    else:
        print("⚠️ 有测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)
