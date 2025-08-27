@echo off
chcp 65001 >nul
title RedFire 量化交易平台启动器

echo.
echo ================================================
echo RedFire 量化交易平台启动器
echo ================================================
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
if not exist "start_redfire.py" (
    echo [错误] 请在项目根目录运行此脚本
    echo 当前目录: %CD%
    pause
    exit /b 1
)

echo [信息] 启动RedFire量化交易平台...
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
python start_redfire.py %ARGS%

if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败，错误代码: %errorlevel%
    echo.
    echo 可能的解决方案:
    echo 1. 检查Python依赖是否安装: pip install -r backend/requirements.txt
    echo 2. 检查Node.js是否安装: node --version
    echo 3. 检查前端依赖是否安装: cd frontend ^&^& npm install
    echo 4. 尝试仅启动后端: python start_simple.py
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [信息] 程序已退出
pause
