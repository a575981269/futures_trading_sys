"""
CTP实时行情接口
"""
from datetime import datetime
from typing import Dict, List, Callable, Optional
from threading import Thread, Event
import time

from database.models import KlineData, TickData
from database.db_manager import DatabaseManager
from market_data.data_handler import DataHandler
from config.settings import settings
from utils.logger import get_logger
from utils.helpers import parse_symbol

logger = get_logger(__name__)


class CTPRealtimeData:
    """CTP实时行情接口"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 auto_save: bool = True):
        """
        初始化实时行情接口
        
        Args:
            db_manager: 数据库管理器
            auto_save: 是否自动保存数据到数据库
        """
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
        
        # CTP接口对象（需要根据实际使用的CTP库初始化）
        self._ctp_api = None
        
        # 模拟数据生成器（用于测试，当没有真实CTP连接时）
        self._simulate_data = True  # 是否启用模拟数据
        self._simulation_thread: Optional[Thread] = None
        
        logger.info("CTP实时行情接口初始化完成")
    
    def connect(self) -> bool:
        """
        连接CTP服务器
        
        Returns:
            是否连接成功
        """
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:51","message":"connect() called","data":{"is_connected":self.is_connected},"timestamp":int(__import__('time').time()*1000)})+'\n')
        except: pass
        # #endregion
        
        if self.is_connected:
            logger.warning("已经连接到CTP服务器")
            return True
        
        try:
            # TODO: 实现CTP连接
            # 示例：使用vnpy-ctp
            # from vnpy.gateway.ctp import CtpGateway
            # self._ctp_api = CtpGateway()
            # self._ctp_api.connect(settings.get_ctp_config())
            # self._ctp_api.register_callback(self._on_tick, self._on_bar)
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:70","message":"WARNING: CTP connection is simulated, not real","data":{"_ctp_api":str(self._ctp_api)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
            
            logger.warning("CTP连接功能待实现，请使用vnpy-ctp或其他CTP库")
            
            # 模拟连接成功
            self.is_connected = True
            
            # 如果启用模拟数据，启动模拟数据生成线程
            if self._simulate_data and self._ctp_api is None:
                logger.info("启用模拟数据生成器（用于测试）")
                self._start_simulation()
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_realtime.py:74","message":"Simulated connection success","data":{"is_connected":self.is_connected,"_ctp_api_is_none":self._ctp_api is None},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
            
            logger.info("CTP服务器连接成功")
            return True
            
        except Exception as e:
            logger.error(f"连接CTP服务器失败: {e}")
            return False
    
    def disconnect(self):
        """断开CTP连接"""
        if not self.is_connected:
            return
        
        # 停止模拟数据生成
        if self._simulate_data:
            self._stop_simulation()
        
        self._stop_event.set()
        self.is_connected = False
        
        # TODO: 断开CTP连接
        # if self._ctp_api:
        #     self._ctp_api.disconnect()
        
        logger.info("已断开CTP连接")
    
    def subscribe(self, symbol: str) -> bool:
        """
        订阅实时行情
        
        Args:
            symbol: 合约代码
        
        Returns:
            是否订阅成功
        """
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ctp_realtime.py:95","message":"subscribe() called","data":{"symbol":symbol,"is_connected":self.is_connected,"_ctp_api_is_none":self._ctp_api is None},"timestamp":int(__import__('time').time()*1000)})+'\n')
        except: pass
        # #endregion
        
        if not self.is_connected:
            logger.error("未连接到CTP服务器，请先调用connect()")
            return False
        
        if symbol in self.subscribed_symbols:
            logger.warning(f"合约 {symbol} 已经订阅")
            return True
        
        try:
            # TODO: 实现CTP订阅
            # self._ctp_api.subscribe(symbol)
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ctp_realtime.py:114","message":"WARNING: CTP subscribe is simulated, not calling real API","data":{"symbol":symbol,"_ctp_api_is_none":self._ctp_api is None},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
            
            self.subscribed_symbols.append(symbol)
            logger.info(f"订阅合约成功: {symbol}")
            
            # 如果启用模拟数据且没有真实CTP连接，启动模拟数据生成
            if self._simulate_data and self._ctp_api is None and self.is_connected:
                if not (self._simulation_thread and self._simulation_thread.is_alive()):
                    logger.info("启用模拟数据生成器（用于测试）")
                    self._start_simulation()
            
            return True
            
        except Exception as e:
            logger.error(f"订阅合约失败: {symbol}, 错误: {e}")
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
            # TODO: 实现CTP取消订阅
            # self._ctp_api.unsubscribe(symbol)
            
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
    
    def _on_tick(self, tick_data: Dict):
        """
        CTP Tick数据回调（内部方法）
        
        Args:
            tick_data: CTP返回的Tick数据字典
        """
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"ctp_realtime.py:231","message":"_on_tick() called - DATA RECEIVED","data":{"symbol":tick_data.get("symbol",tick_data.get("InstrumentID","unknown")),"price":tick_data.get("last_price",0)},"timestamp":int(__import__('time').time()*1000)})+'\n')
        except: pass
        # #endregion
        try:
            # 转换CTP数据格式为TickData对象
            tick = self._convert_tick_data(tick_data)
            
            if not self.data_handler.validate_tick(tick):
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
            logger.error(f"处理Tick数据失败: {e}")
    
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
    
    def _convert_tick_data(self, tick_dict: Dict) -> TickData:
        """
        转换CTP Tick数据格式
        
        Args:
            tick_dict: CTP返回的Tick数据字典
        
        Returns:
            TickData对象
        """
        symbol = tick_dict.get('symbol', '')
        dt = tick_dict.get('datetime', datetime.now())
        
        tick = self.data_handler.create_tick(
            symbol=symbol,
            dt=dt,
            last_price=tick_dict.get('last_price', 0.0),
            volume=tick_dict.get('volume', 0),
            open_interest=tick_dict.get('open_interest', 0),
            bid_price1=tick_dict.get('bid_price1'),
            bid_volume1=tick_dict.get('bid_volume1'),
            ask_price1=tick_dict.get('ask_price1'),
            ask_volume1=tick_dict.get('ask_volume1'),
            turnover=tick_dict.get('turnover', 0.0)
        )
        
        return tick
    
    def _convert_bar_data(self, bar_dict: Dict) -> KlineData:
        """
        转换CTP K线数据格式
        
        Args:
            bar_dict: CTP返回的K线数据字典
        
        Returns:
            KlineData对象
        """
        symbol = bar_dict.get('symbol', '')
        interval = bar_dict.get('interval', '1m')
        dt = bar_dict.get('datetime', datetime.now())
        
        kline = self.data_handler.create_kline(
            symbol=symbol,
            dt=dt,
            interval=interval,
            open_price=bar_dict.get('open', 0.0),
            high_price=bar_dict.get('high', 0.0),
            low_price=bar_dict.get('low', 0.0),
            close_price=bar_dict.get('close', 0.0),
            volume=bar_dict.get('volume', 0),
            open_interest=bar_dict.get('open_interest', 0),
            turnover=bar_dict.get('turnover', 0.0)
        )
        
        return kline
    
    def get_subscribed_symbols(self) -> List[str]:
        """获取已订阅的合约列表"""
        return self.subscribed_symbols.copy()
    
    def _start_simulation(self):
        """启动模拟数据生成线程"""
        if self._simulation_thread and self._simulation_thread.is_alive():
            return
        
        # 重置停止事件
        self._stop_event.clear()
        
        def simulate_market_data():
            """模拟市场数据生成"""
            import random
            import time as time_module
            
            # 为每个合约维护价格状态
            price_states = {}  # {symbol: current_price}
            
            while not self._stop_event.is_set() and self.is_connected:
                if not self.subscribed_symbols:
                    time_module.sleep(0.5)
                    continue
                
                for symbol in list(self.subscribed_symbols):  # 使用副本避免修改时出错
                    try:
                        # 初始化或更新价格状态
                        if symbol not in price_states:
                            # 根据合约代码确定基础价格
                            if symbol.startswith('rb'):  # 螺纹钢
                                base_price = 3500.0
                            elif symbol.startswith('cu'):  # 铜
                                base_price = 70000.0
                            elif symbol.startswith('au'):  # 黄金
                                base_price = 500.0
                            else:
                                base_price = 3500.0
                            price_states[symbol] = base_price
                        
                        # 价格随机波动
                        current_price = price_states[symbol]
                        price_change = random.uniform(-5, 5)
                        current_price = max(1.0, current_price + price_change)
                        price_states[symbol] = current_price
                        
                        # 生成模拟Tick数据
                        tick_data = {
                            'symbol': symbol,
                            'datetime': datetime.now(),
                            'last_price': round(current_price, 2),
                            'volume': random.randint(100, 1000),
                            'open_interest': random.randint(10000, 50000),
                            'bid_price1': round(current_price - 1, 2),
                            'bid_volume1': random.randint(10, 100),
                            'ask_price1': round(current_price + 1, 2),
                            'ask_volume1': random.randint(10, 100),
                            'turnover': round(current_price * random.randint(100, 1000), 2),
                        }
                        
                        # #region agent log
                        import json
                        try:
                            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"ctp_realtime.py:380","message":"Generating simulated tick data","data":{"symbol":symbol,"price":current_price},"timestamp":int(__import__('time').time()*1000)})+'\n')
                        except: pass
                        # #endregion
                        
                        # 调用内部回调
                        self._on_tick(tick_data)
                        
                        # 每5秒生成一条K线
                        current_second = int(time_module.time())
                        if current_second % 5 == 0 and current_second not in getattr(simulate_market_data, '_last_bar_second', {}):
                            if not hasattr(simulate_market_data, '_last_bar_second'):
                                simulate_market_data._last_bar_second = {}
                            if symbol not in simulate_market_data._last_bar_second or simulate_market_data._last_bar_second[symbol] != current_second:
                                simulate_market_data._last_bar_second[symbol] = current_second
                                
                                bar_data = {
                                    'symbol': symbol,
                                    'interval': '1m',
                                    'datetime': datetime.now(),
                                    'open': round(current_price - 2, 2),
                                    'high': round(current_price + 5, 2),
                                    'low': round(current_price - 5, 2),
                                    'close': round(current_price, 2),
                                    'volume': random.randint(500, 2000),
                                    'open_interest': random.randint(10000, 50000),
                                    'turnover': round(current_price * random.randint(500, 2000), 2),
                                }
                                
                                # #region agent log
                                try:
                                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"ctp_realtime.py:396","message":"Generating simulated bar data","data":{"symbol":symbol,"close":current_price},"timestamp":int(__import__('time').time()*1000)})+'\n')
                                except: pass
                                # #endregion
                                
                                self._on_bar(bar_data)
                        
                    except Exception as e:
                        logger.error(f"模拟数据生成失败: {e}")
                
                time_module.sleep(1)  # 每秒生成一次Tick
        
        self._simulation_thread = Thread(target=simulate_market_data, daemon=True)
        self._simulation_thread.start()
        logger.info("模拟数据生成线程已启动")
    
    def _stop_simulation(self):
        """停止模拟数据生成"""
        if self._simulation_thread and self._simulation_thread.is_alive():
            self._stop_event.set()
            self._simulation_thread.join(timeout=2)
            logger.info("模拟数据生成线程已停止")

