"""
实盘交易管理器
"""
from typing import Optional, Type, Dict, Any, List
from datetime import datetime

from trading.live_account import LiveAccount
from trading.ctp_trader import CTPTrader
from trading.trading_interface import TradingInterface
from trading.order import Order, OrderType, OrderDirection
from strategy.base_strategy import BaseStrategy
from risk.risk_manager import RiskManager
from database.models import TickData, KlineData
from utils.logger import get_logger

logger = get_logger(__name__)


class LiveTrader:
    """实盘交易管理器"""
    
    def __init__(self,
                 trading_interface: Optional[TradingInterface] = None,
                 risk_manager: Optional[RiskManager] = None,
                 auto_sync: bool = True,
                 sync_interval: int = 60):
        """
        初始化实盘交易管理器
        
        Args:
            trading_interface: 交易接口，如果为None则创建CTP交易接口
            risk_manager: 风控管理器
            auto_sync: 是否自动同步账户和持仓
            sync_interval: 同步间隔（秒）
        """
        # 交易接口
        if trading_interface is None:
            trading_interface = CTPTrader()
        self.trading_interface = trading_interface
        
        # 账户管理
        self.account = LiveAccount(self.trading_interface)
        
        # 风控管理器
        self.risk_manager = risk_manager
        
        # 策略
        self.strategy: Optional[BaseStrategy] = None
        self.strategy_class: Optional[Type[BaseStrategy]] = None
        self.strategy_params: Dict[str, Any] = {}
        
        # 自动同步
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval
        self._last_sync_time = datetime.now()
        
        # 注册交易接口回调
        self.trading_interface.register_order_callback(self._on_order_update)
        self.trading_interface.register_trade_callback(self._on_trade_update)
        self.trading_interface.register_position_callback(self._on_position_update)
        
        logger.info("实盘交易管理器初始化完成")
    
    def connect(self) -> bool:
        """连接交易接口"""
        if self.account.connect():
            # 初始同步
            self.account.sync_account()
            self.account.sync_positions()
            self.account.sync_orders()
            return True
        return False
    
    def disconnect(self) -> bool:
        """断开连接"""
        return self.account.disconnect()
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.account.is_connected()
    
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
    
    def start(self):
        """启动实盘交易"""
        if not self.is_connected():
            raise ValueError("交易接口未连接")
        
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
        
        logger.info("实盘交易已启动")
    
    def stop(self):
        """停止实盘交易"""
        if self.strategy:
            # 撤销所有订单
            self.cancel_all_orders()
            
            # 策略退出
            self.strategy.on_exit()
            self.strategy.is_active = False
        
        logger.info("实盘交易已停止")
    
    def _bind_trading_methods(self):
        """将交易方法绑定到策略"""
        def buy(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self._submit_order(symbol, OrderDirection.BUY, price, volume, order_type_enum)
        
        def sell(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self._submit_order(symbol, OrderDirection.SELL, price, volume, order_type_enum)
        
        def short(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self._submit_order(symbol, OrderDirection.SHORT, price, volume, order_type_enum)
        
        def cover(symbol, price, volume, order_type="LIMIT"):
            order_type_enum = OrderType.LIMIT if order_type == "LIMIT" else OrderType.MARKET
            return self._submit_order(symbol, OrderDirection.COVER, price, volume, order_type_enum)
        
        # 绑定方法
        self.strategy.buy = buy
        self.strategy.sell = sell
        self.strategy.short = short
        self.strategy.cover = cover
    
    def _submit_order(self, symbol: str, direction: OrderDirection,
                     price: float, volume: int,
                     order_type: OrderType) -> Optional[str]:
        """
        提交订单（内部方法）
        
        Args:
            symbol: 合约代码
            direction: 订单方向
            price: 价格
            volume: 数量
            order_type: 订单类型
            
        Returns:
            订单ID
        """
        from trading.order import Order
        
        # 创建订单
        order = Order(
            symbol=symbol,
            direction=direction,
            price=price,
            volume=volume,
            order_type=order_type
        )
        
        # 风控检查
        if self.risk_manager:
            # 获取当前价格（需要从行情接口获取）
            current_price = self._get_current_price(symbol)
            
            # 使用模拟组合进行风控检查（实际应该使用实盘账户信息）
            from backtest.portfolio import Portfolio
            portfolio = Portfolio()
            result = self.risk_manager.check_order_risk(order, portfolio, current_price)
            
            if not result.passed:
                logger.warning(f"订单风控失败: {result.reason}")
                order.reject(result.reason or "风控检查失败")
                return None
        
        # 提交订单
        order_id = self.trading_interface.submit_order(order)
        if order_id:
            self.account.orders[order_id] = order
            logger.info(f"订单提交成功: {order_id}")
        else:
            logger.error(f"订单提交失败: {symbol}")
        
        return order_id
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格（需要从行情接口获取）"""
        # TODO: 从行情接口获取当前价格
        return None
    
    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        return self.trading_interface.cancel_order(order_id)
    
    def cancel_all_orders(self, symbol: Optional[str] = None):
        """撤销所有订单"""
        orders = self.account.get_active_orders(symbol)
        for order in orders:
            self.cancel_order(order.order_id)
    
    def _on_order_update(self, order: Order):
        """订单状态更新回调"""
        if self.strategy and hasattr(self.strategy, 'on_order_status'):
            try:
                self.strategy.on_order_status(order)
            except Exception as e:
                logger.error(f"策略订单回调执行失败: {e}")
    
    def _on_trade_update(self, order: Order):
        """成交回调"""
        logger.info(f"订单成交: {order}")
        if self.strategy and hasattr(self.strategy, 'on_trade'):
            try:
                self.strategy.on_trade(order)
            except Exception as e:
                logger.error(f"策略成交回调执行失败: {e}")
    
    def _on_position_update(self, position: Position):
        """持仓更新回调"""
        if self.strategy and hasattr(self.strategy, 'on_position_update'):
            try:
                self.strategy.on_position_update(position)
            except Exception as e:
                logger.error(f"策略持仓回调执行失败: {e}")
    
    def on_tick(self, tick: TickData):
        """Tick数据回调"""
        if not self.strategy or not self.strategy.is_active:
            return
        
        # 自动同步（如果需要）
        if self.auto_sync:
            now = datetime.now()
            if (now - self._last_sync_time).seconds >= self.sync_interval:
                self.account.sync_account()
                self.account.sync_positions()
                self._last_sync_time = now
        
        # 调用策略
        try:
            self.strategy.on_tick(tick)
        except Exception as e:
            logger.error(f"策略on_tick执行失败: {e}")
    
    def on_bar(self, bar: KlineData):
        """K线数据回调"""
        if not self.strategy or not self.strategy.is_active:
            return
        
        # 调用策略
        try:
            self.strategy.on_bar(bar)
        except Exception as e:
            logger.error(f"策略on_bar执行失败: {e}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        return self.account.get_account_info()
    
    def get_positions(self) -> List:
        """获取持仓"""
        return self.account.get_positions()
    
    def get_active_orders(self) -> List[Order]:
        """获取活跃订单"""
        return self.account.get_active_orders()

