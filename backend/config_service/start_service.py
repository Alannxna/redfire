#!/usr/bin/env python3
# 🚀 RedFire配置管理服务启动脚本

"""
RedFire配置管理服务启动脚本

简单的启动脚本，用于在开发和测试环境快速启动配置服务。

使用方法:
    python start_service.py                    # 使用默认配置启动
    python start_service.py --config dev.yaml # 使用指定配置文件
    python start_service.py --help            # 查看帮助信息
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.config_service import quick_start

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RedFire配置管理服务启动脚本")
    parser.add_argument(
        "--config", "-c",
        default="backend/config_service/config/development.yaml",
        help="配置文件路径 (默认: development.yaml)"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="监听主机 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8001,
        help="监听端口 (默认: 8001)"
    )
    parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="启用热重载 (仅开发环境)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)"
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    print("🔧 RedFire配置管理服务")
    print("=" * 50)
    print(f"📄 配置文件: {args.config}")
    print(f"🌐 服务地址: http://{args.host}:{args.port}")
    print(f"🔄 热重载: {args.reload}")
    print(f"📝 日志级别: {args.log_level}")
    print("=" * 50)
    
    try:
        # 检查配置文件是否存在
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"⚠️ 配置文件不存在: {config_path}")
            print("将使用环境变量或默认配置")
            args.config = None
        
        # 启动服务
        await quick_start(
            config_file=args.config,
            host=args.host,
            port=args.port,
            reload=args.reload
        )
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
