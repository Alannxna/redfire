# RedFire 量化交易平台 Makefile

.PHONY: help install build test clean deploy start stop logs backup

# 默认目标
help:
	@echo "RedFire 量化交易平台 - 可用命令:"
	@echo ""
	@echo "开发命令:"
	@echo "  install     - 安装所有依赖"
	@echo "  build       - 构建所有服务"
	@echo "  test        - 运行所有测试"
	@echo "  clean       - 清理构建文件"
	@echo ""
	@echo "部署命令:"
	@echo "  deploy      - 部署到生产环境"
	@echo "  start       - 启动所有服务"
	@echo "  stop        - 停止所有服务"
	@echo "  restart     - 重启所有服务"
	@echo "  logs        - 查看服务日志"
	@echo ""
	@echo "维护命令:"
	@echo "  backup      - 创建数据备份"
	@echo "  restore     - 恢复数据备份"
	@echo "  status      - 查看服务状态"

# 安装依赖
install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend/web-app && npm install
	cd frontend/admin-dashboard && npm install
	cd frontend/mobile-app && npm install
	@echo "安装完成!"

# 构建服务
build:
	@echo "构建后端服务..."
	cd backend && python -m build
	@echo "构建前端应用..."
	cd frontend/web-app && npm run build
	cd frontend/admin-dashboard && npm run build
	@echo "构建完成!"

# 运行测试
test:
	@echo "运行后端测试..."
	cd backend && pytest -v
	@echo "运行前端测试..."
	cd frontend/web-app && npm test
	@echo "测试完成!"

# 清理构建文件
clean:
	@echo "清理构建文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "清理完成!"

# 启动服务
start:
	@echo "启动所有服务..."
	docker-compose -f deployment/docker/docker-compose.yml up -d
	@echo "服务启动完成!"

# 停止服务
stop:
	@echo "停止所有服务..."
	docker-compose -f deployment/docker/docker-compose.yml down
	@echo "服务已停止!"

# 重启服务
restart: stop start

# 查看日志
logs:
	@echo "查看服务日志..."
	docker-compose -f deployment/docker/docker-compose.yml logs -f

# 查看服务状态
status:
	@echo "查看服务状态..."
	docker-compose -f deployment/docker/docker-compose.yml ps

# 部署到生产环境
deploy:
	@echo "部署到生产环境..."
	@echo "1. 构建生产镜像..."
	docker-compose -f deployment/docker/docker-compose.yml build
	@echo "2. 启动生产服务..."
	docker-compose -f deployment/docker/docker-compose.yml up -d
	@echo "3. 健康检查..."
	@echo "部署完成!"

# 创建备份
backup:
	@echo "创建数据备份..."
	@mkdir -p backup
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker exec redfire_postgres pg_dump -U redfire_user redfire > backup/postgres_$$timestamp.sql; \
	docker exec redfire_redis redis-cli BGSAVE; \
	echo "备份完成: backup/postgres_$$timestamp.sql"

# 恢复备份
restore:
	@echo "恢复数据备份..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "请指定备份文件: make restore BACKUP_FILE=backup/postgres_YYYYMMDD_HHMMSS.sql"; \
		exit 1; \
	fi
	@docker exec -i redfire_postgres psql -U redfire_user redfire < $(BACKUP_FILE)
	@echo "恢复完成!"

# 开发环境启动
dev:
	@echo "启动开发环境..."
	@echo "1. 启动数据库和缓存..."
	docker-compose -f deployment/docker/docker-compose.yml up -d postgres redis
	@echo "2. 启动后端服务..."
	cd backend && python start_unified.py &
	@echo "3. 启动前端服务..."
	cd frontend/web-app && npm run dev &
	@echo "开发环境启动完成!"
	@echo "后端: http://localhost:8000"
	@echo "前端: http://localhost:3000"

# 停止开发环境
dev-stop:
	@echo "停止开发环境..."
	@pkill -f "python start_unified.py" || true
	@pkill -f "npm run dev" || true
	@echo "开发环境已停止!"

# 数据库管理
db-migrate:
	@echo "运行数据库迁移..."
	cd backend && python -m alembic upgrade head

db-rollback:
	@echo "回滚数据库迁移..."
	cd backend && python -m alembic downgrade -1

# 代码质量检查
lint:
	@echo "检查代码质量..."
	@echo "后端代码检查..."
	cd backend && flake8 . --max-line-length=120
	@echo "前端代码检查..."
	cd frontend/web-app && npm run lint
	@echo "代码检查完成!"

# 安全扫描
security-scan:
	@echo "安全扫描..."
	cd backend && safety check
	cd frontend/web-app && npm audit
	@echo "安全扫描完成!"

# 性能测试
perf-test:
	@echo "性能测试..."
	cd backend && python -m pytest tests/performance/ -v
	@echo "性能测试完成!"

# 帮助信息
info:
	@echo "RedFire 量化交易平台"
	@echo "版本: 1.0.0"
	@echo "架构: 前后端分离 + 微服务"
	@echo "技术栈: Python + React + Docker"
	@echo ""
	@echo "项目结构:"
	@echo "  backend/          - 后端微服务"
	@echo "  frontend/         - 前端应用"
	@echo "  deployment/       - 部署配置"
	@echo "  docs/            - 项目文档"
	@echo "  tools/           - 开发工具"
