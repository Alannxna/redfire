# RedFire 量化交易平台启动指南

## 📋 概述

RedFire 提供多种启动方式，支持完整的前后端启动或单独的后端服务启动。

## 🚀 快速启动

### 方法一：完整启动（推荐）

```bash
# Python脚本启动（跨平台）
python start_redfire.py

# Windows批处理启动
start_redfire.bat

# 自定义配置启动
python start_redfire.py --host 0.0.0.0 --port 8080 --frontend-port 3001
```

### 方法二：仅后端启动

```bash
# 轻量级后端启动
python start_simple.py

# Windows批处理启动
start_simple.bat

# 自定义端口
python start_simple.py --port 8080
```

### 方法三：仅前端启动

```bash
# 前端开发服务器
python start_frontend.py

# 自定义配置
python start_frontend.py --port 3001 --no-browser
```

## 🛠️ 启动脚本详细说明

### 1. start_redfire.py - 完整启动器

**功能特性：**
- ✅ 自动环境检查（Python、Node.js）
- ✅ 自动依赖安装（Python + 前端）
- ✅ 同时启动前后端服务
- ✅ 进程监控和管理
- ✅ 优雅的停止机制
- ✅ 自动打开浏览器

**命令行参数：**
```bash
python start_redfire.py [OPTIONS]

选项:
  --host TEXT               后端服务主机地址 [默认: 127.0.0.1]
  --port INTEGER           后端服务端口 [默认: 8000]
  --frontend-port INTEGER  前端服务端口 [默认: 3000]
  --backend-only           仅启动后端服务
  --no-browser            不自动打开浏览器
  --skip-deps             跳过依赖安装
  --help                  显示帮助信息
```

**使用示例：**
```bash
# 默认启动
python start_redfire.py

# 仅启动后端
python start_redfire.py --backend-only

# 自定义端口和主机
python start_redfire.py --host 0.0.0.0 --port 8080 --frontend-port 3001

# 跳过依赖安装（快速启动）
python start_redfire.py --skip-deps --no-browser
```

### 2. start_simple.py - 简单后端启动器

**功能特性：**
- ✅ 轻量级设计，启动快速
- ✅ 专注后端服务
- ✅ 实时输出监控
- ✅ 基本错误处理

**命令行参数：**
```bash
python start_simple.py [OPTIONS]

选项:
  --host TEXT      服务主机地址 [默认: 127.0.0.1]
  --port INTEGER   服务端口 [默认: 8000]
  --help          显示帮助信息
```

**使用示例：**
```bash
# 默认启动
python start_simple.py

# 自定义配置
python start_simple.py --host 0.0.0.0 --port 8080
```

### 3. start_frontend.py - 前端启动器

**功能特性：**
- ✅ 自动检测包管理器（pnpm/npm）
- ✅ 智能依赖安装
- ✅ 开发服务器启动
- ✅ 自动打开浏览器

**命令行参数：**
```bash
python start_frontend.py [OPTIONS]

选项:
  --host TEXT        服务主机地址 [默认: 127.0.0.1]
  --port INTEGER     服务端口 [默认: 3000]
  --no-browser      不自动打开浏览器
  --skip-install    跳过依赖安装
  --help           显示帮助信息
```

## 🌐 服务访问地址

### 后端服务
- **主页**: http://127.0.0.1:8000
- **API文档**: http://127.0.0.1:8000/docs
- **交互式API**: http://127.0.0.1:8000/redoc
- **健康检查**: http://127.0.0.1:8000/health

### 前端服务
- **主页**: http://127.0.0.1:3000
- **开发工具**: 浏览器开发者工具

## 📋 环境要求

### 必需环境
- **Python**: 3.8+ （推荐 3.11+）
- **Node.js**: 16+ （推荐 18+ LTS）
- **npm**: 8+ 或 **pnpm**: 8+

### 可选工具
- **Git**: 用于版本控制
- **VSCode**: 推荐的开发环境

## 🔧 依赖管理

### Python依赖
```bash
# 安装后端依赖
pip install -r backend/requirements.txt

# 开发依赖
pip install -r backend/requirements-dev.txt
```

### 前端依赖
```bash
# 进入前端目录
cd frontend

# 使用npm安装
npm install

# 或使用pnpm（推荐）
pnpm install
```

## 🐛 故障排除

### 常见问题

#### 1. Python模块导入失败
```bash
# 解决方案
pip install -r backend/requirements.txt
```

#### 2. Node.js依赖安装失败
```bash
# 清理缓存
npm cache clean --force
cd frontend && npm install

# 或使用pnpm
cd frontend && pnpm install
```

#### 3. 端口被占用
```bash
# 查看端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# 使用其他端口
python start_redfire.py --port 8080
```

#### 4. 权限问题
```bash
# Windows: 以管理员身份运行
# macOS/Linux: 使用sudo（不推荐）或更改端口到1024以上
```

### 调试模式

#### 启用详细日志
```bash
# 设置环境变量
export PYTHONPATH=./backend    # macOS/Linux
set PYTHONPATH=./backend       # Windows

# 运行调试
python -m pdb start_redfire.py
```

#### 检查服务状态
```bash
# 检查后端健康状态
curl http://127.0.0.1:8000/health

# 或使用浏览器访问
# http://127.0.0.1:8000/health
```

## 📁 项目结构

```
redfire/
├── start_redfire.py          # 完整启动脚本
├── start_simple.py           # 简单后端启动脚本
├── start_frontend.py         # 前端启动脚本
├── start_redfire.bat         # Windows批处理脚本
├── start_simple.bat          # Windows简单启动脚本
├── README_STARTUP.md         # 本文档
├── backend/                  # 后端代码
│   ├── main.py              # 后端主程序
│   ├── requirements.txt     # Python依赖
│   └── core/                # 核心模块
└── frontend/                 # 前端代码
    ├── package.json         # 前端依赖配置
    ├── pnpm-workspace.yaml  # pnpm工作空间配置
    └── apps/                # 前端应用
```

## 🚀 生产部署

### Docker部署
```bash
# 构建镜像
docker build -t redfire .

# 运行容器
docker run -p 8000:8000 -p 3000:3000 redfire
```

### 传统部署
```bash
# 安装生产依赖
pip install -r backend/requirements.txt

# 构建前端
cd frontend && npm run build

# 启动生产服务
python start_redfire.py --host 0.0.0.0
```

## 📞 支持与反馈

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查系统日志输出
3. 提交Issue到项目仓库
4. 联系开发团队

---

**注意**: 首次启动可能需要较长时间来安装依赖，请耐心等待。