"""
MACD指标
"""
from typing import List, Optional, Tuple
from indicators.ma import EMA


def MACD(prices: List[float],
         fast_period: int = 12,
         slow_period: int = 26,
         signal_period: int = 9) -> Tuple[List[Optional[float]],
                                          List[Optional[float]],
                                          List[Optional[float]]]:
    """
    计算MACD指标
    
    Args:
        prices: 价格列表
        fast_period: 快线周期（默认12）
        slow_period: 慢线周期（默认26）
        signal_period: 信号线周期（默认9）
        
    Returns:
        (DIF, DEA, MACD) 元组
    """
    # 计算快线和慢线EMA
    fast_ema = EMA(prices, fast_period)
    slow_ema = EMA(prices, slow_period)
    
    # 计算DIF（快线 - 慢线）
    dif = []
    for i in range(len(prices)):
        if fast_ema[i] is None or slow_ema[i] is None:
            dif.append(None)
        else:
            dif.append(fast_ema[i] - slow_ema[i])
    
    # 计算DEA（DIF的EMA）
    dea = EMA([d if d is not None else 0 for d in dif], signal_period)
    
    # 计算MACD柱（(DIF - DEA) * 2）
    macd = []
    for i in range(len(prices)):
        if dif[i] is None or dea[i] is None:
            macd.append(None)
        else:
            macd.append((dif[i] - dea[i]) * 2)
    
    return dif, dea, macd

