import React, { useEffect, useRef } from 'react';
import { Card } from 'antd';
import * as echarts from 'echarts';

interface DepthChartProps {
  symbol?: string;
  height?: number;
  className?: string;
}

interface DepthData {
  price: number;
  volume: number;
  side: 'buy' | 'sell';
}

export const DepthChart: React.FC<DepthChartProps> = ({
  symbol = '000001.SZ',
  height = 300,
  className,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  // 生成模拟深度数据
  const generateDepthData = (): { buyOrders: DepthData[]; sellOrders: DepthData[] } => {
    const currentPrice = 12.50;
    const buyOrders: DepthData[] = [];
    const sellOrders: DepthData[] = [];

    // 生成买单数据（价格递减）
    for (let i = 0; i < 20; i++) {
      const price = Number((currentPrice - 0.01 * (i + 1)).toFixed(2));
      const volume = Math.floor(Math.random() * 10000) + 1000;
      buyOrders.push({ price, volume, side: 'buy' });
    }

    // 生成卖单数据（价格递增）
    for (let i = 0; i < 20; i++) {
      const price = Number((currentPrice + 0.01 * (i + 1)).toFixed(2));
      const volume = Math.floor(Math.random() * 10000) + 1000;
      sellOrders.push({ price, volume, side: 'sell' });
    }

    return { buyOrders, sellOrders };
  };

  const initChart = () => {
    if (!chartRef.current) return;

    chartInstance.current = echarts.init(chartRef.current);
    
    const { buyOrders, sellOrders } = generateDepthData();
    
    // 计算累积成交量
    let buyCumulative = 0;
    const buyDepthData = buyOrders.reverse().map(order => {
      buyCumulative += order.volume;
      return [order.price, buyCumulative];
    });

    let sellCumulative = 0;
    const sellDepthData = sellOrders.map(order => {
      sellCumulative += order.volume;
      return [order.price, sellCumulative];
    });

    const option = {
      title: {
        text: `${symbol} 市场深度`,
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
          animation: false,
        },
        backgroundColor: 'rgba(245, 245, 245, 0.95)',
        borderColor: '#ccc',
        textStyle: {
          color: '#000',
        },
        formatter: function (params: any) {
          const param = params[0];
          const price = param.data[0];
          const volume = param.data[1];
          const side = param.seriesName;
          
          return `
            ${side}<br/>
            价格: ¥${price}<br/>
            累积量: ${volume.toLocaleString()}
          `;
        },
      },
      legend: {
        data: ['买盘深度', '卖盘深度'],
        top: 30,
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%',
        top: '15%',
      },
      xAxis: {
        type: 'value',
        name: '价格',
        nameLocation: 'middle',
        nameGap: 25,
        scale: true,
        axisLine: {
          lineStyle: {
            color: '#999',
          },
        },
        axisLabel: {
          formatter: '¥{value}',
        },
      },
      yAxis: {
        type: 'value',
        name: '累积成交量',
        nameLocation: 'middle',
        nameGap: 40,
        scale: true,
        axisLine: {
          lineStyle: {
            color: '#999',
          },
        },
        axisLabel: {
          formatter: function (value: number) {
            if (value >= 10000) {
              return (value / 10000).toFixed(1) + '万';
            }
            return value.toString();
          },
        },
      },
      series: [
        {
          name: '买盘深度',
          type: 'line',
          data: buyDepthData,
          step: 'end',
          lineStyle: {
            color: '#00da3c',
            width: 2,
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: 'rgba(0, 218, 60, 0.3)',
                },
                {
                  offset: 1,
                  color: 'rgba(0, 218, 60, 0.1)',
                },
              ],
            },
          },
          symbol: 'none',
        },
        {
          name: '卖盘深度',
          type: 'line',
          data: sellDepthData,
          step: 'end',
          lineStyle: {
            color: '#ec0000',
            width: 2,
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: 'rgba(236, 0, 0, 0.3)',
                },
                {
                  offset: 1,
                  color: 'rgba(236, 0, 0, 0.1)',
                },
              ],
            },
          },
          symbol: 'none',
        },
      ],
    };

    chartInstance.current.setOption(option);
  };

  useEffect(() => {
    initChart();

    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);

    // 模拟实时数据更新
    const updateInterval = setInterval(() => {
      initChart();
    }, 5000);

    return () => {
      window.removeEventListener('resize', handleResize);
      clearInterval(updateInterval);
      chartInstance.current?.dispose();
    };
  }, []);

  return (
    <Card className={className} title="市场深度">
      <div
        ref={chartRef}
        style={{ width: '100%', height: height }}
      />
    </Card>
  );
};
