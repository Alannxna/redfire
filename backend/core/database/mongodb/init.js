// MongoDB 初始化脚本 for RedFire
// =================================

// 切换到 redfire_logs 数据库
db = db.getSiblingDB('redfire_logs');

// 创建用户
db.createUser({
  user: 'redfire',
  pwd: 'redfire123',
  roles: [
    { role: 'readWrite', db: 'redfire_logs' }
  ]
});

// 创建只读用户
db.createUser({
  user: 'readonly',
  pwd: 'readonly123',
  roles: [
    { role: 'read', db: 'redfire_logs' }
  ]
});

// 创建系统日志集合
db.createCollection('logs', {
  capped: false,
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "level", "category", "message"],
      properties: {
        timestamp: {
          bsonType: "date",
          description: "日志时间戳"
        },
        level: {
          bsonType: "string",
          enum: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
          description: "日志级别"
        },
        category: {
          bsonType: "string",
          enum: ["system", "trading", "strategy", "api", "database", "security", "performance", "audit"],
          description: "日志分类"
        },
        message: {
          bsonType: "string",
          description: "日志消息"
        },
        source: {
          bsonType: "string",
          description: "日志来源"
        },
        user_id: {
          bsonType: "string",
          description: "用户ID"
        },
        session_id: {
          bsonType: "string",
          description: "会话ID"
        },
        request_id: {
          bsonType: "string",
          description: "请求ID"
        }
      }
    }
  }
});

// 创建审计日志集合
db.createCollection('audit_logs', {
  capped: false,
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "user_id", "action", "resource"],
      properties: {
        timestamp: {
          bsonType: "date",
          description: "操作时间"
        },
        user_id: {
          bsonType: "string",
          description: "操作用户ID"
        },
        action: {
          bsonType: "string",
          description: "操作动作"
        },
        resource: {
          bsonType: "string",
          description: "操作资源"
        },
        ip_address: {
          bsonType: "string",
          description: "IP地址"
        },
        user_agent: {
          bsonType: "string",
          description: "用户代理"
        }
      }
    }
  }
});

// 创建性能指标集合
db.createCollection('performance_metrics', {
  capped: false,
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "metric_type", "source", "value"],
      properties: {
        timestamp: {
          bsonType: "date",
          description: "指标时间"
        },
        metric_type: {
          bsonType: "string",
          description: "指标类型"
        },
        source: {
          bsonType: "string",
          description: "指标来源"
        },
        value: {
          bsonType: "number",
          description: "指标值"
        },
        unit: {
          bsonType: "string",
          description: "单位"
        }
      }
    }
  }
});

// 创建系统日志索引
db.logs.createIndex({ "timestamp": -1 });
db.logs.createIndex({ "level": 1 });
db.logs.createIndex({ "category": 1 });
db.logs.createIndex({ "source": 1 });
db.logs.createIndex({ "user_id": 1 });
db.logs.createIndex({ "session_id": 1 });
db.logs.createIndex({ "request_id": 1 });
db.logs.createIndex({ "tags": 1 });

// 复合索引
db.logs.createIndex({ "category": 1, "timestamp": -1 });
db.logs.createIndex({ "level": 1, "timestamp": -1 });
db.logs.createIndex({ "user_id": 1, "timestamp": -1 });
db.logs.createIndex({ "source": 1, "timestamp": -1 });

// 创建审计日志索引
db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "user_id": 1 });
db.audit_logs.createIndex({ "action": 1 });
db.audit_logs.createIndex({ "resource": 1 });
db.audit_logs.createIndex({ "ip_address": 1 });

// 复合索引
db.audit_logs.createIndex({ "user_id": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "action": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "user_id": 1, "action": 1 });

// 创建性能指标索引
db.performance_metrics.createIndex({ "timestamp": -1 });
db.performance_metrics.createIndex({ "metric_type": 1 });
db.performance_metrics.createIndex({ "source": 1 });
db.performance_metrics.createIndex({ "metric_type": 1, "timestamp": -1 });
db.performance_metrics.createIndex({ "source": 1, "timestamp": -1 });

// 创建TTL索引 - 自动清理旧数据
// 系统日志保留30天
db.logs.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 2592000 });

// 审计日志保留90天
db.audit_logs.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 });

// 性能指标保留7天
db.performance_metrics.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 604800 });

// 插入初始化日志
db.logs.insertOne({
  timestamp: new Date(),
  level: "INFO",
  category: "system",
  message: "MongoDB数据库初始化完成",
  source: "database_init",
  data: {
    collections_created: ["logs", "audit_logs", "performance_metrics"],
    indexes_created: true,
    users_created: ["redfire", "readonly"]
  }
});

// 插入系统配置文档
db.createCollection('system_config');
db.system_config.insertMany([
  {
    key: "log_retention_days",
    value: 30,
    description: "系统日志保留天数",
    type: "integer",
    created_at: new Date()
  },
  {
    key: "audit_retention_days", 
    value: 90,
    description: "审计日志保留天数",
    type: "integer",
    created_at: new Date()
  },
  {
    key: "metrics_retention_days",
    value: 7,
    description: "性能指标保留天数", 
    type: "integer",
    created_at: new Date()
  },
  {
    key: "max_log_size",
    value: "10MB",
    description: "单条日志最大大小",
    type: "string",
    created_at: new Date()
  }
]);

// 创建系统配置索引
db.system_config.createIndex({ "key": 1 }, { unique: true });

print("RedFire MongoDB 初始化完成!");
print("创建的集合:", db.getCollectionNames());
print("创建的用户: redfire, readonly");
print("日志保留策略已配置: 系统日志30天, 审计日志90天, 性能指标7天");
