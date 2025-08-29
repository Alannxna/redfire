@echo off
chcp 65001 >nul
title VnPy Web 项目介绍服务器

echo.
echo ========================================
echo 🔥 VnPy Web 量化交易系统
echo ========================================
echo.
echo 正在启动项目介绍服务器...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python环境
    echo 💡 请先安装Python 3.8+
    pause
    exit /b 1
)

REM 切换到项目根目录
cd /d "%~dp0..\.."

REM 启动服务器
python tools/scripts/intro_server.py

echo.
echo 服务器已关闭
pause
