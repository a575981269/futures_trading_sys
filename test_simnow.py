"""
SimNow 模拟环境测试脚本
"""
import sys
import time
from config.settings import settings
from market_data.ctp_realtime import CTPRealtimeData
from trading.ctp_trader import CTPTrader
from utils.logger import get_logger

logger = get_logger(__name__)


def test_connection():
    """测试CTP连接配置"""
    print("=" * 60)
    print("SimNow 模拟环境连接测试")
    print("=" * 60)
    
    # 显示配置信息
    print("\n当前配置:")
    print(f"  经纪商代码: {settings.CTP_BROKER_ID}")
    print(f"  用户代码: {settings.CTP_USER_ID}")
    print(f"  密码: {'*' * len(settings.CTP_PASSWORD) if settings.CTP_PASSWORD else '(未设置)'}")
    print(f"  行情服务器: {settings.CTP_MD_ADDRESS}")
    print(f"  交易服务器: {settings.CTP_TRADE_ADDRESS}")
    print(f"  应用标识: {settings.CTP_APP_ID}")
    print(f"  授权码: {settings.CTP_AUTH_CODE}")
    
    # 验证配置
    if not settings.validate_ctp_config():
        print("\n❌ 配置不完整！")
        print("请检查以下配置项:")
        if not settings.CTP_BROKER_ID:
            print("  - CTP_BROKER_ID (经纪商代码)")
        if not settings.CTP_USER_ID:
            print("  - CTP_USER_ID (用户代码)")
        if not settings.CTP_PASSWORD:
            print("  - CTP_PASSWORD (交易密码) - 请在 .env 文件中设置")
        return False
    
    print("\n✅ 配置验证通过")
    return True


def test_market_data():
    """测试行情接口"""
    print("\n" + "=" * 60)
    print("测试行情接口连接")
    print("=" * 60)
    
    try:
        realtime = CTPRealtimeData(auto_save=True)
        
        # 定义Tick回调
        def on_tick(tick):
            print(f"📊 Tick: {tick.symbol}, 价格={tick.last_price}, 时间={tick.datetime}")
        
        # 定义K线回调
        def on_bar(bar):
            print(f"📈 K线: {bar.symbol}, 收盘={bar.close}, 时间={bar.datetime}")
        
        # 注册回调
        realtime.register_tick_callback(on_tick)
        realtime.register_kline_callback(on_bar)
        
        # 连接
        print("\n正在连接行情服务器...")
        if realtime.connect():
            print("✅ 行情服务器连接成功")
            
            # 订阅测试合约（螺纹钢主力合约）
            test_symbol = "rb2601"  # 可以根据实际情况修改
            print(f"\n正在订阅合约: {test_symbol}")
            if realtime.subscribe(test_symbol):
                print(f"✅ 合约订阅成功: {test_symbol}")
                print("\n等待行情数据... (按Ctrl+C退出)")
                
                try:
                    # 等待一段时间接收数据
                    time.sleep(30)
                except KeyboardInterrupt:
                    print("\n\n用户中断")
                
                realtime.unsubscribe(test_symbol)
            else:
                print(f"❌ 合约订阅失败: {test_symbol}")
            
            realtime.disconnect()
            print("\n✅ 已断开行情连接")
        else:
            print("❌ 行情服务器连接失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ 行情接口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trading():
    """测试交易接口"""
    print("\n" + "=" * 60)
    print("测试交易接口连接")
    print("=" * 60)
    
    try:
        trader = CTPTrader()
        
        # 定义订单回调
        def on_order(order):
            print(f"📋 订单状态: {order.order_id}, {order.symbol}, {order.status.value}")
        
        # 定义成交回调
        def on_trade(order):
            print(f"💰 订单成交: {order.order_id}, {order.symbol}, {order.filled_volume}手")
        
        # 注册回调
        trader.register_order_callback(on_order)
        trader.register_trade_callback(on_trade)
        
        # 连接
        print("\n正在连接交易服务器...")
        if trader.connect():
            print("✅ 交易服务器连接成功")
            
            # 查询账户
            print("\n查询账户信息...")
            account_info = trader.query_account()
            if account_info:
                print("✅ 账户信息:")
                for key, value in account_info.items():
                    print(f"  {key}: {value}")
            else:
                print("⚠️  账户信息为空（可能是模拟环境限制）")
            
            # 查询持仓
            print("\n查询持仓...")
            positions = trader.query_positions()
            print(f"✅ 持仓数量: {len(positions)}")
            for pos in positions:
                print(f"  {pos.symbol}: {pos.volume}手, {pos.direction}")
            
            trader.disconnect()
            print("\n✅ 已断开交易连接")
        else:
            print("❌ 交易服务器连接失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ 交易接口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("SimNow 模拟环境完整测试")
    print("=" * 60)
    print("\n注意：")
    print("1. 请确保已在 .env 文件中设置了 CTP_PASSWORD (SimNow交易密码)")
    print("2. 当前代码为框架代码，实际连接需要实现CTP接口")
    print("3. 建议使用 vnpy-ctp 或其他CTP封装库")
    print("=" * 60)
    
    # 测试配置
    if not test_connection():
        print("\n请先完成配置后再测试")
        return
    
    # 选择测试项目
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        print("\n请选择测试项目:")
        print("1. 测试行情接口 (market)")
        print("2. 测试交易接口 (trading)")
        print("3. 全部测试 (all)")
        choice = input("\n请输入选项 (1/2/3): ").strip()
        
        if choice == "1":
            test_type = "market"
        elif choice == "2":
            test_type = "trading"
        elif choice == "3":
            test_type = "all"
        else:
            print("无效选项")
            return
    
    # 执行测试
    results = []
    
    if test_type in ["market", "all"]:
        results.append(("行情接口", test_market_data()))
    
    if test_type in ["trading", "all"]:
        results.append(("交易接口", test_trading()))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()

