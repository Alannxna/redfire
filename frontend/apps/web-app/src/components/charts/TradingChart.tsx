import React, { useEffect, useRef, useState } from 'react';
import { Card, Select, Button, Space } from 'antd';
import { FullscreenOutlined, SettingOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const { Option } = Select;

interface TradingChartProps {
  symbol?: string;
  height?: number;
  className?: string;
}

interface KLineData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export const TradingChart: React.FC<TradingChartProps> = ({
  symbol = '000001.SZ',
  height = 400,
  className,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [timeframe, setTimeframe] = useState('1d');
  const [loading, setLoading] = useState(false);

  // 模拟K线数据
  const generateMockData = (): KLineData[] => {
    const data: KLineData[] = [];
    let basePrice = 12.5;
    const now = new Date();
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      const open = basePrice + (Math.random() - 0.5) * 0.5;
      const change = (Math.random() - 0.5) * 2;
      const high = open + Math.abs(change) + Math.random() * 0.5;
      const low = open - Math.abs(change) - Math.random() * 0.5;
      const close = open + change;
      
      data.push({
        timestamp: date.toISOString().split('T')[0],
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume: Math.floor(Math.random() * 1000000) + 100000,
      });
      
      basePrice = close;
    }
    
    return data;
  };

  const initChart = () => {
    if (!chartRef.current) return;

    chartInstance.current = echarts.init(chartRef.current);
    
    const data = generateMockData();
    const klineData = data.map(item => [item.open, item.close, item.low, item.high]);
    const volumeData = data.map(item => item.volume);
    const dates = data.map(item => item.timestamp);

    const option = {
      animation: false,
      color: ['#c23531', '#2f4554', '#61a0a8', '#d48265', '#91c7ae'],
      title: {
        text: `${symbol} K线图`,
        left: 0,
        textStyle: {
          color: '#333',
          fontSize: 14,
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        backgroundColor: 'rgba(245, 245, 245, 0.95)',
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 10,
        textStyle: {
          color: '#000',
        },
        formatter: function (params: any) {
          const data = params[0];
          const date = data.axisValue;
          const [open, close, low, high] = data.data;
          const volume = volumeData[data.dataIndex];
          
          return `
            日期: ${date}<br/>
            开盘: ${open}<br/>
            收盘: ${close}<br/>
            最低: ${low}<br/>
            最高: ${high}<br/>
            成交量: ${volume.toLocaleString()}
          `;
        },
      },
      legend: {
        data: ['K线', '成交量'],
        top: 30,
      },
      grid: [
        {
          left: '10%',
          right: '8%',
          height: '50%',
        },
        {
          left: '10%',
          right: '8%',
          top: '63%',
          height: '16%',
        },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          top: '85%',
          start: 50,
          end: 100,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: klineData,
          itemStyle: {
            color: '#ec0000',
            color0: '#00da3c',
            borderColor: '#8A0000',
            borderColor0: '#008F28',
          },
          markPoint: {
            label: {
              formatter: function (param: any) {
                return param != null ? Math.round(param.value) + '' : '';
              },
            },
            data: [
              {
                name: '最高值',
                type: 'max',
                valueDim: 'highest',
              },
              {
                name: '最低值',
                type: 'min',
                valueDim: 'lowest',
              },
            ],
            tooltip: {
              formatter: function (param: any) {
                return param.name + '<br>' + (param.data.coord || '');
              },
            },
          },
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumeData,
          itemStyle: {
            color: function (params: any) {
              const colorList = ['#c23531', '#2f4554', '#61a0a8'];
              return colorList[params.dataIndex % colorList.length];
            },
          },
        },
      ],
    };

    chartInstance.current.setOption(option);
  };

  const handleTimeframeChange = (value: string) => {
    setTimeframe(value);
    setLoading(true);
    
    // 模拟数据加载
    setTimeout(() => {
      initChart();
      setLoading(false);
    }, 500);
  };

  const handleFullscreen = () => {
    if (chartRef.current) {
      if (chartRef.current.requestFullscreen) {
        chartRef.current.requestFullscreen();
      }
    }
  };

  useEffect(() => {
    initChart();

    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, []);

  return (
    <Card
      className={className}
      title={
        <Space>
          <span>技术分析图表</span>
          <Select
            value={timeframe}
            style={{ width: 80 }}
            onChange={handleTimeframeChange}
            size="small"
          >
            <Option value="1m">1分</Option>
            <Option value="5m">5分</Option>
            <Option value="15m">15分</Option>
            <Option value="1h">1时</Option>
            <Option value="1d">日线</Option>
            <Option value="1w">周线</Option>
          </Select>
        </Space>
      }
      extra={
        <Space>
          <Button icon={<SettingOutlined />} size="small" />
          <Button icon={<FullscreenOutlined />} size="small" onClick={handleFullscreen} />
        </Space>
      }
      loading={loading}
    >
      <div
        ref={chartRef}
        style={{ width: '100%', height: height }}
      />
    </Card>
  );
};
