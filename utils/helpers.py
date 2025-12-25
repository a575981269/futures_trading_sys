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


def is_trading_time(dt: Optional[datetime] = None) -> bool:
    """
    检查当前时间是否在交易时间内
    
    Args:
        dt: 要检查的时间，如果为None则使用当前时间
    
    Returns:
        是否在交易时间内
    """
    if dt is None:
        dt = datetime.now()
    
    hour = dt.hour
    minute = dt.minute
    time_minutes = hour * 60 + minute
    
    # 日盘时间：09:00-15:00
    day_start = 9 * 60  # 09:00
    day_end = 15 * 60  # 15:00
    
    # 夜盘时间：21:00-02:30（次日）
    night_start = 21 * 60  # 21:00
    night_end = 24 * 60 + 2 * 60 + 30  # 次日 02:30
    
    # 清算时间：16:00-19:00（CTP主席系统不开放）
    settlement_start = 16 * 60  # 16:00
    settlement_end = 19 * 60  # 19:00
    
    # 检查是否在清算时间内
    if settlement_start <= time_minutes < settlement_end:
        return False
    
    # 检查是否在日盘时间内
    if day_start <= time_minutes < day_end:
        return True
    
    # 检查是否在夜盘时间内（跨日）
    if time_minutes >= night_start or time_minutes < (night_end % (24 * 60)):
        return True
    
    return False


def is_7x24_trading_time(dt: Optional[datetime] = None) -> bool:
    """
    检查当前时间是否在7x24环境的交易时间内
    
    7x24环境交易时间：
    - 交易日：16:00～次日09:00
    - 非交易日：16:00～次日12:00
    
    Args:
        dt: 要检查的时间，如果为None则使用当前时间
    
    Returns:
        是否在7x24环境交易时间内
    """
    if dt is None:
        dt = datetime.now()
    
    hour = dt.hour
    minute = dt.minute
    time_minutes = hour * 60 + minute
    
    # 7x24环境交易时间：
    # - 16:00-24:00（当日）
    # - 00:00-09:00（次日，交易日）
    # - 00:00-12:00（次日，非交易日）
    
    # 16:00之后到24:00之前，属于7x24交易时间
    if time_minutes >= 16 * 60:
        return True
    
    # 00:00到09:00之间，属于7x24交易时间（交易日）
    # 注意：这里简化处理，假设都是交易日
    # 实际应用中可以根据交易日历判断
    if time_minutes < 9 * 60:
        return True
    
    # 09:00-12:00之间，需要判断是否为交易日
    # 这里简化处理，假设都是交易日，所以返回True
    # 实际应用中应该根据交易日历判断
    if 9 * 60 <= time_minutes < 12 * 60:
        # 简化：假设都是交易日
        return True
    
    # 12:00-16:00之间，7x24环境不开放（系统维护时间）
    return False


def get_next_trading_time(dt: Optional[datetime] = None) -> datetime:
    """
    获取下一个交易时间
    
    Args:
        dt: 当前时间，如果为None则使用当前时间
    
    Returns:
        下一个交易时间
    """
    if dt is None:
        dt = datetime.now()
    
    hour = dt.hour
    minute = dt.minute
    time_minutes = hour * 60 + minute
    
    # 清算时间：16:00-19:00
    settlement_start = 16 * 60
    settlement_end = 19 * 60
    
    # 如果在清算时间内，下一个交易时间是夜盘 21:00
    if settlement_start <= time_minutes < settlement_end:
        next_time = dt.replace(hour=21, minute=0, second=0, microsecond=0)
        if next_time <= dt:
            next_time = next_time.replace(day=next_time.day + 1)
        return next_time
    
    # 如果在日盘结束后（15:00-16:00），下一个交易时间是夜盘 21:00
    if 15 * 60 <= time_minutes < settlement_start:
        next_time = dt.replace(hour=21, minute=0, second=0, microsecond=0)
        return next_time
    
    # 如果在夜盘结束后（02:30-09:00），下一个交易时间是日盘 09:00
    if time_minutes < 9 * 60 or (time_minutes >= 2 * 60 + 30 and time_minutes < 9 * 60):
        next_time = dt.replace(hour=9, minute=0, second=0, microsecond=0)
        if next_time <= dt:
            next_time = next_time.replace(day=next_time.day + 1)
        return next_time
    
    # 如果在夜盘结束后（02:30之后），下一个交易时间是日盘 09:00
    if time_minutes >= 2 * 60 + 30 and time_minutes < 9 * 60:
        next_time = dt.replace(hour=9, minute=0, second=0, microsecond=0)
        if next_time <= dt:
            next_time = next_time.replace(day=next_time.day + 1)
        return next_time
    
    # 默认返回下一个日盘时间
    next_time = dt.replace(hour=9, minute=0, second=0, microsecond=0)
    if next_time <= dt:
        next_time = next_time.replace(day=next_time.day + 1)
    return next_time


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

