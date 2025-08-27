import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // 模拟数据
  const statsData = [
    {
      title: '总资产',
      value: '¥1,234,567.89',
      change: '+2.5%',
      trend: 'up'
    },
    {
      title: '今日盈亏',
      value: '¥+12,345.67',
      change: '+1.2%',
      trend: 'up'
    },
    {
      title: '策略数量',
      value: '8个',
      change: '活跃中',
      trend: 'neutral'
    },
    {
      title: '活跃交易',
      value: '15笔',
      change: '本日',
      trend: 'neutral'
    },
  ];

  const positions = [
    { symbol: '000001', name: '平安银行', quantity: 1000, price: 12.56, pnl: 1256.78 },
    { symbol: '000002', name: '万科A', quantity: 500, price: 18.92, pnl: -892.45 },
    { symbol: '600036', name: '招商银行', quantity: 800, price: 45.23, pnl: 2341.56 },
  ];

  return (
    <div style={{ padding: '0' }}>
      {/* 欢迎信息 */}
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '8px',
        marginBottom: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', color: '#333' }}>
          欢迎回来，{user?.username}！
        </h1>
        <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
          今天是 {new Date().toLocaleDateString('zh-CN', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            weekday: 'long'
          })}，祝您交易愉快
        </p>
      </div>

      {/* 统计卡片 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        {statsData.map((stat, index) => (
          <div key={index} style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderLeft: `4px solid ${
              stat.trend === 'up' ? '#52c41a' : 
              stat.trend === 'down' ? '#ff4d4f' : '#1890ff'
            }`
          }}>
            <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
              {stat.title}
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#333', marginBottom: '4px' }}>
              {stat.value}
            </div>
            <div style={{ 
              fontSize: '12px', 
              color: stat.trend === 'up' ? '#52c41a' : stat.trend === 'down' ? '#ff4d4f' : '#666'
            }}>
              {stat.change}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* 主要内容区 */}
        <div>
          {/* 图表区域 */}
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '24px'
          }}>
            <h3 style={{ margin: '0 0 16px 0' }}>市场走势</h3>
            <div style={{
              height: '300px',
              backgroundColor: '#f8f9fa',
              border: '2px dashed #dee2e6',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6c757d'
            }}>
              📈 交易图表区域（待接入实时数据）
            </div>
          </div>

          {/* 持仓明细 */}
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ margin: '0 0 16px 0' }}>当前持仓</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f5f5f5' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #d9d9d9' }}>证券代码</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #d9d9d9' }}>证券名称</th>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #d9d9d9' }}>持仓量</th>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #d9d9d9' }}>当前价格</th>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #d9d9d9' }}>盈亏</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((position, index) => (
                    <tr key={index}>
                      <td style={{ padding: '12px', borderBottom: '1px solid #f0f0f0' }}>
                        {position.symbol}
                      </td>
                      <td style={{ padding: '12px', borderBottom: '1px solid #f0f0f0' }}>
                        {position.name}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f0f0f0' }}>
                        {position.quantity.toLocaleString()}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f0f0f0' }}>
                        ¥{position.price.toFixed(2)}
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'right', 
                        borderBottom: '1px solid #f0f0f0',
                        color: position.pnl >= 0 ? '#52c41a' : '#ff4d4f',
                        fontWeight: '500'
                      }}>
                        {position.pnl >= 0 ? '+' : ''}¥{position.pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* 侧边信息 */}
        <div>
          {/* 市场概览 */}
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '16px'
          }}>
            <h4 style={{ margin: '0 0 16px 0' }}>市场概览</h4>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>上证指数</span>
                <span style={{ color: '#52c41a', fontWeight: '500' }}>↗ 3,245.67</span>
              </div>
              <div style={{ fontSize: '12px', color: '#52c41a' }}>+1.23%</div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>深证成指</span>
                <span style={{ color: '#ff4d4f', fontWeight: '500' }}>↘ 11,234.56</span>
              </div>
              <div style={{ fontSize: '12px', color: '#ff4d4f' }}>-0.45%</div>
            </div>
          </div>

          {/* 策略表现 */}
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '16px'
          }}>
            <h4 style={{ margin: '0 0 16px 0' }}>策略表现</h4>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '14px' }}>总体收益率</span>
                <span style={{ fontSize: '14px', color: '#52c41a' }}>75%</span>
              </div>
              <div style={{ 
                height: '8px', 
                backgroundColor: '#f5f5f5', 
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: '75%',
                  backgroundColor: '#52c41a',
                  borderRadius: '4px'
                }}></div>
              </div>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '14px' }}>最大回撤</span>
                <span style={{ fontSize: '14px', color: '#ff4d4f' }}>15%</span>
              </div>
              <div style={{ 
                height: '8px', 
                backgroundColor: '#f5f5f5', 
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: '15%',
                  backgroundColor: '#ff4d4f',
                  borderRadius: '4px'
                }}></div>
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '14px' }}>胜率</span>
                <span style={{ fontSize: '14px', color: '#1890ff' }}>68%</span>
              </div>
              <div style={{ 
                height: '8px', 
                backgroundColor: '#f5f5f5', 
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: '68%',
                  backgroundColor: '#1890ff',
                  borderRadius: '4px'
                }}></div>
              </div>
            </div>
          </div>

          {/* 快速操作 */}
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ margin: '0 0 16px 0' }}>快速操作</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button style={{
                padding: '8px 16px',
                backgroundColor: '#1890ff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}>
                新建交易
              </button>
              <button style={{
                padding: '8px 16px',
                backgroundColor: '#52c41a',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}>
                策略回测
              </button>
              <button style={{
                padding: '8px 16px',
                backgroundColor: '#faad14',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}>
                风险检查
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
