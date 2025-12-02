"""
实盘账户管理
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock

from trading.trading_interface import TradingInterface
from trading.order import Order, OrderStatus
from backtest.portfolio import Position
from utils.logger import get_logger

logger = get_logger(__name__)


class LiveAccount:
    """实盘账户"""
    
    def __init__(self, trading_interface: TradingInterface):
        """
        初始化实盘账户
        
        Args:
            trading_interface: 交易接口
        """
        self.trading_interface = trading_interface
        self._lock = Lock()
        
        # 账户信息缓存
        self.account_info: Dict[str, Any] = {}
        self.positions: Dict[str, Position] = {}  # {symbol: Position}
        self.orders: Dict[str, Order] = {}  # {order_id: Order}
        
        logger.info("实盘账户初始化完成")
    
    def connect(self) -> bool:
        """连接交易接口"""
        return self.trading_interface.connect()
    
    def disconnect(self) -> bool:
        """断开连接"""
        return self.trading_interface.disconnect()
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.trading_interface.is_connected()
    
    def sync_account(self):
        """同步账户信息"""
        with self._lock:
            self.account_info = self.trading_interface.query_account()
            logger.debug(f"账户信息已同步: {self.account_info}")
    
    def sync_positions(self):
        """同步持仓"""
        with self._lock:
            positions = self.trading_interface.query_positions()
            self.positions = {pos.symbol: pos for pos in positions}
            logger.debug(f"持仓已同步: {len(self.positions)}个")
    
    def sync_orders(self, symbol: Optional[str] = None):
        """同步订单"""
        with self._lock:
            orders = self.trading_interface.query_orders(symbol)
            for order in orders:
                self.orders[order.order_id] = order
            logger.debug(f"订单已同步: {len(orders)}个")
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        return self.account_info.copy()
    
    def get_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定合约的持仓"""
        return self.positions.get(symbol)
    
    def get_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取订单列表"""
        if symbol:
            return [o for o in self.orders.values() if o.symbol == symbol]
        return list(self.orders.values())
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取活跃订单"""
        orders = self.get_orders(symbol)
        return [o for o in orders if o.is_active()]

