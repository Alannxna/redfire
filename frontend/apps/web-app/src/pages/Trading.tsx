import React, { useState } from 'react';

const TradingPage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('000001');
  const [orderForm, setOrderForm] = useState({
    action: 'buy',
    quantity: 100,
    price: 0,
    type: 'limit'
  });

  const orderData = [
    { time: '09:30:15', symbol: '000001', action: 'buy', quantity: 1000, price: 12.56, status: 'filled' },
    { time: '10:15:32', symbol: '600036', action: 'sell', quantity: 500, price: 45.23, status: 'pending' },
    { time: '11:20:18', symbol: '000002', action: 'buy', quantity: 800, price: 18.92, status: 'filled' },
  ];

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
          💹 交易中心
        </h1>
        <p style={{ margin: 0, color: '#666' }}>
          股票交易和订单管理
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* 主图表区域 */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0 }}>实时行情</h3>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              style={{
                padding: '4px 8px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px'
              }}
            >
              <option value="000001">000001 - 平安银行</option>
              <option value="000002">000002 - 万科A</option>
              <option value="600036">600036 - 招商银行</option>
            </select>
          </div>
          
          <div style={{
            height: '400px',
            backgroundColor: '#f8f9fa',
            border: '2px dashed #dee2e6',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#6c757d'
          }}>
            📈 K线图表区域（{selectedSymbol}）
          </div>
        </div>

        {/* 交易面板 */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ margin: '0 0 16px 0' }}>下单面板</h3>
          
          {/* 买卖切换 */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', marginBottom: '8px' }}>
              <button
                onClick={() => setOrderForm({...orderForm, action: 'buy'})}
                style={{
                  flex: 1,
                  padding: '8px',
                  backgroundColor: orderForm.action === 'buy' ? '#52c41a' : '#f5f5f5',
                  color: orderForm.action === 'buy' ? 'white' : '#333',
                  border: 'none',
                  borderRadius: '4px 0 0 4px',
                  cursor: 'pointer'
                }}
              >
                买入
              </button>
              <button
                onClick={() => setOrderForm({...orderForm, action: 'sell'})}
                style={{
                  flex: 1,
                  padding: '8px',
                  backgroundColor: orderForm.action === 'sell' ? '#ff4d4f' : '#f5f5f5',
                  color: orderForm.action === 'sell' ? 'white' : '#333',
                  border: 'none',
                  borderRadius: '0 4px 4px 0',
                  cursor: 'pointer'
                }}
              >
                卖出
              </button>
            </div>
          </div>

          {/* 订单类型 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px' }}>订单类型</label>
            <select
              value={orderForm.type}
              onChange={(e) => setOrderForm({...orderForm, type: e.target.value})}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px'
              }}
            >
              <option value="limit">限价委托</option>
              <option value="market">市价委托</option>
            </select>
          </div>

          {/* 价格 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px' }}>委托价格</label>
            <input
              type="number"
              value={orderForm.price}
              onChange={(e) => setOrderForm({...orderForm, price: parseFloat(e.target.value)})}
              placeholder="12.56"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* 数量 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px' }}>委托数量</label>
            <input
              type="number"
              value={orderForm.quantity}
              onChange={(e) => setOrderForm({...orderForm, quantity: parseInt(e.target.value)})}
              placeholder="100"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* 提交按钮 */}
          <button
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: orderForm.action === 'buy' ? '#52c41a' : '#ff4d4f',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            {orderForm.action === 'buy' ? '买入' : '卖出'} {selectedSymbol}
          </button>
        </div>
      </div>

      {/* 订单记录 */}
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 16px 0' }}>交易记录</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #d9d9d9' }}>时间</th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #d9d9d9' }}>证券代码</th>
                <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #d9d9d9' }}>操作</th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #d9d9d9' }}>数量</th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #d9d9d9' }}>价格</th>
                <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #d9d9d9' }}>状态</th>
              </tr>
            </thead>
            <tbody>
              {orderData.map((order, index) => (
                <tr key={index}>
                  <td style={{ padding: '12px', borderBottom: '1px solid #f0f0f0' }}>
                    {order.time}
                  </td>
                  <td style={{ padding: '12px', borderBottom: '1px solid #f0f0f0' }}>
                    {order.symbol}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      backgroundColor: order.action === 'buy' ? '#f6ffed' : '#fff2f0',
                      color: order.action === 'buy' ? '#52c41a' : '#ff4d4f',
                      border: `1px solid ${order.action === 'buy' ? '#52c41a' : '#ff4d4f'}`
                    }}>
                      {order.action === 'buy' ? '买入' : '卖出'}
                    </span>
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f0f0f0' }}>
                    {order.quantity.toLocaleString()}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f0f0f0' }}>
                    ¥{order.price.toFixed(2)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      backgroundColor: order.status === 'filled' ? '#f6ffed' : order.status === 'pending' ? '#fff7e6' : '#fff2f0',
                      color: order.status === 'filled' ? '#52c41a' : order.status === 'pending' ? '#faad14' : '#ff4d4f'
                    }}>
                      {order.status === 'filled' ? '已成交' : order.status === 'pending' ? '待成交' : '已撤销'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TradingPage;
