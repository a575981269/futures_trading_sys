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
from utils.helpers import parse_symbol, is_trading_time, get_next_trading_time

logger = get_logger(__name__)

# 尝试导入vnpy-ctp
try:
    from vnpy_ctp import CtpGateway
    from vnpy.event import EventEngine
    from vnpy.trader.event import EVENT_LOG, EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, EVENT_POSITION
    from vnpy.trader.object import SubscribeRequest
    from vnpy.trader.constant import Exchange
    VNPY_CTP_AVAILABLE = True
except ImportError:
    try:
        # 尝试备用导入路径
        from vnpy.gateway.ctp import CtpGateway
        from vnpy.event import EventEngine
        from vnpy.trader.event import EVENT_LOG, EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, EVENT_POSITION
        from vnpy.trader.object import SubscribeRequest
        from vnpy.trader.constant import Exchange
        VNPY_CTP_AVAILABLE = True
    except ImportError:
        VNPY_CTP_AVAILABLE = False
        EVENT_LOG = "eLog"
        EVENT_TICK = "eTick"
        EVENT_ORDER = "eOrder"
        EVENT_TRADE = "eTrade"
        EVENT_ACCOUNT = "eAccount"
        EVENT_POSITION = "ePosition"
        SubscribeRequest = None
        Exchange = None
        logger.error("vnpy-ctp未安装或依赖缺失，请运行: pip install vnpy vnpy-ctp")


class CTPRealtimeData:
    """CTP实时行情接口"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 auto_save: bool = True,
                 environment: Optional[str] = None):
        """
        初始化实时行情接口 - SimNow 模拟环境
        
        Args:
            db_manager: 数据库管理器
            auto_save: 是否自动保存数据到数据库
            environment: 环境类型（"normal" 或 "7x24"），如果为None则使用配置中的环境类型
        """
        if not VNPY_CTP_AVAILABLE:
            raise ImportError("vnpy-ctp未安装，无法使用SimNow模拟环境。请运行: pip install vnpy-ctp")
        
        self.db_manager = db_manager or DatabaseManager(settings.DB_URL)
        self.data_handler = DataHandler()
        self.auto_save = auto_save
        self.environment = environment or settings.CTP_ENVIRONMENT
        
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
        
        env_name = "7x24环境" if settings.is_7x24_environment(self.environment) else "CTP主席系统"
        logger.info(f"CTP实时行情接口初始化完成（SimNow模拟环境 - {env_name}）")
    
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
            # 检查交易时间（仅CTP主席系统需要检查，7x24环境全天候开放）
            is_7x24 = settings.is_7x24_environment(self.environment)
            if not is_7x24 and not is_trading_time():
                next_time = get_next_trading_time()
                logger.warning(f"当前不在交易时间内，CTP主席系统不开放")
                logger.info(f"下一个交易时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("提示：如需在非交易时间测试，请使用7x24环境（端口40001/40011）")
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"ctp_realtime.py:connect","message":"Not in trading time","data":{"current_time":datetime.now().strftime('%H:%M:%S'),"next_trading_time":next_time.strftime('%Y-%m-%d %H:%M:%S')},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return False
            
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
            
            # 根据环境类型获取服务器地址
            addresses = settings.get_server_addresses(self.environment)
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"ctp_realtime.py:connect","message":"Addresses retrieved","data":{"environment":self.environment,"md_address":addresses['md_address'],"trade_address":addresses['trade_address']},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"Creating EventEngine and CtpGateway","data":{"environment":self.environment,"is_7x24":is_7x24},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 创建事件引擎
            self._event_engine = EventEngine()
            
            # 创建CTP网关
            self._ctp_gateway = CtpGateway(self._event_engine, "CTP")
            
            # 注册事件处理器（使用正确的事件名称）
            # EVENT_TICK 确认是 'eTick.'（带点）
            # vnpy的事件名称格式可能是 "gateway_name.event_name"，尝试两种格式
            gateway_name = "CTP"
            possible_tick_events = [
                EVENT_TICK,  # 'eTick.'
                f"{gateway_name}.{EVENT_TICK}",  # 'CTP.eTick.'
                "eTick",  # 不带点
                f"{gateway_name}.eTick",  # 'CTP.eTick'
            ]
            
            # 添加通用事件监听器用于调试（捕获所有事件）
            def _debug_all_events(event):
                # #region agent log
                try:
                    event_type = type(event).__name__
                    has_data = hasattr(event, 'data')
                    data_type = type(event.data).__name__ if has_data else None
                    # 尝试获取事件类型字符串
                    event_type_str = str(getattr(event, 'type', None) or getattr(event, '__class__', None) or event_type)
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALL_EVENTS","location":"ctp_realtime.py:connect","message":"All events listener triggered","data":{"event_type":event_type_str[:100],"has_data":has_data,"data_type":data_type},"timestamp":int(time.time()*1000)})+'\n')
                except Exception as e:
                    try:
                        with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALL_EVENTS","location":"ctp_realtime.py:connect","message":"All events listener error","data":{"error":str(e)[:100]},"timestamp":int(time.time()*1000)})+'\n')
                    except: pass
                # #endregion
            
            tick_registered = False
            for tick_event in possible_tick_events:
                try:
                    self._event_engine.register(tick_event, self._on_tick_event)
                    tick_registered = True
                    # #region agent log
                    try:
                        with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ctp_realtime.py:connect","message":"Tick event registered successfully","data":{"event_name":tick_event,"EVENT_TICK":EVENT_TICK},"timestamp":int(time.time()*1000)})+'\n')
                    except: pass
                    # #endregion
                    break
                except Exception as reg_error:
                    # #region agent log
                    try:
                        with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ctp_realtime.py:connect","message":"Tick event registration attempt failed","data":{"event_name":tick_event,"error":str(reg_error)[:100]},"timestamp":int(time.time()*1000)})+'\n')
                    except: pass
                    # #endregion
                    continue
            
            if not tick_registered:
                # 如果都失败，至少注册默认的
                self._event_engine.register(EVENT_TICK, self._on_tick_event)
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ctp_realtime.py:connect","message":"Using default EVENT_TICK registration","data":{"EVENT_TICK":EVENT_TICK},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
            
            self._event_engine.register(EVENT_LOG, self._on_log_event)
            
            # 尝试注册所有可能的事件类型用于调试
            all_possible_events = [EVENT_TICK, EVENT_LOG, "eTick", "eTick.", "CTP.eTick", "CTP.eTick.", "tick", "Tick"]
            for evt in all_possible_events:
                try:
                    self._event_engine.register(evt, _debug_all_events)
                except:
                    pass
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ctp_realtime.py:connect","message":"Events registered","data":{"EVENT_TICK":EVENT_TICK,"EVENT_LOG":EVENT_LOG,"tick_registered":tick_registered},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
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
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"ctp_realtime.py:connect","message":"CTP setting prepared","data":{"行情服务器":ctp_setting["行情服务器"],"交易服务器":ctp_setting["交易服务器"],"addresses_md":addresses['md_address'],"addresses_trade":addresses['trade_address']},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 启动事件引擎
            self._event_engine.start()
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"EventEngine started, calling gateway.connect()","data":{"ctp_setting_keys":list(ctp_setting.keys())},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 连接
            env_name = "7x24环境" if is_7x24 else "CTP主席系统"
            logger.info(f"正在连接SimNow行情服务器（{env_name}）: {addresses['md_address']}")
            try:
                self._ctp_gateway.connect(ctp_setting)
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"gateway.connect() called successfully","data":{},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
            except Exception as connect_error:
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"gateway.connect() raised exception","data":{"error":str(connect_error)},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                raise
            
            # 等待连接完成（最多等待10秒）
            timeout = 10
            start_time = time.time()
            check_count = 0
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                check_count += 1
                # 每1秒记录一次状态
                if check_count % 10 == 0:
                    # #region agent log
                    try:
                        with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:connect","message":"Waiting for connection","data":{"is_connected":self.is_connected,"elapsed":time.time()-start_time,"check_count":check_count},"timestamp":int(time.time()*1000)})+'\n')
                    except: pass
                    # #endregion
            
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
            
            # 获取交易所代码（字符串）
            exchange_str = self._get_exchange_from_symbol(symbol)
            
            # 将字符串转换为Exchange枚举
            exchange_enum = self._get_exchange_enum(exchange_str)
            if not exchange_enum:
                logger.error(f"不支持的交易所: {exchange_str}")
                return False
            
            # 创建订阅请求对象
            # 注意：vnpy-ctp的SubscribeRequest可能需要小写合约代码
            symbol_normalized = symbol.upper()  # 确保大写
            subscribe_req = SubscribeRequest(symbol_normalized, exchange_enum)
            
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"ctp_realtime.py:subscribe","message":"Creating SubscribeRequest","data":{"symbol":symbol,"symbol_normalized":symbol_normalized,"exchange_str":exchange_str,"exchange_enum":str(exchange_enum),"vt_symbol":subscribe_req.vt_symbol},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 尝试先查询合约信息（如果需要）
            try:
                # vnpy-ctp可能需要先查询合约信息
                from vnpy.trader.object import ContractData
                from vnpy.trader.constant import Product
                # 尝试查询合约
                contract_req = ContractData(
                    symbol=symbol_normalized,
                    exchange=exchange_enum,
                    name="",
                    product=Product.FUTURES,
                )
                # 注意：vnpy-ctp的gateway可能没有直接的query_contract方法
                # 但订阅时会自动查询合约信息
            except Exception as contract_error:
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"ctp_realtime.py:subscribe","message":"Contract query attempt","data":{"error":str(contract_error)[:100]},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                pass
            
            # 订阅行情
            self._ctp_gateway.subscribe(subscribe_req)
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"ctp_realtime.py:subscribe","message":"Subscribe called on gateway","data":{"vt_symbol":subscribe_req.vt_symbol,"gateway_type":type(self._ctp_gateway).__name__},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"ctp_realtime.py:subscribe","message":"Subscribe called","data":{"symbol":symbol,"vt_symbol":subscribe_req.vt_symbol,"gateway_exists":self._ctp_gateway is not None,"event_engine_running":self._event_engine is not None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            self.subscribed_symbols.append(symbol)
            logger.info(f"订阅合约成功: {symbol} ({subscribe_req.vt_symbol})")
            
            # 检查交易时间
            from utils.helpers import is_trading_time
            current_time = datetime.now()
            is_trading = is_trading_time(current_time)
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"ctp_realtime.py:subscribe","message":"Trading time check","data":{"symbol":symbol,"current_time":current_time.strftime("%Y-%m-%d %H:%M:%S"),"is_trading_time":is_trading,"environment":self.environment},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 等待一小段时间，看是否有Tick数据到达
            import time as time_module
            time_module.sleep(2.0)  # 增加等待时间到2秒
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"ctp_realtime.py:subscribe","message":"After subscribe wait","data":{"symbol":symbol,"subscribed_count":len(self.subscribed_symbols),"tick_callbacks":len(self.tick_callbacks)},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 如果不在交易时间且不是7x24环境，给出提示
            if not is_trading and not settings.is_7x24_environment(self.environment):
                logger.warning(f"当前不在交易时间内，可能无法收到实时行情数据。当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("提示：如需在非交易时间测试，请使用7x24环境（端口40001/40011）")
            
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
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"TICK","location":"ctp_realtime.py:_on_tick_event","message":"Tick event received","data":{"has_data":hasattr(event,'data'),"event_type":type(event).__name__},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            tick_data = event.data
            
            # #region agent log
            try:
                symbol = tick_data.symbol if hasattr(tick_data, 'symbol') else "UNKNOWN"
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"TICK","location":"ctp_realtime.py:_on_tick_event","message":"Tick data extracted","data":{"symbol":symbol,"tick_type":type(tick_data).__name__},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 转换vnpy-ctp Tick数据格式
            tick = self._convert_vnpy_tick_data(tick_data)
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"TICK","location":"ctp_realtime.py:_on_tick_event","message":"Tick converted","data":{"tick_exists":tick is not None,"tick_symbol":tick.symbol if tick else None,"callback_count":len(self.tick_callbacks)},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            if not tick or not self.data_handler.validate_tick(tick):
                return
            
            # 自动保存到数据库
            if self.auto_save:
                # 保存前创建对象的副本，避免会话绑定问题
                # 提取所有属性值，创建新的未绑定对象
                tick_for_callback = TickData(
                    symbol=tick.symbol,
                    exchange=tick.exchange,
                    datetime=tick.datetime,
                    last_price=tick.last_price,
                    volume=tick.volume,
                    open_interest=tick.open_interest,
                    bid_price1=tick.bid_price1,
                    bid_volume1=tick.bid_volume1,
                    ask_price1=tick.ask_price1,
                    ask_volume1=tick.ask_volume1,
                    turnover=tick.turnover
                )
                
                # 保存原始对象
                self.db_manager.save_tick(tick)
                
                # 使用未绑定的副本调用回调
                tick = tick_for_callback
            else:
                # 如果不保存，直接使用原始对象
                pass
            
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
        vnpy-ctp K线数据事件处理（从Tick数据生成）
        
        注意：vnpy-ctp 通常不直接提供 Bar 事件，需要从 Tick 数据聚合生成
        """
        # 此方法保留用于未来扩展，当前从 Tick 数据生成 K 线
        pass
    
    def _on_log_event(self, event):
        """
        vnpy-ctp 日志事件处理
        
        Args:
            event: vnpy事件对象，包含日志信息
        """
        try:
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"ctp_realtime.py:_on_log_event","message":"Log event RECEIVED","data":{"event_type":type(event).__name__,"has_data":hasattr(event,'data')},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # vnpy 事件对象通常有 data 属性
            if hasattr(event, 'data'):
                log_data = event.data
                # log_data 可能是字符串或对象
                if isinstance(log_data, str):
                    log_msg = log_data
                    log_level = 'INFO'
                elif isinstance(log_data, dict):
                    log_msg = log_data.get('msg', '') or log_data.get('content', '') or str(log_data)
                    log_level = log_data.get('level', 'INFO')
                else:
                    # 可能是对象，尝试获取属性
                    log_msg = getattr(log_data, 'msg', None) or getattr(log_data, 'content', None) or str(log_data)
                    log_level = getattr(log_data, 'level', 'INFO')
            else:
                log_msg = str(event)
                log_level = 'INFO'
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"ctp_realtime.py:_on_log_event","message":"Log event processed","data":{"msg":log_msg[:100] if log_msg else "","level":log_level},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 处理连接状态
            log_msg_lower = log_msg.lower() if log_msg else ''
            if any(keyword in log_msg for keyword in ['连接成功', '登录成功', 'connected', 'login success']) or any(keyword in log_msg_lower for keyword in ['connected', 'login success']):
                self.is_connected = True
                logger.info(f"SimNow连接成功: {log_msg}")
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"ctp_realtime.py:_on_log_event","message":"Connection SUCCESS detected","data":{"is_connected":self.is_connected},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
            elif any(keyword in log_msg for keyword in ['连接失败', '登录失败', 'failed', 'error']) or any(keyword in log_msg_lower for keyword in ['failed', 'error', 'timeout']):
                self.is_connected = False
                logger.error(f"SimNow连接失败: {log_msg}")
            
        except Exception as e:
            logger.debug(f"处理日志事件失败: {e}")
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"ctp_realtime.py:_on_log_event","message":"Exception in log event handler","data":{"error":str(e)},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
    
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
    
    def get_subscribed_symbols(self) -> List[str]:
        """获取已订阅的合约列表"""
        return self.subscribed_symbols.copy()

