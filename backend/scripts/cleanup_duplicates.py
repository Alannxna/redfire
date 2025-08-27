#!/usr/bin/env python3
"""
重复文件清理脚本
===============

清理重复的配置文件和入口文件
"""

import os
import sys
import logging
from pathlib import Path
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DuplicatesCleaner:
    """重复文件清理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.cleanup_dir = self.project_root / "cleanup_backup"
        
    def identify_duplicates(self):
        """识别重复的文件"""
        # 重复的入口文件
        duplicate_entries = [
            "legacy/interfaces/rest/app.py",  # 被新的统一入口替代
            "run_server.py",                  # 被新的main.py替代
            "run_server.bat",                 # 启动脚本，可能需要更新
        ]
        
        # 重复的配置文件
        duplicate_configs = [
            "legacy/database_config.py",     # 被新配置系统替代
            "legacy/core/config/",           # 旧的配置模块
            "core/vnpy-engine/config/backend/app_config.py",  # 重复的应用配置
        ]
        
        # 检查哪些文件实际存在
        existing_duplicates = []
        
        for file_path in duplicate_entries + duplicate_configs:
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_duplicates.append(full_path)
                logger.info(f"发现重复文件: {full_path}")
        
        return existing_duplicates
    
    def backup_files(self, files):
        """备份要删除的文件"""
        if not files:
            logger.info("没有文件需要备份")
            return
        
        # 创建备份目录
        self.cleanup_dir.mkdir(exist_ok=True)
        
        for file_path in files:
            try:
                # 计算相对路径
                relative_path = file_path.relative_to(self.project_root)
                backup_path = self.cleanup_dir / relative_path
                
                # 创建备份目录结构
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 备份文件或目录
                if file_path.is_file():
                    shutil.copy2(file_path, backup_path)
                else:
                    shutil.copytree(file_path, backup_path, dirs_exist_ok=True)
                
                logger.info(f"已备份: {file_path} -> {backup_path}")
                
            except Exception as e:
                logger.error(f"备份失败 {file_path}: {e}")
    
    def remove_files(self, files):
        """删除重复文件"""
        for file_path in files:
            try:
                if file_path.is_file():
                    file_path.unlink()
                    logger.info(f"已删除文件: {file_path}")
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    logger.info(f"已删除目录: {file_path}")
                    
            except Exception as e:
                logger.error(f"删除失败 {file_path}: {e}")
    
    def update_startup_scripts(self):
        """更新启动脚本"""
        # 更新或创建新的启动脚本
        new_startup_script = self.project_root / "start_redfire.py"
        
        startup_content = '''#!/usr/bin/env python3
"""
RedFire 应用启动脚本
==================

使用新的统一入口点启动应用
"""

import uvicorn
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """启动RedFire应用"""
    logger.info("正在启动RedFire应用...")
    
    # 使用新的统一入口点
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
'''
        
        with open(new_startup_script, 'w', encoding='utf-8') as f:
            f.write(startup_content)
        
        # 设置执行权限（Unix系统）
        if os.name != 'nt':
            os.chmod(new_startup_script, 0o755)
        
        logger.info(f"创建新启动脚本: {new_startup_script}")
        
        # 更新批处理脚本（Windows）
        new_bat_script = self.project_root / "start_redfire.bat"
        
        bat_content = '''@echo off
REM RedFire 应用启动脚本 (Windows)
echo 正在启动RedFire应用...

python main.py

pause
'''
        
        with open(new_bat_script, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        logger.info(f"创建新批处理脚本: {new_bat_script}")
    
    def cleanup_empty_directories(self):
        """清理空目录"""
        # 从深层目录开始清理
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        logger.info(f"删除空目录: {dir_path}")
                except Exception as e:
                    # 忽略删除失败的情况
                    pass
    
    def verify_new_structure(self):
        """验证新的项目结构"""
        logger.info("验证新的项目结构...")
        
        # 检查关键文件是否存在
        required_files = [
            "main.py",                              # 统一入口点
            "core/config/__init__.py",              # 配置模块
            "core/config/app_config.py",           # 应用配置
            "core/config/config_manager.py",       # 配置管理器
            "core/app.py",                          # 应用主类
            "core/lifecycle.py",                    # 生命周期管理
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"缺少关键文件: {missing_files}")
            return False
        else:
            logger.info("✅ 项目结构验证通过")
            return True
    
    def cleanup(self, interactive=True):
        """执行清理操作"""
        logger.info("开始清理重复文件...")
        
        # 1. 识别重复文件
        duplicates = self.identify_duplicates()
        
        if not duplicates:
            logger.info("没有找到重复文件")
            return True
        
        # 2. 询问用户确认
        if interactive:
            print(f"\n发现 {len(duplicates)} 个重复文件:")
            for dup in duplicates:
                print(f"  - {dup}")
            
            response = input("\n是否继续清理？(y/n): ").strip().lower()
            if response != 'y':
                logger.info("用户取消清理操作")
                return False
        
        # 3. 备份文件
        self.backup_files(duplicates)
        
        # 4. 删除重复文件
        self.remove_files(duplicates)
        
        # 5. 更新启动脚本
        self.update_startup_scripts()
        
        # 6. 清理空目录
        self.cleanup_empty_directories()
        
        # 7. 验证新结构
        if self.verify_new_structure():
            logger.info("✅ 清理操作完成!")
            return True
        else:
            logger.error("❌ 清理后项目结构验证失败")
            return False


def main():
    """主函数"""
    print("RedFire 重复文件清理工具")
    print("======================")
    print()
    
    cleaner = DuplicatesCleaner()
    
    try:
        success = cleaner.cleanup()
        
        if success:
            print()
            print("🎉 清理完成!")
            print("📁 删除的文件已备份到: cleanup_backup/")
            print("🚀 新启动脚本: start_redfire.py / start_redfire.bat")
            print()
            print("下一步:")
            print("1. 测试新的应用入口: python main.py")
            print("2. 使用新启动脚本: python start_redfire.py")
            print("3. 确认一切正常后可删除备份目录")
        else:
            print("❌ 清理失败，请查看日志信息")
            
    except Exception as e:
        logger.error(f"清理过程中出现错误: {e}")
        print("❌ 清理失败")


if __name__ == "__main__":
    main()
