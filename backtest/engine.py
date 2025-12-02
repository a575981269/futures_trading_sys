"""
回测引擎
"""
from datetime import datetime, timedelta
from typing import List, Optional, Type, Dict, Any
from database.models import KlineData, TickData
from database.db_manager import DatabaseManager
from market_data.ctp_history import CTPHistoryData
from strategy.base_strategy import BaseStrategy
from backtest.portfolio import Portfolio
from backtest.performance import PerformanceAnalyzer
from config.settings import settings
from utils.logger import get_logger
from utils.helpers import parse_datetime

logger = get_logger(__name__)


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = None,
                 commission_rate: float = None,
                 slippage: float = None):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
        """
        # 使用配置或参数
        self.initial_capital = initial_capital or settings.BACKTEST_INITIAL_CAPITAL
        self.commission_rate = commission_rate or settings.BACKTEST_COMMISSION_RATE
        self.slippage = slippage or settings.BACKTEST_SLIPPAGE
        
        # 数据库和历史数据接口
        self.db_manager = DatabaseManager(settings.DB_URL)
        self.history_data = CTPHistoryData(self.db_manager)
        
        # 策略
        self.strategy: Optional[BaseStrategy] = None
        self.strategy_class: Optional[Type[BaseStrategy]] = None
        self.strategy_params: Dict[str, Any] = {}
        
        # 组合和绩效分析
        self.portfolio: Optional[Portfolio] = None
        self.performance: Optional[PerformanceAnalyzer] = None
        
        # 回测数据
        self.symbol: str = ""
        self.interval: str = "1m"
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.klines: List[KlineData] = []
        
        # 回测模式
        self.mode: str = "bar"  # "bar" 或 "tick"
        
        logger.info("回测引擎初始化完成")
    
    def add_strategy(self, strategy_class: Type[BaseStrategy], 
                    params: Dict[str, Any] = None):
        """
        添加策略
        
        Args:
            strategy_class: 策略类
            params: 策略参数
        """
        self.strategy_class = strategy_class
        self.strategy_params = params or {}
        logger.info(f"添加策略: {strategy_class.__name__}")
    
    def set_data(self, symbol: str, start_date: str, end_date: str,
                 interval: str = "1m", from_db: bool = True):
        """
        设置回测数据
        
        Args:
            symbol: 合约代码
            start_date: 开始日期
            end_date: 结束日期
            interval: K线周期
            from_db: 是否从数据库获取
        """
        self.symbol = symbol
        self.interval = interval
        
        start_dt = parse_datetime(start_date)
        end_dt = parse_datetime(end_date)
        
        if not start_dt or not end_dt:
            raise ValueError(f"日期格式错误: {start_date}, {end_date}")
        
        self.start_date = start_dt
        self.end_date = end_dt
        
        # 加载K线数据
        logger.info(f"加载回测数据: {symbol}, {interval}, {start_date} ~ {end_date}")
        self.klines = self.history_data.get_kline(
            symbol, interval, start_date, end_date, from_db=from_db
        )
        
        if not self.klines:
            raise ValueError(f"未找到回测数据: {symbol}, {interval}, {start_date} ~ {end_date}")
        
        logger.info(f"加载完成，共 {len(self.klines)} 条K线数据")
    
    def set_mode(self, mode: str):
        """
        设置回测模式
        
        Args:
            mode: "bar" 或 "tick"
        """
        if mode not in ["bar", "tick"]:
            raise ValueError("回测模式必须是 'bar' 或 'tick'")
        self.mode = mode
        logger.info(f"回测模式: {mode}")
    
    def run_backtest(self) -> Dict[str, Any]:
        """
        运行回测
        
        Returns:
            回测结果字典
        """
        if not self.strategy_class:
            raise ValueError("未添加策略")
        
        if not self.klines:
            raise ValueError("未设置回测数据")
        
        logger.info("开始回测...")
        
        # 初始化组合
        self.portfolio = Portfolio(
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage=self.slippage
        )
        
        # 创建策略实例
        self.strategy = self.strategy_class(
            name=self.strategy_class.__name__,
            params=self.strategy_params
        )
        
        # 将组合的交易方法绑定到策略
        self._bind_trading_methods()
        
        # 初始化策略
        self.strategy.on_init()
        self.strategy.add_symbol(self.symbol)
        
        # 运行回测
        if self.mode == "bar":
            self._run_bar_backtest()
        else:
            self._run_tick_backtest()
        
        # 策略退出
        self.strategy.on_exit()
        
        # 计算绩效
        self.performance = PerformanceAnalyzer(self.portfolio)
        
        # 计算回测天数
        days = (self.end_date - self.start_date).days
        
        # 获取统计结果
        stats = self.performance.get_statistics(days)
        
        logger.info("回测完成")
        self.performance.print_statistics(days)
        
        return stats
    
    def _run_bar_backtest(self):
        """运行基于K线的回测"""
        logger.info("运行K线回测...")
        
        for i, bar in enumerate(self.klines):
            # 更新持仓价格
            self.portfolio.update_price(self.symbol, bar.close)
            
            # 调用策略的on_bar方法
            self.strategy.on_bar(bar)
            
            # 记录权益曲线（每10条记录一次，减少数据量）
            if i % 10 == 0:
                self.portfolio.record_equity(bar.datetime)
        
        # 最后记录一次
        if self.klines:
            self.portfolio.record_equity(self.klines[-1].datetime)
    
    def _run_tick_backtest(self):
        """运行基于Tick的回测（需要Tick数据）"""
        logger.info("运行Tick回测...")
        
        # 加载Tick数据
        ticks = self.history_data.get_tick(
            self.symbol,
            self.start_date.strftime('%Y-%m-%d'),
            self.end_date.strftime('%Y-%m-%d'),
            from_db=True
        )
        
        if not ticks:
            logger.warning("未找到Tick数据，切换到K线回测模式")
            self._run_bar_backtest()
            return
        
        logger.info(f"加载Tick数据: {len(ticks)} 条")
        
        for i, tick in enumerate(ticks):
            # 更新持仓价格
            self.portfolio.update_price(self.symbol, tick.last_price)
            
            # 调用策略的on_tick方法
            self.strategy.on_tick(tick)
            
            # 记录权益曲线（每100条记录一次）
            if i % 100 == 0:
                self.portfolio.record_equity(tick.datetime)
        
        # 最后记录一次
        if ticks:
            self.portfolio.record_equity(ticks[-1].datetime)
    
    def _bind_trading_methods(self):
        """将组合的交易方法绑定到策略"""
        def buy(symbol, price, volume, order_type="LIMIT"):
            return self.portfolio.open_long(symbol, price, volume, datetime.now())
        
        def sell(symbol, price, volume, order_type="LIMIT"):
            return self.portfolio.close_long(symbol, price, volume, datetime.now())
        
        def short(symbol, price, volume, order_type="LIMIT"):
            return self.portfolio.open_short(symbol, price, volume, datetime.now())
        
        def cover(symbol, price, volume, order_type="LIMIT"):
            return self.portfolio.close_short(symbol, price, volume, datetime.now())
        
        # 绑定方法
        self.strategy.buy = buy
        self.strategy.sell = sell
        self.strategy.short = short
        self.strategy.cover = cover
    
    def get_equity_curve(self):
        """获取权益曲线"""
        if self.portfolio:
            return {
                'equity': self.portfolio.equity_curve,
                'time': self.portfolio.equity_times
            }
        return None
    
    def get_trades(self):
        """获取交易记录"""
        if self.portfolio:
            return self.portfolio.get_trades()
        return []

