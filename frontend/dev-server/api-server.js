// RedFire开发环境API模拟服务器
// ================================

const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8000;

// 中间件
app.use(cors());
app.use(express.json());

// 模拟数据
const mockUsers = [
  { id: 1, username: 'admin', role: 'admin', email: 'admin@redfire.com' },
  { id: 2, username: 'trader', role: 'trader', email: 'trader@redfire.com' },
];

const mockTradingData = {
  stocks: [
    { symbol: 'AAPL', price: 150.25, change: 2.15, percent: 1.45, volume: '50.2M' },
    { symbol: 'TSLA', price: 245.80, change: -5.30, percent: -2.11, volume: '35.8M' },
    { symbol: 'MSFT', price: 310.45, change: 1.85, percent: 0.60, volume: '28.9M' },
  ],
  portfolio: {
    totalValue: 1234567.89,
    todayPnL: 5678.90,
    positions: 15,
    winRate: 78.5,
  },
};

// API路由

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 用户认证
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;
  
  if (username === 'admin' && password === 'admin123') {
    res.json({
      success: true,
      user: mockUsers[0],
      token: 'mock-jwt-token-' + Date.now(),
    });
  } else {
    res.status(401).json({
      success: false,
      message: '用户名或密码错误',
    });
  }
});

// 获取用户信息
app.get('/api/auth/profile', (req, res) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  
  if (token && token.startsWith('mock-jwt-token')) {
    res.json({
      success: true,
      user: mockUsers[0],
    });
  } else {
    res.status(401).json({
      success: false,
      message: '未授权访问',
    });
  }
});

// 获取交易数据
app.get('/api/trading/stocks', (req, res) => {
  res.json({
    success: true,
    data: mockTradingData.stocks,
  });
});

// 获取投资组合
app.get('/api/trading/portfolio', (req, res) => {
  res.json({
    success: true,
    data: mockTradingData.portfolio,
  });
});

// 创建订单
app.post('/api/trading/orders', (req, res) => {
  const { symbol, side, quantity, price } = req.body;
  
  // 模拟订单创建
  setTimeout(() => {
    res.json({
      success: true,
      data: {
        orderId: 'ORDER-' + Date.now(),
        symbol,
        side,
        quantity,
        price,
        status: 'filled',
        timestamp: new Date().toISOString(),
      },
    });
  }, 1000); // 模拟网络延迟
});

// 获取历史数据
app.get('/api/market/history/:symbol', (req, res) => {
  const { symbol } = req.params;
  const { period = '1d' } = req.query;
  
  // 生成模拟K线数据
  const data = [];
  const now = Date.now();
  const interval = period === '1m' ? 60000 : period === '1h' ? 3600000 : 86400000;
  
  for (let i = 100; i >= 0; i--) {
    const timestamp = now - (i * interval);
    const basePrice = 150 + Math.random() * 50;
    const open = basePrice + (Math.random() - 0.5) * 10;
    const close = open + (Math.random() - 0.5) * 5;
    const high = Math.max(open, close) + Math.random() * 3;
    const low = Math.min(open, close) - Math.random() * 3;
    const volume = Math.floor(Math.random() * 1000000);
    
    data.push({
      timestamp,
      open: +open.toFixed(2),
      high: +high.toFixed(2),
      low: +low.toFixed(2),
      close: +close.toFixed(2),
      volume,
    });
  }
  
  res.json({
    success: true,
    data: {
      symbol,
      period,
      data,
    },
  });
});

// 错误处理
app.use((err, req, res, next) => {
  console.error('API错误:', err);
  res.status(500).json({
    success: false,
    message: '服务器内部错误',
  });
});

// 404处理
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: '接口不存在',
  });
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`🚀 RedFire API模拟服务器启动成功`);
  console.log(`📡 端口: ${PORT}`);
  console.log(`🌐 地址: http://localhost:${PORT}`);
  console.log(`❤️  健康检查: http://localhost:${PORT}/health`);
});
