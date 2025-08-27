#!/usr/bin/env python3
"""
RedFire 应用启动脚本
简化版本 - 快速启动整个应用栈
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

class AppStarter:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.processes = []
        self.running = True
        
    def print_banner(self):
        print("🚀 RedFire 应用启动器")
        print()
        
    def check_dependencies(self):
        """检查基本依赖"""
        print("📋 检查依赖...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("❌ 需要Python 3.8或更高版本")
            return False
            
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode != 0:
                print("❌ Node.js未安装或不在PATH中")
                return False
            print(f"✅ Node.js: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Node.js未安装")
            return False
            
        # 检查npm
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode != 0:
                print("❌ npm未安装")
                return False
            print(f"✅ npm: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ npm未安装")
            return False
            
        return True
        
    def install_backend_deps(self):
        """安装后端依赖"""
        print("📦 安装后端依赖...")
        backend_dir = self.root_dir / "backend"
        
        if not (backend_dir / "requirements.txt").exists():
            print("⚠️  后端requirements.txt不存在，跳过依赖安装")
            return True
            
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", 
                          str(backend_dir / "requirements.txt")], 
                          check=True, cwd=backend_dir)
            print("✅ 后端依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 后端依赖安装失败: {e}")
            return False
            
    def install_frontend_deps(self):
        """安装前端依赖"""
        print("📦 安装前端依赖...")
        frontend_dir = self.root_dir / "frontend"
        
        if not (frontend_dir / "package.json").exists():
            print("⚠️  前端package.json不存在，跳过依赖安装")
            return True
            
        try:
            subprocess.run(["npm", "install"], check=True, cwd=frontend_dir, shell=True)
            print("✅ 前端依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 前端依赖安装失败: {e}")
            return False
            
    def start_backend(self):
        """启动后端服务"""
        print("🔧 启动后端服务...")
        backend_dir = self.root_dir / "backend"
        
        # 查找主应用文件
        main_files = ["main.py", "app.py", "server.py"]
        main_file = None
        
        for file in main_files:
            if (backend_dir / file).exists():
                main_file = file
                break
                
        if not main_file:
            print("❌ 找不到后端主文件")
            return False
            
        try:
            # 启动后端服务
            process = subprocess.Popen(
                [sys.executable, main_file],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(("后端", process))
            print(f"✅ 后端服务启动中 (PID: {process.pid})")
            
            # 等待服务启动
            time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ 后端启动失败: {e}")
            return False
            
    def start_frontend(self):
        """启动前端服务"""
        print("🎨 启动前端服务...")
        frontend_dir = self.root_dir / "frontend"
        
        # 查找web-app目录
        web_app_dir = frontend_dir / "apps" / "web-app"
        if not web_app_dir.exists():
            web_app_dir = frontend_dir
            
        if not (web_app_dir / "package.json").exists():
            print("❌ 找不到前端package.json")
            return False
            
        try:
            # 启动前端开发服务器
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=web_app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                shell=True
            )
            
            self.processes.append(("前端", process))
            print(f"✅ 前端服务启动中 (PID: {process.pid})")
            
            return True
            
        except Exception as e:
            print(f"❌ 前端启动失败: {e}")
            return False
            
    def monitor_processes(self):
        """监控进程输出"""
        def monitor_output(process, name):
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        print(f"[{name}] {line.rstrip()}")
            except Exception as e:
                print(f"[{name}] 监控错误: {e}")
                
        # 为每个进程启动监控线程
        for name, process in self.processes:
            thread = threading.Thread(
                target=monitor_output, 
                args=(process, name),
                daemon=True
            )
            thread.start()
            
    def wait_for_exit(self):
        """等待退出信号"""
        def signal_handler(signum, frame):
            print("\n🛑 收到退出信号，正在关闭服务...")
            self.running = False
            self.cleanup()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                time.sleep(1)
                # 检查进程是否还在运行
                for name, process in self.processes[:]:
                    if process.poll() is not None:
                        print(f"⚠️  {name}服务已停止")
                        self.processes.remove((name, process))
                        
        except KeyboardInterrupt:
            print("\n🛑 用户中断，正在关闭服务...")
            self.cleanup()
            
    def cleanup(self):
        """清理进程"""
        print("🧹 清理进程...")
        for name, process in self.processes:
            try:
                print(f"🛑 停止{name}服务...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"⚠️  {name}服务未响应，强制终止...")
                process.kill()
            except Exception as e:
                print(f"❌ 停止{name}服务时出错: {e}")
                
    def run(self):
        """运行启动器"""
        self.print_banner()
        
        # 检查依赖
        if not self.check_dependencies():
            print("❌ 依赖检查失败")
            return False
            
        # 安装依赖
        if not self.install_backend_deps():
            print("⚠️  后端依赖安装失败，继续尝试启动...")
            
        if not self.install_frontend_deps():
            print("⚠️  前端依赖安装失败，继续尝试启动...")
            
        # 启动服务
        backend_ok = self.start_backend()
        frontend_ok = self.start_frontend()
        
        if not backend_ok and not frontend_ok:
            print("❌ 所有服务启动失败")
            return False
            
        # 启动监控
        self.monitor_processes()
        
        print("\n🎉 应用启动完成!")
        print("📱 前端地址: http://localhost:3000")
        print("🔧 后端地址: http://localhost:8000")
        print("⏹️  按 Ctrl+C 停止所有服务")
        print()
        
        # 等待退出
        self.wait_for_exit()
        
        return True

if __name__ == "__main__":
    starter = AppStarter()
    success = starter.run()
    sys.exit(0 if success else 1)
