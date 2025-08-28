# Frontend 模块介绍

## 🎯 概述

`frontend` 是 RedFire 量化交易平台的前端应用模块，提供现代化的Web用户界面，支持实时交易、数据可视化、策略管理等功能。该模块采用React + TypeScript技术栈，支持响应式设计和多端适配。

## 📁 目录结构

```
frontend/
├── apps/                     # 🎯 应用模块
├── packages/                 # 📦 共享包
├── shared/                   # 🔗 共享资源
├── contexts/                 # 🎭 React上下文
├── tools/                    # 🛠️ 开发工具
├── scripts/                  # 📜 构建脚本
├── tests/                    # 🧪 测试文件
├── docs/                     # 📚 前端文档
├── dev-server/               # 🖥️ 开发服务器
├── .github/                  # 🔧 GitHub配置
├── .changeset/               # 📝 变更记录
├── .turbo/                   # ⚡ Turbo缓存
├── node_modules/             # 📦 依赖包
├── package.json              # 📋 项目配置
├── package-lock.json         # 🔒 依赖锁定
├── tsconfig.json             # ⚙️ TypeScript配置
├── turbo.json                # ⚡ Turbo配置
├── .eslintrc.js              # 🔍 ESLint配置
├── .prettierrc.js            # 💅 Prettier配置
├── .nvmrc                    # 🐍 Node版本
├── pnpm-workspace.yaml       # 📦 工作区配置
├── tsconfig.tsbuildinfo      # 🔧 TypeScript构建信息
├── Makefile                  # 🔨 构建脚本
├── Dockerfile                # 🐳 Docker配置
├── docker-compose.dev.yml    # 🐳 开发环境Docker
├── nginx.conf                # 🌐 Nginx配置
├── env.example               # 📝 环境变量示例
├── .gitignore                # 🚫 Git忽略文件
└── README.md                 # 📖 说明文档
```

## 🎯 应用模块 (`apps/`)

### **主要应用**:
- **交易界面**: 实时交易操作界面
- **数据可视化**: 图表和数据分析界面
- **策略管理**: 策略开发和部署界面
- **系统管理**: 用户管理和系统配置界面

### **技术特性**:
- React 18 + TypeScript
- 响应式设计
- 实时数据更新
- 组件化架构

## 📦 共享包 (`packages/`)

### **核心包**:
- **UI组件库**: 通用UI组件
- **工具函数**: 通用工具函数
- **类型定义**: TypeScript类型定义
- **API客户端**: 后端API调用

### **包管理**:
- 使用pnpm工作区
- 版本统一管理
- 依赖共享优化

## 🔗 共享资源 (`shared/`)

### **内容**:
- 静态资源文件
- 样式文件
- 图标和图片
- 国际化资源

## 🎭 React上下文 (`contexts/`)

### **主要上下文**:
- **认证上下文**: 用户认证状态管理
- **主题上下文**: 主题切换功能
- **数据上下文**: 全局数据状态管理
- **配置上下文**: 应用配置管理

## 🛠️ 开发工具 (`tools/`)

### **工具集**:
- 代码生成器
- 构建工具
- 开发辅助工具
- 性能分析工具

## 📜 构建脚本 (`scripts/`)

### **脚本功能**:
- 自动化构建
- 环境配置
- 部署脚本
- 测试脚本

## 🧪 测试文件 (`tests/`)

### **测试类型**:
- 单元测试
- 集成测试
- E2E测试
- 性能测试

## 📚 前端文档 (`docs/`)

### **文档内容**:
- 开发指南
- API文档
- 组件文档
- 最佳实践

## 🖥️ 开发服务器 (`dev-server/`)

### **功能**:
- 本地开发服务器
- 热重载支持
- 代理配置
- 调试工具

## ⚡ 构建配置

### **Turbo配置** (`turbo.json`)
```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "lint": {},
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

### **TypeScript配置** (`tsconfig.json`)
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/utils/*": ["./src/utils/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## 🐳 Docker配置

### **Dockerfile**
```dockerfile
# 多阶段构建
FROM node:18-alpine AS base

# 安装依赖
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 复制包管理文件
COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# 构建应用
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 构建所有应用
RUN npm install -g pnpm && pnpm build

# 生产环境
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

# 创建非root用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制构建结果
COPY --from=builder /app/apps/trading/.next/standalone ./
COPY --from=builder /app/apps/trading/.next/static ./apps/trading/.next/static
COPY --from=builder /app/apps/trading/public ./apps/trading/public

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "apps/trading/server.js"]
```

## 🌐 Nginx配置

### **nginx.conf**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }

    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # 前端应用
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API代理
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket支持
        location /ws/ {
            proxy_pass http://backend/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

## 🔧 开发环境配置

### **环境变量** (`env.example`)
```bash
# 应用配置
NEXT_PUBLIC_APP_NAME=RedFire
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_ENVIRONMENT=development

# API配置
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# 认证配置
NEXT_PUBLIC_AUTH_DOMAIN=your-auth-domain
NEXT_PUBLIC_AUTH_CLIENT_ID=your-client-id

# 监控配置
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id

# 功能开关
NEXT_PUBLIC_FEATURE_FLAGS={"newUI":true,"beta":false}
```

## 🚀 开发工作流

### **1. 环境准备**
```bash
# 安装Node.js (使用nvm)
nvm use

# 安装pnpm
npm install -g pnpm

# 安装依赖
pnpm install
```

### **2. 开发启动**
```bash
# 启动所有应用
pnpm dev

# 启动特定应用
pnpm dev --filter=trading

# 启动开发服务器
pnpm dev:server
```

### **3. 构建部署**
```bash
# 构建所有应用
pnpm build

# 构建特定应用
pnpm build --filter=trading

# 生产环境构建
pnpm build:prod
```

## 📊 性能优化

### **1. 代码分割**
- 路由级别的代码分割
- 组件懒加载
- 动态导入

### **2. 缓存策略**
- 静态资源缓存
- API响应缓存
- 组件缓存

### **3. 打包优化**
- Tree shaking
- 依赖分析
- 体积监控

## 🧪 测试策略

### **1. 单元测试**
```typescript
import { render, screen } from '@testing-library/react'
import { TradingView } from './TradingView'

describe('TradingView', () => {
  it('renders trading interface', () => {
    render(<TradingView />)
    expect(screen.getByText('Trading')).toBeInTheDocument()
  })
})
```

### **2. 集成测试**
```typescript
import { render, fireEvent, waitFor } from '@testing-library/react'
import { OrderForm } from './OrderForm'

describe('OrderForm', () => {
  it('submits order successfully', async () => {
    const mockSubmit = jest.fn()
    render(<OrderForm onSubmit={mockSubmit} />)
    
    fireEvent.change(screen.getByLabelText('Symbol'), {
      target: { value: 'AAPL' }
    })
    fireEvent.click(screen.getByText('Submit'))
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        symbol: 'AAPL',
        quantity: 100
      })
    })
  })
})
```

## 🔍 代码质量

### **1. ESLint配置**
```javascript
module.exports = {
  extends: [
    'next/core-web-vitals',
    '@typescript-eslint/recommended',
    'prettier'
  ],
  rules: {
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn',
    'react-hooks/exhaustive-deps': 'warn'
  }
}
```

### **2. Prettier配置**
```javascript
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false
}
```

## 📈 监控和分析

### **1. 性能监控**
- Core Web Vitals监控
- 错误监控
- 用户行为分析

### **2. 错误追踪**
- Sentry集成
- 错误边界处理
- 日志收集

---

**总结**: Frontend模块提供了现代化的Web用户界面，采用React + TypeScript技术栈，支持响应式设计和多端适配。通过组件化架构、性能优化和完整的测试覆盖，为用户提供流畅的交易体验。
