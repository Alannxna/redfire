from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_rpcservice import RpcGateway
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_datamanager import DataManagerApp
from vnpy_riskmanager import RiskManagerApp
from vnpy_scripttrader import ScriptTraderApp
from vnpy_chartwizard import ChartWizardApp
from vnpy_portfoliostrategy import PortfolioStrategyApp
from vnpy_algotrading import AlgoTradingApp
from vnpy_spreadtrading import SpreadTradingApp

# 股票交易接口
# from vnpy_sec import SecGateway        # 证券交易接口
# from vnpy_xtp import XtpGateway        # XTP交易接口
# from vnpy_tora import ToraStockGateway # Tora股票接口
# from vnpy_ib import IbGateway          # 盈透证券接口


def main():
    """"""
    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)

    # 添加RPC网关
    main_engine.add_gateway(RpcGateway)
    
    # 添加股票交易接口
    # main_engine.add_gateway(SecGateway)        # 证券交易接口
    # main_engine.add_gateway(XtpGateway)        # XTP交易接口
    # main_engine.add_gateway(ToraStockGateway)  # Tora股票接口
    # main_engine.add_gateway(IbGateway)         # 盈透证券接口
    
    # 添加功能模块
    main_engine.add_app(CtaStrategyApp)           # CTA策略
    main_engine.add_app(DataManagerApp)           # 数据管理
    main_engine.add_app(RiskManagerApp)           # 风险管理
    main_engine.add_app(ScriptTraderApp)          # 脚本交易
    main_engine.add_app(ChartWizardApp)           # 图表分析
    main_engine.add_app(PortfolioStrategyApp)     # 投资组合
    main_engine.add_app(AlgoTradingApp)           # 算法交易
    main_engine.add_app(SpreadTradingApp)         # 价差交易

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
