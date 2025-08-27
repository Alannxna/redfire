import React, { useState, useEffect } from 'react';
import { Card, Table, Typography, Space, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface OrderBookItem {
  price: number;
  volume: number;
  total: number;
}

interface OrderBookProps {
  symbol?: string;
  className?: string;
}

export const OrderBook: React.FC<OrderBookProps> = ({
  symbol = '000001.SZ',
  className,
}) => {
  const [sellOrders, setSellOrders] = useState<OrderBookItem[]>([]);
  const [buyOrders, setBuyOrders] = useState<OrderBookItem[]>([]);
  const [currentPrice, setCurrentPrice] = useState(12.50);
  const [priceChange, setPriceChange] = useState(0.15);

  // 生成模拟订单数据
  const generateOrderData = () => {
    const basePrice = 12.50;
    const newSellOrders: OrderBookItem[] = [];
    const newBuyOrders: OrderBookItem[] = [];

    // 生成卖盘数据（价格递增）
    for (let i = 1; i <= 10; i++) {
      const price = Number((basePrice + 0.01 * i).toFixed(2));
      const volume = Math.floor(Math.random() * 50000) + 10000;
      const total = Number((price * volume).toFixed(2));
      newSellOrders.push({ price, volume, total });
    }

    // 生成买盘数据（价格递减）
    for (let i = 1; i <= 10; i++) {
      const price = Number((basePrice - 0.01 * i).toFixed(2));
      const volume = Math.floor(Math.random() * 50000) + 10000;
      const total = Number((price * volume).toFixed(2));
      newBuyOrders.push({ price, volume, total });
    }

    setSellOrders(newSellOrders.reverse()); // 卖盘从高到低
    setBuyOrders(newBuyOrders); // 买盘从高到低
  };

  // 卖盘列配置
  const sellColumns = [
    {
      title: '卖价',
      dataIndex: 'price',
      key: 'price',
      align: 'right' as const,
      render: (price: number) => (
        <Text style={{ color: '#f5222d', fontWeight: 500 }}>
          {price.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '数量',
      dataIndex: 'volume',
      key: 'volume',
      align: 'right' as const,
      render: (volume: number) => (
        <Text>{volume.toLocaleString()}</Text>
      ),
    },
    {
      title: '总额',
      dataIndex: 'total',
      key: 'total',
      align: 'right' as const,
      render: (total: number) => (
        <Text>{total.toLocaleString()}</Text>
      ),
    },
  ];

  // 买盘列配置
  const buyColumns = [
    {
      title: '买价',
      dataIndex: 'price',
      key: 'price',
      align: 'right' as const,
      render: (price: number) => (
        <Text style={{ color: '#52c41a', fontWeight: 500 }}>
          {price.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '数量',
      dataIndex: 'volume',
      key: 'volume',
      align: 'right' as const,
      render: (volume: number) => (
        <Text>{volume.toLocaleString()}</Text>
      ),
    },
    {
      title: '总额',
      dataIndex: 'total',
      key: 'total',
      align: 'right' as const,
      render: (total: number) => (
        <Text>{total.toLocaleString()}</Text>
      ),
    },
  ];

  useEffect(() => {
    generateOrderData();

    // 模拟实时数据更新
    const interval = setInterval(() => {
      generateOrderData();
      // 模拟价格变动
      const change = (Math.random() - 0.5) * 0.1;
      setCurrentPrice(prev => Number((prev + change).toFixed(2)));
      setPriceChange(change);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const isPositive = priceChange >= 0;

  return (
    <Card 
      className={className}
      title={
        <Space>
          <span>订单簿</span>
          <Tag color="blue">{symbol}</Tag>
        </Space>
      }
      bodyStyle={{ padding: 0 }}
    >
      <div style={{ padding: '0 16px' }}>
        {/* 卖盘 */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ 
            fontSize: 12, 
            color: '#8c8c8c', 
            marginBottom: 8,
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <span>卖盘</span>
            <span>卖5档</span>
          </div>
          <Table
            columns={sellColumns}
            dataSource={sellOrders.map((item, index) => ({ ...item, key: `sell-${index}` }))}
            pagination={false}
            size="small"
            showHeader={false}
            rowClassName="order-book-sell-row"
            style={{ marginBottom: 8 }}
          />
        </div>

        {/* 当前价格 */}
        <div style={{
          textAlign: 'center',
          padding: '12px 0',
          backgroundColor: '#f5f5f5',
          borderRadius: 4,
          marginBottom: 16
        }}>
          <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 4 }}>
            <Text style={{ color: isPositive ? '#52c41a' : '#f5222d' }}>
              ¥{currentPrice.toFixed(2)}
            </Text>
          </div>
          <div style={{ fontSize: 12 }}>
            <Space>
              {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              <Text style={{ color: isPositive ? '#52c41a' : '#f5222d' }}>
                {isPositive ? '+' : ''}{priceChange.toFixed(2)} 
                ({isPositive ? '+' : ''}{((priceChange / currentPrice) * 100).toFixed(2)}%)
              </Text>
            </Space>
          </div>
        </div>

        {/* 买盘 */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ 
            fontSize: 12, 
            color: '#8c8c8c', 
            marginBottom: 8,
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <span>买盘</span>
            <span>买5档</span>
          </div>
          <Table
            columns={buyColumns}
            dataSource={buyOrders.map((item, index) => ({ ...item, key: `buy-${index}` }))}
            pagination={false}
            size="small"
            showHeader={false}
            rowClassName="order-book-buy-row"
          />
        </div>
      </div>

      <style jsx>{`
        .order-book-sell-row {
          background-color: rgba(245, 34, 45, 0.05);
        }
        .order-book-sell-row:hover {
          background-color: rgba(245, 34, 45, 0.1) !important;
        }
        .order-book-buy-row {
          background-color: rgba(82, 196, 26, 0.05);
        }
        .order-book-buy-row:hover {
          background-color: rgba(82, 196, 26, 0.1) !important;
        }
      `}</style>
    </Card>
  );
};
