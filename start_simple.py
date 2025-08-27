#!/usr/bin/env python3
"""
RedFire 简单启动器
仅启动后端服务的轻量级脚本
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SimpleStarter:
    """简单启动器"""
    
    def __init__(self):
        self.process = None
        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "backend"
        
    def check_backend(self) -> bool:
        """检查后端环境"""
        logger.info("=" * 40)
        logger.info("RedFire 简单启动器")
        logger.info("=" * 40)
        
        # 检查Python版本
        logger.info(f"Python版本: {sys.version}")
        
        # 检查main.py是否存在
        main_file = self.backend_dir / "main.py"
        if not main_file.exists():
            logger.error(f"后端主程序不存在: {main_file}")
            return False
            
        logger.info(f"后端目录: {self.backend_dir}")
        return True
    
    def test_imports(self) -> bool:
        """测试关键模块导入"""
        logger.info("测试后端模块导入...")
        
        # 添加backend目录到Python路径
        sys.path.insert(0, str(self.backend_dir))
        
        try:
            # 测试主程序模块
            import main
            logger.info("✓ 主程序模块导入成功")
            
            # 测试交易引擎模块
            from core.tradingEngine import mainEngine
            logger.info("✓ 交易引擎模块导入成功")
            
            return True
        except ImportError as e:
            logger.error(f"✗ 模块导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ 测试导入时发生错误: {e}")
            return False
    
    def start_backend(self, host: str = "127.0.0.1", port: int = 8000) -> bool:
        """启动后端服务"""
        logger.info("启动后端服务...")
        
        try:
            cmd = [sys.executable, "main.py"]
            
            # 添加主机和端口参数（如果main.py支持）
            cmd.extend(["--host", host, "--port", str(port)])
            
            self.process = subprocess.Popen(
                cmd,
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            logger.info(f"✓ 后端服务已启动 (PID: {self.process.pid})")
            logger.info(f"✓ 服务地址: http://{host}:{port}")
            logger.info(f"✓ API文档: http://{host}:{port}/docs")
            logger.info(f"✓ 健康检查: http://{host}:{port}/health")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ 启动后端服务失败: {e}")
            return False
    
    def monitor_process(self):
        """监控进程输出"""
        if not self.process:
            return
            
        try:
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    print(output.strip())
        except KeyboardInterrupt:
            pass
    
    def stop_service(self):
        """停止服务"""
        if self.process:
            logger.info("正在停止后端服务...")
            try:
                if sys.platform == "win32":
                    self.process.terminate()
                else:
                    self.process.send_signal(signal.SIGTERM)
                
                # 等待进程结束
                try:
                    self.process.wait(timeout=10)
                    logger.info("✓ 后端服务已停止")
                except subprocess.TimeoutExpired:
                    logger.warning("强制停止后端服务...")
                    self.process.kill()
                    self.process.wait()
                    
            except Exception as e:
                logger.error(f"停止服务时发生错误: {e}")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info("\n收到停止信号")
        self.stop_service()
        sys.exit(0)
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """运行启动器"""
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 检查后端环境
        if not self.check_backend():
            logger.error("后端环境检查失败")
            return False
        
        # 测试模块导入
        if not self.test_imports():
            logger.error("模块导入测试失败")
            return False
        
        # 启动后端
        if not self.start_backend(host, port):
            logger.error("后端启动失败")
            return False
        
        logger.info("=" * 40)
        logger.info("服务启动成功！按 Ctrl+C 停止服务")
        logger.info("=" * 40)
        
        # 监控进程
        try:
            self.monitor_process()
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RedFire 简单启动器")
    parser.add_argument("--host", default="127.0.0.1", help="服务主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    
    args = parser.parse_args()
    
    starter = SimpleStarter()
    success = starter.run(args.host, args.port)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
