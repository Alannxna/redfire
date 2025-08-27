#!/usr/bin/env python3
"""
RedFire 后端服务器启动脚本
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """主函数"""
    print("🔥 RedFire 后端服务启动脚本")
    print("=" * 50)
    
    # 确保在正确的目录
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查依赖
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ 核心依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 启动服务器
    try:
        print("\n🚀 启动 FastAPI 服务器...")
        print("📍 服务地址: http://127.0.0.1:8000")
        print("📚 API文档: http://127.0.0.1:8000/api/docs")
        print("🔄 热重载已启用")
        print("\n按 Ctrl+C 停止服务器\n")
        
        # 使用uvicorn启动
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
