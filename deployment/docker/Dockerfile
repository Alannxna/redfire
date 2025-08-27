FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制VnPy源码
COPY . .

# 安装VnPy
RUN pip install -e .

# 设置Python路径
ENV PYTHONPATH=/app

# 创建非root用户
RUN useradd -m -u 1000 vnpy && chown -R vnpy:vnpy /app
USER vnpy

# 创建数据目录
RUN mkdir -p /app/data /app/config

# 启动命令
CMD ["python", "-m", "vnpy.trader.cli"]
