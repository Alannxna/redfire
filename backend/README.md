# RedFire 后端 API 服务

基于 FastAPI 的现代化后端服务，提供用户认证和管理功能。

## 🎉 重构进展 (2025-08-28更新)

### ✅ Phase 3配置系统重构完成
- **🔄 代码重复消除**: 35.7% (590行→235行)
- **⚡ 性能提升**: 缓存加载2.6x提升 (25ms→9ms)  
- **💾 内存优化**: 49%减少 (3.7MB→1.9MB)
- **🧪 测试覆盖**: 100%完整覆盖
- **📋 详细报告**: [配置重构完成报告](shared/config/REFACTOR_COMPLETION_REPORT.md)

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务器

**方式一：使用Python脚本**
```bash
python run_server.py
```

**方式二：使用批处理文件（Windows）**
```bash
run_server.bat
```

**方式三：直接使用uvicorn**
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 访问服务

- 🌐 **API服务**: http://127.0.0.1:8000
- 📚 **API文档**: http://127.0.0.1:8000/api/docs
- 🔍 **ReDoc文档**: http://127.0.0.1:8000/api/redoc
- ❤️ **健康检查**: http://127.0.0.1:8000/health

## 🧪 测试API

运行测试脚本验证API功能：

```bash
python test_api.py
```

## 📋 API 端点

### 认证相关 (`/api/auth`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录 |
| GET | `/me` | 获取当前用户信息 |
| POST | `/logout` | 用户登出 |
| GET | `/verify-token` | 验证令牌有效性 |

### 示例请求

**用户注册**
```json
POST /api/auth/register
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "SecurePassword123!",
  "full_name": "测试用户",
  "phone": "13800138000"
}
```

**用户登录**
```json
POST /api/auth/login
{
  "username": "testuser",
  "password": "SecurePassword123!"
}
```

## 🏗️ 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── run_server.py          # 服务器启动脚本
├── test_api.py            # API测试脚本
├── requirements.txt       # Python依赖
├── database.py           # 数据库配置
├── config.py             # 应用配置
├── models/               # 数据模型
│   ├── database_models.py
│   └── __init__.py
├── schemas/              # Pydantic模式
│   ├── auth_schemas.py
│   └── __init__.py
├── auth/                 # 认证模块
│   ├── security.py
│   └── __init__.py
├── services/             # 业务服务层
│   ├── user_service.py
│   └── __init__.py
└── api/                  # API路由
    ├── auth_routes.py
    └── __init__.py
```

## 🔧 配置

主要配置在 `config.py` 中：

- **数据库**: SQLite（默认）
- **JWT密钥**: 自动生成
- **令牌过期时间**: 24小时
- **密码加密**: bcrypt

## 🔒 安全特性

- ✅ JWT令牌认证
- ✅ 密码哈希加密
- ✅ CORS跨域配置
- ✅ 输入数据验证
- ✅ 错误处理
- ✅ 用户权限管理

## 🗄️ 数据库

使用SQLAlchemy ORM，默认SQLite数据库。

**用户表结构**:
- user_id (主键)
- username (用户名)
- email (邮箱)
- password_hash (密码哈希)
- full_name (全名)
- phone (电话)
- role (角色)
- is_active (是否激活)
- is_verified (是否验证)
- created_at (创建时间)
- updated_at (更新时间)
- last_login (最后登录)

## 🚦 开发模式

服务器在开发模式下运行，支持：
- 🔄 热重载
- 📝 详细日志
- 🐛 调试模式
- 📚 自动生成API文档

## 📞 支持

如有问题，请查看：
1. API文档：http://127.0.0.1:8000/api/docs
2. 运行测试脚本检查功能
3. 检查服务器日志输出
