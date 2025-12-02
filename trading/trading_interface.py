"""
交易接口抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from trading.order import Order
from backtest.portfolio import Position


class TradingInterface(ABC):
    """交易接口抽象基类"""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接交易接口
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开连接
        
        Returns:
            是否断开成功
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            是否已连接
        """
        pass
    
    @abstractmethod
    def submit_order(self, order: Order) -> Optional[str]:
        """
        提交订单
        
        Args:
            order: 订单对象
            
        Returns:
            订单ID，如果失败返回None
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def query_account(self) -> Dict[str, Any]:
        """
        查询账户信息
        
        Returns:
            账户信息字典
        """
        pass
    
    @abstractmethod
    def query_positions(self) -> List[Position]:
        """
        查询持仓
        
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    def query_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        查询订单
        
        Args:
            symbol: 合约代码，如果为None则查询所有订单
            
        Returns:
            订单列表
        """
        pass

