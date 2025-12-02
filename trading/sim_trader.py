"""
模拟交易管理器
"""
from typing import Optional, Type, Dict, Any
from datetime import datetime

from trading.sim_account import SimAccount
from trading.order import OrderType
from strategy.base_strategy import BaseStrategy
from market_data.ctp_realtime import CTPRealtimeData
from database.models import TickData, KlineData
from utils.logger import get_logger

logger = get_logger(__name__)


class SimTrader:
    """模拟交易管理器"""
    
    def __init__(self, account: Optional[SimAccount] = None,
                 initial_capital: float = None,
                 commission_rate: float = None,
                 slippage: float = 0.0):
        """
        初始化模拟交易管理器
        
        Args:
            account: 模拟账户，如果为None则自动创建
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
        """
        self.account = account or SimAccount(
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage=slippage
        )
        
        # 策略
        self.strategy: Optional[BaseStrategy] = None
        self.strategy_class: Optional[Type[BaseStrategy]] = None
        self.strategy_params: Dict[str, Any] = {}
        
        # 行情接口
        self.realtime_data: Optional[CTPRealtimeData] = None
        
        logger.info("模拟交易管理器初始化完成")
    
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
    
    def set_realtime_data(self, realtime_data: CTPRealtimeData):
        """
        设置实时行情接口
        
        Args:
            realtime_data: 实时行情接口对象
        """
        self.realtime_data = realtime_data
        
        # 注册行情回调
        realtime_data.register_tick_callback(self._on_tick)
        realtime_data.register_kline_callback(self._on_bar)
        
        logger.info("实时行情接口已设置")
    
    def start(self):
        """启动模拟交易"""
        if not self.strategy_class:
            raise ValueError("未添加策略")
        
        # 创建策略实例
        self.strategy = self.strategy_class(
            name=self.strategy_class.__name__,
            params=self.strategy_params
        )
        
        # 绑定交易方法到策略
        self._bind_trading_methods()
        
        # 初始化策略
        self.strategy.on_init()
        self.strategy.is_active = True
        
        logger.info("模拟交易已启动")
    
    def stop(self):
        """停止模拟交易"""
        if self.strategy:
            # 撤销所有订单
            self.account.cancel_all_orders()
            
            # 策略退出
            self.strategy.on_exit()
            self.strategy.is_active = False
        
        logger.info("模拟交易已停止")
    
    def _bind_trading_methods(self):
        """将账户的交易方法绑定到策略"""
        def buy(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self.account.buy(symbol, price, volume, order_type_enum)
        
        def sell(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self.account.sell(symbol, price, volume, order_type_enum)
        
        def short(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self.account.short(symbol, price, volume, order_type_enum)
        
        def cover(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self.account.cover(symbol, price, volume, order_type_enum)
        
        # 绑定方法
        self.strategy.buy = buy
        self.strategy.sell = sell
        self.strategy.short = short
        self.strategy.cover = cover
    
    def _on_tick(self, tick: TickData):
        """Tick数据回调"""
        if not self.strategy or not self.strategy.is_active:
            return
        
        # 更新账户价格
        self.account.update_tick(tick)
        
        # 调用策略
        try:
            self.strategy.on_tick(tick)
        except Exception as e:
            logger.error(f"策略on_tick执行失败: {e}")
    
    def _on_bar(self, bar: KlineData):
        """K线数据回调"""
        if not self.strategy or not self.strategy.is_active:
            return
        
        # 更新账户价格
        self.account.update_bar(bar)
        
        # 调用策略
        try:
            self.strategy.on_bar(bar)
        except Exception as e:
            logger.error(f"策略on_bar执行失败: {e}")
    
    def get_account_info(self) -> dict:
        """获取账户信息"""
        return self.account.get_account_info()
    
    def get_positions(self):
        """获取持仓"""
        return self.account.get_all_positions()
    
    def get_active_orders(self):
        """获取活跃订单"""
        return self.account.get_active_orders()
    
    def get_trades(self):
        """获取交易记录"""
        return self.account.get_trades()

