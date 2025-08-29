#!/usr/bin/env python3
"""
配置迁移脚本
============

将现有的分散配置迁移到新的统一配置体系
"""

import os
import sys
import logging
from pathlib import Path
import shutil
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config_manager, AppConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigMigrator:
    """配置迁移器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backup_dir = self.project_root / "config_backup"
        self.legacy_configs = []
        
    def discover_legacy_configs(self):
        """发现旧的配置文件"""
        config_patterns = [
            "config/backend/app_config.py",
            "config/backend/database_config.py", 
            "config/backend/service_config.py",
            "config/backend/monitor_config.py",
            "config/backend/path_config.py",
            "legacy/database_config.py",
            "legacy/core/config/unified_config.py",
            "core/vnpy-engine/config/backend/app_config.py",
        ]
        
        for pattern in config_patterns:
            config_path = self.project_root / pattern
            if config_path.exists():
                self.legacy_configs.append(config_path)
                logger.info(f"发现旧配置文件: {config_path}")
        
        return self.legacy_configs
    
    def backup_legacy_configs(self):
        """备份旧配置文件"""
        if not self.legacy_configs:
            logger.info("没有找到需要备份的配置文件")
            return
        
        # 创建备份目录
        self.backup_dir.mkdir(exist_ok=True)
        
        for config_path in self.legacy_configs:
            # 计算相对路径
            relative_path = config_path.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            
            # 创建备份目录结构
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(config_path, backup_path)
            logger.info(f"已备份: {config_path} -> {backup_path}")
    
    def extract_config_values(self) -> Dict[str, Any]:
        """从旧配置文件中提取配置值"""
        config_values = {}
        
        # 尝试从现有的AppConfig提取值
        try:
            from config.backend.app_config import get_app_config
            old_config = get_app_config()
            
            # 提取重要配置值
            config_mapping = {
                'app_name': getattr(old_config, 'app_name', 'RedFire'),
                'app_version': getattr(old_config, 'app_version', '2.0.0'),
                'debug': getattr(old_config, 'debug', False),
                'host': getattr(old_config, 'host', '0.0.0.0'),
                'port': getattr(old_config, 'port', 8000),
                'secret_key': getattr(old_config, 'secret_key', None),
                'jwt_secret_key': getattr(old_config, 'jwt_secret_key', None),
                'database_url': getattr(old_config, 'database_url', None),
                'redis_url': getattr(old_config, 'redis_url', 'redis://localhost:6379/0'),
                'data_dir': getattr(old_config, 'data_dir', './data'),
                'log_dir': getattr(old_config, 'log_dir', './logs'),
                'vnpy_data_dir': getattr(old_config, 'vnpy_data_dir', './vnpy_data'),
                'cors_origins': getattr(old_config, 'cors_origins', []),
            }
            
            # 过滤掉None值
            config_values = {k: v for k, v in config_mapping.items() if v is not None}
            logger.info(f"从旧配置提取了 {len(config_values)} 个配置项")
            
        except Exception as e:
            logger.warning(f"提取旧配置值失败: {e}")
        
        return config_values
    
    def create_env_file(self, config_values: Dict[str, Any]):
        """创建新的.env文件"""
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            logger.info(".env文件已存在，将备份为.env.old")
            shutil.copy2(env_file, self.project_root / ".env.old")
        
        env_content = ["# RedFire 环境配置文件 (自动迁移生成)", ""]
        
        # 应用基础配置
        env_content.extend([
            "# ===== 应用基础配置 =====",
            f"APP_NAME={config_values.get('app_name', 'RedFire')}",
            f"APP_VERSION={config_values.get('app_version', '2.0.0')}",
            f"DEBUG={str(config_values.get('debug', False)).lower()}",
            f"HOST={config_values.get('host', '0.0.0.0')}",
            f"PORT={config_values.get('port', 8000)}",
            ""
        ])
        
        # 安全配置
        if config_values.get('secret_key'):
            env_content.extend([
                "# ===== 安全配置 =====",
                f"SECRET_KEY={config_values['secret_key']}",
            ])
            if config_values.get('jwt_secret_key'):
                env_content.append(f"JWT_SECRET_KEY={config_values['jwt_secret_key']}")
            env_content.append("")
        
        # 数据库配置
        if config_values.get('database_url'):
            env_content.extend([
                "# ===== 数据库配置 =====",
                f"DATABASE_URL={config_values['database_url']}",
                ""
            ])
        
        # Redis配置
        env_content.extend([
            "# ===== Redis配置 =====",
            f"REDIS_URL={config_values.get('redis_url', 'redis://localhost:6379/0')}",
            ""
        ])
        
        # 目录配置
        env_content.extend([
            "# ===== 目录配置 =====",
            f"DATA_DIR={config_values.get('data_dir', './data')}",
            f"LOG_DIR={config_values.get('log_dir', './logs')}",
            f"VNPY_DATA_DIR={config_values.get('vnpy_data_dir', './vnpy_data')}",
            ""
        ])
        
        # CORS配置
        if config_values.get('cors_origins'):
            cors_origins = str(config_values['cors_origins']).replace("'", '"')
            env_content.extend([
                "# ===== CORS配置 =====",
                f"CORS_ORIGINS={cors_origins}",
                ""
            ])
        
        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(env_content))
        
        logger.info(f"新的.env文件已创建: {env_file}")
    
    def test_new_config(self):
        """测试新的配置系统"""
        try:
            logger.info("测试新的配置系统...")
            
            # 获取配置管理器
            config_manager = get_config_manager()
            
            # 获取应用配置
            app_config = config_manager.get_app_config()
            
            logger.info(f"✅ 配置系统测试成功")
            logger.info(f"   应用名称: {app_config.app_name}")
            logger.info(f"   应用版本: {app_config.app_version}")
            logger.info(f"   运行环境: {app_config.environment}")
            logger.info(f"   服务地址: {app_config.host}:{app_config.port}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置系统测试失败: {e}")
            return False
    
    def cleanup_legacy_configs(self):
        """清理旧的配置文件（可选）"""
        logger.info("是否要删除旧的配置文件？(y/n): ")
        response = input().strip().lower()
        
        if response == 'y':
            for config_path in self.legacy_configs:
                try:
                    config_path.unlink()
                    logger.info(f"已删除: {config_path}")
                except Exception as e:
                    logger.error(f"删除失败 {config_path}: {e}")
        else:
            logger.info("保留旧配置文件，建议在确认新配置正常工作后手动删除")
    
    def migrate(self):
        """执行完整的配置迁移"""
        logger.info("开始配置迁移...")
        
        # 1. 发现旧配置
        self.discover_legacy_configs()
        
        # 2. 备份旧配置
        self.backup_legacy_configs()
        
        # 3. 提取配置值
        config_values = self.extract_config_values()
        
        # 4. 创建新配置文件
        self.create_env_file(config_values)
        
        # 5. 测试新配置
        if self.test_new_config():
            logger.info("✅ 配置迁移成功完成!")
            
            # 6. 可选：清理旧配置
            # self.cleanup_legacy_configs()
            
        else:
            logger.error("❌ 配置迁移失败，请检查错误信息")
            return False
        
        return True


def main():
    """主函数"""
    print("RedFire 配置迁移工具")
    print("==================")
    print()
    
    migrator = ConfigMigrator()
    
    try:
        success = migrator.migrate()
        
        if success:
            print()
            print("🎉 配置迁移完成!")
            print("📁 旧配置已备份到: config_backup/")
            print("⚙️ 新配置文件: .env")
            print("🔧 请检查并根据需要调整配置")
            print()
            print("下一步:")
            print("1. 检查 .env 文件内容")
            print("2. 启动应用测试: python main.py")
            print("3. 确认无误后可删除旧配置文件")
        else:
            print("❌ 配置迁移失败，请查看日志信息")
            
    except Exception as e:
        logger.error(f"迁移过程中出现错误: {e}")
        print("❌ 配置迁移失败")


if __name__ == "__main__":
    main()
