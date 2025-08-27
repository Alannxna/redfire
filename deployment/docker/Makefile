# VnPy Web 项目管理 Makefile

.PHONY: help install dev build test clean docker

# 默认目标
help:
	@echo "VnPy Web 项目管理命令："
	@echo "  install     - 安装所有依赖"
	@echo "  dev         - 启动开发环境"
	@echo "  build       - 构建生产版本"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理构建文件"
	@echo "  docker      - Docker相关操作"

# 安装依赖
install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install

# 开发环境
dev:
	@echo "启动开发环境..."
	@echo "后端服务将在后台启动..."
	cd backend && python run_services.py &
	@echo "前端服务启动中..."
	cd frontend && npm run dev

# 构建生产版本
build:
	@echo "构建前端生产版本..."
	cd frontend && npm run build
	@echo "构建完成！"

# 运行测试
test:
	@echo "运行后端测试..."
	cd backend && python -m pytest tests/
	@echo "运行前端测试..."
	cd frontend && npm run test

# 代码检查
lint:
	@echo "后端代码检查..."
	cd backend && flake8 src/
	@echo "前端代码检查..."
	cd frontend && npm run lint:check

# 代码格式化
format:
	@echo "后端代码格式化..."
	cd backend && black src/ && isort src/
	@echo "前端代码格式化..."
	cd frontend && npm run format

# 清理
clean:
	@echo "清理构建文件..."
	cd frontend && npm run clean
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/dist/
	rm -rf frontend/dist/

# Docker操作
docker-build:
	@echo "构建Docker镜像..."
	docker-compose build

docker-up:
	@echo "启动Docker服务..."
	docker-compose up -d

docker-down:
	@echo "停止Docker服务..."
	docker-compose down

docker-logs:
	@echo "查看Docker日志..."
	docker-compose logs -f

# 数据库操作
db-init:
	@echo "初始化数据库..."
	cd backend && python tools/database_init.py

db-migrate:
	@echo "数据库迁移..."
	cd backend && alembic upgrade head

# 部署相关
deploy-staging:
	@echo "部署到测试环境..."
	# 添加测试环境部署命令

deploy-production:
	@echo "部署到生产环境..."
	# 添加生产环境部署命令
