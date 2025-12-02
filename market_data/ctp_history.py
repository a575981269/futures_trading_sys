"""
CTP历史行情接口
"""
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from database.models import KlineData, TickData
from database.db_manager import DatabaseManager
from market_data.data_handler import DataHandler
from config.settings import settings
from utils.logger import get_logger
from utils.helpers import parse_datetime

logger = get_logger(__name__)


class CTPHistoryData:
    """CTP历史行情数据接口"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化历史行情接口
        
        Args:
            db_manager: 数据库管理器，如果为None则自动创建
        """
        self.db_manager = db_manager or DatabaseManager(settings.DB_URL)
        self.data_handler = DataHandler()
        logger.info("CTP历史行情接口初始化完成")
    
    def get_kline(self, symbol: str, interval: str,
                  start_date: str, end_date: str,
                  from_db: bool = True) -> List[KlineData]:
        """
        获取历史K线数据
        
        Args:
            symbol: 合约代码
            interval: K线周期（1m, 5m, 15m, 30m, 1h, 1d等）
            start_date: 开始日期，格式：'2024-01-01'
            end_date: 结束日期，格式：'2024-01-31'
            from_db: 是否优先从数据库获取（True: 从数据库, False: 从CTP查询）
        
        Returns:
            K线数据列表
        """
        start_dt = parse_datetime(start_date)
        end_dt = parse_datetime(end_date)
        
        if not start_dt or not end_dt:
            logger.error(f"日期格式错误: {start_date}, {end_date}")
            return []
        
        # 如果从数据库获取
        if from_db:
            klines = self.db_manager.get_klines(symbol, interval, start_dt, end_dt)
            if klines:
                logger.info(f"从数据库获取K线数据: {symbol}, {len(klines)}条")
                return klines
        
        # 从CTP查询（需要实现CTP接口调用）
        logger.info(f"从CTP查询K线数据: {symbol}, {interval}, {start_date} ~ {end_date}")
        klines = self._query_kline_from_ctp(symbol, interval, start_dt, end_dt)
        
        # 保存到数据库
        if klines:
            self.db_manager.save_klines_batch(klines)
            logger.info(f"K线数据已保存到数据库: {len(klines)}条")
        
        return klines
    
    def _query_kline_from_ctp(self, symbol: str, interval: str,
                             start_dt: datetime, end_dt: datetime) -> List[KlineData]:
        """
        从CTP查询K线数据（需要实现具体的CTP接口调用）
        
        Args:
            symbol: 合约代码
            interval: K线周期
            start_dt: 开始时间
            end_dt: 结束时间
        
        Returns:
            K线数据列表
        """
        # TODO: 实现CTP接口调用
        # 这里需要根据实际的CTP接口实现
        # 可以使用vnpy-ctp或其他CTP封装库
        
        logger.warning("CTP接口查询功能待实现，请使用vnpy-ctp或其他CTP库")
        
        # 示例：使用vnpy-ctp的接口
        # from vnpy.gateway.ctp import CtpGateway
        # gateway = CtpGateway()
        # gateway.connect(settings.get_ctp_config())
        # data = gateway.query_history(symbol, interval, start_dt, end_dt)
        
        return []
    
    def get_tick(self, symbol: str, start_date: str, end_date: str,
                from_db: bool = True) -> List[TickData]:
        """
        获取历史Tick数据
        
        Args:
            symbol: 合约代码
            start_date: 开始日期
            end_date: 结束日期
            from_db: 是否优先从数据库获取
        
        Returns:
            Tick数据列表
        """
        start_dt = parse_datetime(start_date)
        end_dt = parse_datetime(end_date)
        
        if not start_dt or not end_dt:
            logger.error(f"日期格式错误: {start_date}, {end_date}")
            return []
        
        # 如果从数据库获取
        if from_db:
            ticks = self.db_manager.get_ticks(symbol, start_dt, end_dt)
            if ticks:
                logger.info(f"从数据库获取Tick数据: {symbol}, {len(ticks)}条")
                return ticks
        
        # 从CTP查询
        logger.info(f"从CTP查询Tick数据: {symbol}, {start_date} ~ {end_date}")
        ticks = self._query_tick_from_ctp(symbol, start_dt, end_dt)
        
        # 保存到数据库
        if ticks:
            self.db_manager.save_ticks_batch(ticks)
            logger.info(f"Tick数据已保存到数据库: {len(ticks)}条")
        
        return ticks
    
    def _query_tick_from_ctp(self, symbol: str,
                             start_dt: datetime, end_dt: datetime) -> List[TickData]:
        """
        从CTP查询Tick数据（需要实现具体的CTP接口调用）
        
        Args:
            symbol: 合约代码
            start_dt: 开始时间
            end_dt: 结束时间
        
        Returns:
            Tick数据列表
        """
        # TODO: 实现CTP接口调用
        logger.warning("CTP接口查询功能待实现")
        return []
    
    def download_and_save(self, symbol: str, interval: str,
                         start_date: str, end_date: str):
        """
        下载并保存历史数据到数据库
        
        Args:
            symbol: 合约代码
            interval: K线周期
            start_date: 开始日期
            end_date: 结束日期
        """
        logger.info(f"开始下载历史数据: {symbol}, {interval}, {start_date} ~ {end_date}")
        klines = self.get_kline(symbol, interval, start_date, end_date, from_db=False)
        logger.info(f"历史数据下载完成: {len(klines)}条")
    
    def get_latest_kline(self, symbol: str, interval: str) -> Optional[KlineData]:
        """
        获取最新一条K线数据
        
        Args:
            symbol: 合约代码
            interval: K线周期
        
        Returns:
            最新K线数据，如果不存在返回None
        """
        return self.db_manager.get_latest_kline(symbol, interval)

