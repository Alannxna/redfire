#!/usr/bin/env python3
"""
RedFire 前端启动器
专门用于启动前端开发服务器
"""

import os
import sys
import subprocess
import time
import signal
import logging
import argparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class FrontendStarter:
    """前端启动器"""
    
    def __init__(self):
        self.process = None
        self.project_root = Path(__file__).parent.absolute()
        self.frontend_dir = self.project_root / "frontend"
        
    def check_environment(self) -> bool:
        """检查前端环境"""
        logger.info("=" * 40)
        logger.info("RedFire 前端启动器")
        logger.info("=" * 40)
        
        # 检查前端目录
        if not self.frontend_dir.exists():
            logger.error(f"前端目录不存在: {self.frontend_dir}")
            return False
        
        # 检查package.json
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            logger.error(f"package.json不存在: {package_json}")
            return False
        
        # 检查Node.js
        try:
            result = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True,
                shell=True,
                cwd=self.frontend_dir
            )
            if result.returncode == 0:
                node_version = result.stdout.strip()
                logger.info(f"✓ Node.js版本: {node_version}")
            else:
                logger.error("Node.js未安装或不在PATH中")
                return False
        except FileNotFoundError:
            logger.error("Node.js未找到，请先安装Node.js")
            return False
        
        # 检查包管理器
        pnpm_workspace = self.frontend_dir / "pnpm-workspace.yaml"
        if pnpm_workspace.exists():
            try:
                result = subprocess.run(
                    ["pnpm", "--version"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    cwd=self.frontend_dir
                )
                if result.returncode == 0:
                    pnpm_version = result.stdout.strip()
                    logger.info(f"✓ pnpm版本: {pnpm_version}")
                    self.package_manager = "pnpm"
                else:
                    logger.warning("pnpm未安装，将使用npm")
                    self.package_manager = "npm"
            except FileNotFoundError:
                logger.warning("pnpm未找到，将使用npm")
                self.package_manager = "npm"
        else:
            self.package_manager = "npm"
            try:
                result = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    cwd=self.frontend_dir
                )
                if result.returncode == 0:
                    npm_version = result.stdout.strip()
                    logger.info(f"✓ npm版本: {npm_version}")
                else:
                    logger.error("npm未安装")
                    return False
            except FileNotFoundError:
                logger.error("npm未找到")
                return False
        
        logger.info(f"✓ 使用包管理器: {self.package_manager}")
        logger.info(f"✓ 前端目录: {self.frontend_dir}")
        
        return True
    
    def install_dependencies(self) -> bool:
        """安装前端依赖"""
        logger.info("检查并安装前端依赖...")
        
        # 检查node_modules
        node_modules = self.frontend_dir / "node_modules"
        if node_modules.exists():
            logger.info("✓ node_modules已存在，跳过依赖安装")
            return True
        
        try:
            logger.info(f"使用{self.package_manager}安装依赖...")
            
            if self.package_manager == "pnpm":
                cmd = ["pnpm", "install"]
            else:
                cmd = ["npm", "install"]
            
            result = subprocess.run(
                cmd,
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                logger.info("✓ 前端依赖安装成功")
                return True
            else:
                logger.error(f"✗ 前端依赖安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"安装前端依赖时发生错误: {e}")
            return False
    
    def start_dev_server(self, port: int = 3000, host: str = "127.0.0.1") -> bool:
        """启动开发服务器"""
        logger.info("启动前端开发服务器...")
        
        try:
            # 检查是否为turbo monorepo
            turbo_json = self.frontend_dir / "turbo.json"
            if turbo_json.exists():
                logger.info("检测到Turbo monorepo，启动web-app...")
                if self.package_manager == "pnpm":
                    cmd = ["pnpm", "dev:web"]
                else:
                    cmd = ["npm", "run", "dev:web"]
            else:
                # 传统的单应用项目
                if self.package_manager == "pnpm":
                    cmd = ["pnpm", "dev", "--port", str(port), "--host", host]
                else:
                    cmd = ["npm", "run", "dev", "--", "--port", str(port), "--host", host]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                shell=True
            )
            
            logger.info(f"✓ 前端开发服务器已启动 (PID: {self.process.pid})")
            logger.info(f"✓ 前端地址: http://{host}:{port}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ 启动前端服务器失败: {e}")
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
                    # 过滤一些冗余的输出
                    line = output.strip()
                    if line and not line.startswith('['):
                        print(line)
        except KeyboardInterrupt:
            pass
    
    def stop_service(self):
        """停止服务"""
        if self.process:
            logger.info("正在停止前端服务器...")
            try:
                if sys.platform == "win32":
                    self.process.terminate()
                else:
                    self.process.send_signal(signal.SIGTERM)
                
                # 等待进程结束
                try:
                    self.process.wait(timeout=10)
                    logger.info("✓ 前端服务器已停止")
                except subprocess.TimeoutExpired:
                    logger.warning("强制停止前端服务器...")
                    self.process.kill()
                    self.process.wait()
                    
            except Exception as e:
                logger.error(f"停止服务时发生错误: {e}")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info("\n收到停止信号")
        self.stop_service()
        sys.exit(0)
    
    def run(self, args):
        """运行前端启动器"""
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 检查环境
        if not self.check_environment():
            logger.error("前端环境检查失败")
            return False
        
        # 安装依赖
        if not args.skip_install:
            if not self.install_dependencies():
                logger.error("前端依赖安装失败")
                return False
        
        # 启动开发服务器
        if not self.start_dev_server(args.port, args.host):
            logger.error("前端服务器启动失败")
            return False
        
        # 打开浏览器
        if not args.no_browser:
            try:
                import webbrowser
                time.sleep(3)  # 等待服务器启动
                webbrowser.open(f"http://{args.host}:{args.port}")
                logger.info("✓ 已打开浏览器")
            except Exception as e:
                logger.warning(f"无法打开浏览器: {e}")
        
        logger.info("=" * 40)
        logger.info("前端开发服务器启动成功！")
        logger.info("按 Ctrl+C 停止服务")
        logger.info("=" * 40)
        
        # 监控进程
        try:
            self.monitor_process()
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RedFire 前端启动器")
    parser.add_argument("--host", default="127.0.0.1", help="服务主机地址")
    parser.add_argument("--port", type=int, default=3000, help="服务端口")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--skip-install", action="store_true", help="跳过依赖安装")
    
    args = parser.parse_args()
    
    starter = FrontendStarter()
    success = starter.run(args)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
