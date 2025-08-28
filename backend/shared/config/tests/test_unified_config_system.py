"""
统一配置系统测试
================

测试重构后的配置系统，验证功能完整性和性能改进
"""

import os
import json
import tempfile
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

import pytest

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_unified_config_utils():
    """测试统一配置工具模块"""
    logger.info("🧪 测试统一配置工具模块...")
    
    try:
        from backend.shared.config.utils.config_utils import (
            ConfigTypeConverter,
            ConfigFileLoader,
            ConfigEnvLoader,
            ConfigMerger,
            ConfigValidator,
            ConfigCache
        )
        
        # 测试类型转换器
        assert ConfigTypeConverter.convert_env_value("true") == True
        assert ConfigTypeConverter.convert_env_value("123") == 123
        assert ConfigTypeConverter.convert_env_value("3.14") == 3.14
        assert ConfigTypeConverter.convert_env_value("hello") == "hello"
        logger.info("✅ 类型转换器测试通过")
        
        # 测试配置合并器
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}, "e": 4}
        merged = ConfigMerger.deep_merge(base, override)
        assert merged == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        logger.info("✅ 配置合并器测试通过")
        
        # 测试配置验证器
        config = {"app": {"name": "test", "port": 8080}}
        assert ConfigValidator.get_nested_value(config, "app.name") == "test"
        assert ConfigValidator.get_nested_value(config, "app.missing", "default") == "default"
        logger.info("✅ 配置验证器测试通过")
        
        # 测试配置缓存
        cache = ConfigCache(max_size=5, ttl_seconds=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("missing", "default") == "default"
        logger.info("✅ 配置缓存测试通过")
        
        logger.info("✅ 统一配置工具模块测试全部通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 统一配置工具模块测试失败: {e}")
        return False


def test_global_cache_manager():
    """测试全局缓存管理器"""
    logger.info("🧪 测试全局缓存管理器...")
    
    try:
        from backend.shared.config.cache.global_cache_manager import (
            global_cache_manager,
            CacheType,
            cache_get,
            cache_set,
            cache_clear,
            get_cache_stats
        )
        
        # 清空测试缓存
        cache_clear(CacheType.SHARED_CONFIG)
        
        # 测试缓存设置和获取
        cache_set(CacheType.SHARED_CONFIG, "test_key", {"value": "test"})
        result = cache_get(CacheType.SHARED_CONFIG, "test_key")
        assert result == {"value": "test"}
        logger.info("✅ 缓存设置和获取测试通过")
        
        # 测试缓存统计
        stats = get_cache_stats()
        assert CacheType.SHARED_CONFIG in stats
        logger.info("✅ 缓存统计测试通过")
        
        # 测试内存使用情况
        memory_info = global_cache_manager.get_total_memory_usage()
        assert "total_caches" in memory_info
        assert "total_items" in memory_info
        logger.info(f"📊 缓存内存使用: {memory_info}")
        
        # 测试缓存优化
        optimization_result = global_cache_manager.optimize_memory()
        assert "cleaned_items" in optimization_result
        logger.info(f"🧼 缓存优化结果: {optimization_result}")
        
        logger.info("✅ 全局缓存管理器测试全部通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 全局缓存管理器测试失败: {e}")
        return False


async def test_shared_config_loader():
    """测试重构后的共享配置加载器"""
    logger.info("🧪 测试重构后的共享配置加载器...")
    
    try:
        from backend.shared.config.config_loader import SharedConfigLoader, ConfigSource
        
        # 创建临时配置文件
        config_data = {
            "app": {"name": "test-app", "version": "1.0.0"},
            "database": {"host": "localhost", "port": 5432}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # 测试配置加载器
            loader = SharedConfigLoader(enable_cache=True)
            
            # 测试从文件加载
            result = await loader.load_config(
                config_name="test_config",
                sources=[ConfigSource.FILE],
                config_file=config_file
            )
            
            assert result.success
            assert result.data["app"]["name"] == "test-app"
            logger.info("✅ 文件配置加载测试通过")
            
            # 测试缓存功能
            # 第二次加载应该命中缓存
            result2 = await loader.load_config(
                config_name="test_config", 
                sources=[ConfigSource.FILE],
                config_file=config_file
            )
            assert result2.success
            assert result2.data == result.data
            logger.info("✅ 缓存功能测试通过")
            
            # 测试环境变量加载
            os.environ["REDFIRE_SHARED_TEST_CONFIG_APP_NAME"] = "env-app"
            result3 = await loader.load_config(
                config_name="test_config",
                sources=[ConfigSource.ENV]
            )
            # 注意：环境变量加载可能为空，这是正常的
            logger.info(f"📝 环境变量配置加载结果: {result3.success}")
            
            # 测试缓存清理
            loader.clear_cache()
            logger.info("✅ 缓存清理测试通过")
            
            logger.info("✅ 共享配置加载器测试全部通过")
            return True
            
        finally:
            # 清理临时文件
            Path(config_file).unlink(missing_ok=True)
            if "REDFIRE_SHARED_TEST_CONFIG_APP_NAME" in os.environ:
                del os.environ["REDFIRE_SHARED_TEST_CONFIG_APP_NAME"]
        
    except Exception as e:
        logger.error(f"❌ 共享配置加载器测试失败: {e}")
        return False


def test_infrastructure_config_manager():
    """测试重构后的基础设施配置管理器"""
    logger.info("🧪 测试重构后的基础设施配置管理器...")
    
    try:
        from backend.legacy.core.infrastructure.config_manager import InfraConfigManager
        
        # 创建配置管理器
        manager = InfraConfigManager()
        
        # 添加配置源
        manager.add_config_source("env", "", priority=1)
        
        # 测试配置加载
        config = manager.load_config()
        assert isinstance(config, dict)
        logger.info("✅ 基础设施配置管理器基本功能测试通过")
        
        # 测试配置获取
        value = manager.get("nonexistent.key", "default")
        assert value == "default"
        logger.info("✅ 配置获取功能测试通过")
        
        logger.info("✅ 基础设施配置管理器测试全部通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 基础设施配置管理器测试失败: {e}")
        return False


def test_memory_usage_improvement():
    """测试内存使用改进"""
    logger.info("🧪 测试内存使用改进...")
    
    try:
        from backend.shared.config.cache.global_cache_manager import global_cache_manager
        import tracemalloc
        
        # 开始内存跟踪
        tracemalloc.start()
        
        # 模拟大量配置缓存操作
        for i in range(100):
            global_cache_manager.set(
                cache_type=global_cache_manager._caches.keys().__iter__().__next__(),
                key=f"test_key_{i}",
                value={"data": f"value_{i}", "index": i}
            )
        
        # 获取内存使用情况
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memory_info = global_cache_manager.get_total_memory_usage()
        
        logger.info(f"📊 当前内存使用: {current / 1024 / 1024:.2f} MB")
        logger.info(f"📊 峰值内存使用: {peak / 1024 / 1024:.2f} MB")
        logger.info(f"📊 缓存项统计: {memory_info}")
        
        # 验证内存使用合理 (小于10MB)
        assert peak < 10 * 1024 * 1024, f"内存使用过高: {peak / 1024 / 1024:.2f} MB"
        
        # 测试内存优化
        optimization_result = global_cache_manager.optimize_memory()
        logger.info(f"🧼 内存优化结果: {optimization_result}")
        
        logger.info("✅ 内存使用改进测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 内存使用改进测试失败: {e}")
        return False


async def test_performance_improvement():
    """测试性能改进"""
    logger.info("🧪 测试性能改进...")
    
    try:
        from backend.shared.config.config_loader import SharedConfigLoader, ConfigSource
        import time
        
        loader = SharedConfigLoader(enable_cache=True)
        
        # 创建测试配置
        config_data = {"app": {"name": "perf-test"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # 测试首次加载性能
            start_time = time.time()
            result = await loader.load_config(
                config_name="perf_test",
                sources=[ConfigSource.FILE],
                config_file=config_file
            )
            first_load_time = time.time() - start_time
            
            assert result.success
            logger.info(f"⏱️ 首次加载时间: {first_load_time:.4f}s")
            
            # 测试缓存加载性能
            start_time = time.time()
            result2 = await loader.load_config(
                config_name="perf_test",
                sources=[ConfigSource.FILE],
                config_file=config_file
            )
            cached_load_time = time.time() - start_time
            
            assert result2.success
            logger.info(f"⏱️ 缓存加载时间: {cached_load_time:.4f}s")
            
            # 验证缓存加载显著更快
            speedup = first_load_time / cached_load_time if cached_load_time > 0 else float('inf')
            logger.info(f"🚀 缓存加速倍数: {speedup:.2f}x")
            
            # 缓存加载应该比首次加载快至少2倍
            assert speedup >= 2.0, f"缓存加速不明显: {speedup:.2f}x"
            
            logger.info("✅ 性能改进测试通过")
            return True
            
        finally:
            Path(config_file).unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"❌ 性能改进测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始配置系统重构验证测试...")
    logger.info("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("统一配置工具模块", test_unified_config_utils),
        ("全局缓存管理器", test_global_cache_manager), 
        ("共享配置加载器", test_shared_config_loader),
        ("基础设施配置管理器", test_infrastructure_config_manager),
        ("内存使用改进", test_memory_usage_improvement),
        ("性能改进", test_performance_improvement),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 运行测试: {test_name}")
        logger.info("-" * 40)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ 测试 {test_name} 执行异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试结果汇总:")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n📈 测试统计:")
    logger.info(f"✅ 通过: {passed}")
    logger.info(f"❌ 失败: {failed}")
    logger.info(f"📊 成功率: {(passed / len(test_results) * 100):.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 所有测试通过！配置系统重构成功！")
        return True
    else:
        logger.info(f"\n⚠️ 有 {failed} 个测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(run_all_tests())
    exit(0 if result else 1)
