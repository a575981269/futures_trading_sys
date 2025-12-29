"""
CTP历史行情接口
"""
from datetime import datetime, timedelta
from typing import List, Optional, Callable
import time
from database.models import KlineData, TickData
from database.db_manager import DatabaseManager
from market_data.data_handler import DataHandler
from config.settings import settings
from utils.logger import get_logger
from utils.helpers import parse_datetime, parse_symbol

logger = get_logger(__name__)

# 尝试导入vnpy-ctp
try:
    from vnpy_ctp import CtpGateway
    from vnpy.event import EventEngine
    from vnpy.trader.object import HistoryRequest
    from vnpy.trader.constant import Exchange, Interval
    VNPY_CTP_AVAILABLE = True
except ImportError:
    try:
        from vnpy.gateway.ctp import CtpGateway
        from vnpy.event import EventEngine
        from vnpy.trader.object import HistoryRequest
        from vnpy.trader.constant import Exchange, Interval
        VNPY_CTP_AVAILABLE = True
    except ImportError:
        VNPY_CTP_AVAILABLE = False
        HistoryRequest = None
        Exchange = None
        Interval = None
        logger.warning("vnpy-ctp未安装，历史数据查询功能将不可用")


class CTPHistoryData:
    """CTP历史行情数据接口"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 environment: Optional[str] = None):
        """
        初始化历史行情接口
        
        Args:
            db_manager: 数据库管理器，如果为None则自动创建
            environment: 环境类型（"normal" 或 "7x24"），如果为None则使用配置中的环境类型
        """
        self.db_manager = db_manager or DatabaseManager(settings.DB_URL)
        self.data_handler = DataHandler()
        self.environment = environment or settings.CTP_ENVIRONMENT
        self._ctp_gateway: Optional[CtpGateway] = None
        self._event_engine: Optional[EventEngine] = None
        self._connected = False
        
        env_name = "7x24环境" if settings.is_7x24_environment(self.environment) else "CTP主席系统"
        logger.info(f"CTP历史行情接口初始化完成（{env_name}）")
    
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
            else:
                logger.info(f"数据库中未找到K线数据: {symbol}, {interval}, {start_date} ~ {end_date}")
                logger.info("提示：如需从CTP查询，请使用 from_db=False（注意：CTP API 通常不支持直接查询历史数据）")
                return []
        
        # 从CTP查询（需要实现CTP接口调用）
        # 注意：CTP API 通常不支持直接查询历史数据，此方法可能返回空
        logger.info(f"从CTP查询K线数据: {symbol}, {interval}, {start_date} ~ {end_date}")
        logger.warning("提示：CTP API 通常不支持直接查询历史数据，建议使用 from_db=True 从数据库获取")
        klines = self._query_kline_from_ctp(symbol, interval, start_dt, end_dt)
        
        # 保存到数据库
        if klines:
            self.db_manager.save_klines_batch(klines)
            logger.info(f"K线数据已保存到数据库: {len(klines)}条")
        else:
            logger.info("未从CTP查询到数据，建议使用实时行情接口积累数据到数据库")
        
        return klines
    
    def _connect_ctp(self) -> bool:
        """
        连接到CTP服务器（如果需要查询历史数据）
        
        Returns:
            是否连接成功
        """
        if self._connected:
            return True
        
        if not VNPY_CTP_AVAILABLE:
            logger.error("vnpy-ctp未安装，无法查询历史数据")
            return False
        
        # 检查交易时间（仅CTP主席系统需要检查，7x24环境全天候开放）
        from utils.helpers import is_trading_time, get_next_trading_time
        is_7x24 = settings.is_7x24_environment(self.environment)
        if not is_7x24 and not is_trading_time():
            next_time = get_next_trading_time()
            logger.warning(f"当前不在交易时间内，CTP主席系统不开放")
            logger.info(f"下一个交易时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("提示：如需在非交易时间查询，请使用7x24环境")
            return False
        
        try:
            # 创建事件引擎
            self._event_engine = EventEngine()
            self._event_engine.start()
            
            # 创建CTP网关
            self._ctp_gateway = CtpGateway(self._event_engine, "CTP")
            
            # 根据环境类型获取服务器地址
            addresses = settings.get_server_addresses(self.environment)
            
            env_name = "7x24环境" if is_7x24 else "CTP主席系统"
            logger.info(f"正在连接CTP服务器（{env_name}）: {addresses['md_address']}")
            
            # 配置CTP连接参数
            ctp_setting = {
                "用户名": settings.CTP_USER_ID,
                "密码": settings.CTP_PASSWORD,
                "经纪商代码": settings.CTP_BROKER_ID,
                "交易服务器": addresses['trade_address'],
                "行情服务器": addresses['md_address'],
                "产品名称": settings.CTP_APP_ID,
                "授权编码": settings.CTP_AUTH_CODE,
            }
            
            # 连接
            self._ctp_gateway.connect(ctp_setting)
            
            # 等待连接完成（最多等待10秒）
            import time
            timeout = 10
            start_time = time.time()
            
            # 注册日志事件来检测连接状态
            from vnpy.trader.event import EVENT_LOG
            connection_events = []
            
            def on_log(event):
                if hasattr(event, 'data') and event.data:
                    msg = str(event.data.msg) if hasattr(event.data, 'msg') else str(event.data)
                    connection_events.append(msg)
                    if '登录成功' in msg or '行情服务器登录成功' in msg or '交易服务器登录成功' in msg:
                        self._connected = True
            
            self._event_engine.register(EVENT_LOG, on_log)
            
            while not self._connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # 如果超时，检查是否有连接相关的日志
            if not self._connected and connection_events:
                logger.debug(f"连接日志: {connection_events[-5:]}")  # 显示最后5条日志
            
            if self._connected:
                logger.info("CTP连接成功，可以查询历史数据")
            else:
                logger.warning("CTP连接超时，历史数据查询可能失败")
            
            return self._connected
            
        except Exception as e:
            logger.error(f"连接CTP失败: {e}")
            return False
    
    def _get_exchange_enum(self, exchange_str: str):
        """将交易所字符串转换为Exchange枚举"""
        if not VNPY_CTP_AVAILABLE or not Exchange:
            return None
        
        exchange_map = {
            'SHFE': Exchange.SHFE,
            'DCE': Exchange.DCE,
            'CZCE': Exchange.CZCE,
            'CFFEX': Exchange.CFFEX,
            'INE': Exchange.INE,
            'GFEX': Exchange.GFEX,
        }
        return exchange_map.get(exchange_str)
    
    def _get_interval_enum(self, interval_str: str):
        """
        将K线周期字符串转换为Interval枚举
        
        注意：vnpy 的 Interval 枚举只支持基本周期：
        - MINUTE (1分钟)
        - HOUR (1小时)
        - DAILY (日线)
        - WEEKLY (周线)
        - TICK (Tick数据)
        
        对于 5m, 15m, 30m 等周期，vnpy-ctp 可能不支持直接查询，
        需要从 1分钟数据聚合生成。
        """
        if not VNPY_CTP_AVAILABLE or not Interval:
            return None
        
        interval_map = {
            '1m': Interval.MINUTE,
            '5m': Interval.MINUTE,  # vnpy 不支持 5m，使用 1m 然后聚合
            '15m': Interval.MINUTE,  # vnpy 不支持 15m，使用 1m 然后聚合
            '30m': Interval.MINUTE,  # vnpy 不支持 30m，使用 1m 然后聚合
            '1h': Interval.HOUR,
            '1d': Interval.DAILY,
        }
        return interval_map.get(interval_str)
    
    def _query_kline_from_ctp(self, symbol: str, interval: str,
                             start_dt: datetime, end_dt: datetime) -> List[KlineData]:
        """
        从CTP查询K线数据
        
        Args:
            symbol: 合约代码
            interval: K线周期
            start_dt: 开始时间
            end_dt: 结束时间
        
        Returns:
            K线数据列表
        """
        if not VNPY_CTP_AVAILABLE:
            logger.warning("vnpy-ctp未安装，无法查询历史数据")
            return []
        
        # 连接到CTP（如果需要）
        if not self._connect_ctp():
            logger.warning("CTP连接失败，无法查询历史数据")
            return []
        
        try:
            # 获取交易所和周期枚举
            exchange_str = self._get_exchange_from_symbol(symbol)
            exchange_enum = self._get_exchange_enum(exchange_str)
            interval_enum = self._get_interval_enum(interval)
            
            if not exchange_enum:
                logger.error(f"不支持的交易所: {exchange_str}")
                return []
            
            if not interval_enum:
                logger.error(f"不支持的K线周期: {interval}")
                return []
            
            # 对于非1分钟周期，需要先查询1分钟数据然后聚合
            # vnpy 只支持 MINUTE, HOUR, DAILY 等基本周期
            query_interval = interval
            need_aggregate = interval not in ['1m', '1h', '1d']
            
            if need_aggregate:
                logger.info(f"周期 {interval} 需要从1分钟数据聚合，先查询1分钟数据")
                query_interval = '1m'
                interval_enum = Interval.MINUTE
            
            # 创建历史数据查询请求
            history_req = HistoryRequest(
                symbol=symbol,
                exchange=exchange_enum,
                start=start_dt,
                end=end_dt,
                interval=interval_enum
            )
            
            # 查询历史数据
            logger.info(f"正在查询历史K线数据: {symbol}, {query_interval}, {start_dt} ~ {end_dt}")
            
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H","location":"ctp_history.py:_query_kline_from_ctp","message":"Calling query_history","data":{"symbol":symbol,"exchange":str(exchange_enum),"interval":str(interval_enum),"start":start_dt.isoformat(),"end":end_dt.isoformat()},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 注意：vnpy-ctp 的 query_history 方法可能未实现或返回空
            # CTP API 本身不直接支持历史数据查询
            # 历史数据通常需要：
            # 1. 从数据库获取（推荐，使用 from_db=True）
            # 2. 从实时数据积累
            # 3. 从第三方数据源获取
            
            try:
                bar_data_list = self._ctp_gateway.query_history(history_req)
            except Exception as e:
                logger.warning(f"query_history 调用失败: {e}")
                logger.info("提示：CTP API 通常不支持直接查询历史数据，建议使用 from_db=True 从数据库获取")
                bar_data_list = None
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H","location":"ctp_history.py:_query_kline_from_ctp","message":"query_history returned","data":{"result_type":type(bar_data_list).__name__ if bar_data_list else "None","result_length":len(bar_data_list) if bar_data_list else 0,"result_is_none":bar_data_list is None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            if not bar_data_list:
                logger.warning("未查询到历史数据")
                logger.info("提示：")
                logger.info("1. CTP API 通常不支持直接查询历史数据")
                logger.info("2. 建议使用 from_db=True 从数据库获取历史数据")
                logger.info("3. 或者使用实时行情接口积累数据到数据库")
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"ctp_history.py:_query_kline_from_ctp","message":"No data returned from query_history","data":{"symbol":symbol,"start":start_dt.isoformat(),"end":end_dt.isoformat(),"note":"CTP API may not support direct history query"},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return []
            
            # 转换vnpy BarData为KlineData
            klines = []
            for bar_data in bar_data_list:
                kline = self._convert_vnpy_bar_data(bar_data, query_interval)
                if kline:
                    klines.append(kline)
            
            # 如果需要聚合，将1分钟数据聚合为指定周期
            if need_aggregate and klines:
                logger.info(f"将 {len(klines)} 条1分钟数据聚合为 {interval} 周期")
                klines = self._aggregate_klines(klines, interval)
                logger.info(f"聚合后得到 {len(klines)} 条 {interval} 周期数据")
            
            logger.info(f"查询到 {len(klines)} 条历史K线数据")
            return klines
            
        except Exception as e:
            logger.error(f"查询历史K线数据失败: {e}", exc_info=True)
            return []
    
    def _get_exchange_from_symbol(self, symbol: str) -> str:
        """从合约代码获取交易所代码（字符串）"""
        # 根据合约代码前缀判断交易所
        if symbol.startswith('rb') or symbol.startswith('cu') or symbol.startswith('au') or symbol.startswith('ag'):
            return 'SHFE'  # 上海期货交易所
        elif symbol.startswith('i') or symbol.startswith('j') or symbol.startswith('jm') or symbol.startswith('c'):
            return 'DCE'  # 大连商品交易所
        elif symbol.startswith('CF') or symbol.startswith('SR') or symbol.startswith('MA') or symbol.startswith('ZC'):
            return 'CZCE'  # 郑州商品交易所
        elif symbol.startswith('IF') or symbol.startswith('IC') or symbol.startswith('IH') or symbol.startswith('IM'):
            return 'CFFEX'  # 中国金融期货交易所
        elif symbol.startswith('sc') or symbol.startswith('lu') or symbol.startswith('bc'):
            return 'INE'  # 上海国际能源交易中心
        else:
            return 'SHFE'  # 默认
    
    def _aggregate_klines(self, klines: List[KlineData], target_interval: str) -> List[KlineData]:
        """
        将1分钟K线数据聚合为指定周期
        
        Args:
            klines: 1分钟K线数据列表（必须已按时间排序）
            target_interval: 目标周期（5m, 15m, 30m等）
        
        Returns:
            聚合后的K线数据列表
        """
        if not klines:
            return []
        
        # 解析目标周期（分钟数）
        try:
            minutes = int(target_interval.replace('m', ''))
        except:
            logger.error(f"无法解析周期: {target_interval}")
            return klines
        
        if minutes <= 1:
            return klines
        
        aggregated = []
        current_group = []
        
        for kline in klines:
            if not current_group:
                # 开始新的一组
                current_group = [kline]
            else:
                # 计算时间差（分钟）
                time_diff = (kline.datetime - current_group[0].datetime).total_seconds() / 60
                
                if time_diff < minutes:
                    # 仍在同一组内
                    current_group.append(kline)
                else:
                    # 完成当前组，开始新组
                    if current_group:
                        aggregated_kline = self._merge_klines(current_group, target_interval)
                        if aggregated_kline:
                            aggregated.append(aggregated_kline)
                    current_group = [kline]
        
        # 处理最后一组
        if current_group:
            aggregated_kline = self._merge_klines(current_group, target_interval)
            if aggregated_kline:
                aggregated.append(aggregated_kline)
        
        return aggregated
    
    def _merge_klines(self, klines: List[KlineData], interval: str) -> Optional[KlineData]:
        """
        合并一组K线数据为一条K线
        
        Args:
            klines: 同一周期内的K线数据列表
            interval: 目标周期
        
        Returns:
            合并后的K线数据
        """
        if not klines:
            return None
        
        # 使用第一条的开盘价，最后一条的收盘价
        open_price = klines[0].open
        close_price = klines[-1].close
        
        # 最高价和最低价
        high_price = max(k.high for k in klines)
        low_price = min(k.low for k in klines)
        
        # 成交量和成交额求和
        volume = sum(k.volume for k in klines)
        turnover = sum(k.turnover for k in klines)
        
        # 持仓量使用最后一条
        open_interest = klines[-1].open_interest if klines else 0
        
        # 使用第一条的时间作为K线时间
        dt = klines[0].datetime
        
        return self.data_handler.create_kline(
            symbol=klines[0].symbol,
            dt=dt,
            interval=interval,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            open_interest=open_interest,
            turnover=turnover
        )
    
    def _convert_vnpy_bar_data(self, bar_data, interval: str) -> Optional[KlineData]:
        """
        转换vnpy BarData为KlineData
        
        Args:
            bar_data: vnpy BarData对象
            interval: K线周期
        
        Returns:
            KlineData对象
        """
        try:
            symbol = bar_data.symbol.split('.')[0] if '.' in bar_data.symbol else bar_data.symbol
            dt = bar_data.datetime if hasattr(bar_data, 'datetime') else datetime.now()
            
            kline = self.data_handler.create_kline(
                symbol=symbol,
                dt=dt,
                interval=interval,
                open_price=float(bar_data.open_price) if hasattr(bar_data, 'open_price') else 0.0,
                high_price=float(bar_data.high_price) if hasattr(bar_data, 'high_price') else 0.0,
                low_price=float(bar_data.low_price) if hasattr(bar_data, 'low_price') else 0.0,
                close_price=float(bar_data.close_price) if hasattr(bar_data, 'close_price') else 0.0,
                volume=int(bar_data.volume) if hasattr(bar_data, 'volume') else 0,
                open_interest=int(bar_data.open_interest) if hasattr(bar_data, 'open_interest') else 0,
                turnover=float(bar_data.turnover) if hasattr(bar_data, 'turnover') else 0.0
            )
            
            return kline
            
        except Exception as e:
            logger.error(f"转换Bar数据失败: {e}")
            return None
    
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

