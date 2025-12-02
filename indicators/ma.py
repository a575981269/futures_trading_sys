"""
均线指标
"""
from typing import List, Optional
import numpy as np

from database.models import KlineData
from utils.logger import get_logger

logger = get_logger(__name__)


def MA(prices: List[float], period: int) -> List[Optional[float]]:
    """
    计算简单移动平均线（MA）
    
    Args:
        prices: 价格列表
        period: 周期
        
    Returns:
        MA值列表
    """
    if len(prices) < period:
        return [None] * len(prices)
    
    ma_values = []
    for i in range(len(prices)):
        if i < period - 1:
            ma_values.append(None)
        else:
            ma = sum(prices[i - period + 1:i + 1]) / period
            ma_values.append(ma)
    
    return ma_values


def SMA(prices: List[float], period: int) -> List[Optional[float]]:
    """
    计算简单移动平均线（SMA，与MA相同）
    
    Args:
        prices: 价格列表
        period: 周期
        
    Returns:
        SMA值列表
    """
    return MA(prices, period)


def EMA(prices: List[float], period: int) -> List[Optional[float]]:
    """
    计算指数移动平均线（EMA）
    
    Args:
        prices: 价格列表
        period: 周期
        
    Returns:
        EMA值列表
    """
    if len(prices) < period:
        return [None] * len(prices)
    
    multiplier = 2.0 / (period + 1)
    ema_values = []
    
    # 第一个EMA值使用SMA
    first_ema = sum(prices[:period]) / period
    ema_values.extend([None] * (period - 1))
    ema_values.append(first_ema)
    
    # 计算后续EMA值
    for i in range(period, len(prices)):
        ema = (prices[i] - ema_values[i - 1]) * multiplier + ema_values[i - 1]
        ema_values.append(ema)
    
    return ema_values


def calculate_ma_from_klines(klines: List[KlineData],
                            period: int,
                            price_type: str = 'close',
                            ma_type: str = 'SMA') -> List[Optional[float]]:
    """
    从K线数据计算均线
    
    Args:
        klines: K线数据列表
        period: 周期
        price_type: 价格类型（'open', 'high', 'low', 'close'）
        ma_type: 均线类型（'SMA', 'EMA'）
        
    Returns:
        均线值列表
    """
    # 提取价格
    price_map = {
        'open': lambda k: k.open,
        'high': lambda k: k.high,
        'low': lambda k: k.low,
        'close': lambda k: k.close,
    }
    
    get_price = price_map.get(price_type, lambda k: k.close)
    prices = [get_price(k) for k in klines]
    
    # 计算均线
    if ma_type == 'EMA':
        return EMA(prices, period)
    else:
        return SMA(prices, period)

