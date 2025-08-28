# Deployment 模块介绍

## 🎯 概述

`deployment` 是 RedFire 量化交易平台的部署管理模块，提供完整的系统部署解决方案，包括容器化部署、自动化部署、云原生部署等。该模块支持多种部署环境和部署方式，确保系统的高可用性和可扩展性。

## 📁 目录结构

```
deployment/
├── docker/                   # 🐳 Docker部署
├── scripts/                  # 📜 部署脚本
├── terraform/                # 🏗️ Terraform基础设施
└── kubernetes/               # ☸️ Kubernetes部署
```

## 🐳 Docker部署 (`docker/`)

### **作用**: 容器化部署配置

### **主要组件**:

#### 1. **Dockerfile**
```dockerfile
# 后端服务Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. **Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端服务
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/redfire
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  # 前端服务
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  # 数据库服务
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=redfire
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis服务
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  # Nginx服务
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
```

#### 3. **多阶段构建**
```dockerfile
# 多阶段构建Dockerfile
# 构建阶段
FROM node:16 AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

# 运行阶段
FROM nginx:alpine
COPY --from=frontend-builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📜 部署脚本 (`scripts/`)

### **作用**: 自动化部署脚本

### **脚本类型**:

#### 1. **环境准备脚本**
```bash
#!/bin/bash
# setup_environment.sh

echo "开始准备部署环境..."

# 检查系统要求
check_system_requirements() {
    echo "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo "Docker未安装，正在安装..."
        curl -fsSL https://get.docker.com | sh
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "Docker Compose未安装，正在安装..."
        sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # 检查磁盘空间
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ $available_space -lt 10485760 ]; then
        echo "警告: 磁盘空间不足 (需要至少10GB)"
        exit 1
    fi
}

# 创建必要目录
create_directories() {
    echo "创建必要目录..."
    mkdir -p /opt/redfire/{data,logs,config}
    mkdir -p /opt/redfire/data/{market_data,factor_data,research_data}
    mkdir -p /opt/redfire/logs/{application,access,error}
}

# 设置权限
setup_permissions() {
    echo "设置权限..."
    sudo chown -R $USER:$USER /opt/redfire
    chmod -R 755 /opt/redfire
}

# 主函数
main() {
    check_system_requirements
    create_directories
    setup_permissions
    echo "环境准备完成！"
}

main "$@"
```

#### 2. **部署脚本**
```bash
#!/bin/bash
# deploy.sh

set -e

# 配置变量
PROJECT_NAME="redfire"
DEPLOY_ENV="${1:-production}"
DOCKER_REGISTRY="your-registry.com"

echo "开始部署 RedFire 到 $DEPLOY_ENV 环境..."

# 拉取最新代码
pull_latest_code() {
    echo "拉取最新代码..."
    git pull origin main
}

# 构建镜像
build_images() {
    echo "构建Docker镜像..."
    
    # 构建后端镜像
    docker build -t $DOCKER_REGISTRY/redfire-backend:latest ./backend
    
    # 构建前端镜像
    docker build -t $DOCKER_REGISTRY/redfire-frontend:latest ./frontend
    
    # 推送镜像
    docker push $DOCKER_REGISTRY/redfire-backend:latest
    docker push $DOCKER_REGISTRY/redfire-frontend:latest
}

# 部署服务
deploy_services() {
    echo "部署服务..."
    
    # 停止现有服务
    docker-compose down
    
    # 拉取最新镜像
    docker-compose pull
    
    # 启动服务
    docker-compose up -d
    
    # 等待服务启动
    sleep 30
    
    # 检查服务状态
    check_service_health
}

# 健康检查
check_service_health() {
    echo "检查服务健康状态..."
    
    # 检查后端服务
    if curl -f http://localhost:8000/health; then
        echo "后端服务健康"
    else
        echo "后端服务异常"
        exit 1
    fi
    
    # 检查前端服务
    if curl -f http://localhost:3000; then
        echo "前端服务健康"
    else
        echo "前端服务异常"
        exit 1
    fi
}

# 数据库迁移
run_migrations() {
    echo "运行数据库迁移..."
    docker-compose exec backend python manage.py migrate
}

# 清理旧镜像
cleanup_old_images() {
    echo "清理旧镜像..."
    docker image prune -f
}

# 主函数
main() {
    pull_latest_code
    build_images
    deploy_services
    run_migrations
    cleanup_old_images
    echo "部署完成！"
}

main "$@"
```

#### 3. **回滚脚本**
```bash
#!/bin/bash
# rollback.sh

set -e

VERSION="${1:-previous}"
echo "回滚到版本: $VERSION"

# 停止服务
docker-compose down

# 切换到指定版本
git checkout $VERSION

# 重新部署
docker-compose up -d

# 健康检查
sleep 30
check_service_health

echo "回滚完成！"
```

## 🏗️ Terraform基础设施 (`terraform/`)

### **作用**: 基础设施即代码管理

### **主要组件**:

#### 1. **主配置文件**
```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket = "redfire-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC配置
module "vpc" {
  source = "./modules/vpc"
  
  vpc_name = "redfire-vpc"
  cidr_block = "10.0.0.0/16"
  
  public_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.3.0/24", "10.0.4.0/24"]
}

# ECS集群
module "ecs" {
  source = "./modules/ecs"
  
  cluster_name = "redfire-cluster"
  vpc_id = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
}

# RDS数据库
module "rds" {
  source = "./modules/rds"
  
  db_name = "redfire"
  db_username = var.db_username
  db_password = var.db_password
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"
  
  cluster_name = "redfire-redis"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}
```

#### 2. **变量定义**
```hcl
# variables.tf
variable "aws_region" {
  description = "AWS区域"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "部署环境"
  type        = string
  default     = "production"
}

variable "db_username" {
  description = "数据库用户名"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "数据库密码"
  type        = string
  sensitive   = true
}

variable "instance_type" {
  description = "EC2实例类型"
  type        = string
  default     = "t3.medium"
}
```

#### 3. **输出定义**
```hcl
# outputs.tf
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "cluster_name" {
  description = "ECS集群名称"
  value       = module.ecs.cluster_name
}

output "db_endpoint" {
  description = "数据库端点"
  value       = module.rds.db_endpoint
}

output "redis_endpoint" {
  description = "Redis端点"
  value       = module.redis.endpoint
}
```

## ☸️ Kubernetes部署 (`kubernetes/`)

### **作用**: Kubernetes集群部署配置

### **主要组件**:

#### 1. **命名空间配置**
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: redfire
  labels:
    name: redfire
    environment: production
```

#### 2. **ConfigMap配置**
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redfire-config
  namespace: redfire
data:
  config.yaml: |
    database:
      url: "postgresql://user:pass@redfire-db:5432/redfire"
    redis:
      url: "redis://redfire-redis:6379"
    app:
      debug: false
      secret_key: "your-secret-key"
      host: "0.0.0.0"
      port: 8000
```

#### 3. **Secret配置**
```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: redfire-secrets
  namespace: redfire
type: Opaque
data:
  db-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-jwt-secret>
```

#### 4. **后端服务部署**
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redfire-backend
  namespace: redfire
spec:
  replicas: 3
  selector:
    matchLabels:
      app: redfire-backend
  template:
    metadata:
      labels:
        app: redfire-backend
    spec:
      containers:
      - name: backend
        image: redfire/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: redfire-config
              key: database_url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redfire-config
              key: redis_url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: redfire-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 5. **服务配置**
```yaml
# backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: redfire-backend-service
  namespace: redfire
spec:
  selector:
    app: redfire-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### 6. **Ingress配置**
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: redfire-ingress
  namespace: redfire
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - redfire.example.com
    secretName: redfire-tls
  rules:
  - host: redfire.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: redfire-backend-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: redfire-frontend-service
            port:
              number: 80
```

#### 7. **水平Pod自动扩缩容**
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: redfire-backend-hpa
  namespace: redfire
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: redfire-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🔧 部署工具

### **1. 部署状态监控**
```python
class DeploymentMonitor:
    def __init__(self, k8s_client):
        self.k8s_client = k8s_client
    
    async def check_deployment_status(self, namespace, deployment_name):
        """检查部署状态"""
        try:
            deployment = self.k8s_client.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            
            status = {
                "name": deployment.metadata.name,
                "replicas": deployment.spec.replicas,
                "available": deployment.status.available_replicas,
                "ready": deployment.status.ready_replicas,
                "updated": deployment.status.updated_replicas,
                "conditions": deployment.status.conditions
            }
            
            return status
        except Exception as e:
            return {"error": str(e)}
    
    async def check_pod_status(self, namespace, label_selector):
        """检查Pod状态"""
        try:
            pods = self.k8s_client.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            pod_statuses = []
            for pod in pods.items:
                status = {
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "ready": pod.status.ready,
                    "restart_count": pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0
                }
                pod_statuses.append(status)
            
            return pod_statuses
        except Exception as e:
            return {"error": str(e)}
```

### **2. 自动扩缩容管理**
```python
class AutoScaler:
    def __init__(self, k8s_client):
        self.k8s_client = k8s_client
    
    async def scale_deployment(self, namespace, deployment_name, replicas):
        """扩缩容部署"""
        try:
            # 获取当前部署
            deployment = self.k8s_client.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            
            # 更新副本数
            deployment.spec.replicas = replicas
            
            # 应用更新
            self.k8s_client.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            return {"success": True, "replicas": replicas}
        except Exception as e:
            return {"error": str(e)}
    
    async def auto_scale_based_on_metrics(self, namespace, deployment_name):
        """基于指标自动扩缩容"""
        # 获取CPU和内存使用率
        cpu_usage = await self.get_cpu_usage(namespace, deployment_name)
        memory_usage = await self.get_memory_usage(namespace, deployment_name)
        
        # 获取当前副本数
        current_replicas = await self.get_current_replicas(namespace, deployment_name)
        
        # 计算目标副本数
        target_replicas = self.calculate_target_replicas(
            cpu_usage, memory_usage, current_replicas
        )
        
        # 执行扩缩容
        if target_replicas != current_replicas:
            await self.scale_deployment(namespace, deployment_name, target_replicas)
```

## 📊 部署监控

### **1. 部署指标监控**
```python
class DeploymentMetrics:
    def __init__(self, prometheus_client):
        self.prometheus = prometheus_client
    
    async def get_deployment_metrics(self, namespace, deployment_name):
        """获取部署指标"""
        metrics = {}
        
        # CPU使用率
        cpu_query = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod=~"{deployment_name}-.*"}}[5m])'
        cpu_result = await self.prometheus.query(cpu_query)
        metrics['cpu_usage'] = cpu_result
        
        # 内存使用率
        memory_query = f'container_memory_usage_bytes{{namespace="{namespace}",pod=~"{deployment_name}-.*"}}'
        memory_result = await self.prometheus.query(memory_query)
        metrics['memory_usage'] = memory_result
        
        # 请求延迟
        latency_query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{namespace="{namespace}",service="{deployment_name}"}}[5m]))'
        latency_result = await self.prometheus.query(latency_query)
        metrics['request_latency'] = latency_result
        
        return metrics
```

### **2. 部署告警**
```yaml
# prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: redfire-alerts
  namespace: redfire
spec:
  groups:
  - name: redfire.rules
    rules:
    - alert: HighCPUUsage
      expr: rate(container_cpu_usage_seconds_total{namespace="redfire"}[5m]) > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage detected"
        description: "CPU usage is above 80% for 5 minutes"
    
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes{namespace="redfire"} / container_spec_memory_limit_bytes{namespace="redfire"} > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage detected"
        description: "Memory usage is above 80% for 5 minutes"
    
    - alert: PodRestarting
      expr: increase(kube_pod_container_status_restarts_total{namespace="redfire"}[5m]) > 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Pod is restarting frequently"
        description: "Pod has restarted more than 0 times in the last 5 minutes"
```

## 🚀 部署最佳实践

### **1. 蓝绿部署**
```bash
#!/bin/bash
# blue-green-deployment.sh

# 当前生产环境是蓝色
CURRENT_COLOR="blue"
NEW_COLOR="green"

echo "开始蓝绿部署..."

# 部署新版本到绿色环境
deploy_to_green() {
    echo "部署到绿色环境..."
    kubectl apply -f k8s/green/
    
    # 等待绿色环境就绪
    kubectl wait --for=condition=ready pod -l app=redfire-backend -n redfire-green --timeout=300s
}

# 切换流量到绿色环境
switch_traffic() {
    echo "切换流量到绿色环境..."
    kubectl patch ingress redfire-ingress -n redfire -p '{"spec":{"rules":[{"host":"redfire.example.com","http":{"paths":[{"path":"/api","pathType":"Prefix","backend":{"service":{"name":"redfire-backend-service-green","port":{"number":80}}}}]}}]}}'
}

# 验证新环境
verify_green() {
    echo "验证绿色环境..."
    for i in {1..10}; do
        if curl -f http://redfire.example.com/api/health; then
            echo "绿色环境验证成功"
            return 0
        fi
        sleep 10
    done
    echo "绿色环境验证失败"
    return 1
}

# 回滚到蓝色环境
rollback_to_blue() {
    echo "回滚到蓝色环境..."
    kubectl patch ingress redfire-ingress -n redfire -p '{"spec":{"rules":[{"host":"redfire.example.com","http":{"paths":[{"path":"/api","pathType":"Prefix","backend":{"service":{"name":"redfire-backend-service-blue","port":{"number":80}}}}]}}]}}'
}

# 主函数
main() {
    deploy_to_green
    
    if verify_green; then
        switch_traffic
        echo "蓝绿部署成功！"
    else
        rollback_to_blue
        echo "蓝绿部署失败，已回滚！"
        exit 1
    fi
}

main "$@"
```

### **2. 金丝雀部署**
```yaml
# canary-deployment.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: redfire-backend
  namespace: redfire
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: redfire-backend
  progressDeadlineSeconds: 600
  service:
    port: 80
    targetPort: 8000
  analysis:
    interval: 30s
    threshold: 10
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
    webhooks:
      - name: load-test
        url: http://flagger-loadtester.redfire/
        timeout: 5s
        metadata:
          cmd: "hey -z 1m -q 10 -c 2 http://redfire-backend-canary.redfire:80/"
```

---

**总结**: Deployment模块提供了完整的部署解决方案，支持Docker容器化、Kubernetes集群部署、Terraform基础设施管理等多种部署方式。通过自动化脚本、监控告警和最佳实践，确保系统的高可用性、可扩展性和稳定性。
