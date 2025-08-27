import React, { useState } from 'react';
import { 
  Card, 
  Form, 
  InputNumber, 
  Button, 
  Select, 
  Radio, 
  Space, 
  Divider, 
  Typography,
  Row,
  Col,
  Alert
} from 'antd';
import { 
  PlusOutlined, 
  MinusOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { Text } = Typography;

interface TradingPanelProps {
  symbol?: string;
  currentPrice?: number;
  className?: string;
}

interface OrderForm {
  orderType: 'limit' | 'market';
  quantity: number;
  price?: number;
  stopPrice?: number;
}

export const TradingPanel: React.FC<TradingPanelProps> = ({
  symbol = '000001.SZ',
  currentPrice = 12.50,
  className,
}) => {
  const [form] = Form.useForm();
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState<'limit' | 'market'>('limit');
  const [loading, setLoading] = useState(false);
  const [availableFund, _setAvailableFund] = useState(100000); // 可用资金
  const [availableShares, _setAvailableShares] = useState(1000); // 可用股数

  // 计算最大可买/卖数量
  const calculateMaxQuantity = () => {
    if (side === 'buy') {
      const price = orderType === 'limit' ? form.getFieldValue('price') || currentPrice : currentPrice;
      return Math.floor(availableFund / price / 100) * 100; // 按手计算
    } else {
      return availableShares;
    }
  };

  // 处理百分比买入
  const handlePercentageBuy = (percentage: number) => {
    const price = orderType === 'limit' ? form.getFieldValue('price') || currentPrice : currentPrice;
    const maxQuantity = Math.floor((availableFund * percentage / 100) / price / 100) * 100;
    form.setFieldsValue({ quantity: maxQuantity });
  };

  // 处理百分比卖出
  const handlePercentageSell = (percentage: number) => {
    const quantity = Math.floor((availableShares * percentage / 100) / 100) * 100;
    form.setFieldsValue({ quantity: quantity });
  };

  // 提交订单
  const handleSubmit = async (values: OrderForm) => {
    setLoading(true);
    
    try {
      console.log('提交订单:', {
        symbol,
        side,
        ...values,
      });
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 重置表单
      form.resetFields();
      
      // 这里可以显示成功提示
    } catch (error) {
      console.error('订单提交失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const isBuy = side === 'buy';
  const buttonColor = isBuy ? '#52c41a' : '#f5222d';

  return (
    <Card 
      className={className}
      title={
        <Space>
          <span>交易面板</span>
          <Text type="secondary">{symbol}</Text>
        </Space>
      }
    >
      {/* 买卖切换 */}
      <Radio.Group 
        value={side} 
        onChange={(e) => setSide(e.target.value)}
        style={{ width: '100%', marginBottom: 16 }}
      >
        <Radio.Button value="buy" style={{ width: '50%', textAlign: 'center' }}>
          <PlusOutlined /> 买入
        </Radio.Button>
        <Radio.Button value="sell" style={{ width: '50%', textAlign: 'center' }}>
          <MinusOutlined /> 卖出
        </Radio.Button>
      </Radio.Group>

      {/* 账户信息 */}
      <Alert
        message={
          <Row>
            <Col span={12}>
              <Text type="secondary">可用资金:</Text>
              <br />
              <Text strong>¥{availableFund.toLocaleString()}</Text>
            </Col>
            <Col span={12}>
              <Text type="secondary">可用股数:</Text>
              <br />
              <Text strong>{availableShares.toLocaleString()}</Text>
            </Col>
          </Row>
        }
        type="info"
        style={{ marginBottom: 16 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          orderType: 'limit',
          price: currentPrice,
        }}
      >
        {/* 订单类型 */}
        <Form.Item label="订单类型" name="orderType">
          <Select onChange={setOrderType}>
            <Option value="limit">限价单</Option>
            <Option value="market">市价单</Option>
          </Select>
        </Form.Item>

        {/* 价格输入 */}
        {orderType === 'limit' && (
          <Form.Item 
            label="价格" 
            name="price"
            rules={[{ required: true, message: '请输入价格' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              precision={2}
              min={0.01}
              max={999999}
              addonAfter="元"
              placeholder="0.00"
            />
          </Form.Item>
        )}

        {/* 数量输入 */}
        <Form.Item 
          label="数量" 
          name="quantity"
          rules={[
            { required: true, message: '请输入数量' },
            { type: 'number', min: 100, message: '最小100股' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={100}
            max={calculateMaxQuantity()}
            step={100}
            addonAfter="股"
            placeholder="100"
          />
        </Form.Item>

        {/* 快速选择按钮 */}
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
            快速选择:
          </Text>
          <Space wrap>
            {isBuy ? (
              <>
                <Button size="small" onClick={() => handlePercentageBuy(25)}>
                  1/4仓
                </Button>
                <Button size="small" onClick={() => handlePercentageBuy(50)}>
                  1/2仓
                </Button>
                <Button size="small" onClick={() => handlePercentageBuy(75)}>
                  3/4仓
                </Button>
                <Button size="small" onClick={() => handlePercentageBuy(100)}>
                  全仓
                </Button>
              </>
            ) : (
              <>
                <Button size="small" onClick={() => handlePercentageSell(25)}>
                  1/4仓
                </Button>
                <Button size="small" onClick={() => handlePercentageSell(50)}>
                  1/2仓
                </Button>
                <Button size="small" onClick={() => handlePercentageSell(75)}>
                  3/4仓
                </Button>
                <Button size="small" onClick={() => handlePercentageSell(100)}>
                  全部
                </Button>
              </>
            )}
          </Space>
        </div>

        <Divider />

        {/* 预估信息 */}
        <div style={{ marginBottom: 16 }}>
          <Row>
            <Col span={12}>
              <Text type="secondary">预估金额:</Text>
              <br />
              <Text strong>
                ¥{(
                  (form.getFieldValue('quantity') || 0) * 
                  (orderType === 'limit' ? form.getFieldValue('price') || currentPrice : currentPrice)
                ).toLocaleString()}
              </Text>
            </Col>
            <Col span={12}>
              <Text type="secondary">预估手续费:</Text>
              <br />
              <Text>¥15.00</Text>
            </Col>
          </Row>
        </div>

        {/* 提交按钮 */}
        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
            size="large"
            style={{ 
              backgroundColor: buttonColor,
              borderColor: buttonColor,
              fontWeight: 'bold'
            }}
          >
            {loading ? '提交中...' : `${isBuy ? '买入' : '卖出'} ${symbol}`}
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};
