"""
虚拟盘模拟交易账户
"""
from datetime import datetime
from typing import Dict, List, Optional, Callable
from threading import Lock

from trading.order import Order, OrderType, OrderStatus, OrderDirection
from backtest.portfolio import Portfolio, Direction, Position
from config.contracts import get_contract_multiplier, get_price_tick
from config.settings import settings
from utils.logger import get_logger
from database.models import TickData, KlineData

logger = get_logger(__name__)


class SimAccount:
    """虚拟盘模拟交易账户"""
    
    def __init__(self, initial_capital: float = None,
                 commission_rate: float = None,
                 slippage: float = 0.0,
                 auto_fill: bool = True):
        """
        初始化模拟账户
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点（按价格比例，如0.001表示0.1%）
            auto_fill: 是否自动成交（True: 立即成交, False: 挂单等待）
        """
        # 使用配置或参数
        self.initial_capital = initial_capital or settings.BACKTEST_INITIAL_CAPITAL
        self.commission_rate = commission_rate or settings.BACKTEST_COMMISSION_RATE
        self.slippage = slippage or settings.BACKTEST_SLIPPAGE
        self.auto_fill = auto_fill
        
        # 组合管理（复用回测的组合管理）
        self.portfolio = Portfolio(
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage=self.slippage
        )
        
        # 订单管理
        self.orders: Dict[str, Order] = {}  # {order_id: Order}
        self.active_orders: Dict[str, List[str]] = {}  # {symbol: [order_ids]}
        
        # 价格缓存（用于订单匹配）
        self.price_cache: Dict[str, float] = {}  # {symbol: price}
        
        # 回调函数
        self.order_callbacks: List[Callable[[Order], None]] = []
        self.trade_callbacks: List[Callable[[Order], None]] = []
        
        # 线程锁
        self._lock = Lock()
        
        logger.info(f"模拟账户初始化: 初始资金={self.initial_capital}, "
                   f"手续费率={self.commission_rate}, 滑点={self.slippage}")
    
    def update_price(self, symbol: str, price: float):
        """
        更新价格（用于订单匹配）
        
        Args:
            symbol: 合约代码
            price: 当前价格
        """
        with self._lock:
            self.price_cache[symbol] = price
            self.portfolio.update_price(symbol, price)
            
            # 检查是否有订单可以成交
            if self.auto_fill:
                self._check_orders(symbol, price)
    
    def update_tick(self, tick: TickData):
        """更新Tick数据"""
        self.update_price(tick.symbol, tick.last_price)
    
    def update_bar(self, bar: KlineData):
        """更新K线数据"""
        self.update_price(bar.symbol, bar.close)
    
    def buy(self, symbol: str, price: float, volume: int,
            order_type: OrderType = OrderType.LIMIT) -> Optional[str]:
        """
        买入开仓
        
        Args:
            symbol: 合约代码
            price: 价格
            volume: 数量（手）
            order_type: 订单类型
        
        Returns:
            订单ID，如果下单失败返回None
        """
        return self._submit_order(symbol, OrderDirection.BUY, price, volume, order_type)
    
    def sell(self, symbol: str, price: float, volume: int,
             order_type: OrderType = OrderType.LIMIT) -> Optional[str]:
        """
        卖出平仓
        
        Args:
            symbol: 合约代码
            price: 价格
            volume: 数量（手）
            order_type: 订单类型
        
        Returns:
            订单ID，如果下单失败返回None
        """
        return self._submit_order(symbol, OrderDirection.SELL, price, volume, order_type)
    
    def short(self, symbol: str, price: float, volume: int,
              order_type: OrderType = OrderType.LIMIT) -> Optional[str]:
        """
        卖出开仓（做空）
        
        Args:
            symbol: 合约代码
            price: 价格
            volume: 数量（手）
            order_type: 订单类型
        
        Returns:
            订单ID，如果下单失败返回None
        """
        return self._submit_order(symbol, OrderDirection.SHORT, price, volume, order_type)
    
    def cover(self, symbol: str, price: float, volume: int,
              order_type: OrderType = OrderType.LIMIT) -> Optional[str]:
        """
        买入平仓（平空）
        
        Args:
            symbol: 合约代码
            price: 价格
            volume: 数量（手）
            order_type: 订单类型
        
        Returns:
            订单ID，如果下单失败返回None
        """
        return self._submit_order(symbol, OrderDirection.COVER, price, volume, order_type)
    
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
        if volume <= 0:
            logger.warning(f"订单数量必须大于0: {symbol}, {volume}")
            return None
        
        # 创建订单
        order = Order(
            symbol=symbol,
            direction=direction,
            price=price,
            volume=volume,
            order_type=order_type
        )
        
        with self._lock:
            # 检查资金和持仓
            if not self._validate_order(order):
                return None
            
            # 保存订单
            self.orders[order.order_id] = order
            
            if symbol not in self.active_orders:
                self.active_orders[symbol] = []
            self.active_orders[symbol].append(order.order_id)
            
            # 更新订单状态
            order.status = OrderStatus.SUBMITTED
            logger.info(f"订单提交成功: {order}")
            
            # 如果是自动成交模式，立即尝试成交
            if self.auto_fill and symbol in self.price_cache:
                current_price = self.price_cache[symbol]
                self._try_fill_order(order, current_price)
            
            # 调用订单回调
            for callback in self.order_callbacks:
                try:
                    callback(order)
                except Exception as e:
                    logger.error(f"订单回调执行失败: {e}")
        
        return order.order_id
    
    def _validate_order(self, order: Order) -> bool:
        """
        验证订单是否有效
        
        Args:
            order: 订单对象
        
        Returns:
            是否有效
        """
        symbol = order.symbol
        direction = order.direction
        price = order.price
        volume = order.volume
        
        # 获取合约信息
        multiplier = get_contract_multiplier(symbol)
        
        # 计算所需资金
        if direction in [OrderDirection.BUY, OrderDirection.COVER]:
            # 买入需要资金
            required_capital = price * volume * multiplier * (1 + self.commission_rate)
            if required_capital > self.portfolio.current_capital:
                order.reject(f"资金不足: 需要{required_capital:.2f}, 可用{self.portfolio.current_capital:.2f}")
                return False
        
        # 检查平仓数量
        if direction == OrderDirection.SELL:
            # 平多仓
            pos = self.portfolio.get_position(symbol)
            if not pos or pos.direction != Direction.LONG:
                order.reject(f"无多仓可平: {symbol}")
                return False
            if volume > pos.volume:
                order.reject(f"平仓数量超过持仓: 持仓{pos.volume}, 平仓{volume}")
                return False
        
        elif direction == OrderDirection.COVER:
            # 平空仓
            pos = self.portfolio.get_position(symbol)
            if not pos or pos.direction != Direction.SHORT:
                order.reject(f"无空仓可平: {symbol}")
                return False
            if volume > pos.volume:
                order.reject(f"平仓数量超过持仓: 持仓{pos.volume}, 平仓{volume}")
                return False
        
        return True
    
    def _check_orders(self, symbol: str, price: float):
        """
        检查订单是否可以成交
        
        Args:
            symbol: 合约代码
            price: 当前价格
        """
        if symbol not in self.active_orders:
            return
        
        # 复制订单ID列表，避免在迭代时修改
        order_ids = self.active_orders[symbol].copy()
        
        for order_id in order_ids:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.is_active():
                    self._try_fill_order(order, price)
    
    def _try_fill_order(self, order: Order, current_price: float):
        """
        尝试成交订单
        
        Args:
            order: 订单对象
            current_price: 当前价格
        """
        if not order.is_active():
            return
        
        # 限价单需要检查价格
        if order.order_type == OrderType.LIMIT:
            if order.direction in [OrderDirection.BUY, OrderDirection.COVER]:
                # 买入：当前价格必须 <= 限价
                if current_price > order.price:
                    return
            else:
                # 卖出：当前价格必须 >= 限价
                if current_price < order.price:
                    return
        
        # 市价单直接成交
        fill_price = current_price
        
        # 应用滑点
        if order.direction in [OrderDirection.BUY, OrderDirection.COVER]:
            fill_price = fill_price * (1 + self.slippage)
        else:
            fill_price = fill_price * (1 - self.slippage)
        
        # 成交
        remaining = order.get_remaining_volume()
        fill_volume = remaining  # 全部成交
        
        self._fill_order(order, fill_volume, fill_price)
    
    def _fill_order(self, order: Order, fill_volume: int, fill_price: float):
        """
        执行订单成交
        
        Args:
            order: 订单对象
            fill_volume: 成交数量
            fill_price: 成交价格
        """
        if fill_volume <= 0:
            return
        
        # 更新订单
        order.update_fill(fill_volume, fill_price)
        
        # 更新持仓
        symbol = order.symbol
        direction = order.direction
        time = datetime.now()
        
        if direction == OrderDirection.BUY:
            self.portfolio.open_long(symbol, fill_price, fill_volume, time)
        elif direction == OrderDirection.SELL:
            self.portfolio.close_long(symbol, fill_price, fill_volume, time)
        elif direction == OrderDirection.SHORT:
            self.portfolio.open_short(symbol, fill_price, fill_volume, time)
        elif direction == OrderDirection.COVER:
            self.portfolio.close_short(symbol, fill_price, fill_volume, time)
        
        # 如果订单全部成交，从活跃订单中移除
        if order.is_filled():
            if symbol in self.active_orders:
                if order.order_id in self.active_orders[symbol]:
                    self.active_orders[symbol].remove(order.order_id)
                if not self.active_orders[symbol]:
                    del self.active_orders[symbol]
        
        # 调用成交回调
        for callback in self.trade_callbacks:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"成交回调执行失败: {e}")
    
    def cancel_order(self, order_id: str) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            是否成功
        """
        with self._lock:
            if order_id not in self.orders:
                logger.warning(f"订单不存在: {order_id}")
                return False
            
            order = self.orders[order_id]
            if order.cancel():
                # 从活跃订单中移除
                symbol = order.symbol
                if symbol in self.active_orders:
                    if order_id in self.active_orders[symbol]:
                        self.active_orders[symbol].remove(order_id)
                    if not self.active_orders[symbol]:
                        del self.active_orders[symbol]
                return True
        
        return False
    
    def cancel_all_orders(self, symbol: Optional[str] = None):
        """
        撤销所有订单
        
        Args:
            symbol: 合约代码，如果为None则撤销所有订单
        """
        with self._lock:
            if symbol:
                if symbol in self.active_orders:
                    order_ids = self.active_orders[symbol].copy()
                    for order_id in order_ids:
                        self.cancel_order(order_id)
            else:
                # 撤销所有活跃订单
                all_order_ids = []
                for symbol_orders in self.active_orders.values():
                    all_order_ids.extend(symbol_orders)
                
                for order_id in all_order_ids:
                    self.cancel_order(order_id)
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        获取活跃订单列表
        
        Args:
            symbol: 合约代码，如果为None则返回所有活跃订单
        
        Returns:
            订单列表
        """
        with self._lock:
            orders = []
            if symbol:
                if symbol in self.active_orders:
                    for order_id in self.active_orders[symbol]:
                        if order_id in self.orders:
                            order = self.orders[order_id]
                            if order.is_active():
                                orders.append(order)
            else:
                for symbol_orders in self.active_orders.values():
                    for order_id in symbol_orders:
                        if order_id in self.orders:
                            order = self.orders[order_id]
                            if order.is_active():
                                orders.append(order)
            return orders
    
    def get_all_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        获取所有订单
        
        Args:
            symbol: 合约代码，如果为None则返回所有订单
        
        Returns:
            订单列表
        """
        with self._lock:
            if symbol:
                return [order for order in self.orders.values() if order.symbol == symbol]
            return list(self.orders.values())
    
    def register_order_callback(self, callback: Callable[[Order], None]):
        """注册订单回调函数"""
        if callback not in self.order_callbacks:
            self.order_callbacks.append(callback)
    
    def register_trade_callback(self, callback: Callable[[Order], None]):
        """注册成交回调函数"""
        if callback not in self.trade_callbacks:
            self.trade_callbacks.append(callback)
    
    def get_balance(self) -> float:
        """获取账户余额"""
        return self.portfolio.current_capital
    
    def get_equity(self) -> float:
        """获取账户权益（资金 + 持仓浮动盈亏）"""
        return self.portfolio.get_total_equity()
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.portfolio.get_position(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
        return self.portfolio.get_all_positions()
    
    def get_trades(self):
        """获取交易记录"""
        return self.portfolio.get_trades()
    
    def get_account_info(self) -> dict:
        """获取账户信息"""
        return {
            'initial_capital': self.initial_capital,
            'balance': self.get_balance(),
            'equity': self.get_equity(),
            'frozen': 0.0,  # 冻结资金（可以扩展）
            'available': self.get_balance(),  # 可用资金
            'margin': 0.0,  # 占用保证金（可以扩展）
            'positions': len(self.portfolio.get_all_positions()),
            'active_orders': len(self.get_active_orders()),
        }

