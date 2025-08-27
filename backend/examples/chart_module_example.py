"""
图表模块使用示例

演示如何使用图表模块的各种功能
"""

import asyncio
from datetime import datetime, timedelta
from typing import List

from src.modules.chart import (
    Chart, BarData, Indicator, ChartType, Interval, IndicatorType,
    ChartApplicationService, ChartContainer
)


async def main():
    """主示例函数"""
    
    # 初始化依赖注入容器
    container = ChartContainer()
    container.wire(modules=[__name__])
    
    # 获取图表应用服务
    chart_service = container.chart_application_service()
    
    print("=== 图表模块使用示例 ===\n")
    
    # 1. 创建图表
    print("1. 创建图表")
    chart = await chart_service.create_chart(
        symbol="BTCUSDT",
        chart_type=ChartType.CANDLESTICK,
        interval=Interval.ONE_MINUTE,
        title="BTC/USDT 1分钟K线图",
        description="比特币对泰达币1分钟K线图表"
    )
    print(f"创建图表成功: {chart.chart_id}")
    print(f"交易品种: {chart.symbol}")
    print(f"图表类型: {chart.chart_type.value}")
    print(f"时间周期: {chart.interval.value}")
    print()
    
    # 2. 获取图表信息
    print("2. 获取图表信息")
    retrieved_chart = await chart_service.get_chart(chart.chart_id)
    print(f"图表标题: {retrieved_chart.title}")
    print(f"图表描述: {retrieved_chart.description}")
    print(f"是否激活: {retrieved_chart.is_active}")
    print(f"订阅者数量: {retrieved_chart.subscriber_count}")
    print()
    
    # 3. 添加模拟K线数据
    print("3. 添加模拟K线数据")
    bar_data_repo = container.bar_data_repository()
    
    # 生成模拟K线数据
    base_time = datetime.now() - timedelta(minutes=100)
    base_price = 50000.0
    
    for i in range(100):
        bar_time = base_time + timedelta(minutes=i)
        open_price = base_price + (i * 10)
        high_price = open_price + 100
        low_price = open_price - 80
        close_price = open_price + 50
        volume = 1000.0 + (i * 10)
        
        bar = BarData.create(
            symbol="BTCUSDT",
            datetime=bar_time,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume
        )
        await bar_data_repo.save_bar(bar)
    
    print("生成100根模拟K线数据")
    print()
    
    # 4. 获取K线数据
    print("4. 获取K线数据")
    bars = await chart_service.get_chart_bars(chart.chart_id, limit=10)
    print(f"获取到 {len(bars)} 根K线数据")
    
    if bars:
        latest_bar = bars[-1]
        print(f"最新K线: {latest_bar.datetime}")
        print(f"开盘价: {latest_bar.open_price}")
        print(f"最高价: {latest_bar.high_price}")
        print(f"最低价: {latest_bar.low_price}")
        print(f"收盘价: {latest_bar.close_price}")
        print(f"成交量: {latest_bar.volume}")
    print()
    
    # 5. 添加技术指标
    print("5. 添加技术指标")
    
    # 添加MA指标
    ma_indicator = await chart_service.add_indicator(
        chart_id=chart.chart_id,
        indicator_type=IndicatorType.MA,
        name="MA20",
        parameters={"period": 20}
    )
    print(f"添加MA指标: {ma_indicator.indicator_id}")
    
    # 添加RSI指标
    rsi_indicator = await chart_service.add_indicator(
        chart_id=chart.chart_id,
        indicator_type=IndicatorType.RSI,
        name="RSI14",
        parameters={"period": 14}
    )
    print(f"添加RSI指标: {rsi_indicator.indicator_id}")
    print()
    
    # 6. 获取图表指标
    print("6. 获取图表指标")
    indicators = await chart_service.get_chart_indicators(chart.chart_id)
    print(f"图表共有 {len(indicators)} 个指标:")
    
    for indicator in indicators:
        print(f"- {indicator.name} ({indicator.indicator_type.value})")
        print(f"  参数: {indicator.parameters}")
        print(f"  状态: {indicator.status.value}")
    print()
    
    # 7. 订阅图表
    print("7. 订阅图表")
    await chart_service.subscribe_chart(chart.chart_id)
    print("订阅图表成功")
    
    updated_chart = await chart_service.get_chart(chart.chart_id)
    print(f"当前订阅者数量: {updated_chart.subscriber_count}")
    print()
    
    # 8. 更新图表信息
    print("8. 更新图表信息")
    updated_chart = await chart_service.update_chart(
        chart_id=chart.chart_id,
        title="BTC/USDT 实时K线图",
        description="更新后的比特币实时K线图表"
    )
    print(f"更新后标题: {updated_chart.title}")
    print(f"更新后描述: {updated_chart.description}")
    print()
    
    # 9. 根据交易品种查找图表
    print("9. 根据交易品种查找图表")
    charts_by_symbol = await chart_service.get_charts_by_symbol("BTCUSDT")
    print(f"找到 {len(charts_by_symbol)} 个BTCUSDT图表")
    print()
    
    # 10. 取消订阅图表
    print("10. 取消订阅图表")
    await chart_service.unsubscribe_chart(chart.chart_id)
    print("取消订阅成功")
    
    final_chart = await chart_service.get_chart(chart.chart_id)
    print(f"当前订阅者数量: {final_chart.subscriber_count}")
    print()
    
    # 11. 清理资源
    print("11. 清理资源")
    
    # 删除指标
    for indicator in indicators:
        await chart_service.remove_indicator(indicator.indicator_id)
        print(f"删除指标: {indicator.name}")
    
    # 删除图表
    success = await chart_service.delete_chart(chart.chart_id)
    if success:
        print("删除图表成功")
    else:
        print("删除图表失败")
    
    print("\n=== 示例完成 ===")


def demonstrate_value_objects():
    """演示值对象的使用"""
    print("\n=== 值对象使用示例 ===\n")
    
    # 图表类型
    print("1. 图表类型")
    for chart_type in ChartType:
        print(f"- {chart_type.value}: {chart_type.name}")
    print()
    
    # 时间周期
    print("2. 时间周期")
    intervals = [
        Interval.ONE_MINUTE, Interval.FIVE_MINUTES, Interval.FIFTEEN_MINUTES,
        Interval.ONE_HOUR, Interval.FOUR_HOURS, Interval.ONE_DAY
    ]
    for interval in intervals:
        print(f"- {interval.value}: {interval.name}")
    print()
    
    # 指标类型
    print("3. 指标类型")
    for indicator_type in IndicatorType:
        print(f"- {indicator_type.value}: {indicator_type.name}")
    print()


def demonstrate_entities():
    """演示实体的使用"""
    print("\n=== 实体使用示例 ===\n")
    
    # 创建图表实体
    print("1. 创建图表实体")
    chart = Chart.create(
        symbol="ETHUSDT",
        chart_type=ChartType.LINE,
        interval=Interval.FIVE_MINUTES,
        title="ETH/USDT 5分钟线形图"
    )
    print(f"图表ID: {chart.chart_id}")
    print(f"创建时间: {chart.created_at}")
    print()
    
    # 创建K线数据实体
    print("2. 创建K线数据实体")
    bar = BarData.create(
        symbol="ETHUSDT",
        datetime=datetime.now(),
        open_price=3000.0,
        high_price=3100.0,
        low_price=2950.0,
        close_price=3050.0,
        volume=500.0
    )
    print(f"K线时间: {bar.datetime}")
    print(f"价格区间: {bar.low_price} - {bar.high_price}")
    print()
    
    # 创建指标实体
    print("3. 创建指标实体")
    indicator = Indicator.create(
        indicator_type=IndicatorType.MA,
        name="MA10",
        parameters={"period": 10}
    )
    print(f"指标ID: {indicator.indicator_id}")
    print(f"指标类型: {indicator.indicator_type.value}")
    print(f"指标参数: {indicator.parameters}")
    print()


if __name__ == "__main__":
    # 运行示例
    demonstrate_value_objects()
    demonstrate_entities()
    
    # 运行异步示例
    asyncio.run(main())


