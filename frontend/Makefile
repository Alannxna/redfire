# RedFire前端项目Makefile
# ==========================

.PHONY: help setup dev build test clean docker lint format

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## 显示帮助信息
	@echo "$(BLUE)RedFire前端项目 - 可用命令:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# 🚀 开发环境
setup: ## 初始化项目（安装依赖、构建包）
	@echo "$(YELLOW)🚀 初始化RedFire前端项目...$(NC)"
	npm install
	npm run setup
	@echo "$(GREEN)✅ 项目初始化完成！$(NC)"

dev: ## 启动开发服务器（所有应用）
	@echo "$(YELLOW)🔧 启动开发环境...$(NC)"
	npm run dev

dev-web: ## 启动Web应用开发服务器
	@echo "$(YELLOW)🌐 启动Web应用...$(NC)"
	npm run dev:web

dev-packages: ## 启动包开发模式
	@echo "$(YELLOW)📦 启动包开发模式...$(NC)"
	npm run dev:packages

# 🏗️ 构建
build: ## 构建所有应用和包
	@echo "$(YELLOW)🏗️ 构建所有项目...$(NC)"
	npm run build
	@echo "$(GREEN)✅ 构建完成！$(NC)"

build-web: ## 构建Web应用
	@echo "$(YELLOW)🌐 构建Web应用...$(NC)"
	npm run build:web

build-packages: ## 构建所有包
	@echo "$(YELLOW)📦 构建所有包...$(NC)"
	npm run build:packages

build-affected: ## 构建受影响的项目（基于Git差异）
	@echo "$(YELLOW)🎯 构建受影响的项目...$(NC)"
	npm run build:affected

# 🧪 测试
test: ## 运行所有测试
	@echo "$(YELLOW)🧪 运行测试...$(NC)"
	npm run test

test-watch: ## 运行测试（监听模式）
	@echo "$(YELLOW)👀 运行测试（监听模式）...$(NC)"
	npm run test:watch

test-coverage: ## 运行测试并生成覆盖率报告
	@echo "$(YELLOW)📊 生成测试覆盖率报告...$(NC)"
	npm run test:coverage

test-e2e: ## 运行端到端测试
	@echo "$(YELLOW)🎭 运行E2E测试...$(NC)"
	npm run test:e2e

# 🔍 代码质量
lint: ## 运行代码检查
	@echo "$(YELLOW)🔍 运行代码检查...$(NC)"
	npm run lint

lint-fix: ## 自动修复代码问题
	@echo "$(YELLOW)🔧 自动修复代码问题...$(NC)"
	npm run lint:fix

format: ## 格式化代码
	@echo "$(YELLOW)💅 格式化代码...$(NC)"
	npm run format

format-check: ## 检查代码格式
	@echo "$(YELLOW)📋 检查代码格式...$(NC)"
	npm run format:check

type-check: ## TypeScript类型检查
	@echo "$(YELLOW)🔤 TypeScript类型检查...$(NC)"
	npm run type-check

# 🧹 清理
clean: ## 清理所有构建产物和依赖
	@echo "$(YELLOW)🧹 清理项目...$(NC)"
	npm run clean
	@echo "$(GREEN)✅ 清理完成！$(NC)"

clean-dist: ## 清理构建产物
	@echo "$(YELLOW)🗑️ 清理构建产物...$(NC)"
	npm run clean:dist

clean-cache: ## 清理Turbo缓存
	@echo "$(YELLOW)💨 清理Turbo缓存...$(NC)"
	npm run clean:cache

clean-deps: ## 清理所有依赖
	@echo "$(YELLOW)📦 清理依赖...$(NC)"
	npm run clean:deps

# 🐳 Docker
docker-build: ## 构建Docker镜像
	@echo "$(YELLOW)🐳 构建Docker镜像...$(NC)"
	docker build -t redfire-frontend:latest .
	@echo "$(GREEN)✅ Docker镜像构建完成！$(NC)"

docker-dev: ## 启动Docker开发环境
	@echo "$(YELLOW)🐳 启动Docker开发环境...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Docker开发环境已启动！$(NC)"

docker-down: ## 停止Docker开发环境
	@echo "$(YELLOW)🛑 停止Docker开发环境...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Docker开发环境已停止！$(NC)"

docker-logs: ## 查看Docker日志
	@echo "$(YELLOW)📋 查看Docker日志...$(NC)"
	docker-compose -f docker-compose.dev.yml logs -f

# 📊 分析和监控
analyze: ## 分析打包体积
	@echo "$(YELLOW)📊 分析打包体积...$(NC)"
	npm run analyze

storybook: ## 启动Storybook
	@echo "$(YELLOW)📚 启动Storybook...$(NC)"
	npm run storybook

build-storybook: ## 构建Storybook
	@echo "$(YELLOW)📚 构建Storybook...$(NC)"
	npm run build-storybook

# 🔄 版本管理
changeset: ## 创建changeset
	@echo "$(YELLOW)📝 创建changeset...$(NC)"
	npm run changeset

version: ## 更新版本号
	@echo "$(YELLOW)🔢 更新版本号...$(NC)"
	npm run version-packages

release: ## 发布新版本
	@echo "$(YELLOW)🚀 发布新版本...$(NC)"
	npm run release

# 🎯 快速命令
quick-start: setup dev ## 快速开始（设置+开发）

check: lint type-check test ## 全面检查（lint+类型+测试）

ci: clean setup check build ## CI流水线（清理+设置+检查+构建）

# 📈 性能测试
perf: ## 运行性能测试
	@echo "$(YELLOW)⚡ 运行性能测试...$(NC)"
	npm run build
	npm run preview &
	sleep 5
	npx lighthouse http://localhost:4173 --output html --output-path ./lighthouse-report.html
	@echo "$(GREEN)✅ 性能测试完成！报告: lighthouse-report.html$(NC)"

# 📱 移动端预览
mobile-preview: ## 移动端预览模式
	@echo "$(YELLOW)📱 启动移动端预览...$(NC)"
	npm run build:web
	npm run preview &
	@echo "$(GREEN)🌐 预览地址: http://localhost:4173$(NC)"
	@echo "$(BLUE)📱 使用手机访问同网段IP进行测试$(NC)"

# 状态信息
status: ## 显示项目状态
	@echo "$(BLUE)📊 RedFire前端项目状态:$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 依赖状态:$(NC)"
	@npm ls --depth=0 2>/dev/null || echo "$(RED)❌ 需要运行 make setup$(NC)"
	@echo ""
	@echo "$(YELLOW)🏗️ 构建状态:$(NC)"
	@if [ -d "dist" ] || [ -d "apps/web-app/dist" ]; then echo "$(GREEN)✅ 存在构建产物$(NC)"; else echo "$(RED)❌ 需要运行 make build$(NC)"; fi
	@echo ""
	@echo "$(YELLOW)🧪 测试覆盖率:$(NC)"
	@if [ -d "coverage" ]; then echo "$(GREEN)✅ 已生成覆盖率报告$(NC)"; else echo "$(YELLOW)⚠️ 运行 make test-coverage 生成$(NC)"; fi
