"""
订单管理模块
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

from utils.logger import get_logger

logger = get_logger(__name__)


class OrderType(Enum):
    """订单类型"""
    LIMIT = "LIMIT"      # 限价单
    MARKET = "MARKET"    # 市价单
    STOP = "STOP"        # 止损单
    STOP_LIMIT = "STOP_LIMIT"  # 止损限价单


class OrderStatus(Enum):
    """订单状态"""
    SUBMITTING = "SUBMITTING"    # 提交中
    SUBMITTED = "SUBMITTED"      # 已提交
    PARTIAL = "PARTIAL"          # 部分成交
    FILLED = "FILLED"            # 全部成交
    CANCELLED = "CANCELLED"      # 已撤销
    REJECTED = "REJECTED"        # 已拒绝


class OrderDirection(Enum):
    """订单方向"""
    BUY = "BUY"          # 买入
    SELL = "SELL"        # 卖出
    SHORT = "SHORT"      # 做空
    COVER = "COVER"      # 平空


@dataclass
class Order:
    """订单对象"""
    symbol: str
    direction: OrderDirection
    price: float
    volume: int
    order_type: OrderType = OrderType.LIMIT
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: OrderStatus = OrderStatus.SUBMITTING
    filled_volume: int = 0  # 已成交数量
    filled_price: float = 0.0  # 平均成交价
    submit_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    cancel_time: Optional[datetime] = None
    reject_reason: Optional[str] = None
    
    def is_active(self) -> bool:
        """判断订单是否活跃（可撤销）"""
        return self.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIAL]
    
    def is_filled(self) -> bool:
        """判断订单是否全部成交"""
        return self.status == OrderStatus.FILLED
    
    def is_cancelled(self) -> bool:
        """判断订单是否已撤销"""
        return self.status == OrderStatus.CANCELLED
    
    def is_rejected(self) -> bool:
        """判断订单是否被拒绝"""
        return self.status == OrderStatus.REJECTED
    
    def get_remaining_volume(self) -> int:
        """获取剩余未成交数量"""
        return self.volume - self.filled_volume
    
    def update_fill(self, fill_volume: int, fill_price: float):
        """
        更新成交信息
        
        Args:
            fill_volume: 成交数量
            fill_price: 成交价格
        """
        self.filled_volume += fill_volume
        
        # 计算平均成交价
        if self.filled_volume > 0:
            total_cost = self.filled_price * (self.filled_volume - fill_volume) + fill_price * fill_volume
            self.filled_price = total_cost / self.filled_volume
        
        # 更新状态
        if self.filled_volume >= self.volume:
            self.status = OrderStatus.FILLED
        elif self.filled_volume > 0:
            self.status = OrderStatus.PARTIAL
        else:
            self.status = OrderStatus.SUBMITTED
        
        self.update_time = datetime.now()
        logger.info(f"订单成交: {self.order_id}, {self.symbol}, {fill_volume}手@{fill_price}, "
                   f"已成交{self.filled_volume}/{self.volume}")
    
    def cancel(self):
        """撤销订单"""
        if not self.is_active():
            logger.warning(f"订单{self.order_id}无法撤销，当前状态: {self.status}")
            return False
        
        self.status = OrderStatus.CANCELLED
        self.cancel_time = datetime.now()
        self.update_time = datetime.now()
        logger.info(f"订单已撤销: {self.order_id}, {self.symbol}")
        return True
    
    def reject(self, reason: str):
        """
        拒绝订单
        
        Args:
            reason: 拒绝原因
        """
        self.status = OrderStatus.REJECTED
        self.reject_reason = reason
        self.update_time = datetime.now()
        logger.warning(f"订单被拒绝: {self.order_id}, {self.symbol}, 原因: {reason}")
    
    def __repr__(self):
        return (f"Order(id={self.order_id}, symbol={self.symbol}, "
                f"direction={self.direction.value}, price={self.price}, "
                f"volume={self.volume}, status={self.status.value}, "
                f"filled={self.filled_volume}/{self.volume})")

