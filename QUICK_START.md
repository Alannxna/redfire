# 🚀 RedFire 快速启动指南

## 📋 一分钟快速启动

### Windows用户
```cmd
# 双击运行
start_redfire.bat

# 或命令行运行
python start_redfire.py
```

### 其他系统
```bash
python start_redfire.py
```

## 🎯 常用启动命令

### 1. 完整启动（推荐）
```bash
# 启动前后端服务
python start_redfire.py

# 自定义端口
python start_redfire.py --port 8080 --frontend-port 3001

# 跳过依赖安装（快速启动）
python start_redfire.py --skip-deps
```

### 2. 仅后端启动
```bash
# 轻量级后端
python start_simple.py

# 完整后端（无前端）
python start_redfire.py --backend-only
```

### 3. 仅前端启动
```bash
# 前端开发服务器
python start_frontend.py
```

## 🔧 环境要求

| 组件 | 版本要求 | 状态 |
|------|---------|------|
| Python | 3.8+ | ✅ 必需 |
| Node.js | 16+ | ⚠️ 前端必需 |
| npm/pnpm | 最新 | ⚠️ 前端必需 |

## 📱 访问地址

启动成功后，访问以下地址：

- **前端应用**: http://127.0.0.1:3000
- **后端API**: http://127.0.0.1:8000
- **API文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health

## 🐛 常见问题

### Q: 前端启动失败？
**A**: 检查Node.js和npm是否安装：
```bash
node --version
npm --version
```

### Q: 端口被占用？
**A**: 使用其他端口：
```bash
python start_redfire.py --port 8080
```

### Q: 依赖安装失败？
**A**: 手动安装：
```bash
# Python依赖
pip install -r backend/requirements.txt

# 前端依赖
cd frontend && npm install
```

### Q: 只想用后端？
**A**: 使用仅后端模式：
```bash
python start_redfire.py --backend-only
# 或
python start_simple.py
```

## 🔍 测试工具

运行测试检查环境：
```bash
python test_startup.py
```

## 📞 获取帮助

查看详细帮助：
```bash
python start_redfire.py --help
python start_simple.py --help
python start_frontend.py --help
```

---

**提示**: 首次启动需要安装依赖，请耐心等待。后续启动可使用 `--skip-deps` 参数加速。