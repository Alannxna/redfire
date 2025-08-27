// RedFire开发环境WebSocket模拟服务器
// ====================================

const WebSocket = require('ws');

const PORT = process.env.PORT || 8001;

// 创建WebSocket服务器
const wss = new WebSocket.Server({ 
  port: PORT,
  path: '/ws'
});

console.log(`🚀 RedFire WebSocket模拟服务器启动成功`);
console.log(`📡 端口: ${PORT}`);
console.log(`🌐 地址: ws://localhost:${PORT}/ws`);

// 模拟交易数据
const mockSymbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA'];

// 生成随机价格数据
function generatePriceData(symbol) {
  const basePrice = 100 + Math.random() * 200;
  const change = (Math.random() - 0.5) * 10;
  const percent = (change / basePrice) * 100;
  
  return {
    type: 'price_update',
    data: {
      symbol,
      price: +(basePrice + change).toFixed(2),
      change: +change.toFixed(2),
      percent: +percent.toFixed(2),
      volume: Math.floor(Math.random() * 1000000),
      timestamp: Date.now(),
    },
  };
}

// 生成交易信号
function generateTradeSignal() {
  const symbols = ['AAPL', 'TSLA', 'MSFT'];
  const sides = ['buy', 'sell'];
  const symbol = symbols[Math.floor(Math.random() * symbols.length)];
  const side = sides[Math.floor(Math.random() * sides.length)];
  
  return {
    type: 'trade_signal',
    data: {
      symbol,
      side,
      price: +(100 + Math.random() * 200).toFixed(2),
      confidence: +(Math.random() * 100).toFixed(1),
      strategy: 'demo_strategy',
      timestamp: Date.now(),
    },
  };
}

// 生成系统通知
function generateNotification() {
  const messages = [
    '策略执行成功',
    '风险预警：当前持仓风险度较高',
    '交易完成：买入订单已成交',
    '系统维护通知',
    '市场数据更新完成',
  ];
  
  const types = ['success', 'warning', 'info', 'error'];
  const message = messages[Math.floor(Math.random() * messages.length)];
  const type = types[Math.floor(Math.random() * types.length)];
  
  return {
    type: 'notification',
    data: {
      id: 'notify-' + Date.now(),
      title: '系统通知',
      message,
      type,
      timestamp: Date.now(),
    },
  };
}

// 客户端连接处理
wss.on('connection', (ws, req) => {
  console.log(`✅ 新客户端连接: ${req.socket.remoteAddress}`);
  
  // 发送欢迎消息
  ws.send(JSON.stringify({
    type: 'welcome',
    data: {
      message: '欢迎连接RedFire WebSocket服务',
      timestamp: Date.now(),
    },
  }));
  
  // 处理客户端消息
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      console.log(`📩 收到消息:`, data);
      
      // 根据消息类型处理
      switch (data.type) {
        case 'subscribe':
          // 订阅特定symbol的价格数据
          ws.subscription = data.symbol;
          ws.send(JSON.stringify({
            type: 'subscribed',
            data: {
              symbol: data.symbol,
              message: `已订阅 ${data.symbol} 的实时数据`,
            },
          }));
          break;
          
        case 'unsubscribe':
          // 取消订阅
          ws.subscription = null;
          ws.send(JSON.stringify({
            type: 'unsubscribed',
            data: {
              message: '已取消订阅',
            },
          }));
          break;
          
        case 'ping':
          // 心跳响应
          ws.send(JSON.stringify({
            type: 'pong',
            data: {
              timestamp: Date.now(),
            },
          }));
          break;
          
        default:
          ws.send(JSON.stringify({
            type: 'error',
            data: {
              message: '未知消息类型',
            },
          }));
      }
    } catch (error) {
      console.error('❌ 消息解析错误:', error);
      ws.send(JSON.stringify({
        type: 'error',
        data: {
          message: '消息格式错误',
        },
      }));
    }
  });
  
  // 连接断开处理
  ws.on('close', (code, reason) => {
    console.log(`❌ 客户端断开连接: ${code} ${reason}`);
  });
  
  // 错误处理
  ws.on('error', (error) => {
    console.error('❌ WebSocket错误:', error);
  });
});

// 广播价格数据
setInterval(() => {
  const symbol = mockSymbols[Math.floor(Math.random() * mockSymbols.length)];
  const priceData = generatePriceData(symbol);
  
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      // 如果客户端订阅了特定symbol，只发送相关数据
      if (!client.subscription || client.subscription === symbol) {
        client.send(JSON.stringify(priceData));
      }
    }
  });
}, 1000); // 每秒发送价格数据

// 广播交易信号
setInterval(() => {
  const signal = generateTradeSignal();
  
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(signal));
    }
  });
}, 5000); // 每5秒发送交易信号

// 广播系统通知
setInterval(() => {
  const notification = generateNotification();
  
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(notification));
    }
  });
}, 15000); // 每15秒发送通知

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('📴 收到SIGTERM信号，正在关闭WebSocket服务器...');
  wss.close(() => {
    console.log('✅ WebSocket服务器已关闭');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('📴 收到SIGINT信号，正在关闭WebSocket服务器...');
  wss.close(() => {
    console.log('✅ WebSocket服务器已关闭');
    process.exit(0);
  });
});
