@echo off
chcp 65001 >nul
title RedFire 简单启动器 - 仅后端

echo.
echo ========================================
echo RedFire 简单启动器 - 仅后端
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或不在PATH中
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查当前目录是否正确
if not exist "start_simple.py" (
    echo [错误] 请在项目根目录运行此脚本
    echo 当前目录: %CD%
    pause
    exit /b 1
)

echo [信息] 启动RedFire后端服务...
echo.

REM 解析命令行参数
set "ARGS="
:parse_args
if "%~1"=="" goto run_python
set "ARGS=%ARGS% %1"
shift
goto parse_args

:run_python
REM 运行Python启动脚本
python start_simple.py %ARGS%

if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败，错误代码: %errorlevel%
    echo.
    echo 可能的解决方案:
    echo 1. 检查Python依赖: pip install -r backend/requirements.txt
    echo 2. 检查backend/main.py是否存在
    echo 3. 检查Python路径配置
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [信息] 程序已退出
pause
