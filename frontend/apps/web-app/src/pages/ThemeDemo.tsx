import React from 'react';
import { 
  Card, 
  Button, 
  Input, 
  Table, 
  Tag, 
  Space, 
  Typography, 
  Row, 
  Col,
  Statistic,
  Progress,
  Avatar,
  List
} from 'antd';
import {
  UserOutlined,
  SettingOutlined,
  LineChartOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons';
import { useTheme } from '@redfire/theme-system';

const { Title, Text, Paragraph } = Typography;

/**
 * 主题演示页面
 * 展示黑白灰三色主题在各种组件中的效果
 */
const ThemeDemo: React.FC = () => {
  const { currentTheme, themeName } = useTheme();

  // 示例表格数据
  const tableData = [
    {
      key: '1',
      symbol: 'AAPL',
      price: '150.25',
      change: '+2.15',
      percent: '+1.45%',
      volume: '50.2M',
      status: 'rising'
    },
    {
      key: '2',
      symbol: 'TSLA',
      price: '245.80',
      change: '-5.30',
      percent: '-2.11%',
      volume: '35.8M',
      status: 'falling'
    },
    {
      key: '3',
      symbol: 'MSFT',
      price: '310.45',
      change: '+1.85',
      percent: '+0.60%',
      volume: '28.9M',
      status: 'rising'
    }
  ];

  const tableColumns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '当前价格',
      dataIndex: 'price',
      key: 'price',
      render: (text: string) => <Text>{text}</Text>
    },
    {
      title: '涨跌',
      dataIndex: 'change',
      key: 'change',
      render: (text: string, record: any) => (
        <Text type={record.status === 'rising' ? 'success' : 'danger'}>
          {record.status === 'rising' ? <RiseOutlined /> : <FallOutlined />} {text}
        </Text>
      )
    },
    {
      title: '涨跌幅',
      dataIndex: 'percent',
      key: 'percent',
      render: (text: string, record: any) => (
        <Tag color={record.status === 'rising' ? 'green' : 'red'}>
          {text}
        </Tag>
      )
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume'
    }
  ];

  // 示例列表数据
  const listData = [
    {
      title: '策略执行成功',
      description: '均线策略已成功执行买入操作',
      time: '2分钟前',
      type: 'success'
    },
    {
      title: '风险预警',
      description: '当前持仓风险度较高，建议调整仓位',
      time: '5分钟前',
      type: 'warning'
    },
    {
      title: '交易完成',
      description: 'AAPL 100股卖出订单已成交',
      time: '10分钟前',
      type: 'info'
    }
  ];

  const getThemeDescription = () => {
    switch (themeName) {
      case 'light':
        return '浅色主题采用白色背景，提供清新明亮的视觉体验，适合日常办公使用。';
      case 'dark':
        return '深色主题采用黑色背景，降低眼部疲劳，适合夜间或长时间交易。';
      case 'gray':
        return '灰色主题平衡专业感与舒适度，适合专业交易员长时间工作。';
      default:
        return '当前主题提供优秀的视觉体验。';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 主题信息区域 */}
      <Card className="mb-3">
        <Row gutter={[24, 24]}>
          <Col span={24}>
            <Title level={2}>
              🎨 RedFire 黑白灰三色主题演示
            </Title>
            <Paragraph>
              当前主题: <Tag color="blue">{themeName}</Tag>
            </Paragraph>
            <Paragraph type="secondary">
              {getThemeDescription()}
            </Paragraph>
          </Col>
        </Row>
      </Card>

      {/* 统计信息卡片 */}
      <Row gutter={[16, 16]} className="mb-3">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总资产"
              value={1234567.89}
              precision={2}
              valueStyle={{ color: currentTheme.colors.primary }}
              prefix="¥"
              suffix="元"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日收益"
              value={5678.90}
              precision={2}
              valueStyle={{ color: '#10B981' }}
              prefix={<RiseOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="持仓数量"
              value={15}
              valueStyle={{ color: currentTheme.colors.secondary }}
              suffix="只"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="胜率"
              value={78.5}
              precision={1}
              valueStyle={{ color: currentTheme.colors.primary }}
              suffix="%"
            />
            <Progress 
              percent={78.5} 
              size="small" 
              showInfo={false}
              strokeColor={currentTheme.colors.primary}
            />
          </Card>
        </Col>
      </Row>

      {/* 表格和表单区域 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="股票行情" extra={<Button size="small">刷新</Button>}>
            <Table 
              dataSource={tableData} 
              columns={tableColumns}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="快速交易" className="mb-3">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input placeholder="股票代码" prefix={<LineChartOutlined />} />
              <Input placeholder="交易数量" />
              <Row gutter={8}>
                <Col span={12}>
                  <Button type="primary" danger block>
                    卖出
                  </Button>
                </Col>
                <Col span={12}>
                  <Button type="primary" block>
                    买入
                  </Button>
                </Col>
              </Row>
            </Space>
          </Card>

          <Card title="最近活动">
            <List
              dataSource={listData}
              renderItem={(item, index) => (
                <List.Item key={index}>
                  <List.Item.Meta
                    avatar={
                      <Avatar 
                        icon={
                          item.type === 'success' ? <TrophyOutlined /> :
                          item.type === 'warning' ? <SettingOutlined /> :
                          <UserOutlined />
                        }
                        style={{
                          backgroundColor: 
                            item.type === 'success' ? '#10B981' :
                            item.type === 'warning' ? '#F59E0B' :
                            currentTheme.colors.primary
                        }}
                      />
                    }
                    title={item.title}
                    description={
                      <div>
                        <div style={{ marginBottom: '4px' }}>{item.description}</div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {item.time}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 主题切换说明 */}
      <Card className="mt-3">
        <Title level={4}>🔄 主题切换说明</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card size="small" title="☀️ 浅色主题">
              <Paragraph>
                • 白色背景，深灰色文字<br/>
                • 清新明亮，护眼舒适<br/>
                • 适合日间办公使用<br/>
                • 经典商务风格
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" title="⚪ 灰色主题">
              <Paragraph>
                • 灰色背景，深色文字<br/>
                • 专业稳重，减少疲劳<br/>
                • 适合长时间工作<br/>
                • 平衡视觉效果
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" title="🌙 深色主题">
              <Paragraph>
                • 黑色背景，浅色文字<br/>
                • 护眼模式，降低疲劳<br/>
                • 适合夜间交易<br/>
                • 现代科技感
              </Paragraph>
            </Card>
          </Col>
        </Row>
        <Paragraph className="mt-2">
          <Text type="secondary">
            💡 提示: 点击右上角的主题切换按钮可以体验不同主题效果。
            主题偏好会自动保存到本地存储，下次访问时会记住您的选择。
          </Text>
        </Paragraph>
      </Card>
    </div>
  );
};

export default ThemeDemo;
