#!/usr/bin/env python3
"""
RedFire 统一应用入口点
===================

整合所有功能模块的单一主入口点
支持统一配置管理和多环境部署
"""

import logging
import os
import sys
from pathlib import Path

# 确保能够导入项目模块
sys.path.insert(0, str(Path(__file__).parent))

from core.app import create_app, get_app_instance
from core.config import get_config_manager, get_app_config

# 配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_config():
    """设置配置"""
    try:
        # 获取配置管理器
        config_manager = get_config_manager()
        
        # 加载配置文件（如果存在）
        config_files = ['.env', 'config.yaml', 'config.yml']
        for config_file in config_files:
            if os.path.exists(config_file):
                config_manager.load_from_file(config_file)
                logger.info(f"已加载配置文件: {config_file}")
        
        # 获取应用配置
        app_config = get_app_config()
        logger.info(f"应用配置加载完成 - 环境: {app_config.environment}")
        
        return app_config
        
    except Exception as e:
        logger.error(f"配置设置失败: {e}")
        raise

def create_application():
    """创建应用实例"""
    try:
        # 设置配置
        config = setup_config()
        
        # 创建应用
        app = create_app(config)
        
        logger.info("RedFire应用创建完成")
        return app
        
    except Exception as e:
        logger.error(f"应用创建失败: {e}")
        raise

# 创建FastAPI应用实例
app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    # 开发环境运行配置
    config = get_app_config()
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.is_development(),
        log_level=config.log_level.lower()
    )