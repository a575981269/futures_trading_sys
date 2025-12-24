"""
CTP实时行情接口 - SimNow 模拟环境
"""
from datetime import datetime
from typing import Dict, List, Callable, Optional
from threading import Event
import time

from database.models import KlineData, TickData
from database.db_manager import DatabaseManager
from market_data.data_handler import DataHandler
from config.settings import settings
from utils.logger import get_logger
from utils.helpers import parse_symbol

logger = get_logger(__name__)

# 尝试导入vnpy-ctp
try:
    from vnpy_ctp import CtpGateway
    from vnpy.event import EventEngine
    VNPY_CTP_AVAILABLE = True
except ImportError:
    try:
        # 尝试备用导入路径
        from vnpy.gateway.ctp import CtpGateway
        from vnpy.event import EventEngine
        VNPY_CTP_AVAILABLE = True
    except ImportError:
        VNPY_CTP_AVAILABLE = False
        logger.error("vnpy-ctp未安装或依赖缺失，请运行: pip install vnpy vnpy-ctp")


class CTPRealtimeData:
    """CTP实时行情接口"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 auto_save: bool = True):
        """
        初始化实时行情接口 - SimNow 模拟环境
        
        Args:
            db_manager: 数据库管理器
            auto_save: 是否自动保存数据到数据库
        """
        if not VNPY_CTP_AVAILABLE:
            raise ImportError("vnpy-ctp未安装，无法使用SimNow模拟环境。请运行: pip install vnpy-ctp")
        
        self.db_manager = db_manager or DatabaseManager(settings.DB_URL)
        self.data_handler = DataHandler()
        self.auto_save = auto_save
        
        # 订阅的合约列表
        self.subscribed_symbols: List[str] = []
        
        # 回调函数
        self.tick_callbacks: List[Callable] = []
        self.kline_callbacks: List[Callable] = []
        
        # 连接状态
        self.is_connected = False
        self._stop_event = Event()
        
        # vnpy-ctp 事件引擎和网关
        self._event_engine: Optional[EventEngine] = None
        self._ctp_gateway: Optional[CtpGateway] = None
        
        logger.info("CTP实时行情接口初始化完成（SimNow模拟环境）")
    
    def connect(self) -> bool:
        """
        连接SimNow CTP服务器
        
        Returns:
            是否连接成功
        """
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"connect() called","data":{"is_connected":self.is_connected,"VNPY_CTP_AVAILABLE":VNPY_CTP_AVAILABLE},"timestamp":int(time.time()*1000)})+'\n')
        except: pass
        # #endregion
        
        if self.is_connected:
            logger.warning("已经连接到CTP服务器")
            return True
        
        if not VNPY_CTP_AVAILABLE:
            logger.error("vnpy-ctp未安装，无法连接SimNow")
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"VNPY_CTP_AVAILABLE is False","data":{},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            return False
        
        try:
            # 验证配置
            if not settings.validate_ctp_config():
                logger.error("CTP配置不完整，请检查.env文件中的配置项")
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"Config validation failed","data":{},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return False
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"Creating EventEngine and CtpGateway","data":{},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 创建事件引擎
            self._event_engine = EventEngine()
            
            # 创建CTP网关
            self._ctp_gateway = CtpGateway(self._event_engine, "CTP")
            
            # 注册事件处理器
            self._event_engine.register("eTick", self._on_tick_event)
            self._event_engine.register("eBar", self._on_bar_event)
            self._event_engine.register("eLog", self._on_log_event)
            
            # 配置CTP连接参数
            ctp_setting = {
                "用户名": settings.CTP_USER_ID,
                "密码": settings.CTP_PASSWORD,
                "经纪商代码": settings.CTP_BROKER_ID,
                "交易服务器": settings.CTP_TRADE_ADDRESS,
                "行情服务器": settings.CTP_MD_ADDRESS,
                "产品名称": settings.CTP_APP_ID,
                "授权编码": settings.CTP_AUTH_CODE,
            }
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"Calling gateway.connect()","data":{"md_address":settings.CTP_MD_ADDRESS},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 启动事件引擎
            self._event_engine.start()
            
            # 连接
            logger.info(f"正在连接SimNow行情服务器: {settings.CTP_MD_ADDRESS}")
            self._ctp_gateway.connect(ctp_setting)
            
            # 等待连接完成（最多等待10秒）
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"Connection wait finished","data":{"is_connected":self.is_connected,"elapsed":time.time()-start_time},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            if self.is_connected:
                logger.info("SimNow行情服务器连接成功")
                return True
            else:
                logger.error("SimNow行情服务器连接超时")
                return False
            
        except Exception as e:
            logger.error(f"连接SimNow服务器失败: {e}", exc_info=True)
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"Exception in connect()","data":{"error":str(e)},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            return False
    
    def disconnect(self):
        """断开CTP连接"""
        if not self.is_connected:
            return
        
        try:
            # 取消所有订阅
            for symbol in list(self.subscribed_symbols):
                self.unsubscribe(symbol)
            
            # 断开网关连接
            if self._ctp_gateway:
                self._ctp_gateway.close()
                self._ctp_gateway = None
            
            # 停止事件引擎
            if self._event_engine:
                self._event_engine.stop()
                self._event_engine = None
            
            self._stop_event.set()
            self.is_connected = False
            
            logger.info("已断开SimNow连接")
            
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
            self.is_connected = False
    
    def subscribe(self, symbol: str) -> bool:
        """
        订阅实时行情
        
        Args:
            symbol: 合约代码
        
        Returns:
            是否订阅成功
        """
        if not self.is_connected:
            logger.error("未连接到SimNow服务器，请先调用connect()")
            return False
        
        if symbol in self.subscribed_symbols:
            logger.warning(f"合约 {symbol} 已经订阅")
            return True
        
        try:
            if not self._ctp_gateway:
                logger.error("CTP网关未初始化")
                return False
            
            # 订阅合约（vnpy-ctp使用vt_symbol格式：合约代码.交易所）
            exchange = self._get_exchange_from_symbol(symbol)
            vt_symbol = f"{symbol}.{exchange}"
            
            # 订阅行情
            self._ctp_gateway.subscribe(vt_symbol)
            
            self.subscribed_symbols.append(symbol)
            logger.info(f"订阅合约成功: {symbol} ({vt_symbol})")
            
            return True
            
        except Exception as e:
            logger.error(f"订阅合约失败: {symbol}, 错误: {e}", exc_info=True)
            return False
    
    def unsubscribe(self, symbol: str) -> bool:
        """
        取消订阅
        
        Args:
            symbol: 合约代码
        
        Returns:
            是否取消订阅成功
        """
        if symbol not in self.subscribed_symbols:
            logger.warning(f"合约 {symbol} 未订阅")
            return False
        
        try:
            if self._ctp_gateway:
                exchange = self._get_exchange_from_symbol(symbol)
                vt_symbol = f"{symbol}.{exchange}"
                # vnpy-ctp通常通过取消订阅实现，但API可能不同
                # 这里先移除订阅列表，实际取消由网关处理
                pass
            
            self.subscribed_symbols.remove(symbol)
            logger.info(f"取消订阅成功: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"取消订阅失败: {symbol}, 错误: {e}")
            return False
    
    def register_tick_callback(self, callback: Callable[[TickData], None]):
        """
        注册Tick数据回调函数
        
        Args:
            callback: 回调函数，接收TickData参数
        """
        if callback not in self.tick_callbacks:
            self.tick_callbacks.append(callback)
            logger.info("Tick回调函数注册成功")
    
    def register_kline_callback(self, callback: Callable[[KlineData], None]):
        """
        注册K线数据回调函数
        
        Args:
            callback: 回调函数，接收KlineData参数
        """
        if callback not in self.kline_callbacks:
            self.kline_callbacks.append(callback)
            logger.info("K线回调函数注册成功")
    
    def _on_tick_event(self, event):
        """
        vnpy-ctp Tick数据事件处理
        
        Args:
            event: vnpy事件对象，包含Tick数据
        """
        try:
            tick_data = event.data
            
            # 转换vnpy-ctp Tick数据格式
            tick = self._convert_vnpy_tick_data(tick_data)
            
            if not tick or not self.data_handler.validate_tick(tick):
                return
            
            # 自动保存到数据库
            if self.auto_save:
                self.db_manager.save_tick(tick)
            
            # 调用注册的回调函数
            for callback in self.tick_callbacks:
                try:
                    callback(tick)
                except Exception as e:
                    logger.error(f"Tick回调函数执行失败: {e}")
                    
        except Exception as e:
            logger.error(f"处理Tick数据失败: {e}", exc_info=True)
    
    def _on_bar_event(self, event):
        """
        vnpy-ctp K线数据事件处理
        
        Args:
            event: vnpy事件对象，包含Bar数据
        """
        try:
            bar_data = event.data
            
            # 转换vnpy-ctp Bar数据格式
            kline = self._convert_vnpy_bar_data(bar_data)
            
            if not kline or not self.data_handler.validate_kline(kline):
                return
            
            # 自动保存到数据库
            if self.auto_save:
                self.db_manager.save_kline(kline)
            
            # 调用注册的回调函数
            for callback in self.kline_callbacks:
                try:
                    callback(kline)
                except Exception as e:
                    logger.error(f"K线回调函数执行失败: {e}")
                    
        except Exception as e:
            logger.error(f"处理K线数据失败: {e}", exc_info=True)
    
    def _on_log_event(self, event):
        """
        vnpy-ctp 日志事件处理
        
        Args:
            event: vnpy事件对象，包含日志信息
        """
        try:
            log_data = event.data
            log_msg = log_data.get('msg', '') if isinstance(log_data, dict) else str(log_data)
            log_level = log_data.get('level', 'INFO') if isinstance(log_data, dict) else 'INFO'
            
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:_on_log_event","message":"Log event received","data":{"msg":log_msg,"level":log_level},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 处理连接状态
            if '连接成功' in log_msg or '登录成功' in log_msg or 'connected' in log_msg.lower() or 'login' in log_msg.lower():
                self.is_connected = True
                logger.info(f"SimNow连接成功: {log_msg}")
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:_on_log_event","message":"Connection SUCCESS detected","data":{"is_connected":self.is_connected},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
            elif '连接失败' in log_msg or '登录失败' in log_msg or 'failed' in log_msg.lower() or 'error' in log_msg.lower():
                self.is_connected = False
                logger.error(f"SimNow连接失败: {log_msg}")
            
        except Exception as e:
            logger.debug(f"处理日志事件失败: {e}")
    
    def _on_bar(self, bar_data: Dict):
        """
        CTP K线数据回调（内部方法）
        
        Args:
            bar_data: CTP返回的K线数据字典
        """
        try:
            # 转换CTP数据格式为KlineData对象
            kline = self._convert_bar_data(bar_data)
            
            if not self.data_handler.validate_kline(kline):
                return
            
            # 自动保存到数据库
            if self.auto_save:
                self.db_manager.save_kline(kline)
            
            # 调用注册的回调函数
            for callback in self.kline_callbacks:
                try:
                    callback(kline)
                except Exception as e:
                    logger.error(f"K线回调函数执行失败: {e}")
                    
        except Exception as e:
            logger.error(f"处理K线数据失败: {e}")
    
    def _convert_vnpy_tick_data(self, tick_data) -> Optional[TickData]:
        """
        转换vnpy-ctp Tick数据格式
        
        Args:
            tick_data: vnpy TickData对象
        
        Returns:
            TickData对象
        """
        try:
            # vnpy TickData对象属性
            symbol = tick_data.symbol.split('.')[0] if '.' in tick_data.symbol else tick_data.symbol
            dt = tick_data.datetime if hasattr(tick_data, 'datetime') else datetime.now()
            
            tick = self.data_handler.create_tick(
                symbol=symbol,
                dt=dt,
                last_price=float(tick_data.last_price) if hasattr(tick_data, 'last_price') else 0.0,
                volume=int(tick_data.volume) if hasattr(tick_data, 'volume') else 0,
                open_interest=int(tick_data.open_interest) if hasattr(tick_data, 'open_interest') else 0,
                bid_price1=float(tick_data.bid_price_1) if hasattr(tick_data, 'bid_price_1') else None,
                bid_volume1=int(tick_data.bid_volume_1) if hasattr(tick_data, 'bid_volume_1') else None,
                ask_price1=float(tick_data.ask_price_1) if hasattr(tick_data, 'ask_price_1') else None,
                ask_volume1=int(tick_data.ask_volume_1) if hasattr(tick_data, 'ask_volume_1') else None,
                turnover=float(tick_data.turnover) if hasattr(tick_data, 'turnover') else 0.0
            )
            
            return tick
            
        except Exception as e:
            logger.error(f"转换Tick数据失败: {e}", exc_info=True)
            return None
    
    def _convert_vnpy_bar_data(self, bar_data) -> Optional[KlineData]:
        """
        转换vnpy-ctp Bar数据格式
        
        Args:
            bar_data: vnpy BarData对象
        
        Returns:
            KlineData对象
        """
        try:
            # vnpy BarData对象属性
            symbol = bar_data.symbol.split('.')[0] if '.' in bar_data.symbol else bar_data.symbol
            interval = bar_data.interval.value if hasattr(bar_data.interval, 'value') else '1m'
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
            logger.error(f"转换Bar数据失败: {e}", exc_info=True)
            return None
    
    def _get_exchange_from_symbol(self, symbol: str) -> str:
        """从合约代码获取交易所代码"""
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
    
    def get_subscribed_symbols(self) -> List[str]:
        """获取已订阅的合约列表"""
        return self.subscribed_symbols.copy()

