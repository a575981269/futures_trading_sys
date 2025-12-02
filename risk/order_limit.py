"""
订单限制风控
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque
from risk.risk_rules import RiskResult, RiskLevel
from trading.order import Order
from config.contracts import get_price_tick
from utils.logger import get_logger

logger = get_logger(__name__)


class OrderLimit:
    """订单限制"""
    
    def __init__(self,
                 max_orders_per_minute: Optional[int] = None,
                 max_orders_per_symbol_per_minute: Optional[int] = None,
                 max_price_deviation_ratio: Optional[float] = None):
        """
        初始化订单限制
        
        Args:
            max_orders_per_minute: 每分钟最大订单数
            max_orders_per_symbol_per_minute: 单品种每分钟最大订单数
            max_price_deviation_ratio: 价格偏离当前价的最大比例（0-1）
        """
        self.max_orders_per_minute = max_orders_per_minute
        self.max_orders_per_symbol_per_minute = max_orders_per_symbol_per_minute
        self.max_price_deviation_ratio = max_price_deviation_ratio
        
        # 订单时间记录（用于频率限制）
        self.order_times: deque = deque()  # 所有订单时间
        self.symbol_order_times: Dict[str, deque] = {}  # 按品种的订单时间
        
        logger.info(f"订单限制初始化: 每分钟最大={max_orders_per_minute}, "
                   f"单品种每分钟最大={max_orders_per_symbol_per_minute}, "
                   f"价格偏离比例={max_price_deviation_ratio}")
    
    def check_order_risk(self,
                         order: Order,
                         current_price: Optional[float] = None) -> RiskResult:
        """
        检查订单风险
        
        Args:
            order: 订单对象
            current_price: 当前市场价格（用于价格偏离检查）
            
        Returns:
            风控结果
        """
        now = datetime.now()
        
        # 检查每分钟订单数限制
        if self.max_orders_per_minute is not None:
            # 清理1分钟前的记录
            cutoff_time = now - timedelta(minutes=1)
            while self.order_times and self.order_times[0] < cutoff_time:
                self.order_times.popleft()
            
            if len(self.order_times) >= self.max_orders_per_minute:
                return RiskResult.block(
                    f"下单频率超限",
                    f"过去1分钟内已有{len(self.order_times)}笔订单，"
                    f"超过限制{self.max_orders_per_minute}笔"
                )
        
        # 检查单品种每分钟订单数限制
        if self.max_orders_per_symbol_per_minute is not None:
            if order.symbol not in self.symbol_order_times:
                self.symbol_order_times[order.symbol] = deque()
            
            symbol_times = self.symbol_order_times[order.symbol]
            cutoff_time = now - timedelta(minutes=1)
            while symbol_times and symbol_times[0] < cutoff_time:
                symbol_times.popleft()
            
            if len(symbol_times) >= self.max_orders_per_symbol_per_minute:
                return RiskResult.block(
                    f"单品种下单频率超限: {order.symbol}",
                    f"过去1分钟内已有{len(symbol_times)}笔订单，"
                    f"超过限制{self.max_orders_per_symbol_per_minute}笔"
                )
        
        # 检查价格偏离
        if self.max_price_deviation_ratio is not None and current_price is not None:
            if current_price > 0:
                deviation_ratio = abs(order.price - current_price) / current_price
                if deviation_ratio > self.max_price_deviation_ratio:
                    return RiskResult.block(
                        f"订单价格偏离过大: {order.symbol}",
                        f"订单价格{order.price}，当前价{current_price}，"
                        f"偏离{deviation_ratio*100:.2f}%，超过限制{self.max_price_deviation_ratio*100:.2f}%"
                    )
        
        # 记录订单时间
        self.order_times.append(now)
        if order.symbol in self.symbol_order_times:
            self.symbol_order_times[order.symbol].append(now)
        else:
            self.symbol_order_times[order.symbol] = deque([now])
        
        return RiskResult.safe(f"订单风控检查通过: {order.symbol}")

