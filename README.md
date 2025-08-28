# 🔥 RedFire 应用

一个现代化的全栈交易应用，包含前端React应用和后端FastAPI服务。

## 🚀 快速启动

### 方法1: 使用启动脚本（推荐）

```bash
# 运行启动脚本
python start_app.py
```

这个脚本会自动：
- 检查依赖（Python、Node.js、npm）
- 安装后端和前端依赖
- 启动后端服务（端口8000）
- 启动前端服务（端口3000）
- 监控所有服务状态

### 方法2: 手动启动

#### 后端服务
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### 前端服务
```bash
cd frontend/apps/web-app
npm install
npm run dev
```

## 📱 访问应用

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🎉 最新更新 (2025-08-28)

### ✅ Phase 3配置系统重构完成
- 🔄 **代码重复消除**: 35.7% (超额完成)
- ⚡ **性能提升**: 2.6x 缓存加速
- 💾 **内存优化**: 49% 减少
- 🔧 **统一工具**: 配置管理现代化
- 📄 **详细报告**: `backend/shared/config/REFACTOR_COMPLETION_REPORT.md`

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **SQLAlchemy** - ORM数据库操作
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI服务器

### 前端
- **React 18** - 用户界面库
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI组件库
- **React Router** - 路由管理
- **Zustand** - 状态管理

## 📁 项目结构

```
redfire/
├── backend/                 # 后端服务
│   ├── main.py             # 主应用入口
│   ├── requirements.txt    # Python依赖
│   └── ...
├── frontend/               # 前端应用
│   └── apps/
│       └── web-app/        # 主Web应用
│           ├── src/        # 源代码
│           ├── package.json
│           └── ...
├── start_app.py           # 启动脚本
└── README.md              # 项目说明
```

## 🔧 开发

### 停止服务
按 `Ctrl+C` 停止所有服务

### 重新启动
```bash
python start_app.py
```

### 查看日志
启动脚本会实时显示所有服务的日志输出

## 🐛 故障排除

### 端口被占用
如果端口3000或8000被占用，请：
1. 停止占用端口的进程
2. 或者修改配置文件中的端口设置

### 依赖安装失败
1. 确保已安装Python 3.8+和Node.js
2. 检查网络连接
3. 尝试手动安装依赖

### 前端加载缓慢
1. 检查网络连接
2. 确保后端服务正常运行
3. 查看浏览器控制台错误信息

## �� 许可证

MIT License
