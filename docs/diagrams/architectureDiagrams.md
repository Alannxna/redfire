# 📊 RedFire架构图表

## 📋 概述

本文档包含RedFire项目的各种架构图表，使用Mermaid语法绘制，支持在GitHub、GitLab等平台上直接渲染。

## 🏗️ 系统整体架构图

```mermaid
graph TB
    User[🌐 用户层<br/>Web用户 | 移动用户 | 专业交易员]
    Frontend[🎨 前端层<br/>React + TypeScript<br/>Ant Design + 组件库<br/>移动应用 + 管理后台<br/>专业交易界面]
    Gateway[🔌 API网关层<br/>FastAPI网关<br/>WebSocket + 认证授权]
    Backend[⚙️ 后端层<br/>主交易引擎 + 事件引擎<br/>CTP/IB/OKEX引擎<br/>风险管理 + 数据管理<br/>策略管理 + 微服务架构<br/>DDD架构 + 插件系统<br/>引擎管理器 + 网关接口<br/>模拟网关 + 测试环境<br/>传统应用 + Vue.js后端]
    Data[🗄️ 数据层<br/>PostgreSQL主数据库<br/>Redis缓存层<br/>InfluxDB时序数据<br/>MongoDB文档数据]
    External[🌍 外部接口<br/>CTP期货接口<br/>IB交易接口<br/>OKEX接口<br/>市场数据源]
    
    User --> Frontend
    Frontend --> Gateway
    Gateway --> Backend
    Backend --> Data
    Backend --> External
    Data --> External
    
    classDef userLayer fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef frontendLayer fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef gatewayLayer fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef backendLayer fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef dataLayer fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    classDef externalLayer fill:#fffff0,stroke:#cccc00,stroke-width:2px
    
    class User userLayer
    class Frontend frontendLayer
    class Gateway gatewayLayer
    class Backend backendLayer
    class Data dataLayer
    class External externalLayer
```

## 🔄 数据流架构图

```mermaid
flowchart LR
    Input[📊 数据输入层<br/>市场数据源<br/>用户操作<br/>系统事件<br/>外部API]
    Process[🔄 数据处理层<br/>数据管理应用<br/>事件引擎<br/>策略引擎<br/>风险引擎]
    Execution[💹 交易执行层<br/>交易引擎<br/>网关接口<br/>订单管理<br/>持仓管理]
    Output[📈 数据输出层<br/>实时行情<br/>交易记录<br/>风险报告<br/>策略结果]
    Storage[🗄️ 数据存储层<br/>PostgreSQL主数据库<br/>Redis缓存层<br/>InfluxDB时序数据库<br/>MongoDB文档数据库]
    
    Input --> Process
    Process --> Execution
    Execution --> Output
    Output --> Storage
    Process --> Storage
    
    classDef inputLayer fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef processLayer fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef executionLayer fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef outputLayer fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef storageLayer fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    
    class Input inputLayer
    class Process processLayer
    class Execution executionLayer
    class Output outputLayer
    class Storage storageLayer
```

## 🏗️ 后端架构详细图

```mermaid
graph TB
    MainEngine[🚀 主交易引擎<br/>主控制器<br/>组件管理器]
    EventSystem[⚡ 事件系统<br/>事件分发器<br/>事件队列]
    Management[🔧 管理组件<br/>引擎管理器<br/>插件管理器]
    TradingEngine[💹 交易引擎实现<br/>CTP引擎 (期货交易)<br/>IB引擎 (国际经纪)<br/>OKEX引擎 (加密货币)<br/>模拟网关 (测试环境)]
    AppComponent[📊 应用组件<br/>风险管理应用<br/>数据管理应用<br/>策略管理应用<br/>实时监控、预警]
    Gateway[🌐 网关接口<br/>基础网关抽象<br/>具体网关实现<br/>连接管理<br/>CTP/IB/OKEX接口]
    DataStorage[🗄️ 数据存储<br/>PostgreSQL主数据库<br/>Redis缓存<br/>InfluxDB时序数据<br/>MongoDB文档数据]
    
    MainEngine --> EventSystem
    MainEngine --> Management
    Management --> TradingEngine
    EventSystem --> AppComponent
    TradingEngine --> Gateway
    AppComponent --> DataStorage
    
    classDef mainEngine fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef eventSystem fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef management fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef tradingEngine fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef appComponent fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    classDef gateway fill:#fffff0,stroke:#cccc00,stroke-width:2px
    classDef dataStorage fill:#f0f0ff,stroke:#0066cc,stroke-width:2px
    
    class MainEngine mainEngine
    class EventSystem eventSystem
    class Management management
    class TradingEngine tradingEngine
    class AppComponent appComponent
    class Gateway gateway
    class DataStorage dataStorage
```

## 🎨 前端架构详细图

```mermaid
graph TB
    AppLayer[📱 应用层<br/>Web应用 (React + TypeScript)<br/>移动应用 (React Native)<br/>管理后台 (Ant Design)<br/>专业交易界面]
    SharedLayer[📦 共享包层<br/>UI组件库<br/>业务组件库<br/>类型定义<br/>API客户端]
    BuildTools[🏗️ 构建工具<br/>Turborepo (Monorepo管理)<br/>Vite (快速构建)<br/>TypeScript (类型安全)<br/>ESLint + Prettier]
    Testing[🧪 测试体系<br/>Jest (单元测试)<br/>React Testing Library<br/>Cypress (E2E测试)<br/>Storybook (组件文档)]
    ThemeSystem[🎨 主题系统<br/>主题配置<br/>颜色系统<br/>组件样式<br/>响应式设计]
    Utils[🔧 工具库<br/>日期处理<br/>数据格式化<br/>验证工具<br/>HTTP客户端]
    
    AppLayer --> SharedLayer
    SharedLayer --> BuildTools
    AppLayer --> Testing
    SharedLayer --> ThemeSystem
    BuildTools --> Utils
    
    classDef appLayer fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef sharedLayer fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef buildTools fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef testing fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef themeSystem fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    classDef utils fill:#fffff0,stroke:#cccc00,stroke-width:2px
    
    class AppLayer appLayer
    class SharedLayer sharedLayer
    class BuildTools buildTools
    class Testing testing
    class ThemeSystem themeSystem
    class Utils utils
```

## 🔐 安全架构图

```mermaid
graph TB
    Protection[🛡️ 安全防护层<br/>防火墙<br/>WAF + DDoS防护]
    Auth[🔐 认证授权层<br/>JWT认证<br/>OAuth2.0 + RBAC]
    DataSecurity[🔒 数据安全层<br/>数据加密<br/>传输加密 + 密钥管理]
    Monitoring[📊 监控审计层<br/>访问日志<br/>操作审计 + 异常检测]
    BusinessSecurity[🔄 业务安全层<br/>风险控制<br/>交易限额<br/>异常交易检测<br/>合规检查]
    Alert[🚨 安全告警<br/>实时告警<br/>告警分级<br/>告警通知<br/>告警处理]
    
    Protection --> Auth
    Auth --> DataSecurity
    DataSecurity --> Monitoring
    Monitoring --> BusinessSecurity
    BusinessSecurity --> Alert
    
    classDef protection fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef auth fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef dataSecurity fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef monitoring fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef businessSecurity fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    classDef alert fill:#fffff0,stroke:#cccc00,stroke-width:2px
    
    class Protection protection
    class Auth auth
    class DataSecurity dataSecurity
    class Monitoring monitoring
    class BusinessSecurity businessSecurity
    class Alert alert
```

## 🚀 部署架构图

```mermaid
graph TB
    LoadBalancer[🌐 负载均衡层<br/>Nginx负载均衡器<br/>CDN加速 + SSL终止]
    Gateway[🔌 API网关层<br/>FastAPI网关集群<br/>WebSocket集群]
    AppService[⚙️ 应用服务层<br/>Web应用集群<br/>移动API集群]
    TradingService[💹 交易服务层<br/>交易服务集群<br/>策略服务集群<br/>数据服务集群<br/>风险服务集群]
    DataStorage[🗄️ 数据存储层<br/>PostgreSQL主从<br/>Redis集群<br/>InfluxDB集群<br/>MongoDB集群]
    Monitoring[📊 监控运维层<br/>Prometheus监控<br/>Grafana可视化<br/>ELK日志分析<br/>Jaeger链路追踪]
    
    LoadBalancer --> Gateway
    Gateway --> AppService
    Gateway --> TradingService
    AppService --> DataStorage
    TradingService --> Monitoring
    DataStorage --> Monitoring
    
    classDef loadBalancer fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef gateway fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef appService fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef tradingService fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef dataStorage fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    classDef monitoring fill:#fffff0,stroke:#cccc00,stroke-width:2px
    
    class LoadBalancer loadBalancer
    class Gateway gateway
    class AppService appService
    class TradingService tradingService
    class DataStorage dataStorage
    class Monitoring monitoring
```

## 🔄 事件驱动架构图

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端
    participant Gateway as API网关
    participant EventEngine as 事件引擎
    participant TradingEngine as 交易引擎
    participant RiskEngine as 风险引擎
    participant Database as 数据库
    
    User->>Frontend: 提交订单
    Frontend->>Gateway: 发送订单请求
    Gateway->>EventEngine: 发布订单事件
    EventEngine->>RiskEngine: 风险检查事件
    RiskEngine->>EventEngine: 风险检查结果
    EventEngine->>TradingEngine: 订单执行事件
    TradingEngine->>Database: 保存订单
    TradingEngine->>EventEngine: 订单状态更新
    EventEngine->>Frontend: 推送订单状态
    Frontend->>User: 显示订单状态
```

## 📊 性能监控架构图

```mermaid
graph TB
    App[📱 应用层<br/>Web应用<br/>移动应用<br/>API服务]
    Metrics[📈 指标收集<br/>应用指标<br/>业务指标<br/>系统指标]
    Storage[💾 指标存储<br/>Prometheus<br/>InfluxDB<br/>Elasticsearch]
    Visualization[📊 可视化<br/>Grafana<br/>Kibana<br/>自定义面板]
    Alert[🚨 告警系统<br/>告警规则<br/>告警通知<br/>告警处理]
    
    App --> Metrics
    Metrics --> Storage
    Storage --> Visualization
    Storage --> Alert
    
    classDef app fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef metrics fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef storage fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef visualization fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef alert fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    
    class App app
    class Metrics metrics
    class Storage storage
    class Visualization visualization
    class Alert alert
```

## 🔧 微服务架构图

```mermaid
graph TB
    Gateway[🔌 API网关<br/>路由<br/>认证<br/>限流]
    UserService[👤 用户服务<br/>用户管理<br/>权限控制<br/>认证授权]
    TradingService[💹 交易服务<br/>订单管理<br/>持仓管理<br/>成交记录]
    StrategyService[📊 策略服务<br/>策略管理<br/>回测分析<br/>策略执行]
    DataService[📈 数据服务<br/>市场数据<br/>历史数据<br/>数据清洗]
    RiskService[🛡️ 风险服务<br/>风险计算<br/>限额控制<br/>风险预警]
    NotificationService[📢 通知服务<br/>邮件通知<br/>短信通知<br/>推送通知]
    
    Gateway --> UserService
    Gateway --> TradingService
    Gateway --> StrategyService
    Gateway --> DataService
    Gateway --> RiskService
    Gateway --> NotificationService
    
    TradingService --> RiskService
    StrategyService --> DataService
    StrategyService --> RiskService
    
    classDef gateway fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    classDef userService fill:#fff0f0,stroke:#cc0000,stroke-width:2px
    classDef tradingService fill:#f0fff0,stroke:#00cc00,stroke-width:2px
    classDef strategyService fill:#fff8f0,stroke:#cc6600,stroke-width:2px
    classDef dataService fill:#f8f0ff,stroke:#6600cc,stroke-width:2px
    classDef riskService fill:#fffff0,stroke:#cccc00,stroke-width:2px
    classDef notificationService fill:#f0f8ff,stroke:#0066cc,stroke-width:2px
    
    class Gateway gateway
    class UserService userService
    class TradingService tradingService
    class StrategyService strategyService
    class DataService dataService
    class RiskService riskService
    class NotificationService notificationService
```

## 📋 图表使用说明

### 🎯 图表特点
1. **Mermaid语法**: 所有图表都使用Mermaid语法，支持GitHub、GitLab等平台
2. **层次清晰**: 从系统整体到组件细节，层次分明
3. **关系明确**: 清晰展示各组件间的依赖关系
4. **颜色丰富**: 使用不同颜色区分不同模块

### 🔧 使用方法
1. **直接渲染**: 在支持Mermaid的平台上直接显示
2. **导出图片**: 使用Mermaid Live Editor导出为PNG/SVG
3. **嵌入文档**: 将图表代码嵌入到其他文档中

### 🎨 自定义选项
- 修改颜色: 更改classDef中的fill和stroke属性
- 调整布局: 修改graph的方向（TB/LR/BT/RL）
- 添加样式: 在classDef中添加更多CSS样式

---

*RedFire架构图表 - 可视化系统架构，理解系统设计* 🔥
