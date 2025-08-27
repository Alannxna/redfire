# RedFire后端 Makefile

.PHONY: help install test lint format clean dev prod

help: ## 显示帮助信息
	@echo "RedFire后端服务 - 可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## 运行测试
	pytest tests/ -v --cov=apps --cov=shared --cov=core

lint: ## 代码检查
	flake8 apps/ shared/ core/
	mypy apps/ shared/ core/

format: ## 代码格式化
	black apps/ shared/ core/
	isort apps/ shared/ core/

clean: ## 清理构建文件
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	docker-compose down -v

dev: ## 启动开发环境
	docker-compose up -d postgres redis kafka zookeeper
	@echo "开发环境已启动，请手动启动各个微服务"

prod: ## 启动生产环境
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

migrate: ## 数据库迁移
	cd apps/trading-service && alembic upgrade head
	cd apps/strategy-service && alembic upgrade head
	cd apps/data-service && alembic upgrade head
	cd apps/user-service && alembic upgrade head

logs: ## 查看服务日志
	docker-compose logs -f

restart: ## 重启所有服务
	docker-compose restart
