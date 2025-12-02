"""
RSI指标
"""
from typing import List, Optional


def RSI(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    计算RSI指标（相对强弱指标）
    
    Args:
        prices: 价格列表
        period: 周期（默认14）
        
    Returns:
        RSI值列表（0-100）
    """
    if len(prices) < period + 1:
        return [None] * len(prices)
    
    rsi_values = [None] * period
    
    # 计算价格变化
    changes = []
    for i in range(1, len(prices)):
        changes.append(prices[i] - prices[i - 1])
    
    # 计算初始平均涨幅和平均跌幅
    gains = [max(0, c) for c in changes[:period]]
    losses = [max(0, -c) for c in changes[:period]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    # 计算第一个RSI值
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    rsi_values.append(rsi)
    
    # 计算后续RSI值（使用平滑移动平均）
    for i in range(period, len(changes)):
        change = changes[i]
        gain = max(0, change)
        loss = max(0, -change)
        
        # 平滑移动平均
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values

