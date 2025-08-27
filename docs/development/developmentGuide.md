# 🚀 RedFire开发环境搭建指南

## 📋 概述

本指南将帮助开发者快速搭建RedFire项目的开发环境，包括后端、前端、数据库和开发工具的配置。

## 🖥️ 系统要求

### 最低要求
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **内存**: 8GB RAM
- **存储**: 20GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Windows 11, macOS 12+, Ubuntu 20.04+
- **内存**: 16GB RAM
- **存储**: 50GB SSD
- **网络**: 高速互联网连接

## 🔧 必需软件

### 1. Python环境
```bash
# 检查Python版本 (需要3.9+)
python --version
# 或
python3 --version

# 如果没有安装，下载并安装Python 3.9+
# Windows: https://www.python.org/downloads/
# macOS: brew install python@3.9
# Ubuntu: sudo apt install python3.9 python3.9-venv
```

### 2. Node.js环境
```bash
# 检查Node.js版本 (需要16+)
node --version
npm --version

# 如果没有安装，下载并安装Node.js 16+
# Windows/macOS: https://nodejs.org/
# Ubuntu: curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
```

### 3. Git版本控制
```bash
# 检查Git版本
git --version

# 如果没有安装
# Windows: https://git-scm.com/download/win
# macOS: brew install git
# Ubuntu: sudo apt install git
```

### 4. Docker环境
```bash
# 检查Docker版本
docker --version
docker-compose --version

# 如果没有安装
# Windows/macOS: https://www.docker.com/products/docker-desktop
# Ubuntu: https://docs.docker.com/engine/install/ubuntu/
```

## 🏗️ 项目克隆与初始化

### 1. 克隆项目
```bash
# 克隆项目到本地
git clone https://github.com/your-org/redfire.git
cd redfire

# 检查项目结构
ls -la
```

### 2. 创建虚拟环境
```bash
# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 验证激活
which python  # 应该指向venv目录
```

### 3. 安装Python依赖
```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 4. 安装Node.js依赖
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 或者使用yarn
yarn install
```

## 🗄️ 数据库配置

### 1. PostgreSQL配置
```bash
# 使用Docker启动PostgreSQL
docker run -d \
  --name redfire-postgres \
  -e POSTGRES_DB=redfire \
  -e POSTGRES_USER=redfire \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:14

# 或者使用本地安装
# Windows: https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Ubuntu: sudo apt install postgresql postgresql-contrib
```

### 2. Redis配置
```bash
# 使用Docker启动Redis
docker run -d \
  --name redfire-redis \
  -p 6379:6379 \
  redis:6-alpine

# 或者使用本地安装
# Windows: https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Ubuntu: sudo apt install redis-server
```

### 3. 数据库初始化
```bash
# 创建数据库表
python scripts/init_database.py

# 或者使用Alembic迁移
alembic upgrade head
```

## ⚙️ 环境配置

### 1. 环境变量配置
```bash
# 复制环境变量模板
cp config/config.env.template config/config.env

# 编辑环境变量文件
# Windows
notepad config/config.env

# macOS/Linux
nano config/config.env
```

### 2. 环境变量内容
```bash
# 数据库配置
DATABASE_URL=postgresql://redfire:password@localhost:5432/redfire
REDIS_URL=redis://localhost:6379

# 应用配置
APP_NAME=RedFire
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# API配置
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 外部接口配置
CTP_HOST=localhost
CTP_PORT=17001
IB_HOST=localhost
IB_PORT=7497
```

### 3. 配置文件
```python
# config/backend/app_config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    app_name: str = "RedFire"
    app_env: str = "development"
    debug: bool = True
    
    # 数据库配置
    database_url: str = os.getenv("DATABASE_URL")
    redis_url: str = os.getenv("REDIS_URL")
    
    # API配置
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # 安全配置
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 🚀 启动开发环境

### 1. 使用Docker Compose (推荐)
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2. 手动启动服务
```bash
# 启动后端服务
cd backend
python main.py

# 启动前端服务
cd frontend
npm run dev

# 启动数据库服务 (如果使用本地安装)
# PostgreSQL
sudo systemctl start postgresql

# Redis
sudo systemctl start redis
```

### 3. 验证服务状态
```bash
# 检查后端API
curl http://localhost:8000/health

# 检查前端应用
# 浏览器访问 http://localhost:3000

# 检查数据库连接
python scripts/test_connection.py
```

## 🧪 开发工具配置

### 1. VS Code配置
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### 2. VS Code扩展推荐
- **Python**: Python语言支持
- **Python Indent**: Python缩进
- **Black Formatter**: 代码格式化
- **ESLint**: JavaScript代码检查
- **Prettier**: 代码格式化
- **GitLens**: Git增强功能
- **Docker**: Docker支持

### 3. 代码质量工具
```bash
# 安装代码质量工具
pip install black isort pylint mypy

# 代码格式化
black src/
isort src/

# 代码检查
pylint src/
mypy src/

# 前端代码检查
cd frontend
npm run lint
npm run type-check
```

## 📊 开发工作流

### 1. 分支管理
```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发完成后提交
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature

# 创建Pull Request
# 在GitHub/GitLab上创建PR
```

### 2. 代码审查
- 所有代码变更都需要通过Pull Request
- 至少需要一名团队成员审查
- 通过所有自动化测试
- 符合代码规范要求

### 3. 测试策略
```bash
# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/

# 运行前端测试
cd frontend
npm test
npm run test:e2e
```

## 🔍 调试技巧

### 1. 后端调试
```python
# 使用pdb调试
import pdb; pdb.set_trace()

# 使用logging记录日志
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 使用FastAPI调试模式
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

### 2. 前端调试
```typescript
// 使用console调试
console.log('调试信息:', data);
console.error('错误信息:', error);

// 使用React DevTools
// 安装Chrome扩展: React Developer Tools

// 使用Redux DevTools
// 安装Chrome扩展: Redux DevTools
```

### 3. 数据库调试
```bash
# 连接PostgreSQL
psql -h localhost -U redfire -d redfire

# 查看表结构
\dt

# 执行查询
SELECT * FROM orders LIMIT 10;

# 连接Redis
redis-cli

# 查看键
KEYS *

# 获取值
GET key_name
```

## 🚨 常见问题解决

### 1. 端口冲突
```bash
# 查看端口占用
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000

# 杀死进程
# Windows
taskkill /PID <PID> /F

# macOS/Linux
kill -9 <PID>
```

### 2. 依赖安装失败
```bash
# 清理缓存
pip cache purge
npm cache clean --force

# 重新安装
pip install -r requirements.txt --force-reinstall
npm install --force
```

### 3. 数据库连接失败
```bash
# 检查服务状态
docker-compose ps

# 重启服务
docker-compose restart postgres redis

# 检查网络
docker network ls
docker network inspect redfire_default
```

## 📚 学习资源

### 1. 官方文档
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [React官方文档](https://react.dev/)
- [TypeScript官方文档](https://www.typescriptlang.org/)
- [PostgreSQL官方文档](https://www.postgresql.org/docs/)

### 2. 社区资源
- [Stack Overflow](https://stackoverflow.com/)
- [GitHub Discussions](https://github.com/your-org/redfire/discussions)
- [Reddit r/Python](https://www.reddit.com/r/Python/)
- [Reddit r/reactjs](https://www.reddit.com/r/reactjs/)

### 3. 在线课程
- [Python异步编程](https://realpython.com/async-io-python/)
- [React Hooks](https://react.dev/learn/hooks-overview)
- [TypeScript基础](https://www.typescriptlang.org/docs/)

## 🔮 下一步

### 1. 熟悉项目结构
- 阅读架构文档
- 理解代码组织
- 学习设计模式

### 2. 参与开发
- 选择简单的任务开始
- 阅读现有代码
- 提出改进建议

### 3. 贡献代码
- 修复Bug
- 添加新功能
- 改进文档

---

*RedFire开发环境搭建指南 - 让开发更高效，让代码更优雅* 🔥
