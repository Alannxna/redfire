@echo off
echo 🔥 RedFire 后端服务启动
echo ================================

cd /d "%~dp0"

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未找到，请安装Python 3.8+
    pause
    exit /b 1
)

echo 启动FastAPI服务器...
echo 📍 服务地址: http://127.0.0.1:8000
echo 📚 API文档: http://127.0.0.1:8000/api/docs
echo.
echo 按 Ctrl+C 停止服务器
echo.

python run_server.py

pause
