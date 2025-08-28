# 配置文件迁移报告

**生成时间**: 2025-08-28T15:24:03.056970
**模式**: ACTUAL MIGRATION
**总计迁移**: 17 个文件
**错误数量**: 0

## 迁移详情

- ✅ **migrate**: backend\config.yaml -> backend\config\shared\development\application.yaml
- ✅ **migrate**: backend\.env -> backend\config\shared\development\application.yaml
- ✅ **migrate**: backend\docker-compose.yml -> backend\config\shared\development\application.yaml
- ✅ **migrate**: backend\config_service\config\development.yaml -> backend\config\services\config-service\development\application.yaml
- ✅ **migrate**: backend\core\vnpy-engine\config\.env -> backend\config\services\vnpy-service\development\application.yaml
- ✅ **migrate**: backend\core\vnpy-engine\config\config.env -> backend\config\services\vnpy-service\development\vnpy.yaml
- ✅ **migrate**: backend\core\vnpy-engine\config\backend\config.env -> backend\config\services\vnpy-service\development\vnpy.yaml
- ✅ **migrate**: backend\core\vnpy-engine\config\vt_setting.json -> backend\config\services\vnpy-service\development\vnpy.yaml
- ✅ **migrate**: backend\core\database\docker-compose.database.yml -> backend\config\shared\development\database.yaml
- ✅ **migrate**: backend\gateway\docker-compose.yml -> backend\config\services\gateway-service\development\application.yaml
- ✅ **migrate**: backend\gateway\monitoring\logstash\config\logstash.yml -> backend\config\services\gateway-service\development\logging.yaml
- ✅ **migrate**: backend\legacy\core\config\.env -> backend\config\services\legacy-service\development\application.yaml
- ✅ **migrate**: backend\shared\config\config\shared\development\database.yaml -> backend\config\shared\development\database.yaml
- ✅ **migrate**: backend\shared\config\config\trading\development\config.yaml -> backend\config\services\trading-service\development\application.yaml
- ✅ **migrate**: backend\shared\config\config\user\development\config.yaml -> backend\config\services\user-service\development\application.yaml
- ✅ **migrate**: backend\gateway\monitoring\grafana\dashboards\redfire-system-overview.json -> backend\config\services\monitor-service\development\dashboards\redfire-system-overview.json
- ✅ **migrate**: backend\gateway\monitoring\grafana\dashboards\redfire-vnpy-trading.json -> backend\config\services\monitor-service\development\dashboards\redfire-vnpy-trading.json

## 下一步

1. 验证迁移后的配置文件正确性
2. 更新服务中的配置文件加载路径
3. 测试所有服务的配置加载
4. 删除旧的配置文件（确认无误后）