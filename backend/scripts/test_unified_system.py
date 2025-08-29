#!/usr/bin/env python3
"""
统一系统测试脚本
===============

测试新的统一入口点和配置管理系统
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
import traceback

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_config_system():
    """测试配置系统"""
    logger.info("=== 测试配置系统 ===")
    
    try:
        from core.config import get_config_manager, get_app_config
        
        # 测试配置管理器
        config_manager = get_config_manager()
        logger.info("✅ 配置管理器创建成功")
        
        # 测试应用配置
        app_config = get_app_config()
        logger.info("✅ 应用配置加载成功")
        
        # 验证配置值
        logger.info(f"   应用名称: {app_config.app_name}")
        logger.info(f"   应用版本: {app_config.app_version}")
        logger.info(f"   运行环境: {app_config.environment}")
        logger.info(f"   调试模式: {app_config.debug}")
        logger.info(f"   服务地址: {app_config.host}:{app_config.port}")
        
        # 测试配置验证
        app_config._validate_config()
        logger.info("✅ 配置验证通过")
        
        # 测试目录创建
        app_config.create_directories()
        logger.info("✅ 目录创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置系统测试失败: {e}")
        traceback.print_exc()
        return False


async def test_database_system():
    """测试数据库系统"""
    logger.info("=== 测试数据库系统 ===")
    
    try:
        from database import DatabaseManager
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        logger.info("✅ 数据库管理器创建成功")
        
        # 初始化数据库（使用默认SQLite）
        database_url = "sqlite:///./data/test_redfire.db"
        await db_manager.initialize(database_url)
        logger.info("✅ 数据库初始化成功")
        
        # 测试连接
        session = db_manager.get_session()
        session.close()
        logger.info("✅ 数据库连接测试成功")
        
        # 关闭连接
        await db_manager.close()
        logger.info("✅ 数据库连接关闭成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库系统测试失败: {e}")
        traceback.print_exc()
        return False


async def test_app_creation():
    """测试应用创建"""
    logger.info("=== 测试应用创建 ===")
    
    try:
        from core.app import create_app, RedFireApplication
        
        # 创建应用实例
        redfire_app = RedFireApplication()
        logger.info("✅ RedFire应用实例创建成功")
        
        # 创建FastAPI应用
        fastapi_app = redfire_app.create_app()
        logger.info("✅ FastAPI应用创建成功")
        
        # 验证应用属性
        assert fastapi_app.title == redfire_app.config.app_name
        assert fastapi_app.version == redfire_app.config.app_version
        logger.info("✅ 应用属性验证通过")
        
        # 测试路由
        routes = [route.path for route in fastapi_app.routes]
        expected_routes = ["/", "/health"]
        
        for expected_route in expected_routes:
            if expected_route in routes:
                logger.info(f"✅ 路由存在: {expected_route}")
            else:
                logger.warning(f"⚠️ 路由缺失: {expected_route}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 应用创建测试失败: {e}")
        traceback.print_exc()
        return False


async def test_main_entry():
    """测试主入口点"""
    logger.info("=== 测试主入口点 ===")
    
    try:
        # 导入主入口模块
        import main
        logger.info("✅ 主入口模块导入成功")
        
        # 验证app实例
        assert hasattr(main, 'app')
        assert main.app is not None
        logger.info("✅ FastAPI应用实例存在")
        
        # 验证应用类型
        from fastapi import FastAPI
        assert isinstance(main.app, FastAPI)
        logger.info("✅ 应用类型验证通过")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 主入口点测试失败: {e}")
        traceback.print_exc()
        return False


async def test_middleware_system():
    """测试中间件系统"""
    logger.info("=== 测试中间件系统 ===")
    
    try:
        from core.middleware import setup_middleware
        from core.middleware.logging_middleware import LoggingMiddleware
        from core.middleware.error_middleware import ErrorHandlingMiddleware
        from core.config import get_app_config
        from fastapi import FastAPI
        
        # 创建测试应用
        test_app = FastAPI()
        config = get_app_config()
        
        # 设置中间件
        setup_middleware(test_app, config)
        logger.info("✅ 中间件设置成功")
        
        # 创建中间件实例测试
        logging_middleware = LoggingMiddleware(config)
        error_middleware = ErrorHandlingMiddleware(config)
        logger.info("✅ 中间件实例创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 中间件系统测试失败: {e}")
        traceback.print_exc()
        return False


async def test_component_initializer():
    """测试组件初始化器"""
    logger.info("=== 测试组件初始化器 ===")
    
    try:
        from core.initializer import ComponentInitializer
        from core.config import get_app_config
        
        config = get_app_config()
        initializer = ComponentInitializer(config)
        logger.info("✅ 组件初始化器创建成功")
        
        # 测试数据库初始化
        await initializer.initialize_database()
        logger.info("✅ 数据库组件初始化成功")
        
        # 测试组件关闭
        await initializer.shutdown_database()
        logger.info("✅ 数据库组件关闭成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 组件初始化器测试失败: {e}")
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print("RedFire 统一系统测试")
    print("==================")
    print()
    
    tests = [
        ("配置系统", test_config_system),
        ("数据库系统", test_database_system),
        ("应用创建", test_app_creation),
        ("主入口点", test_main_entry),
        ("中间件系统", test_middleware_system),
        ("组件初始化器", test_component_initializer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n开始测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed == 0:
        print("\n🎉 所有测试通过! 统一系统运行正常")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查相关组件")
        return False


def main():
    """主函数"""
    try:
        success = asyncio.run(run_all_tests())
        
        if success:
            print("\n下一步建议:")
            print("1. 运行应用: python main.py")
            print("2. 访问健康检查: http://localhost:8000/health")
            print("3. 查看API文档: http://localhost:8000/docs")
        else:
            print("\n请修复失败的测试后再启动应用")
            
    except Exception as e:
        logger.error(f"测试运行出现异常: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
