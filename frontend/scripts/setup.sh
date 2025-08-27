#!/bin/bash

# RedFire Frontend Setup Script
# 自动化项目设置脚本

echo "🔥 RedFire Frontend Setup Script"
echo "=================================="

# 检查Node.js版本
check_node() {
    echo "📋 检查Node.js版本..."
    if ! command -v node &> /dev/null; then
        echo "❌ 错误: 未找到Node.js，请先安装Node.js (>= 18.0.0)"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    REQUIRED_VERSION="18.0.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        echo "❌ 错误: Node.js版本过低，当前版本: $NODE_VERSION，要求版本: >= $REQUIRED_VERSION"
        exit 1
    fi
    
    echo "✅ Node.js版本检查通过: $NODE_VERSION"
}

# 检查npm版本
check_npm() {
    echo "📋 检查npm版本..."
    if ! command -v npm &> /dev/null; then
        echo "❌ 错误: 未找到npm"
        exit 1
    fi
    
    NPM_VERSION=$(npm -v)
    echo "✅ npm版本: $NPM_VERSION"
}

# 安装依赖
install_dependencies() {
    echo "📦 安装项目依赖..."
    
    if [ -f "package-lock.json" ]; then
        echo "🔧 使用npm ci进行快速安装..."
        npm ci
    else
        echo "🔧 使用npm install安装依赖..."
        npm install
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ 依赖安装完成"
    else
        echo "❌ 依赖安装失败"
        exit 1
    fi
}

# 构建共享包
build_packages() {
    echo "🏗️ 构建共享包..."
    
    npm run build --filter=@redfire/shared-types
    npm run build --filter=@redfire/ui-components  
    npm run build --filter=@redfire/theme-system
    
    if [ $? -eq 0 ]; then
        echo "✅ 共享包构建完成"
    else
        echo "❌ 共享包构建失败"
        exit 1
    fi
}

# 设置环境配置
setup_env() {
    echo "⚙️ 设置环境配置..."
    
    if [ ! -f ".env.local" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env.local
            echo "✅ 环境配置文件已创建: .env.local"
            echo "💡 提示: 请根据需要修改 .env.local 文件中的配置"
        else
            echo "⚠️ 警告: 未找到环境配置模板文件"
        fi
    else
        echo "ℹ️ 环境配置文件已存在: .env.local"
    fi
}

# 运行健康检查
health_check() {
    echo "🏥 运行健康检查..."
    
    # 类型检查
    echo "📝 类型检查..."
    npm run type-check
    
    if [ $? -eq 0 ]; then
        echo "✅ 类型检查通过"
    else
        echo "⚠️ 警告: 类型检查发现问题"
    fi
    
    # 代码检查
    echo "🔍 代码检查..."
    npm run lint
    
    if [ $? -eq 0 ]; then
        echo "✅ 代码检查通过"
    else
        echo "⚠️ 警告: 代码检查发现问题"
    fi
}

# 主函数
main() {
    echo "开始设置RedFire前端项目..."
    echo ""
    
    check_node
    check_npm
    install_dependencies
    build_packages
    setup_env
    health_check
    
    echo ""
    echo "🎉 项目设置完成！"
    echo ""
    echo "🚀 快速开始："
    echo "  npm run dev              # 启动所有应用"
    echo "  npm run dev:web          # 启动Web应用"
    echo "  npm run dev:mobile       # 启动移动应用"
    echo "  npm run dev:admin        # 启动管理后台"
    echo "  npm run dev:terminal     # 启动交易终端"
    echo ""
    echo "📖 更多信息请查看 README.md"
    echo ""
    echo "Happy coding! 🔥"
}

# 执行主函数
main
