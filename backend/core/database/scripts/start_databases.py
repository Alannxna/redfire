#!/usr/bin/env python3
"""
RedFire 数据库启动脚本
===================

一键启动所有数据库服务并进行初始化检查
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional
import click

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)


class DatabaseStarter:
    """数据库启动管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.database_dir = Path(__file__).parent.parent
        self.docker_compose_file = self.database_dir / "docker-compose.database.yml"
        
        # 检查Docker Compose文件是否存在
        if not self.docker_compose_file.exists():
            raise FileNotFoundError(f"Docker Compose文件不存在: {self.docker_compose_file}")
    
    def check_docker(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            logger.info(f"Docker版本: {result.stdout.strip()}")
            
            result = subprocess.run(
                ["docker-compose", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            logger.info(f"Docker Compose版本: {result.stdout.strip()}")
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Docker检查失败: {e}")
            return False
    
    def create_env_file(self):
        """创建环境变量文件"""
        env_file = self.database_dir / ".env"
        
        if env_file.exists():
            logger.info("环境变量文件已存在")
            return
        
        env_content = """# RedFire 数据库环境变量
# ========================

# MySQL配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=vnpy

# MySQL从库配置
DB_SLAVE_HOST=localhost
DB_SLAVE_PORT=3307

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# InfluxDB配置
INFLUX_PORT=8086
INFLUX_ADMIN_USER=admin
INFLUX_ADMIN_PASSWORD=admin123
INFLUX_ORG=redfire
INFLUX_BUCKET=trading_data
INFLUX_TOKEN=redfire-token

# MongoDB配置
MONGO_PORT=27017
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=admin123
MONGO_DATABASE=redfire_logs
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.info(f"创建环境变量文件: {env_file}")
    
    def start_services(self, services: Optional[List[str]] = None) -> bool:
        """启动数据库服务"""
        try:
            cmd = [
                "docker-compose", 
                "-f", str(self.docker_compose_file),
                "up", "-d"
            ]
            
            if services:
                cmd.extend(services)
            
            logger.info(f"启动数据库服务: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, cwd=self.database_dir, check=True)
            
            if result.returncode == 0:
                logger.info("✅ 数据库服务启动成功")
                return True
            else:
                logger.error("❌ 数据库服务启动失败")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"启动数据库服务失败: {e}")
            return False
    
    def stop_services(self) -> bool:
        """停止数据库服务"""
        try:
            cmd = [
                "docker-compose", 
                "-f", str(self.docker_compose_file),
                "down"
            ]
            
            logger.info("停止数据库服务...")
            result = subprocess.run(cmd, cwd=self.database_dir, check=True)
            
            if result.returncode == 0:
                logger.info("✅ 数据库服务停止成功")
                return True
            else:
                logger.error("❌ 数据库服务停止失败")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"停止数据库服务失败: {e}")
            return False
    
    def check_services_health(self) -> Dict[str, bool]:
        """检查服务健康状态"""
        services = {
            "mysql-master": False,
            "mysql-slave": False, 
            "redis": False,
            "influxdb": False,
            "mongodb": False
        }
        
        try:
            cmd = [
                "docker-compose", 
                "-f", str(self.docker_compose_file),
                "ps"
            ]
            
            result = subprocess.run(
                cmd, 
                cwd=self.database_dir, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            output = result.stdout
            
            for service in services.keys():
                if service in output and "Up" in output:
                    services[service] = True
            
            return services
            
        except subprocess.CalledProcessError as e:
            logger.error(f"检查服务状态失败: {e}")
            return services
    
    def wait_for_services(self, timeout: int = 120) -> bool:
        """等待服务启动完成"""
        logger.info(f"等待服务启动完成 (最大等待 {timeout} 秒)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            services = self.check_services_health()
            healthy_count = sum(services.values())
            total_count = len(services)
            
            logger.info(f"服务健康状态: {healthy_count}/{total_count}")
            
            if healthy_count == total_count:
                logger.info("✅ 所有服务启动完成")
                return True
            
            time.sleep(5)
        
        logger.warning("⚠️ 部分服务可能未完全启动")
        return False
    
    def show_service_status(self):
        """显示服务状态"""
        services = self.check_services_health()
        
        print("\n" + "="*50)
        print("🔍 数据库服务状态")
        print("="*50)
        
        for service, is_healthy in services.items():
            status = "✅ 运行中" if is_healthy else "❌ 未运行"
            print(f"{service:15} : {status}")
        
        print("="*50)
        
        # 显示连接信息
        if services.get("mysql-master"):
            print("🔗 MySQL主库: localhost:3306")
        if services.get("mysql-slave"):
            print("🔗 MySQL从库: localhost:3307")
        if services.get("redis"):
            print("🔗 Redis缓存: localhost:6379")
        if services.get("influxdb"):
            print("🔗 InfluxDB: http://localhost:8086")
        if services.get("mongodb"):
            print("🔗 MongoDB: localhost:27017")
        
        print("\n🌐 管理界面:")
        print("   Adminer (MySQL管理): http://localhost:8080")
        print("   Redis Commander: http://localhost:8081")
        print("   Mongo Express: http://localhost:8082")
        print("   InfluxDB UI: http://localhost:8086")
    
    def initialize_databases(self) -> bool:
        """初始化数据库"""
        logger.info("开始初始化数据库...")
        
        try:
            # 导入数据库初始化模块
            from backend.core.database import initialize_databases
            
            success = initialize_databases()
            
            if success:
                logger.info("✅ 数据库初始化成功")
                return True
            else:
                logger.error("❌ 数据库初始化失败")
                return False
                
        except Exception as e:
            logger.error(f"数据库初始化异常: {e}")
            return False
    
    def show_logs(self, service: Optional[str] = None):
        """显示服务日志"""
        try:
            cmd = [
                "docker-compose", 
                "-f", str(self.docker_compose_file),
                "logs", "-f"
            ]
            
            if service:
                cmd.append(service)
            
            logger.info(f"显示日志: {' '.join(cmd)}")
            subprocess.run(cmd, cwd=self.database_dir)
            
        except KeyboardInterrupt:
            logger.info("日志查看已停止")
        except subprocess.CalledProcessError as e:
            logger.error(f"显示日志失败: {e}")


@click.group()
def cli():
    """RedFire 数据库管理工具"""
    pass


@cli.command()
@click.option('--services', '-s', help='指定要启动的服务 (用逗号分隔)')
@click.option('--wait/--no-wait', default=True, help='是否等待服务启动完成')
@click.option('--init/--no-init', default=True, help='是否进行数据库初始化')
def start(services: Optional[str], wait: bool, init: bool):
    """启动数据库服务"""
    starter = DatabaseStarter()
    
    # 检查Docker
    if not starter.check_docker():
        click.echo("❌ Docker不可用，请先安装Docker和Docker Compose")
        sys.exit(1)
    
    # 创建环境变量文件
    starter.create_env_file()
    
    # 解析服务列表
    service_list = None
    if services:
        service_list = [s.strip() for s in services.split(',')]
    
    # 启动服务
    if starter.start_services(service_list):
        if wait:
            starter.wait_for_services()
        
        starter.show_service_status()
        
        # 数据库初始化
        if init:
            time.sleep(10)  # 等待服务完全启动
            starter.initialize_databases()
        
        click.echo("\n🎉 数据库服务启动完成！")
    else:
        click.echo("❌ 数据库服务启动失败")
        sys.exit(1)


@cli.command()
def stop():
    """停止数据库服务"""
    starter = DatabaseStarter()
    
    if starter.stop_services():
        click.echo("✅ 数据库服务已停止")
    else:
        click.echo("❌ 停止数据库服务失败")
        sys.exit(1)


@cli.command()
def status():
    """查看服务状态"""
    starter = DatabaseStarter()
    starter.show_service_status()


@cli.command()
@click.option('--service', '-s', help='指定服务名称')
def logs(service: Optional[str]):
    """查看服务日志"""
    starter = DatabaseStarter()
    starter.show_logs(service)


@cli.command()
def init():
    """初始化数据库"""
    starter = DatabaseStarter()
    
    if starter.initialize_databases():
        click.echo("✅ 数据库初始化完成")
    else:
        click.echo("❌ 数据库初始化失败")
        sys.exit(1)


@cli.command()
def restart():
    """重启数据库服务"""
    starter = DatabaseStarter()
    
    click.echo("停止服务...")
    starter.stop_services()
    
    time.sleep(5)
    
    click.echo("启动服务...")
    if starter.start_services():
        starter.wait_for_services()
        starter.show_service_status()
        click.echo("✅ 数据库服务重启完成")
    else:
        click.echo("❌ 数据库服务重启失败")
        sys.exit(1)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    cli()
