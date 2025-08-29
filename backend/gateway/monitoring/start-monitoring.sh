#!/bin/bash

# RedFire监控系统一键启动脚本
# 基于完善的Docker配置和监控组件

set -e

echo "🚀 启动RedFire监控系统..."

# 检查Docker和docker-compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建监控配置目录..."
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/logstash/pipeline
mkdir -p monitoring/logstash/config
mkdir -p logs

# 创建Prometheus配置文件
echo "⚙️ 创建Prometheus配置..."
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'redfire-gateway'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redfire-services'
    static_configs:
      - targets: ['user-service:8001', 'strategy-service:8002']
    metrics_path: '/health'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
EOF

# 创建Grafana数据源配置
echo "📊 创建Grafana数据源配置..."
cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# 创建Grafana仪表板配置
echo "📈 创建Grafana仪表板配置..."
cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'RedFire Dashboards'
    orgId: 1
    folder: 'RedFire'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# 检查端口占用
echo "🔍 检查端口占用情况..."
PORTS=(3000 5044 5601 6379 8000 8001 8002 9090 9200 9300 9600)
OCCUPIED_PORTS=()

for port in "${PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        OCCUPIED_PORTS+=($port)
    fi
done

if [ ${#OCCUPIED_PORTS[@]} -gt 0 ]; then
    echo "⚠️  以下端口已被占用: ${OCCUPIED_PORTS[*]}"
    echo "请确保这些端口可用，或修改docker-compose.yml中的端口映射"
    read -p "是否继续启动？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 拉取Docker镜像
echo "📥 拉取Docker镜像..."
docker-compose pull

# 构建本地镜像
echo "🔨 构建应用镜像..."
docker-compose build

# 启动服务
echo "🚀 启动监控服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 健康检查
echo "🏥 执行健康检查..."

# 检查Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus (http://localhost:9090) - 运行正常"
else
    echo "❌ Prometheus - 启动失败或未就绪"
fi

# 检查Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana (http://localhost:3000) - 运行正常"
    echo "   默认登录: admin/admin"
else
    echo "❌ Grafana - 启动失败或未就绪"
fi

# 检查Elasticsearch
if curl -s http://localhost:9200/_cluster/health > /dev/null; then
    echo "✅ Elasticsearch (http://localhost:9200) - 运行正常"
else
    echo "❌ Elasticsearch - 启动失败或未就绪"
fi

# 检查Kibana
sleep 10  # Kibana需要更多时间启动
if curl -s http://localhost:5601/api/status > /dev/null; then
    echo "✅ Kibana (http://localhost:5601) - 运行正常"
else
    echo "⏳ Kibana - 仍在启动中，请稍后访问 http://localhost:5601"
fi

# 检查Redis
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis - 运行正常"
else
    echo "❌ Redis - 启动失败"
fi

echo ""
echo "🎉 RedFire监控系统启动完成！"
echo ""
echo "📊 访问地址:"
echo "  - Grafana仪表板: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Kibana日志分析: http://localhost:5601"
echo "  - Elasticsearch: http://localhost:9200"
echo ""
echo "🔧 管理命令:"
echo "  查看日志: docker-compose logs -f [service_name]"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart [service_name]"
echo "  查看状态: docker-compose ps"
echo ""
echo "📚 更多信息请查看: docs/operations/monitoringGuide.md"
