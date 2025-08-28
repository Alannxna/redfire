# 🚀 RedFire外部配置管理服务 - 主入口
# 简单直接的服务启动，完全舍弃DDD架构复杂性

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional
import uvicorn
import click

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.config_service.core.config_manager import initialize_config, config_manager
from backend.config_service.api.config_api import create_app
from backend.config_service.models.config_models import Environment

# =============================================================================
# 日志配置
# =============================================================================

def setup_logging(log_level: str = "INFO", log_format: Optional[str] = None):
    """配置日志系统"""
    
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("config_service.log", encoding="utf-8")
        ]
    )
    
    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

# =============================================================================
# 服务启动函数
# =============================================================================

async def initialize_service(
    config_file: Optional[str] = None,
    environment: Optional[str] = None
) -> None:
    """初始化配置服务"""
    
    logger = logging.getLogger(__name__)
    logger.info("🔧 初始化RedFire配置管理服务...")
    
    try:
        # 1. 确定配置文件路径
        if not config_file:
            # 根据环境确定默认配置文件
            env = environment or os.getenv("APP_ENV", "development")
            config_file = f"config/{env}.yaml"
            
            # 检查配置文件是否存在
            if not Path(config_file).exists():
                logger.warning(f"⚠️ 配置文件不存在: {config_file}，将使用环境变量")
                config_file = None
        
        # 2. 初始化配置管理器
        config = await initialize_config(
            config_file=config_file,
            enable_file_watching=True,
            enable_cache=True
        )
        
        logger.info("✅ 配置管理器初始化成功")
        logger.info(f"📊 配置环境: {config.environment}")
        logger.info(f"🏠 服务地址: {config.host}:{config.port}")
        logger.info(f"🔧 调试模式: {config.debug}")
        logger.info(f"📝 日志级别: {config.log_level}")
        
        # 3. 配置变更回调
        def on_config_change(new_config):
            logger.info(f"📢 配置已更新: {new_config.app_name} v{new_config.app_version}")
        
        config_manager.add_change_callback(on_config_change)
        
        return config
        
    except Exception as e:
        logger.error(f"❌ 配置服务初始化失败: {e}")
        raise

def create_configured_app():
    """创建已配置的FastAPI应用"""
    
    # 创建FastAPI应用
    app = create_app()
    
    # 获取配置
    if config_manager.is_initialized:
        config = config_manager.get_config()
        
        # 更新应用配置
        app.title = config.app_name
        app.version = config.app_version
        app.debug = config.debug
    
    return app

async def run_service(
    host: str = "0.0.0.0",
    port: int = 8001,
    workers: int = 1,
    reload: bool = False,
    access_log: bool = True
) -> None:
    """运行配置服务"""
    
    logger = logging.getLogger(__name__)
    
    try:
        # 创建配置的应用
        app = create_configured_app()
        
        # 获取配置
        if config_manager.is_initialized:
            config = config_manager.get_config()
            host = config.host
            port = config.port
            workers = config.workers
            reload = config.debug
        
        logger.info(f"🚀 启动配置管理服务...")
        logger.info(f"🌐 服务地址: http://{host}:{port}")
        logger.info(f"👥 工作进程数: {workers}")
        logger.info(f"🔄 热重载: {reload}")
        logger.info(f"📚 API文档: http://{host}:{port}/docs")
        
        # 配置uvicorn
        config_uvicorn = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            workers=workers if not reload else 1,  # 热重载模式只能单进程
            reload=reload,
            access_log=access_log,
            log_level="info"
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        # 启动服务器
        await server.serve()
        
    except Exception as e:
        logger.error(f"❌ 配置服务启动失败: {e}")
        raise
    
    finally:
        # 清理资源
        logger.info("🛑 正在关闭配置管理服务...")
        await config_manager.shutdown()
        logger.info("✅ 配置管理服务已关闭")

# =============================================================================
# CLI命令行接口
# =============================================================================

@click.group()
@click.option('--log-level', default='INFO', help='日志级别')
@click.option('--log-format', default=None, help='日志格式')
def cli(log_level: str, log_format: Optional[str]):
    """RedFire配置管理服务命令行工具"""
    setup_logging(log_level, log_format)

@cli.command()
@click.option('--config-file', '-c', default=None, help='配置文件路径')
@click.option('--environment', '-e', default=None, help='运行环境')
@click.option('--host', default='0.0.0.0', help='监听主机')
@click.option('--port', default=8001, help='监听端口')
@click.option('--workers', default=1, help='工作进程数')
@click.option('--reload', is_flag=True, help='启用热重载')
@click.option('--no-access-log', is_flag=True, help='禁用访问日志')
def run(
    config_file: Optional[str],
    environment: Optional[str],
    host: str,
    port: int,
    workers: int,
    reload: bool,
    no_access_log: bool
):
    """运行配置管理服务"""
    
    async def main():
        # 初始化服务
        await initialize_service(config_file, environment)
        
        # 运行服务
        await run_service(
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            access_log=not no_access_log
        )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        click.echo("🛑 服务已停止")
    except Exception as e:
        click.echo(f"❌ 服务运行失败: {e}")
        sys.exit(1)

@cli.command()
@click.option('--config-file', '-c', required=True, help='配置文件路径')
def validate(config_file: str):
    """验证配置文件"""
    
    async def main():
        try:
            click.echo(f"🔍 验证配置文件: {config_file}")
            
            # 初始化配置
            config = await initialize_config(
                config_file=config_file,
                enable_file_watching=False,
                enable_cache=False
            )
            
            click.echo("✅ 配置文件验证通过")
            click.echo(f"📊 应用名称: {config.app_name}")
            click.echo(f"📊 应用版本: {config.app_version}")
            click.echo(f"📊 运行环境: {config.environment}")
            click.echo(f"📊 调试模式: {config.debug}")
            
        except Exception as e:
            click.echo(f"❌ 配置文件验证失败: {e}")
            sys.exit(1)
        
        finally:
            await config_manager.shutdown()
    
    asyncio.run(main())

@cli.command()
@click.option('--output', '-o', default='config_template.yaml', help='输出文件路径')
@click.option('--format', default='yaml', help='输出格式 (yaml/json)')
def template(output: str, format: str):
    """生成配置文件模板"""
    
    try:
        from backend.config_service.models.config_models import export_config_template
        
        click.echo(f"📄 生成配置模板: {output}")
        
        export_config_template(output, format)
        
        click.echo("✅ 配置模板生成成功")
        click.echo(f"📄 模板文件: {output}")
        
    except Exception as e:
        click.echo(f"❌ 配置模板生成失败: {e}")
        sys.exit(1)

@cli.command()
@click.option('--config-file', '-c', default=None, help='配置文件路径')
def info(config_file: Optional[str]):
    """显示配置信息"""
    
    async def main():
        try:
            # 初始化配置
            config = await initialize_service(config_file)
            
            # 显示配置信息
            click.echo("📊 配置管理服务信息:")
            click.echo(f"  应用名称: {config.app_name}")
            click.echo(f"  应用版本: {config.app_version}")
            click.echo(f"  运行环境: {config.environment}")
            click.echo(f"  服务地址: {config.host}:{config.port}")
            click.echo(f"  工作进程: {config.workers}")
            click.echo(f"  调试模式: {config.debug}")
            click.echo(f"  日志级别: {config.log_level}")
            
            # 显示管理器信息
            manager_info = config_manager.get_config_info()
            click.echo("\n🔧 配置管理器信息:")
            click.echo(f"  初始化状态: {manager_info['initialized']}")
            click.echo(f"  配置源: {manager_info['config_sources']}")
            click.echo(f"  文件监听: {manager_info['file_watching_enabled']}")
            click.echo(f"  缓存启用: {manager_info['cache_enabled']}")
            click.echo(f"  变更回调数: {manager_info['change_callbacks_count']}")
            
        except Exception as e:
            click.echo(f"❌ 获取配置信息失败: {e}")
            sys.exit(1)
        
        finally:
            await config_manager.shutdown()
    
    asyncio.run(main())

@cli.command()
def health():
    """检查服务健康状态"""
    
    import aiohttp
    import json
    
    async def main():
        try:
            # 尝试连接服务
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8001/health', timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        click.echo("✅ 配置管理服务运行正常")
                        click.echo(f"📊 健康状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    else:
                        click.echo(f"⚠️ 服务响应异常: HTTP {response.status}")
                        
        except aiohttp.ClientError as e:
            click.echo(f"❌ 无法连接到配置管理服务: {e}")
            click.echo("💡 请确保服务正在运行在 http://localhost:8001")
            sys.exit(1)
        
        except Exception as e:
            click.echo(f"❌ 健康检查失败: {e}")
            sys.exit(1)
    
    asyncio.run(main())

# =============================================================================
# 直接运行支持
# =============================================================================

if __name__ == "__main__":
    # 支持直接运行
    import sys
    
    if len(sys.argv) == 1:
        # 无参数时默认运行服务
        async def main():
            setup_logging()
            await initialize_service()
            await run_service()
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("🛑 服务已停止")
        except Exception as e:
            print(f"❌ 服务运行失败: {e}")
            sys.exit(1)
    else:
        # 有参数时使用CLI
        cli()
