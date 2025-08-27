import React from 'react';

const SimplePage: React.FC<{ title: string; icon: string; description: string }> = ({ title, icon, description }) => {
  return (
    <div style={{ padding: '0' }}>
      {/* 页面标题 */}
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '8px',
        marginBottom: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', color: '#333' }}>
          {icon} {title}
        </h1>
        <p style={{ margin: 0, color: '#666' }}>
          {description}
        </p>
      </div>

      {/* 主要内容 */}
      <div style={{
        backgroundColor: 'white',
        padding: '60px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        textAlign: 'center',
        minHeight: '400px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>
          {icon}
        </div>
        <h3 style={{ color: '#333', marginBottom: '8px' }}>
          {title}功能正在开发中
        </h3>
        <p style={{ color: '#666' }}>
          敬请期待更多功能上线
        </p>
        
        <div style={{
          marginTop: '32px',
          padding: '16px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>计划功能:</h4>
          <ul style={{ 
            textAlign: 'left', 
            margin: 0, 
            padding: '0 0 0 20px', 
            color: '#666',
            fontSize: '14px'
          }}>
            <li>实时数据更新</li>
            <li>交互式图表</li>
            <li>高级配置选项</li>
            <li>数据导出功能</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// 策略管理页面
export const StrategyPage: React.FC = () => (
  <SimplePage 
    title="策略管理" 
    icon="🧠" 
    description="交易策略的创建、测试和优化"
  />
);

// 市场数据页面
export const DataPage: React.FC = () => (
  <SimplePage 
    title="市场数据" 
    icon="📈" 
    description="实时行情数据和历史数据分析"
  />
);

// 风险控制页面
export const RiskPage: React.FC = () => (
  <SimplePage 
    title="风险控制" 
    icon="🛡️" 
    description="投资组合风险监控和管理"
  />
);

// 系统设置页面
export const SettingsPage: React.FC = () => (
  <SimplePage 
    title="系统设置" 
    icon="⚙️" 
    description="账户设置和系统配置"
  />
);
