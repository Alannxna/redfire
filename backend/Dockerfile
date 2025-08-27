# RedFire Backend统一Docker镜像
# 支持After和Backend系统的统一部署

# 多阶段构建 - 基础镜像
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    pkg-config \
    libpq-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libffi-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash redfire
WORKDIR /home/redfire

# 开发阶段
FROM base as development

# 复制依赖文件
COPY requirements.txt pyproject.toml ./

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 安装开发依赖
RUN pip install --no-cache-dir -e .[dev]

# 复制应用代码
COPY . .

# 设置权限
RUN chown -R redfire:redfire /home/redfire
USER redfire

# 暴露端口
EXPOSE 8000 8001 8080 6379

# 开发服务器启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 生产阶段
FROM base as production

# 只安装生产依赖
COPY requirements.txt pyproject.toml ./

# 安装生产依赖（不包括开发工具）
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# 复制应用代码（排除开发文件）
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY config/ ./config/

# 创建必要的目录
RUN mkdir -p logs data temp uploads downloads

# 设置权限
RUN chown -R redfire:redfire /home/redfire
USER redfire

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 生产服务器启动命令
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# 轻量级阶段（仅核心功能）
FROM python:3.11-alpine as lightweight

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装必要的系统依赖
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    curl

# 创建应用目录
WORKDIR /app

# 复制核心依赖
COPY requirements.txt* ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg2-binary redis pydantic

# 复制核心应用代码
COPY src/core/ ./src/core/
COPY src/api/ ./src/api/
COPY src/main.py ./src/

# 暴露端口
EXPOSE 8000

# 轻量级启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]