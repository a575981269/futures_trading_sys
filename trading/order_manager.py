"""
订单管理器（增强版）
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

from trading.order import Order, OrderStatus, OrderDirection
from utils.logger import get_logger

logger = get_logger(__name__)


class OrderManager:
    """订单管理器"""
    
    def __init__(self):
        """初始化订单管理器"""
        self.orders: Dict[str, Order] = {}  # {order_id: Order}
        self.symbol_orders: Dict[str, List[str]] = defaultdict(list)  # {symbol: [order_ids]}
        self.status_orders: Dict[OrderStatus, List[str]] = defaultdict(list)  # {status: [order_ids]}
        
        # 订单历史（保留最近N条）
        self.order_history: List[Order] = []
        self.max_history_size = 10000
        
        # 回调函数
        self.order_callbacks: List[Callable[[Order], None]] = []
        self.trade_callbacks: List[Callable[[Order], None]] = []
        
        # 线程锁
        self._lock = Lock()
        
        logger.info("订单管理器初始化完成")
    
    def add_order(self, order: Order) -> bool:
        """
        添加订单
        
        Args:
            order: 订单对象
            
        Returns:
            是否成功
        """
        with self._lock:
            if order.order_id in self.orders:
                logger.warning(f"订单已存在: {order.order_id}")
                return False
            
            self.orders[order.order_id] = order
            self.symbol_orders[order.symbol].append(order.order_id)
            self.status_orders[order.status].append(order.order_id)
            
            # 添加到历史
            self.order_history.append(order)
            if len(self.order_history) > self.max_history_size:
                self.order_history.pop(0)
            
            logger.debug(f"订单已添加: {order.order_id}, {order.symbol}")
            return True
    
    def update_order(self, order: Order) -> bool:
        """
        更新订单
        
        Args:
            order: 订单对象
            
        Returns:
            是否成功
        """
        with self._lock:
            if order.order_id not in self.orders:
                logger.warning(f"订单不存在: {order.order_id}")
                return False
            
            old_status = self.orders[order.order_id].status
            new_status = order.status
            
            # 更新订单
            self.orders[order.order_id] = order
            
            # 更新状态索引
            if old_status != new_status:
                if order.order_id in self.status_orders[old_status]:
                    self.status_orders[old_status].remove(order.order_id)
                self.status_orders[new_status].append(order.order_id)
            
            # 调用回调
            self._trigger_order_callbacks(order)
            
            # 如果订单成交，调用成交回调
            if order.is_filled():
                self._trigger_trade_callbacks(order)
            
            logger.debug(f"订单已更新: {order.order_id}, 状态: {old_status.value} -> {new_status.value}")
            return True
    
    def remove_order(self, order_id: str) -> bool:
        """
        移除订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if order_id not in self.orders:
                return False
            
            order = self.orders[order_id]
            
            # 从索引中移除
            if order_id in self.symbol_orders[order.symbol]:
                self.symbol_orders[order.symbol].remove(order_id)
            if order_id in self.status_orders[order.status]:
                self.status_orders[order.status].remove(order_id)
            
            # 从订单字典中移除
            del self.orders[order_id]
            
            logger.debug(f"订单已移除: {order_id}")
            return True
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)
    
    def get_orders(self, symbol: Optional[str] = None,
                   status: Optional[OrderStatus] = None) -> List[Order]:
        """
        获取订单列表
        
        Args:
            symbol: 合约代码，如果为None则返回所有订单
            status: 订单状态，如果为None则返回所有状态
            
        Returns:
            订单列表
        """
        with self._lock:
            if symbol and status:
                # 按品种和状态筛选
                order_ids = set(self.symbol_orders.get(symbol, []))
                status_order_ids = set(self.status_orders.get(status, []))
                order_ids = order_ids & status_order_ids
            elif symbol:
                # 按品种筛选
                order_ids = set(self.symbol_orders.get(symbol, []))
            elif status:
                # 按状态筛选
                order_ids = set(self.status_orders.get(status, []))
            else:
                # 返回所有订单
                order_ids = set(self.orders.keys())
            
            return [self.orders[oid] for oid in order_ids if oid in self.orders]
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        获取活跃订单
        
        Args:
            symbol: 合约代码，如果为None则返回所有活跃订单
            
        Returns:
            活跃订单列表
        """
        active_statuses = [OrderStatus.SUBMITTED, OrderStatus.PARTIAL]
        orders = []
        
        for status in active_statuses:
            status_orders = self.get_orders(symbol=symbol, status=status)
            orders.extend(status_orders)
        
        return orders
    
    def get_filled_orders(self, symbol: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[Order]:
        """
        获取已成交订单
        
        Args:
            symbol: 合约代码
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            已成交订单列表
        """
        orders = self.get_orders(symbol=symbol, status=OrderStatus.FILLED)
        
        if start_time or end_time:
            filtered = []
            for order in orders:
                if start_time and order.update_time < start_time:
                    continue
                if end_time and order.update_time > end_time:
                    continue
                filtered.append(order)
            return filtered
        
        return orders
    
    def get_order_statistics(self, symbol: Optional[str] = None,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Dict:
        """
        获取订单统计
        
        Args:
            symbol: 合约代码
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计字典
        """
        orders = self.get_orders(symbol=symbol)
        
        if start_time or end_time:
            orders = [o for o in orders
                     if (not start_time or o.submit_time >= start_time)
                     and (not end_time or o.submit_time <= end_time)]
        
        stats = {
            'total_orders': len(orders),
            'submitted': len([o for o in orders if o.status == OrderStatus.SUBMITTED]),
            'filled': len([o for o in orders if o.status == OrderStatus.FILLED]),
            'partial': len([o for o in orders if o.status == OrderStatus.PARTIAL]),
            'cancelled': len([o for o in orders if o.status == OrderStatus.CANCELLED]),
            'rejected': len([o for o in orders if o.status == OrderStatus.REJECTED]),
            'total_volume': sum(o.volume for o in orders),
            'filled_volume': sum(o.filled_volume for o in orders),
        }
        
        # 计算成交率
        if stats['total_orders'] > 0:
            stats['fill_rate'] = stats['filled'] / stats['total_orders'] * 100
        else:
            stats['fill_rate'] = 0.0
        
        return stats
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        撤销所有活跃订单
        
        Args:
            symbol: 合约代码，如果为None则撤销所有活跃订单
            
        Returns:
            撤销的订单数
        """
        active_orders = self.get_active_orders(symbol)
        count = 0
        
        for order in active_orders:
            if order.cancel():
                self.update_order(order)
                count += 1
        
        logger.info(f"已撤销{count}个订单")
        return count
    
    def register_order_callback(self, callback: Callable[[Order], None]):
        """注册订单回调"""
        if callback not in self.order_callbacks:
            self.order_callbacks.append(callback)
    
    def register_trade_callback(self, callback: Callable[[Order], None]):
        """注册成交回调"""
        if callback not in self.trade_callbacks:
            self.trade_callbacks.append(callback)
    
    def _trigger_order_callbacks(self, order: Order):
        """触发订单回调"""
        for callback in self.order_callbacks:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"订单回调执行失败: {e}")
    
    def _trigger_trade_callbacks(self, order: Order):
        """触发成交回调"""
        for callback in self.trade_callbacks:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"成交回调执行失败: {e}")
    
    def cleanup_old_orders(self, days: int = 7):
        """
        清理旧订单
        
        Args:
            days: 保留最近N天的订单
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            to_remove = []
            for order_id, order in self.orders.items():
                # 只清理已完成的订单（成交、撤销、拒绝）
                if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                    if order.update_time < cutoff_time:
                        to_remove.append(order_id)
            
            for order_id in to_remove:
                self.remove_order(order_id)
            
            logger.info(f"已清理{len(to_remove)}个旧订单")

