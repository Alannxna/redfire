#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VnPy Web 项目介绍服务器
在 http://localhost:9999 提供项目说明和API文档
"""

import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import threading
import time

class VnPyIntroHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        # 设置服务目录为当前目录
        super().__init__(*args, directory=str(Path.cwd()), **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        # 根路径重定向到项目说明页面
        if self.path == '/':
            self.path = '/docs/web-intro/项目整体说明.html'
        elif self.path == '/api':
            self.path = '/docs/api/api-docs.html'
        elif self.path == '/docs':
            self.path = '/docs/api/api-docs.html'
            
        # 处理中文文件名编码
        try:
            return super().do_GET()
        except Exception as e:
            print(f"请求处理错误: {e}")
            self.send_error(404, "页面未找到")
    
    def end_headers(self):
        """添加自定义响应头"""
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def check_html_files():
    """检查HTML文件是否存在"""
    files_to_check = [
        "docs/web-intro/项目整体说明.html",
        "docs/api/api-docs.html"
    ]
    
    missing_files = []
    for file in files_to_check:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少以下文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ 所有HTML文件已就绪")
    return True

def start_server(port=9999, auto_open=True):
    """启动HTTP服务器"""
    
    print("🚀 VnPy Web 项目介绍服务器启动中...")
    print(f"📁 服务目录: {Path.cwd()}")
    
    # 检查HTML文件
    if not check_html_files():
        print("❌ 请先确保HTML文件存在")
        return False
    
    try:
        # 创建服务器
        server = HTTPServer(('localhost', port), VnPyIntroHandler)
        
        print(f"✅ 服务器启动成功!")
        print(f"🌐 访问地址:")
        print(f"   - 项目说明: http://localhost:{port}/")
        print(f"   - API文档:  http://localhost:{port}/api")
        print(f"   - 直接访问: http://localhost:{port}/api-docs.html")
        print("")
        print("💡 快捷操作:")
        print("   - 查看项目整体说明")
        print("   - 查看API接口文档")
        print("")
        print("按 Ctrl+C 停止服务器")
        
        # 自动打开浏览器
        if auto_open:
            def open_browser():
                time.sleep(1)  # 等待服务器启动
                try:
                    webbrowser.open(f'http://localhost:{port}/')
                    print("🌐 已自动打开浏览器")
                except Exception as e:
                    print(f"⚠️  无法自动打开浏览器: {e}")
            
            threading.Thread(target=open_browser, daemon=True).start()
        
        # 启动服务器
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🔄 正在关闭服务器...")
        server.server_close()
        print("✅ 服务器已关闭")
        return True
        
    except OSError as e:
        if e.errno == 10048:  # Windows: 端口已被占用
            print(f"❌ 端口 {port} 已被占用，请尝试其他端口")
            print(f"💡 可以使用: python intro_server.py --port 9998")
        else:
            print(f"❌ 服务器启动失败: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def create_desktop_shortcut():
    """创建桌面快捷方式（Windows）"""
    try:
        if sys.platform == "win32":
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "VnPy项目说明.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{__file__}"'
            shortcut.WorkingDirectory = str(Path.cwd())
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            print(f"✅ 已创建桌面快捷方式: {shortcut_path}")
            
    except ImportError:
        print("💡 提示: 安装 pywin32 和 winshell 可创建桌面快捷方式")
    except Exception as e:
        print(f"⚠️  创建快捷方式失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VnPy Web 项目介绍服务器')
    parser.add_argument('--port', '-p', type=int, default=9999, 
                       help='服务端口 (默认: 9999)')
    parser.add_argument('--no-browser', action='store_true', 
                       help='不自动打开浏览器')
    parser.add_argument('--create-shortcut', action='store_true',
                       help='创建桌面快捷方式')
    
    args = parser.parse_args()
    
    if args.create_shortcut:
        create_desktop_shortcut()
        return
    
    # 显示欢迎信息
    print("=" * 60)
    print("🔥 VnPy Web 量化交易系统 - 项目介绍服务器")
    print("=" * 60)
    
    success = start_server(
        port=args.port, 
        auto_open=not args.no_browser
    )
    
    if success:
        print("\n🎉 感谢使用 VnPy Web 量化交易系统!")
    else:
        print("\n❌ 服务器启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
