"""
策略基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime

from database.models import KlineData, TickData
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        self.name = name
        self.params = params or {}
        self.is_active = False
        self.symbols = []  # 策略关注的合约列表
        
        logger.info(f"策略初始化: {self.name}, 参数: {self.params}")
    
    @abstractmethod
    def on_init(self):
        """
        策略初始化回调
        在策略启动时调用，用于初始化指标、变量等
        """
        pass
    
    @abstractmethod
    def on_tick(self, tick: TickData):
        """
        Tick数据回调
        
        Args:
            tick: Tick数据对象
        """
        pass
    
    @abstractmethod
    def on_bar(self, bar: KlineData):
        """
        K线数据回调
        
        Args:
            bar: K线数据对象
        """
        pass
    
    def on_exit(self):
        """
        策略退出回调
        在策略停止时调用，用于清理资源
        """
        logger.info(f"策略退出: {self.name}")
    
    def add_symbol(self, symbol: str):
        """
        添加关注的合约
        
        Args:
            symbol: 合约代码
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info(f"策略 {self.name} 添加合约: {symbol}")
    
    def remove_symbol(self, symbol: str):
        """
        移除关注的合约
        
        Args:
            symbol: 合约代码
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            logger.info(f"策略 {self.name} 移除合约: {symbol}")
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """
        获取策略参数
        
        Args:
            key: 参数名
            default: 默认值
        
        Returns:
            参数值
        """
        return self.params.get(key, default)
    
    def set_param(self, key: str, value: Any):
        """
        设置策略参数
        
        Args:
            key: 参数名
            value: 参数值
        """
        self.params[key] = value
        logger.info(f"策略 {self.name} 设置参数: {key} = {value}")
    
    def buy(self, symbol: str, price: float, volume: int, 
            order_type: str = "LIMIT") -> Optional[str]:
        """
        买入开仓
        
        Args:
            symbol: 合约代码
            price: 价格
            volume: 数量（手）
            order_type: 订单类型（LIMIT, MARKET等）
        
        Returns:
            订单ID，如果下单失败返回None
        """
        logger.info(f"策略 {self.name} 买入信号: {symbol}, 价格={price}, 数量={volume}")
        # 注意：此方法需要由SimTrader或BacktestEngine绑定实际的交易接口
        return None
    
    def sell(self, symbol: str, price: float, volume: int,
             order_type: str = "LIMIT") -> Optional[str]:
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
        logger.info(f"策略 {self.name} 卖出信号: {symbol}, 价格={price}, 数量={volume}")
        # 注意：此方法需要由SimTrader或BacktestEngine绑定实际的交易接口
        return None
    
    def short(self, symbol: str, price: float, volume: int,
              order_type: str = "LIMIT") -> Optional[str]:
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
        logger.info(f"策略 {self.name} 做空信号: {symbol}, 价格={price}, 数量={volume}")
        # 注意：此方法需要由SimTrader或BacktestEngine绑定实际的交易接口
        return None
    
    def cover(self, symbol: str, price: float, volume: int,
              order_type: str = "LIMIT") -> Optional[str]:
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
        logger.info(f"策略 {self.name} 平空信号: {symbol}, 价格={price}, 数量={volume}")
        # 注意：此方法需要由SimTrader或BacktestEngine绑定实际的交易接口
        return None
    
    def write_log(self, msg: str):
        """
        写日志
        
        Args:
            msg: 日志消息
        """
        logger.info(f"[{self.name}] {msg}")
    
    def on_order_status(self, order):
        """
        订单状态更新回调（可选实现）
        
        Args:
            order: 订单对象
        """
        pass
    
    def on_trade(self, order):
        """
        订单成交回调（可选实现）
        
        Args:
            order: 订单对象
        """
        pass
    
    def on_position_update(self, position):
        """
        持仓更新回调（可选实现）
        
        Args:
            position: 持仓对象
        """
        pass
    
    def get_risk_params(self) -> Dict[str, Any]:
        """
        获取风控参数（可选实现）
        
        Returns:
            风控参数字典
        """
        return {}

