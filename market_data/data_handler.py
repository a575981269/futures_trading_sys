"""
行情数据处理模块
"""
from datetime import datetime
from typing import Dict, Optional, List
from database.models import KlineData, TickData
from utils.logger import get_logger
from utils.helpers import parse_symbol

logger = get_logger(__name__)


class DataHandler:
    """行情数据处理器"""
    
    @staticmethod
    def create_kline(symbol: str, dt: datetime, interval: str,
                    open_price: float, high_price: float, 
                    low_price: float, close_price: float,
                    volume: int = 0, open_interest: int = 0,
                    turnover: float = 0.0) -> KlineData:
        """
        创建K线数据对象
        
        Args:
            symbol: 合约代码
            dt: K线时间
            interval: K线周期
            open_price: 开盘价
            high_price: 最高价
            low_price: 最低价
            close_price: 收盘价
            volume: 成交量
            open_interest: 持仓量
            turnover: 成交额
        
        Returns:
            KlineData对象
        """
        symbol_code, exchange = parse_symbol(symbol)
        
        kline = KlineData(
            symbol=symbol_code,
            exchange=exchange,
            datetime=dt,
            interval=interval,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            open_interest=open_interest,
            turnover=turnover
        )
        
        return kline
    
    @staticmethod
    def create_tick(symbol: str, dt: datetime,
                   last_price: float, volume: int = 0,
                   open_interest: int = 0,
                   bid_price1: Optional[float] = None,
                   bid_volume1: Optional[int] = None,
                   ask_price1: Optional[float] = None,
                   ask_volume1: Optional[int] = None,
                   turnover: float = 0.0) -> TickData:
        """
        创建Tick数据对象
        
        Args:
            symbol: 合约代码
            dt: Tick时间
            last_price: 最新价
            volume: 成交量
            open_interest: 持仓量
            bid_price1: 买一价
            bid_volume1: 买一量
            ask_price1: 卖一价
            ask_volume1: 卖一量
            turnover: 成交额
        
        Returns:
            TickData对象
        """
        symbol_code, exchange = parse_symbol(symbol)
        
        tick = TickData(
            symbol=symbol_code,
            exchange=exchange,
            datetime=dt,
            last_price=last_price,
            volume=volume,
            open_interest=open_interest,
            bid_price1=bid_price1,
            bid_volume1=bid_volume1,
            ask_price1=ask_price1,
            ask_volume1=ask_volume1,
            turnover=turnover
        )
        
        return tick
    
    @staticmethod
    def validate_kline(kline: KlineData) -> bool:
        """
        验证K线数据有效性
        
        Args:
            kline: K线数据对象
        
        Returns:
            是否有效
        """
        if kline.high < kline.low:
            logger.warning(f"K线数据无效：最高价 < 最低价, {kline}")
            return False
        
        if kline.open < kline.low or kline.open > kline.high:
            logger.warning(f"K线数据无效：开盘价超出范围, {kline}")
            return False
        
        if kline.close < kline.low or kline.close > kline.high:
            logger.warning(f"K线数据无效：收盘价超出范围, {kline}")
            return False
        
        if kline.volume < 0:
            logger.warning(f"K线数据无效：成交量为负, {kline}")
            return False
        
        return True
    
    @staticmethod
    def validate_tick(tick: TickData) -> bool:
        """
        验证Tick数据有效性
        
        Args:
            tick: Tick数据对象
        
        Returns:
            是否有效
        """
        if tick.last_price <= 0:
            logger.warning(f"Tick数据无效：价格 <= 0, {tick}")
            return False
        
        if tick.volume < 0:
            logger.warning(f"Tick数据无效：成交量为负, {tick}")
            return False
        
        if tick.bid_price1 and tick.ask_price1:
            if tick.bid_price1 > tick.ask_price1:
                logger.warning(f"Tick数据无效：买一价 > 卖一价, {tick}")
                return False
        
        return True
    
    @staticmethod
    def kline_to_dict(kline: KlineData) -> Dict:
        """
        将K线数据转换为字典
        
        Args:
            kline: K线数据对象
        
        Returns:
            字典格式的数据
        """
        return {
            'symbol': kline.symbol,
            'exchange': kline.exchange,
            'datetime': kline.datetime,
            'interval': kline.interval,
            'open': kline.open,
            'high': kline.high,
            'low': kline.low,
            'close': kline.close,
            'volume': kline.volume,
            'open_interest': kline.open_interest,
            'turnover': kline.turnover,
        }
    
    @staticmethod
    def tick_to_dict(tick: TickData) -> Dict:
        """
        将Tick数据转换为字典
        
        Args:
            tick: Tick数据对象
        
        Returns:
            字典格式的数据
        """
        return {
            'symbol': tick.symbol,
            'exchange': tick.exchange,
            'datetime': tick.datetime,
            'last_price': tick.last_price,
            'volume': tick.volume,
            'open_interest': tick.open_interest,
            'bid_price1': tick.bid_price1,
            'bid_volume1': tick.bid_volume1,
            'ask_price1': tick.ask_price1,
            'ask_volume1': tick.ask_volume1,
            'turnover': tick.turnover,
        }
    
    @staticmethod
    def klines_to_dataframe(klines: List[KlineData]):
        """
        将K线数据列表转换为pandas DataFrame
        
        Args:
            klines: K线数据列表
        
        Returns:
            pandas DataFrame
        """
        try:
            import pandas as pd
            
            data = [DataHandler.kline_to_dict(k) for k in klines]
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('datetime', inplace=True)
            return df
        except ImportError:
            logger.error("pandas未安装，无法转换为DataFrame")
            return None

