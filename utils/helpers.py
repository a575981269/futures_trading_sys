"""
辅助函数模块
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re


def parse_symbol(symbol: str) -> Tuple[str, str]:
    """
    解析合约代码，提取品种和交易所
    
    Args:
        symbol: 合约代码，如 'rb2501' 或 'rb2501.SHFE'
    
    Returns:
        (品种代码, 交易所代码)
    """
    # 如果包含点号，说明有交易所后缀
    if '.' in symbol:
        parts = symbol.split('.')
        return parts[0], parts[1]
    
    # 否则根据品种代码推断交易所
    # 这里可以根据实际情况扩展
    exchange_map = {
        'rb': 'SHFE',  # 螺纹钢 - 上期所
        'hc': 'SHFE',  # 热卷 - 上期所
        'cu': 'SHFE',  # 铜 - 上期所
        'al': 'SHFE',  # 铝 - 上期所
        'zn': 'SHFE',  # 锌 - 上期所
        'au': 'SHFE',  # 黄金 - 上期所
        'ag': 'SHFE',  # 白银 - 上期所
        'i': 'DCE',    # 铁矿石 - 大商所
        'j': 'DCE',    # 焦炭 - 大商所
        'jm': 'DCE',   # 焦煤 - 大商所
        'c': 'DCE',    # 玉米 - 大商所
        'cs': 'DCE',   # 玉米淀粉 - 大商所
        'CF': 'CZCE',  # 棉花 - 郑商所
        'TA': 'CZCE',  # PTA - 郑商所
        'MA': 'CZCE',  # 甲醇 - 郑商所
        'IF': 'CFFEX', # 沪深300 - 中金所
        'IC': 'CFFEX', # 中证500 - 中金所
        'IH': 'CFFEX', # 上证50 - 中金所
    }
    
    # 提取品种代码（去掉数字部分）
    product_code = re.sub(r'\d+', '', symbol).lower()
    
    # 处理大写品种代码
    if product_code == '':
        product_code = re.sub(r'\d+', '', symbol)
    
    exchange = exchange_map.get(product_code, 'UNKNOWN')
    return symbol, exchange


def parse_datetime(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串，支持多种格式
                 '2024-01-01', '2024-01-01 10:00:00', '20240101'
    
    Returns:
        datetime对象，解析失败返回None
    """
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y%m%d',
        '%Y/%m/%d',
        '%Y/%m/%d %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def get_trading_days(start_date: datetime, end_date: datetime) -> list:
    """
    获取交易日列表（简化版，实际应该从交易所获取）
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        交易日列表
    """
    # 这里简化处理，实际应该排除周末和节假日
    days = []
    current = start_date
    while current <= end_date:
        # 排除周末
        if current.weekday() < 5:  # 0-4 是周一到周五
            days.append(current)
        current += timedelta(days=1)
    return days


def format_number(value: float, decimals: int = 2) -> str:
    """
    格式化数字显示
    
    Args:
        value: 数值
        decimals: 小数位数
    
    Returns:
        格式化后的字符串
    """
    return f"{value:.{decimals}f}"


def calculate_pnl(entry_price: float, exit_price: float, 
                  volume: int, direction: int, 
                  multiplier: int = 1) -> float:
    """
    计算盈亏
    
    Args:
        entry_price: 开仓价
        exit_price: 平仓价
        volume: 手数
        direction: 方向（1: 多头, -1: 空头）
        multiplier: 合约乘数
    
    Returns:
        盈亏金额
    """
    if direction == 1:  # 多头
        return (exit_price - entry_price) * volume * multiplier
    else:  # 空头
        return (entry_price - exit_price) * volume * multiplier

