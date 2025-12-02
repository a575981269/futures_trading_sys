"""
中国期货量化系统主入口
"""
import sys
from datetime import datetime

from backtest.engine import BacktestEngine
from strategy.strategy_template import StrategyTemplate
from market_data.ctp_realtime import CTPRealtimeData
from market_data.ctp_history import CTPHistoryData
from trading.sim_trader import SimTrader
from trading.sim_account import SimAccount
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def example_backtest():
    """回测示例"""
    print("=" * 60)
    print("期货量化系统 - 回测示例")
    print("=" * 60)
    
    # 创建回测引擎
    engine = BacktestEngine(
        initial_capital=1000000.0,
        commission_rate=0.0001,
        slippage=0.0
    )
    
    # 添加策略
    engine.add_strategy(StrategyTemplate, {"param1": 100})
    
    # 设置回测数据
    # 注意：需要先有历史数据，可以通过CTP接口下载或手动导入
    try:
        engine.set_data(
            symbol="rb2501",
            start_date="2024-01-01",
            end_date="2024-01-31",
            interval="1m",
            from_db=True
        )
        
        # 运行回测
        results = engine.run_backtest()
        
        print("\n回测结果:")
        print(results)
        
    except ValueError as e:
        print(f"回测失败: {e}")
        print("提示：请先下载历史数据或确保数据库中有相应的K线数据")


def example_realtime():
    """实时行情示例"""
    print("=" * 60)
    print("期货量化系统 - 实时行情示例")
    print("=" * 60)
    
    # 检查CTP配置
    if not settings.validate_ctp_config():
        print("警告：CTP配置不完整，请设置环境变量或编辑config/settings.py")
        print("需要的配置：CTP_BROKER_ID, CTP_USER_ID, CTP_PASSWORD")
        return
    
    # 创建实时行情接口
    realtime = CTPRealtimeData(auto_save=True)
    
    # 连接CTP
    if not realtime.connect():
        print("连接CTP失败，请检查配置和网络")
        return
    
    # 定义Tick回调函数
    def on_tick(tick):
        print(f"Tick: {tick.symbol}, 价格={tick.last_price}, 时间={tick.datetime}")
    
    # 定义K线回调函数
    def on_bar(bar):
        print(f"K线: {bar.symbol}, 收盘价={bar.close}, 时间={bar.datetime}")
    
    # 注册回调
    realtime.register_tick_callback(on_tick)
    realtime.register_kline_callback(on_bar)
    
    # 订阅合约
    symbol = "rb2501"
    if realtime.subscribe(symbol):
        print(f"已订阅合约: {symbol}")
        print("按Ctrl+C退出...")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在断开连接...")
            realtime.disconnect()
    else:
        print(f"订阅合约失败: {symbol}")


def example_history():
    """历史行情示例"""
    print("=" * 60)
    print("期货量化系统 - 历史行情示例")
    print("=" * 60)
    
    # 创建历史行情接口
    history = CTPHistoryData()
    
    # 下载历史数据
    symbol = "rb2501"
    interval = "1m"
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    print(f"下载历史数据: {symbol}, {interval}, {start_date} ~ {end_date}")
    history.download_and_save(symbol, interval, start_date, end_date)
    
    # 查询历史数据
    klines = history.get_kline(symbol, interval, start_date, end_date, from_db=True)
    print(f"查询到 {len(klines)} 条K线数据")
    
    if klines:
        print(f"第一条: {klines[0]}")
        print(f"最后一条: {klines[-1]}")


def example_sim_trading():
    """模拟交易示例"""
    print("=" * 60)
    print("期货量化系统 - 模拟交易示例")
    print("=" * 60)
    
    # 检查CTP配置
    if not settings.validate_ctp_config():
        print("警告：CTP配置不完整，请设置环境变量或编辑config/settings.py")
        print("需要的配置：CTP_BROKER_ID, CTP_USER_ID, CTP_PASSWORD")
        return
    
    # 创建模拟账户
    account = SimAccount(
        initial_capital=1000000.0,
        commission_rate=0.0001,
        slippage=0.0
    )
    
    # 创建模拟交易管理器
    trader = SimTrader(
        account=account,
        initial_capital=1000000.0,
        commission_rate=0.0001,
        slippage=0.0
    )
    
    # 添加策略
    trader.add_strategy(StrategyTemplate, {"param1": 100})
    
    # 创建实时行情接口
    realtime = CTPRealtimeData(auto_save=True)
    
    # 连接CTP
    if not realtime.connect():
        print("连接CTP失败，请检查配置和网络")
        return
    
    # 设置实时行情接口
    trader.set_realtime_data(realtime)
    
    # 定义账户信息打印函数
    def print_account_info():
        info = trader.get_account_info()
        print(f"\n账户信息:")
        print(f"  初始资金: {info['initial_capital']:,.2f}")
        print(f"  账户余额: {info['balance']:,.2f}")
        print(f"  账户权益: {info['equity']:,.2f}")
        print(f"  持仓数: {info['positions']}")
        print(f"  活跃订单: {info['active_orders']}")
    
    # 定义订单回调
    def on_order(order):
        print(f"订单状态更新: {order}")
    
    # 定义成交回调
    def on_trade(order):
        print(f"订单成交: {order}")
        print_account_info()
    
    # 注册回调
    account.register_order_callback(on_order)
    account.register_trade_callback(on_trade)
    
    # 启动模拟交易
    trader.start()
    
    # 订阅合约
    symbol = "rb2501"
    if realtime.subscribe(symbol):
        print(f"已订阅合约: {symbol}")
        print("模拟交易已启动，按Ctrl+C退出...")
        print_account_info()
        
        try:
            import time
            while True:
                time.sleep(5)
                print_account_info()
        except KeyboardInterrupt:
            print("\n正在停止模拟交易...")
            trader.stop()
            realtime.disconnect()
            print("模拟交易已停止")
    else:
        print(f"订阅合约失败: {symbol}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py backtest    # 运行回测示例")
        print("  python main.py realtime    # 运行实时行情示例")
        print("  python main.py history     # 运行历史行情示例")
        print("  python main.py sim         # 运行模拟交易示例")
        return
    
    command = sys.argv[1].lower()
    
    if command == "backtest":
        example_backtest()
    elif command == "realtime":
        example_realtime()
    elif command == "history":
        example_history()
    elif command == "sim":
        example_sim_trading()
    else:
        print(f"未知命令: {command}")
        print("可用命令: backtest, realtime, history, sim")


if __name__ == "__main__":
    main()

