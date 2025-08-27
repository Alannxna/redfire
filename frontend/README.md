# 🔥 RedFire Frontend v2.0

> 专业量化交易平台前端 - 统一现代化架构

## 📋 项目概述

RedFire Frontend v2.0 是一个基于现代前端技术栈构建的专业量化交易平台前端系统。采用 **Monorepo + 微前端** 架构，提供统一的开发体验和高性能的用户界面。

### ✨ 核心特性

- 🏗️ **微前端架构** - 模块化、可独立部署的应用架构
- 📦 **Monorepo管理** - 使用 Turborepo 实现高效的多包管理
- ⚡ **现代技术栈** - React 18 + TypeScript + Vite 构建
- 🎨 **组件化设计** - 统一的UI组件库和设计系统
- 📱 **响应式设计** - 完美适配桌面端和移动端
- 🔌 **实时数据** - WebSocket + HTTP 混合数据传输
- 🛡️ **类型安全** - 完整的 TypeScript 类型系统
- 🧪 **测试驱动** - 完善的单元测试和E2E测试
- ⚡ **性能优化** - 代码分割、懒加载、缓存策略

## 🏗️ 项目架构

```
frontend/
├── 📱 apps/                          # 应用层
│   ├── web-app/                     # 主Web应用
│   ├── mobile-app/                  # 移动应用
│   ├── admin-dashboard/             # 管理后台
│   └── trading-terminal/            # 专业交易终端
│
├── 📦 packages/                      # 共享包层
│   ├── ui-components/              # UI组件库
│   ├── business-components/        # 业务组件库
│   ├── shared-types/              # 类型定义
│   ├── api-client/                # API客户端
│   ├── theme-system/              # 主题系统
│   └── utils/                     # 工具库
│
├── 🏗️ tools/                        # 工具配置
├── 🌐 shared/                       # 共享资源
├── 📄 docs/                         # 文档
└── 🧪 tests/                        # 测试
```

## 🚀 快速开始

### 环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0
- Git

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/redfire/redfire.git
cd redfire/frontend

# 安装依赖
npm install

# 初始化设置（构建共享包）
npm run setup
```

### 环境配置

```bash
# 复制环境配置文件
cp .env.example .env.local

# 编辑配置文件
nano .env.local
```

### 启动开发服务器

```bash
# 启动所有应用
npm run dev

# 启动特定应用
npm run dev:web        # Web应用
npm run dev:mobile     # 移动应用
npm run dev:admin      # 管理后台
npm run dev:terminal   # 交易终端
```

访问地址：
- 📱 Web应用: http://localhost:3000
- 📱 移动应用: http://localhost:3001
- 🔧 管理后台: http://localhost:3002
- 💹 交易终端: http://localhost:3003

## 📦 主要应用介绍

### 🌐 Web应用 (`apps/web-app`)

主要的Web端应用，提供完整的量化交易功能：

- **仪表盘** - 资产概览、收益分析、风险监控
- **交易中心** - 股票交易、订单管理、实时行情
- **策略管理** - 策略创建、回测、监控
- **风险控制** - 实时风险监控、预警系统
- **数据中心** - 市场数据、数据源管理

### 📱 移动应用 (`apps/mobile-app`)

基于 React Native 的移动端应用：

- 轻量级交易功能
- 实时行情查看
- 持仓管理
- 推送通知

### 🔧 管理后台 (`apps/admin-dashboard`)

系统管理和配置界面：

- 用户管理
- 系统配置
- 监控面板
- 数据统计

### 💹 交易终端 (`apps/trading-terminal`)

专业交易员使用的高级终端：

- 多屏幕支持
- 高级图表分析
- 快速交易功能
- 自定义工作空间

## 🛠️ 开发指南

### 代码结构

```bash
src/
├── components/         # 页面组件
├── hooks/             # 自定义Hooks
├── services/          # 业务服务层
├── stores/            # 状态管理
├── utils/             # 工具函数
├── types/             # 类型定义
├── styles/            # 样式文件
└── __tests__/         # 测试文件
```

### 开发规范

- 使用 TypeScript 进行类型检查
- 遵循 ESLint 和 Prettier 代码规范
- 组件采用函数式写法 + Hooks
- 使用 CSS Modules 或 styled-components
- 编写单元测试和集成测试

### 常用命令

```bash
# 开发
npm run dev                # 启动所有应用
npm run dev:web           # 启动Web应用

# 构建
npm run build             # 构建所有应用
npm run build:web         # 构建Web应用

# 测试
npm run test              # 运行测试
npm run test:watch        # 监听模式测试
npm run test:coverage     # 测试覆盖率

# 代码检查
npm run lint              # 代码检查
npm run lint:fix          # 修复代码问题
npm run type-check        # 类型检查

# 工具
npm run clean             # 清理构建文件
npm run analyze           # 包大小分析
```

## 🧪 测试

项目采用分层测试策略：

```bash
# 单元测试
npm run test

# 监听模式
npm run test:watch

# 覆盖率报告
npm run test:coverage

# E2E测试
npm run test:e2e
```

### 测试覆盖率目标

- 单元测试覆盖率 > 90%
- 集成测试覆盖率 > 80%
- E2E测试覆盖关键用户流程

## 📦 部署

### 构建生产版本

```bash
# 构建所有应用
npm run build

# 构建特定应用
npm run build:web
npm run build:mobile
npm run build:admin
npm run build:terminal
```

### 预览构建结果

```bash
npm run preview
```

### Docker部署

```bash
# 构建Docker镜像
docker build -t redfire-frontend .

# 运行容器
docker run -p 3000:3000 redfire-frontend
```

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `VITE_API_URL` | API服务器地址 | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket地址 | `ws://localhost:8001` |
| `VITE_APP_NAME` | 应用名称 | `RedFire` |

### 构建配置

项目使用 Vite 作为构建工具，配置文件：
- `vite.config.ts` - 主要构建配置
- `tsconfig.json` - TypeScript配置
- `eslint.config.js` - ESLint配置

## 🔄 更新日志

### v2.0.0 (2024-01-15)

- 🎉 全新的微前端架构
- ⚡ 采用 React 18 + TypeScript
- 📦 Monorepo 项目结构
- 🎨 统一的设计系统
- 📱 响应式移动端支持
- 🔌 实时数据传输
- 🧪 完善的测试体系

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

### 代码规范

- 遵循现有的代码风格
- 添加适当的测试
- 更新相关文档
- 确保所有检查通过

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 团队

- **前端架构** - RedFire前端团队
- **UI/UX设计** - RedFire设计团队
- **产品管理** - RedFire产品团队

## 📞 支持

如果您有任何问题或建议，请通过以下方式联系我们：

- 📧 Email: frontend@redfire.com
- 🐛 Issues: [GitHub Issues](https://github.com/redfire/redfire/issues)
- 📖 文档: [项目文档](https://docs.redfire.com)

---

**RedFire Frontend v2.0** - 专业量化交易平台前端系统 🔥