#!/usr/bin/env python3
"""
RedFire 量化交易平台启动器
完整的前后端启动脚本
"""

import os
import sys
import subprocess
import time
import signal
import threading
import logging
import argparse
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class RedfireStarter:
    """RedFire 启动器主类"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.running = False
        
    def check_environment(self) -> bool:
        """检查运行环境"""
        logger.info("=" * 50)
        logger.info("RedFire 量化交易平台启动器")
        logger.info("=" * 50)
        
        # 检查Python版本
        python_version = sys.version
        logger.info(f"Python版本: {python_version}")
        
        # 检查Node.js版本
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
                logger.info(f"Node.js版本: {node_version}")
            else:
                logger.warning("Node.js未安装或不在PATH中")
                return False
        except FileNotFoundError:
            logger.error("Node.js未找到，请先安装Node.js")
            return False
            
        # 检查包管理器
        self.has_npm = False
        self.has_pnpm = False
        
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
                logger.info(f"npm版本: {npm_version}")
                self.has_npm = True
        except FileNotFoundError:
            logger.warning("npm未找到")
            
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
                logger.info(f"pnpm版本: {pnpm_version}")
                self.has_pnpm = True
        except FileNotFoundError:
            logger.warning("pnpm未找到")
            
        if not self.has_npm and not self.has_pnpm:
            logger.warning("未找到可用的包管理器，前端功能将不可用")
            
        return True
    
    def install_python_dependencies(self) -> bool:
        """安装Python依赖"""
        logger.info("检查Python依赖...")
        
        requirements_file = self.backend_dir / "requirements.txt"
        if not requirements_file.exists():
            logger.warning("requirements.txt不存在，跳过Python依赖安装")
            return True
            
        try:
            logger.info("安装Python依赖包...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], cwd=self.backend_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Python依赖安装成功")
                return True
            else:
                logger.error(f"Python依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"安装Python依赖时发生错误: {e}")
            return False
    
    def install_frontend_dependencies(self) -> bool:
        """安装前端依赖"""
        logger.info("安装前端依赖...")
        
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            logger.warning("frontend/package.json不存在，跳过前端依赖安装")
            return True
        
        # 检查是否有可用的包管理器
        if not hasattr(self, 'has_npm') or not hasattr(self, 'has_pnpm'):
            logger.warning("包管理器状态未知，跳过前端依赖安装")
            return True
            
        if not self.has_npm and not self.has_pnpm:
            logger.warning("没有可用的包管理器，跳过前端依赖安装")
            return True
            
        try:
            # 优先使用pnpm（如果有pnpm-workspace.yaml）
            pnpm_workspace = self.frontend_dir / "pnpm-workspace.yaml"
            if pnpm_workspace.exists() and self.has_pnpm:
                logger.info("检测到pnpm workspace，使用pnpm安装依赖...")
                cmd = ["pnpm", "install"]
            elif self.has_npm:
                logger.info("使用npm安装前端依赖...")
                cmd = ["npm", "install"]
            elif self.has_pnpm:
                logger.info("使用pnpm安装前端依赖...")
                cmd = ["pnpm", "install"]
            else:
                logger.warning("没有可用的包管理器")
                return True
                
            result = subprocess.run(
                cmd,
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                logger.info("前端依赖安装成功")
                return True
            else:
                logger.error(f"前端依赖安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"安装前端依赖时发生错误: {e}")
            logger.error("前端依赖安装失败")
            return False
    
    def test_backend_import(self) -> bool:
        """测试后端模块导入"""
        logger.info("测试后端模块导入...")
        
        # 添加backend目录到Python路径
        sys.path.insert(0, str(self.backend_dir))
        
        try:
            # 测试主程序模块
            import main
            logger.info("主程序模块导入成功")
            
            # 测试交易引擎模块
            from core.tradingEngine import mainEngine
            logger.info("交易引擎模块导入成功")
            
            return True
        except ImportError as e:
            logger.error(f"模块导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"测试导入时发生错误: {e}")
            return False
    
    def start_backend(self, host: str = "127.0.0.1", port: int = 8000) -> bool:
        """启动后端服务"""
        logger.info("启动后端服务...")
        
        try:
            # 后端main.py不接受命令行参数，使用默认配置
            cmd = [sys.executable, "main.py"]
            
            process = subprocess.Popen(
                cmd,
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes["backend"] = process
            logger.info(f"后端服务已启动 (PID: {process.pid})")
            logger.info(f"后端地址: http://{host}:{port}")
            
            return True
            
        except Exception as e:
            logger.error(f"启动后端服务失败: {e}")
            return False
    
    def start_frontend(self, port: int = 3000) -> bool:
        """启动前端服务"""
        logger.info("启动前端服务...")
        
        # 检查是否有可用的包管理器
        if not hasattr(self, 'has_npm') or not hasattr(self, 'has_pnpm'):
            logger.error("包管理器状态未知，无法启动前端服务")
            return False
            
        if not self.has_npm and not self.has_pnpm:
            logger.error("没有可用的包管理器，无法启动前端服务")
            return False
        
        try:
            # 检查是否为turbo monorepo
            turbo_json = self.frontend_dir / "turbo.json"
            if turbo_json.exists():
                logger.info("检测到Turbo monorepo，启动web-app...")
                if self.has_pnpm:
                    cmd = ["pnpm", "dev:web"]
                elif self.has_npm:
                    cmd = ["npm", "run", "dev:web"]
                else:
                    logger.error("没有可用的包管理器")
                    return False
            else:
                # 传统的单应用项目
                if self.has_pnpm:
                    cmd = ["pnpm", "dev", "--port", str(port)]
                elif self.has_npm:
                    cmd = ["npm", "run", "dev", "--", "--port", str(port)]
                else:
                    logger.error("没有可用的包管理器")
                    return False
            
            process = subprocess.Popen(
                cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            self.processes["frontend"] = process
            logger.info(f"前端服务已启动 (PID: {process.pid})")
            logger.info(f"前端地址: http://127.0.0.1:{port}")
            
            return True
            
        except Exception as e:
            logger.error(f"启动前端服务失败: {e}")
            return False
    
    def wait_for_service(self, url: str, timeout: int = 90) -> bool:
        """等待服务就绪"""
        import urllib.request
        import urllib.error
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                urllib.request.urlopen(url, timeout=5)
                return True
            except urllib.error.URLError:
                time.sleep(2)
                continue
        return False
    
    def monitor_processes(self):
        """监控进程状态"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    logger.warning(f"{name}服务意外停止")
                    del self.processes[name]
            time.sleep(5)
    
    def stop_services(self):
        """停止所有服务"""
        logger.info("正在停止服务...")
        
        for name, process in self.processes.items():
            try:
                logger.info(f"停止{name}服务...")
                if sys.platform == "win32":
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
                
                # 等待进程结束
                try:
                    process.wait(timeout=10)
                    logger.info(f"{name}服务已停止")
                except subprocess.TimeoutExpired:
                    logger.warning(f"强制停止{name}服务...")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                logger.error(f"停止{name}服务时发生错误: {e}")
        
        self.processes.clear()
        self.running = False
        logger.info("所有服务已停止")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info("收到停止信号")
        self.stop_services()
        sys.exit(0)
    
    def run(self, args):
        """主运行方法"""
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 检查环境
        if not self.check_environment():
            logger.error("环境检查失败")
            return False
        
        # 检查是否强制仅后端模式
        force_backend_only = args.backend_only or (not self.has_npm and not self.has_pnpm)
        if force_backend_only and not args.backend_only:
            logger.warning("由于缺少前端环境，自动切换到仅后端模式")
        
        # 安装依赖
        if not args.skip_deps:
            if not self.install_python_dependencies():
                logger.error("Python依赖安装失败")
                return False
                
            if not force_backend_only:
                if not self.install_frontend_dependencies():
                    logger.warning("前端依赖安装失败，将仅启动后端服务")
                    force_backend_only = True
        
        # 测试后端导入
        if not self.test_backend_import():
            logger.error("后端模块测试失败")
            return False
        
        # 启动后端
        if not self.start_backend(args.host, args.port):
            logger.error("后端启动失败")
            return False
        
        # 启动前端（如果不是仅后端模式）
        if not force_backend_only:
            if not self.start_frontend(args.frontend_port):
                logger.warning("前端启动失败，仅运行后端服务")
                force_backend_only = True
        
        # 等待服务就绪
        backend_url = f"http://{args.host}:{args.port}/health"
        if not self.wait_for_service(backend_url):
            logger.warning("等待后端服务就绪超时")
        
        self.running = True
        
        # 启动进程监控
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # 打开浏览器
        if not args.no_browser and not force_backend_only:
            try:
                import webbrowser
                webbrowser.open(f"http://127.0.0.1:{args.frontend_port}")
            except Exception:
                pass
        elif not args.no_browser and force_backend_only:
            # 如果只有后端，打开后端文档页面
            try:
                import webbrowser
                webbrowser.open(f"http://{args.host}:{args.port}/docs")
            except Exception:
                pass
        
        logger.info("RedFire 量化交易平台已启动")
        logger.info("按 Ctrl+C 停止服务")
        
        # 等待停止信号
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RedFire 量化交易平台启动器")
    parser.add_argument("--host", default="127.0.0.1", help="后端服务主机地址")
    parser.add_argument("--port", type=int, default=8000, help="后端服务端口")
    parser.add_argument("--frontend-port", type=int, default=3000, help="前端服务端口")
    parser.add_argument("--backend-only", action="store_true", help="仅启动后端服务")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")
    
    args = parser.parse_args()
    
    starter = RedfireStarter()
    success = starter.run(args)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()