"""
布林带指标
"""
from typing import List, Optional, Tuple
from indicators.ma import SMA
import statistics


def BollingerBands(prices: List[float],
                  period: int = 20,
                  num_std: float = 2.0) -> Tuple[List[Optional[float]],
                                                 List[Optional[float]],
                                                 List[Optional[float]]]:
    """
    计算布林带指标
    
    Args:
        prices: 价格列表
        period: 周期（默认20）
        num_std: 标准差倍数（默认2.0）
        
    Returns:
        (上轨, 中轨, 下轨) 元组
    """
    if len(prices) < period:
        return ([None] * len(prices),
                [None] * len(prices),
                [None] * len(prices))
    
    # 计算中轨（SMA）
    middle_band = SMA(prices, period)
    
    # 计算上轨和下轨
    upper_band = []
    lower_band = []
    
    for i in range(len(prices)):
        if i < period - 1:
            upper_band.append(None)
            lower_band.append(None)
        else:
            # 计算标准差
            period_prices = prices[i - period + 1:i + 1]
            std = statistics.stdev(period_prices)
            
            # 计算上下轨
            middle = middle_band[i]
            if middle is not None:
                upper_band.append(middle + num_std * std)
                lower_band.append(middle - num_std * std)
            else:
                upper_band.append(None)
                lower_band.append(None)
    
    return upper_band, middle_band, lower_band

