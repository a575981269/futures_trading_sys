"""
实盘交易接口测试脚本
"""
import sys
import time
from datetime import datetime

from trading.ctp_trader import CTPTrader
from trading.live_trader import LiveTrader
from trading.live_account import LiveAccount
from trading.order import Order, OrderDirection, OrderType
from risk.risk_manager import RiskManager
from risk.position_limit import PositionLimit
from risk.capital_limit import CapitalLimit
from risk.order_limit import OrderLimit
from risk.risk_config import RiskConfigManager
from risk.risk_monitor import RiskMonitor
from risk.risk_adapter import LiveAccountAdapter
from risk.risk_audit import RiskAuditLogger
from market_data.ctp_realtime import CTPRealtimeData
from database.models import TickData
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def test_ctp_connection():
    """测试CTP连接"""
    print("\n" + "="*60)
    print("测试CTP交易接口连接")
    print("="*60)
    
    trader = CTPTrader()
    
    print(f"\n连接参数:")
    print(f"  交易服务器: {trader.trade_address}")
    print(f"  经纪商代码: {trader.broker_id}")
    print(f"  用户代码: {trader.user_id}")
    
    print("\n正在连接...")
    if trader.connect():
        print("[OK] CTP交易接口连接成功")
        
        # 查询账户
        print("\n查询账户信息...")
        account_info = trader.query_account()
        if account_info:
            print("[OK] 账户信息:")
            for key, value in account_info.items():
                print(f"  {key}: {value}")
        else:
            print("[WARNING] 账户信息为空")
        
        # 查询持仓
        print("\n查询持仓...")
        positions = trader.query_positions()
        print(f"[OK] 持仓数量: {len(positions)}")
        for pos in positions:
            print(f"  {pos.symbol}: {pos.volume}手, {pos.direction}")
        
        # 断开连接
        trader.disconnect()
        print("\n[OK] 已断开连接")
        return True
    else:
        print("[ERROR] CTP交易接口连接失败")
        return False


def test_order_submit():
    """测试订单提交"""
    print("\n" + "="*60)
    print("测试订单提交")
    print("="*60)
    
    trader = CTPTrader()
    
    if not trader.connect():
        print("[ERROR] 无法连接CTP接口")
        return False
    
    try:
        # 创建测试订单
        test_order = Order(
            symbol="rb2501",
            direction=OrderDirection.BUY,
            price=3500.0,
            volume=1,
            order_type=OrderType.LIMIT
        )
        
        print(f"\n提交测试订单:")
        print(f"  合约: {test_order.symbol}")
        print(f"  方向: {test_order.direction.value}")
        print(f"  价格: {test_order.price}")
        print(f"  数量: {test_order.volume}")
        
        order_id = trader.submit_order(test_order)
        
        if order_id:
            print(f"[OK] 订单提交成功: {order_id}")
            
            # 等待一下
            time.sleep(1)
            
            # 查询订单
            orders = trader.query_orders()
            print(f"[OK] 当前订单数: {len(orders)}")
            
            # 撤销订单
            print(f"\n撤销订单: {order_id}")
            if trader.cancel_order(order_id):
                print("[OK] 订单撤销成功")
            else:
                print("[WARNING] 订单撤销失败")
            
            return True
        else:
            print("[ERROR] 订单提交失败")
            return False
            
    finally:
        trader.disconnect()


def test_live_trader():
    """测试实盘交易管理器"""
    print("\n" + "="*60)
    print("测试实盘交易管理器")
    print("="*60)
    
    # 创建风控管理器
    position_limit = PositionLimit(
        max_position_per_symbol=10,
        max_total_positions=5,
        max_position_value_ratio=0.3
    )
    capital_limit = CapitalLimit(
        max_order_amount=100000.0,
        max_daily_loss=50000.0,
        max_daily_loss_ratio=0.1
    )
    order_limit = OrderLimit(
        max_orders_per_minute=10,
        max_price_deviation_ratio=0.05
    )
    
    risk_manager = RiskManager(
        position_limit=position_limit,
        capital_limit=capital_limit,
        order_limit=order_limit
    )
    
    # 创建实盘交易管理器
    live_trader = LiveTrader(risk_manager=risk_manager)
    
    print("\n连接实盘交易接口...")
    if live_trader.connect():
        print("[OK] 实盘交易接口连接成功")
        
        # 获取账户信息
        account_info = live_trader.get_account_info()
        print(f"\n[OK] 账户信息:")
        for key, value in account_info.items():
            print(f"  {key}: {value}")
        
        # 获取持仓
        positions = live_trader.get_positions()
        print(f"\n[OK] 持仓数量: {len(positions)}")
        
        # 断开连接
        live_trader.disconnect()
        print("\n[OK] 已断开连接")
        return True
    else:
        print("[ERROR] 实盘交易接口连接失败")
        return False


def test_risk_config():
    """测试风控配置"""
    print("\n" + "="*60)
    print("测试风控配置管理")
    print("="*60)
    
    config_manager = RiskConfigManager()
    
    # 获取默认配置
    default_config = config_manager.get_config()
    print(f"\n[OK] 默认配置:")
    print(f"  单品种最大持仓: {default_config.max_position_per_symbol}")
    print(f"  总持仓品种数: {default_config.max_total_positions}")
    print(f"  单笔最大金额: {default_config.max_order_amount}")
    print(f"  单日最大亏损: {default_config.max_daily_loss}")
    
    # 创建风控管理器
    risk_manager = config_manager.create_risk_manager()
    print(f"\n[OK] 风控管理器创建成功")
    
    # 列出所有配置
    configs = config_manager.list_configs()
    print(f"\n[OK] 可用配置: {configs}")
    
    return True


def test_risk_monitor():
    """测试风控监控"""
    print("\n" + "="*60)
    print("测试风控监控")
    print("="*60)
    
    # 创建账户和风控管理器
    trader = CTPTrader()
    account = LiveAccount(trader)
    
    if not account.connect():
        print("[ERROR] 无法连接账户")
        return False
    
    try:
        # 创建风控管理器
        config_manager = RiskConfigManager()
        risk_manager = config_manager.create_risk_manager()
        
        # 创建监控器
        monitor = RiskMonitor(
            risk_manager=risk_manager,
            live_account=account,
            check_interval=5
        )
        
        print("\n启动风控监控...")
        monitor.start()
        
        # 运行一段时间
        print("监控运行中（10秒）...")
        time.sleep(10)
        
        # 获取当前指标
        metrics = monitor.get_current_metrics()
        print(f"\n[OK] 当前风险指标:")
        for key, value in metrics.items():
            if key != 'timestamp':
                print(f"  {key}: {value}")
        
        # 获取告警
        alerts = monitor.get_recent_alerts(5)
        print(f"\n[OK] 最近告警: {len(alerts)}条")
        for alert in alerts:
            print(f"  [{alert['level']}] {alert['message']}")
        
        # 停止监控
        monitor.stop()
        print("\n[OK] 风控监控已停止")
        
        return True
        
    finally:
        account.disconnect()


def test_live_trader_with_order():
    """测试实盘交易管理器提交订单（触发风控检查）"""
    print("\n" + "="*60)
    print("测试实盘交易管理器订单提交（含风控检查）")
    print("="*60)
    
    # 创建风控管理器
    position_limit = PositionLimit(
        max_position_per_symbol=10,
        max_total_positions=5,
        max_position_value_ratio=0.3
    )
    capital_limit = CapitalLimit(
        max_order_amount=100000.0,
        max_daily_loss=50000.0,
        max_daily_loss_ratio=0.1
    )
    order_limit = OrderLimit(
        max_orders_per_minute=10,
        max_price_deviation_ratio=0.05
    )
    
    risk_manager = RiskManager(
        position_limit=position_limit,
        capital_limit=capital_limit,
        order_limit=order_limit
    )
    
    # 创建实盘交易管理器
    live_trader = LiveTrader(risk_manager=risk_manager)
    
    print("\n连接实盘交易接口...")
    if not live_trader.connect():
        print("[ERROR] 实盘交易接口连接失败")
        return False
    
    try:
        # 模拟一个Tick数据来设置价格缓存
        from database.models import TickData
        from datetime import datetime
        tick = TickData(
            symbol="rb2501",
            exchange="SHFE",
            datetime=datetime.now(),
            last_price=3500.0,
            volume=1000,
            open_interest=50000
        )
        live_trader.on_tick(tick)
        print(f"[OK] 设置价格缓存: rb2501 = 3500.0")
        
        # 通过LiveTrader提交订单（会触发风控检查）
        print("\n通过LiveTrader提交订单（会触发风控检查）...")
        order_id = live_trader._submit_order(
            symbol="rb2501",
            direction=OrderDirection.BUY,
            price=3500.0,
            volume=1,
            order_type=OrderType.LIMIT
        )
        
        if order_id:
            print(f"[OK] 订单提交成功（通过风控检查）: {order_id}")
            
            # 查询订单
            orders = live_trader.get_active_orders()
            print(f"[OK] 当前活跃订单数: {len(orders)}")
            
            return True
        else:
            print("[WARNING] 订单提交失败（可能被风控拒绝）")
            return False
            
    finally:
        live_trader.disconnect()
        print("\n[OK] 已断开连接")


def test_risk_adapter():
    """测试风控适配器"""
    print("\n" + "="*60)
    print("测试风控适配器")
    print("="*60)
    
    # 创建账户
    trader = CTPTrader()
    account = LiveAccount(trader)
    
    if not account.connect():
        print("[ERROR] 无法连接账户")
        return False
    
    try:
        # 同步账户信息
        account.sync_account()
        
        # 创建适配器
        adapter = LiveAccountAdapter(account)
        
        # 转换为Portfolio
        portfolio = adapter.to_portfolio()
        print(f"\n[OK] Portfolio转换成功:")
        print(f"  初始资金: {portfolio.initial_capital}")
        print(f"  当前资金: {portfolio.current_capital}")
        print(f"  持仓数量: {len(portfolio.positions)}")
        
        # 获取账户指标
        metrics = adapter.get_account_metrics()
        print(f"\n[OK] 账户指标:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        return True
        
    finally:
        account.disconnect()


def test_risk_audit():
    """测试风控审计日志"""
    print("\n" + "="*60)
    print("测试风控审计日志")
    print("="*60)
    
    # 创建审计日志记录器
    audit_logger = RiskAuditLogger()
    
    # 创建测试订单
    test_order = Order(
        symbol="rb2501",
        direction=OrderDirection.BUY,
        price=3500.0,
        volume=1,
        order_type=OrderType.LIMIT
    )
    
    # 创建风控管理器
    position_limit = PositionLimit(max_position_per_symbol=10)
    capital_limit = CapitalLimit(max_order_amount=100000.0)
    risk_manager = RiskManager(
        position_limit=position_limit,
        capital_limit=capital_limit
    )
    
    # 创建Portfolio进行测试
    from backtest.portfolio import Portfolio
    portfolio = Portfolio(initial_capital=1000000.0)
    
    # 执行风控检查并记录
    result = risk_manager.check_order_risk(test_order, portfolio, 3500.0)
    audit_logger.log_order_risk(test_order, result)
    
    print(f"\n[OK] 风控检查结果: {result.passed}, {result.message}")
    print(f"[OK] 审计日志已记录")
    
    # 获取统计信息
    stats = audit_logger.get_statistics()
    print(f"\n[OK] 审计统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 获取最近记录
    records = audit_logger.get_recent_records(5)
    print(f"\n[OK] 最近记录数: {len(records)}")
    
    return True


def test_risk_rules():
    """测试风控规则（各种限制场景）"""
    print("\n" + "="*60)
    print("测试风控规则（各种限制场景）")
    print("="*60)
    
    from backtest.portfolio import Portfolio
    
    # 测试1: 持仓超限
    print("\n测试1: 持仓超限检查")
    position_limit = PositionLimit(max_position_per_symbol=5)
    risk_manager = RiskManager(position_limit=position_limit)
    
    portfolio = Portfolio(initial_capital=1000000.0)
    # 模拟已有持仓
    from backtest.portfolio import Position, Direction
    from datetime import datetime
    pos = Position(
        symbol="rb2501",
        direction=Direction.LONG,
        volume=5,
        entry_price=3500.0,
        entry_time=datetime.now(),
        current_price=3500.0,
        multiplier=10
    )
    portfolio.positions["rb2501"] = pos
    
    test_order = Order(
        symbol="rb2501",
        direction=OrderDirection.BUY,
        price=3500.0,
        volume=6,  # 超过限制
        order_type=OrderType.LIMIT
    )
    
    result = risk_manager.check_order_risk(test_order, portfolio, 3500.0)
    if not result.passed:
        print(f"[OK] 持仓超限检查通过: {result.reason}")
    else:
        print(f"[WARNING] 持仓超限检查未生效")
    
    # 测试2: 资金超限
    print("\n测试2: 资金超限检查")
    capital_limit = CapitalLimit(max_order_amount=50000.0)
    risk_manager2 = RiskManager(capital_limit=capital_limit)
    
    portfolio2 = Portfolio(initial_capital=100000.0)
    test_order2 = Order(
        symbol="rb2501",
        direction=OrderDirection.BUY,
        price=3500.0,
        volume=20,  # 金额 = 3500 * 20 * 10 = 700000，超过限制
        order_type=OrderType.LIMIT
    )
    
    result2 = risk_manager2.check_order_risk(test_order2, portfolio2, 3500.0)
    if not result2.passed:
        print(f"[OK] 资金超限检查通过: {result2.reason}")
    else:
        print(f"[WARNING] 资金超限检查未生效")
    
    # 测试3: 订单频率超限
    print("\n测试3: 订单频率超限检查")
    order_limit = OrderLimit(max_orders_per_minute=2)
    risk_manager3 = RiskManager(order_limit=order_limit)
    
    portfolio3 = Portfolio(initial_capital=1000000.0)
    test_order3 = Order(
        symbol="rb2501",
        direction=OrderDirection.BUY,
        price=3500.0,
        volume=1,
        order_type=OrderType.LIMIT
    )
    
    # 快速提交3个订单
    for i in range(3):
        result3 = risk_manager3.check_order_risk(test_order3, portfolio3, 3500.0)
        if i < 2:
            if result3.passed:
                print(f"[OK] 订单{i+1}通过检查")
            else:
                print(f"[WARNING] 订单{i+1}意外失败: {result3.reason}")
        else:
            if not result3.passed:
                print(f"[OK] 订单频率超限检查通过: {result3.reason}")
            else:
                print(f"[WARNING] 订单频率超限检查未生效")
    
    return True


def test_price_cache():
    """测试价格缓存功能"""
    print("\n" + "="*60)
    print("测试价格缓存功能")
    print("="*60)
    
    # 创建实盘交易管理器
    live_trader = LiveTrader()
    
    if not live_trader.connect():
        print("[ERROR] 无法连接")
        return False
    
    try:
        # 模拟Tick数据
        from database.models import TickData
        from datetime import datetime
        
        tick = TickData(
            symbol="rb2501",
            exchange="SHFE",
            datetime=datetime.now(),
            last_price=3500.0,
            volume=1000,
            open_interest=50000
        )
        
        # 更新价格缓存
        live_trader.on_tick(tick)
        print(f"[OK] 价格缓存已更新: rb2501 = 3500.0")
        
        # 获取价格
        price = live_trader._get_current_price("rb2501")
        if price == 3500.0:
            print(f"[OK] 价格获取成功: {price}")
        else:
            print(f"[WARNING] 价格获取异常: {price}")
            return False
        
        # 测试不存在的合约
        price2 = live_trader._get_current_price("cu2501")
        if price2 is None:
            print(f"[OK] 不存在合约返回None（正确）")
        else:
            print(f"[WARNING] 不存在合约应返回None，但返回了: {price2}")
        
        return True
        
    finally:
        live_trader.disconnect()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("实盘交易接口和风控模块测试")
    print("="*60)
    
    # 验证配置
    if not settings.validate_ctp_config():
        print("\n[ERROR] CTP配置不完整，请检查.env文件")
        print("  需要配置: CTP_BROKER_ID, CTP_USER_ID, CTP_PASSWORD")
        return
    
    # 选择测试项目
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "all"
    
    results = []
    
    if test_type in ["all", "connection"]:
        results.append(("CTP连接", test_ctp_connection()))
    
    if test_type in ["all", "order"]:
        results.append(("订单提交", test_order_submit()))
    
    if test_type in ["all", "trader"]:
        results.append(("实盘交易管理器", test_live_trader()))
    
    if test_type in ["all", "config"]:
        results.append(("风控配置", test_risk_config()))
    
    if test_type in ["all", "monitor"]:
        results.append(("风控监控", test_risk_monitor()))
    
    if test_type in ["all", "trader_order"]:
        results.append(("实盘交易订单（风控）", test_live_trader_with_order()))
    
    if test_type in ["all", "adapter"]:
        results.append(("风控适配器", test_risk_adapter()))
    
    if test_type in ["all", "audit"]:
        results.append(("风控审计", test_risk_audit()))
    
    if test_type in ["all", "rules"]:
        results.append(("风控规则", test_risk_rules()))
    
    if test_type in ["all", "price"]:
        results.append(("价格缓存", test_price_cache()))
    
    # 输出结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results:
        status = "[OK] 通过" if result else "[ERROR] 失败"
        print(f"{name}: {status}")
    print("="*60)


if __name__ == "__main__":
    main()

