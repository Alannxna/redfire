"""
配置文件迁移工具

将现有的分散配置文件迁移到标准化路径结构
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil
import yaml
import json
from datetime import datetime

# 添加路径以便导入
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.standards.path_standards import (
    ConfigPathStandards, ConfigType, Environment,
    get_standard_service_name
)


class ConfigMigrator:
    """配置文件迁移器"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.migration_log: List[Dict] = []
        self.errors: List[str] = []
        
        # 确保标准目录存在
        ConfigPathStandards.ensure_directories()
    
    def add_log(self, action: str, source: str, target: str, status: str = "success"):
        """添加迁移日志"""
        self.migration_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "source": source,
            "target": target,
            "status": status,
            "dry_run": self.dry_run
        })
    
    def migrate_root_configs(self) -> None:
        """迁移根目录配置文件"""
        print("🔄 迁移根目录配置文件...")
        
        # 根目录的配置文件映射
        root_configs = [
            ("backend/config.yaml", "shared", ConfigType.APPLICATION),
            ("backend/.env", "shared", ConfigType.APPLICATION),
            ("backend/docker-compose.yml", "shared", ConfigType.APPLICATION),
        ]
        
        for old_path_str, target_type, config_type in root_configs:
            old_path = Path(old_path_str)
            if old_path.exists():
                if target_type == "shared":
                    new_path = ConfigPathStandards.get_shared_config_path(
                        config_type, Environment.DEVELOPMENT
                    )
                
                self._migrate_file(old_path, new_path, "root_config")
    
    def migrate_service_configs(self) -> None:
        """迁移服务配置文件"""
        print("🔄 迁移服务配置文件...")
        
        # 服务配置映射
        service_configs = [
            # Config Service
            ("backend/config_service/config/development.yaml", "config-service", ConfigType.APPLICATION),
            
            # Core configs
            ("backend/core/vnpy-engine/config/.env", "vnpy-service", ConfigType.APPLICATION),
            ("backend/core/vnpy-engine/config/config.env", "vnpy-service", ConfigType.VNPY),
            ("backend/core/vnpy-engine/config/backend/config.env", "vnpy-service", ConfigType.VNPY),
            ("backend/core/vnpy-engine/config/vt_setting.json", "vnpy-service", ConfigType.VNPY),
            
            # Database configs
            ("backend/core/database/docker-compose.database.yml", "shared", ConfigType.DATABASE),
            
            # Gateway configs
            ("backend/gateway/docker-compose.yml", "gateway-service", ConfigType.APPLICATION),
            ("backend/gateway/monitoring/logstash/config/logstash.yml", "gateway-service", ConfigType.LOGGING),
            
            # Legacy configs
            ("backend/legacy/core/config/.env", "legacy-service", ConfigType.APPLICATION),
            
            # Shared configs
            ("backend/shared/config/config/shared/development/database.yaml", "shared", ConfigType.DATABASE),
            ("backend/shared/config/config/trading/development/config.yaml", "trading-service", ConfigType.APPLICATION),
            ("backend/shared/config/config/user/development/config.yaml", "user-service", ConfigType.APPLICATION),
        ]
        
        for old_path_str, service_name, config_type in service_configs:
            old_path = Path(old_path_str)
            if old_path.exists():
                if service_name == "shared":
                    new_path = ConfigPathStandards.get_shared_config_path(
                        config_type, Environment.DEVELOPMENT
                    )
                else:
                    new_path = ConfigPathStandards.get_service_config_path(
                        service_name, config_type, Environment.DEVELOPMENT
                    )
                
                self._migrate_file(old_path, new_path, "service_config")
    
    def migrate_dashboard_configs(self) -> None:
        """迁移监控面板配置"""
        print("🔄 迁移监控面板配置...")
        
        dashboard_configs = [
            ("backend/gateway/monitoring/grafana/dashboards/redfire-system-overview.json", 
             "monitor-service", ConfigType.MONITORING),
            ("backend/gateway/monitoring/grafana/dashboards/redfire-vnpy-trading.json", 
             "monitor-service", ConfigType.MONITORING),
        ]
        
        for old_path_str, service_name, config_type in dashboard_configs:
            old_path = Path(old_path_str)
            if old_path.exists():
                # 为监控配置创建特殊路径
                new_path = (ConfigPathStandards.SERVICES_CONFIG_DIR / 
                           service_name / 
                           Environment.DEVELOPMENT.value / 
                           "dashboards" / 
                           old_path.name)
                
                self._migrate_file(old_path, new_path, "dashboard_config")
    
    def _migrate_file(self, old_path: Path, new_path: Path, migration_type: str) -> bool:
        """迁移单个文件"""
        try:
            print(f"  📄 {old_path} -> {new_path}")
            
            if self.dry_run:
                print(f"    [DRY RUN] 将迁移到: {new_path}")
                self.add_log("migrate", str(old_path), str(new_path), "dry_run")
                return True
            
            # 确保目标目录存在
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(old_path, new_path)
            
            # 验证文件内容
            if self._validate_migrated_file(old_path, new_path):
                print(f"    ✅ 迁移成功")
                self.add_log("migrate", str(old_path), str(new_path), "success")
                return True
            else:
                print(f"    ❌ 文件验证失败")
                self.add_log("migrate", str(old_path), str(new_path), "validation_failed")
                return False
                
        except Exception as e:
            error_msg = f"迁移文件失败 {old_path} -> {new_path}: {e}"
            print(f"    ❌ {error_msg}")
            self.errors.append(error_msg)
            self.add_log("migrate", str(old_path), str(new_path), f"error: {e}")
            return False
    
    def _validate_migrated_file(self, old_path: Path, new_path: Path) -> bool:
        """验证迁移的文件"""
        try:
            # 检查文件大小
            if old_path.stat().st_size != new_path.stat().st_size:
                return False
            
            # 对于特定类型文件进行内容验证
            if old_path.suffix in ['.yaml', '.yml']:
                with open(old_path, 'r', encoding='utf-8') as f:
                    old_content = yaml.safe_load(f)
                with open(new_path, 'r', encoding='utf-8') as f:
                    new_content = yaml.safe_load(f)
                return old_content == new_content
            
            elif old_path.suffix == '.json':
                with open(old_path, 'r', encoding='utf-8') as f:
                    old_content = json.load(f)
                with open(new_path, 'r', encoding='utf-8') as f:
                    new_content = json.load(f)
                return old_content == new_content
            
            else:
                # 对于其他文件类型，比较内容
                with open(old_path, 'rb') as f:
                    old_content = f.read()
                with open(new_path, 'rb') as f:
                    new_content = f.read()
                return old_content == new_content
                
        except Exception as e:
            print(f"    ⚠️ 验证过程中出错: {e}")
            return False
    
    def create_legacy_backup(self) -> None:
        """创建遗留配置的备份"""
        if self.dry_run:
            print("🔄 [DRY RUN] 将创建遗留配置备份...")
            return
        
        print("🔄 创建遗留配置备份...")
        
        backup_dir = ConfigPathStandards.LEGACY_CONFIG_DIR / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 要备份的路径
        backup_paths = [
            "backend/config.yaml",
            "backend/.env", 
            "backend/config_service/config/",
            "backend/core/vnpy-engine/config/",
            "backend/gateway/monitoring/",
            "backend/legacy/core/config/",
            "backend/shared/config/config/"
        ]
        
        for path_str in backup_paths:
            path = Path(path_str)
            if path.exists():
                try:
                    if path.is_file():
                        target = backup_dir / path.name
                        shutil.copy2(path, target)
                    else:
                        target = backup_dir / path.name
                        shutil.copytree(path, target, dirs_exist_ok=True)
                    
                    print(f"  ✅ 备份: {path} -> {target}")
                except Exception as e:
                    print(f"  ❌ 备份失败 {path}: {e}")
    
    def generate_migration_report(self) -> str:
        """生成迁移报告"""
        report_lines = [
            "# 配置文件迁移报告",
            f"",
            f"**生成时间**: {datetime.now().isoformat()}",
            f"**模式**: {'DRY RUN' if self.dry_run else 'ACTUAL MIGRATION'}",
            f"**总计迁移**: {len(self.migration_log)} 个文件",
            f"**错误数量**: {len(self.errors)}",
            f"",
            "## 迁移详情",
            ""
        ]
        
        for log_entry in self.migration_log:
            status_emoji = "✅" if log_entry["status"] == "success" else "❌"
            report_lines.append(
                f"- {status_emoji} **{log_entry['action']}**: {log_entry['source']} -> {log_entry['target']}"
            )
        
        if self.errors:
            report_lines.extend([
                "",
                "## 错误详情",
                ""
            ])
            for error in self.errors:
                report_lines.append(f"- ❌ {error}")
        
        report_lines.extend([
            "",
            "## 下一步",
            "",
            "1. 验证迁移后的配置文件正确性",
            "2. 更新服务中的配置文件加载路径", 
            "3. 测试所有服务的配置加载",
            "4. 删除旧的配置文件（确认无误后）"
        ])
        
        return "\n".join(report_lines)
    
    def run_migration(self) -> None:
        """运行完整迁移流程"""
        print(f"🚀 开始配置文件迁移 {'(DRY RUN)' if self.dry_run else '(ACTUAL)'}")
        print("=" * 60)
        
        try:
            # 1. 创建备份
            self.create_legacy_backup()
            print()
            
            # 2. 迁移各类配置
            self.migrate_root_configs()
            print()
            
            self.migrate_service_configs()
            print()
            
            self.migrate_dashboard_configs()
            print()
            
            # 3. 生成报告
            report = self.generate_migration_report()
            report_path = Path("config_migration_report.md")
            
            if not self.dry_run:
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"📋 迁移报告已生成: {report_path}")
            else:
                print("📋 迁移报告预览:")
                print("-" * 40)
                print(report)
            
            print("=" * 60)
            print(f"🎉 配置文件迁移完成!")
            
            if self.errors:
                print(f"⚠️ 发现 {len(self.errors)} 个错误，请检查报告")
            else:
                print("✅ 所有配置文件迁移成功!")
                
        except Exception as e:
            print(f"❌ 迁移过程中发生错误: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RedFire 配置文件迁移工具")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="仅预览迁移，不实际移动文件")
    parser.add_argument("--execute", action="store_true", 
                       help="执行实际迁移")
    
    args = parser.parse_args()
    
    # 如果指定了 --execute，则关闭 dry_run
    if args.execute:
        dry_run = False
    else:
        dry_run = args.dry_run
    
    migrator = ConfigMigrator(dry_run=dry_run)
    migrator.run_migration()


if __name__ == "__main__":
    main()
