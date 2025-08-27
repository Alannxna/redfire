@echo off
REM RedFire Frontend Setup Script for Windows
REM 自动化项目设置脚本

echo 🔥 RedFire Frontend Setup Script
echo ==================================

REM 检查Node.js
echo 📋 检查Node.js版本...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Node.js，请先安装Node.js ^(^>= 18.0.0^)
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✅ Node.js版本检查通过: %NODE_VERSION%

REM 检查npm
echo 📋 检查npm版本...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到npm
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo ✅ npm版本: %NPM_VERSION%

REM 安装依赖
echo 📦 安装项目依赖...
if exist package-lock.json (
    echo 🔧 使用npm ci进行快速安装...
    npm ci
) else (
    echo 🔧 使用npm install安装依赖...
    npm install
)

if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

REM 构建共享包
echo 🏗️ 构建共享包...
call npm run build --filter=@redfire/shared-types
call npm run build --filter=@redfire/ui-components
call npm run build --filter=@redfire/theme-system

if errorlevel 1 (
    echo ❌ 共享包构建失败
    pause
    exit /b 1
)
echo ✅ 共享包构建完成

REM 设置环境配置
echo ⚙️ 设置环境配置...
if not exist .env.local (
    if exist env.example (
        copy env.example .env.local >nul
        echo ✅ 环境配置文件已创建: .env.local
        echo 💡 提示: 请根据需要修改 .env.local 文件中的配置
    ) else (
        echo ⚠️ 警告: 未找到环境配置模板文件
    )
) else (
    echo ℹ️ 环境配置文件已存在: .env.local
)

REM 运行健康检查
echo 🏥 运行健康检查...

echo 📝 类型检查...
call npm run type-check
if errorlevel 1 (
    echo ⚠️ 警告: 类型检查发现问题
) else (
    echo ✅ 类型检查通过
)

echo 🔍 代码检查...
call npm run lint
if errorlevel 1 (
    echo ⚠️ 警告: 代码检查发现问题
) else (
    echo ✅ 代码检查通过
)

echo.
echo 🎉 项目设置完成！
echo.
echo 🚀 快速开始：
echo   npm run dev              # 启动所有应用
echo   npm run dev:web          # 启动Web应用
echo   npm run dev:mobile       # 启动移动应用
echo   npm run dev:admin        # 启动管理后台
echo   npm run dev:terminal     # 启动交易终端
echo.
echo 📖 更多信息请查看 README.md
echo.
echo Happy coding! 🔥

pause
