# 多阶段构建 - RedFire前端应用
# ============================================

# 阶段1: 依赖安装和构建基础镜像
FROM node:18-alpine AS base
LABEL maintainer="RedFire Team"

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖
RUN apk add --no-cache \
    libc6-compat \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# 复制包管理文件
COPY package*.json ./
COPY turbo.json ./
COPY .npmrc* ./

# 复制workspace配置
COPY packages/*/package.json ./packages/
COPY apps/*/package.json ./apps/

# ============================================
# 阶段2: 依赖安装
FROM base AS deps

# 安装所有依赖
RUN npm ci --only=production --ignore-scripts && \
    npm cache clean --force

# ============================================
# 阶段3: 开发依赖和构建工具
FROM base AS build-deps

# 安装所有依赖（包括开发依赖）
RUN npm ci --ignore-scripts && \
    npm cache clean --force

# ============================================
# 阶段4: 构建应用
FROM build-deps AS builder

# 复制源代码
COPY . .

# 生成prisma客户端（如果有）
RUN npm run generate || true

# 构建所有包和应用
RUN npm run build

# ============================================
# 阶段5: Web应用运行时镜像
FROM nginx:alpine AS web-app

# 安装Node.js用于SSR（如果需要）
RUN apk add --no-cache nodejs npm

# 复制构建产物
COPY --from=builder /app/apps/web-app/dist /usr/share/nginx/html
COPY --from=builder /app/apps/web-app/package.json /app/

# 自定义Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]

# ============================================
# 阶段6: Node.js应用运行时镜像（用于SSR应用）
FROM node:18-alpine AS app-runtime

WORKDIR /app

# 创建非root用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制必要文件
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/apps/web-app/.next ./apps/web-app/.next
COPY --from=builder /app/apps/web-app/package.json ./apps/web-app/

USER nextjs

EXPOSE 3000

ENV NODE_ENV=production
ENV PORT=3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "apps/web-app/server.js"]

# ============================================
# 阶段7: 开发环境镜像
FROM build-deps AS dev

# 安装开发工具
RUN npm install -g nodemon concurrently

# 复制源代码
COPY . .

EXPOSE 3000 3001 3002 3003

CMD ["npm", "run", "dev"]
