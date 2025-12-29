"""
CTP交易接口封装
"""
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
from threading import Thread, Event, Lock
import time

from trading.trading_interface import TradingInterface
from trading.order import Order, OrderStatus, OrderDirection, OrderType
from backtest.portfolio import Position, Direction
from config.settings import settings
from config.contracts import get_contract_multiplier
from utils.logger import get_logger
from utils.helpers import is_trading_time, get_next_trading_time

logger = get_logger(__name__)

# 尝试导入vnpy-ctp
try:
    from vnpy_ctp import CtpGateway
    from vnpy.trader.event import EVENT_LOG, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, EVENT_POSITION
    VNPY_CTP_AVAILABLE = True
except ImportError:
    try:
        # 尝试备用导入路径
        from vnpy.gateway.ctp import CtpGateway
        from vnpy.trader.event import EVENT_LOG, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, EVENT_POSITION
        VNPY_CTP_AVAILABLE = True
    except ImportError:
        VNPY_CTP_AVAILABLE = False
        EVENT_LOG = "eLog"
        EVENT_ORDER = "eOrder"
        EVENT_TRADE = "eTrade"
        EVENT_ACCOUNT = "eAccount"
        EVENT_POSITION = "ePosition"
        logger.error("vnpy-ctp未安装或依赖缺失，请运行: pip install vnpy vnpy-ctp")


class CTPTrader(TradingInterface):
    """CTP交易接口封装"""
    
    def __init__(self,
                 broker_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 trade_address: Optional[str] = None,
                 environment: Optional[str] = None):
        """
        初始化CTP交易接口
        
        Args:
            broker_id: 经纪商代码
            user_id: 用户代码
            password: 密码
            trade_address: 交易服务器地址
            environment: 环境类型（"normal" 或 "7x24"），如果为None则使用配置中的环境类型
        """
        self.broker_id = broker_id or settings.CTP_BROKER_ID
        self.user_id = user_id or settings.CTP_USER_ID
        self.password = password or settings.CTP_PASSWORD
        self.environment = environment or settings.CTP_ENVIRONMENT
        
        # 根据环境类型获取服务器地址
        addresses = settings.get_server_addresses(self.environment)
        self.trade_address = trade_address or addresses['trade_address']
        self.md_address = addresses['md_address']
        
        # 连接状态
        self._connected = False
        self._lock = Lock()
        
        # CTP API对象（vnpy-ctp）
        self._ctp_api = None
        
        if not VNPY_CTP_AVAILABLE:
            logger.error("vnpy-ctp未安装，无法使用SimNow模拟环境。请运行: pip install vnpy-ctp")
        
        # 订单管理
        self.orders: Dict[str, Order] = {}  # {order_id: Order}
        self.positions: Dict[str, Position] = {}  # {symbol: Position}
        
        # 账户信息
        self.account_info: Dict[str, Any] = {}
        
        # 回调函数
        self.on_order_callback: Optional[Callable[[Order], None]] = None
        self.on_trade_callback: Optional[Callable[[Order], None]] = None
        self.on_position_callback: Optional[Callable[[Position], None]] = None
        self.on_account_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # 订单引用映射（用于CTP回调）
        self._order_ref_map: Dict[str, str] = {}  # {order_ref: order_id}
        self._order_ref_counter = 0
        
        # 查询等待事件
        self._account_query_event = Event()
        self._position_query_event = Event()
        self._order_query_event = Event()
        
        env_name = "7x24环境" if settings.is_7x24_environment(self.environment) else "CTP主席系统"
        logger.info(f"CTP交易接口初始化完成（SimNow模拟环境 - {env_name}）")
    
    def connect(self) -> bool:
        """
        连接CTP交易接口
        
        Returns:
            是否连接成功
        """
        with self._lock:
            if self._connected:
                logger.warning("CTP交易接口已连接")
                return True
            
            if not VNPY_CTP_AVAILABLE:
                logger.error("vnpy-ctp未安装，无法连接SimNow")
                return False
            
            try:
                # 检查交易时间（仅CTP主席系统需要检查，7x24环境全天候开放）
                is_7x24 = settings.is_7x24_environment(self.environment)
                if not is_7x24 and not is_trading_time():
                    next_time = get_next_trading_time()
                    logger.warning(f"当前不在交易时间内，CTP主席系统不开放")
                    logger.info(f"下一个交易时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info("提示：如需在非交易时间测试，请使用7x24环境（端口40001/40011）")
                    return False
                
                # 验证配置
                if not settings.validate_ctp_config():
                    logger.error("CTP配置不完整，请检查.env文件中的配置项")
                    return False
                
                env_name = "7x24环境" if is_7x24 else "CTP主席系统"
                logger.info(f"正在连接SimNow交易服务器（{env_name}）: {self.trade_address}")
                
                # 创建事件引擎
                from vnpy.event import EventEngine
                event_engine = EventEngine()
                
                # 创建vnpy-ctp网关
                self._ctp_api = CtpGateway(event_engine, "CTP")
                
                # 注册事件处理器（使用正确的事件名称）
                event_engine.register(EVENT_ORDER, self._on_order_callback)
                event_engine.register(EVENT_TRADE, self._on_trade_callback)
                event_engine.register(EVENT_POSITION, self._on_position_callback)
                event_engine.register(EVENT_ACCOUNT, self._on_account_callback)
                event_engine.register(EVENT_LOG, self._on_log_callback)
                
                # 配置CTP参数
                ctp_setting = {
                    "用户名": self.user_id,
                    "密码": self.password,
                    "经纪商代码": self.broker_id,
                    "交易服务器": self.trade_address,
                    "行情服务器": self.md_address,
                    "产品名称": settings.CTP_APP_ID,
                    "授权编码": settings.CTP_AUTH_CODE,
                }
                
                # 启动事件引擎
                event_engine.start()
                
                # 连接
                self._ctp_api.connect(ctp_setting)
                
                # 等待连接完成（最多等待10秒）
                timeout = 10
                start_time = time.time()
                while not self._connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self._connected:
                    logger.info("SimNow交易服务器连接成功")
                    # 查询账户和持仓
                    self.query_account()
                    self.query_positions()
                    return True
                else:
                    logger.error("SimNow交易服务器连接超时")
                    return False
                
            except Exception as e:
                logger.error(f"CTP交易接口连接失败: {e}", exc_info=True)
                self._connected = False
                return False
    
    def disconnect(self) -> bool:
        """
        断开连接
        
        Returns:
            是否断开成功
        """
        with self._lock:
            if not self._connected:
                return True
            
            try:
                logger.info("断开CTP交易接口连接")
                
                if self._ctp_api:
                    # 断开vnpy-ctp连接
                    try:
                        self._ctp_api.close()
                    except Exception as e:
                        logger.warning(f"关闭CTP连接时出错: {e}")
                
                self._connected = False
                self._ctp_api = None
                logger.info("CTP交易接口已断开")
                return True
                
            except Exception as e:
                logger.error(f"CTP交易接口断开失败: {e}")
                return False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def submit_order(self, order: Order) -> Optional[str]:
        """
        提交订单
        
        Args:
            order: 订单对象
            
        Returns:
            订单ID，如果失败返回None
        """
        if not self._connected:
            logger.error("CTP交易接口未连接")
            return None
        
        try:
            # 真实CTP下单
            if not self._ctp_api:
                logger.error("CTP API未初始化")
                order.status = OrderStatus.REJECTED
                order.reject_reason = "CTP API未初始化"
                return None
            
            # 生成订单引用
            self._order_ref_counter += 1
            order_ref = str(self._order_ref_counter)
            self._order_ref_map[order_ref] = order.order_id
            
            # 构建下单请求
            req = {
                'symbol': order.symbol,
                'exchange': self._get_exchange_from_symbol(order.symbol),
                'type': self._convert_order_type(order.order_type),
                'direction': self._convert_direction(order.direction),
                'offset': self._get_offset_from_direction(order.direction),
                'price': order.price,
                'volume': order.volume,
                'reference': order_ref,
            }
            
            # 提交订单
            order_id = self._ctp_api.send_order(req)
            
            if order_id:
                order.order_id = order_id
                order.status = OrderStatus.SUBMITTED
                self.orders[order.order_id] = order
                
                logger.info(f"订单提交成功: {order.order_id}, {order.symbol}")
                
                # 调用回调
                if self.on_order_callback:
                    try:
                        self.on_order_callback(order)
                    except Exception as e:
                        logger.error(f"订单回调执行失败: {e}")
                
                return order.order_id
            else:
                order.status = OrderStatus.REJECTED
                order.reject_reason = "CTP下单失败"
                logger.error(f"订单提交失败: {order.symbol}")
                return None
            
        except Exception as e:
            logger.error(f"提交订单失败: {e}", exc_info=True)
            order.status = OrderStatus.REJECTED
            order.reject_reason = str(e)
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功
        """
        if not self._connected:
            logger.error("CTP交易接口未连接")
            return False
        
        if order_id not in self.orders:
            logger.warning(f"订单不存在: {order_id}")
            return False
        
        order = self.orders[order_id]
        if not order.is_active():
            logger.warning(f"订单无法撤销，当前状态: {order.status}")
            return False
        
        try:
            
            # 真实CTP撤单
            if not self._ctp_api:
                logger.error("CTP API未初始化")
                return False
            
            # 查找订单引用
            order_ref = None
            for ref, oid in self._order_ref_map.items():
                if oid == order_id:
                    order_ref = ref
                    break
            
            if not order_ref:
                logger.warning(f"找不到订单引用: {order_id}")
                return False
            
            # 构建撤单请求
            req = {
                'orderid': order_id,
                'symbol': order.symbol,
                'exchange': self._get_exchange_from_symbol(order.symbol),
            }
            
            # 撤销订单
            result = self._ctp_api.cancel_order(req)
            
            if result:
                logger.info(f"订单撤销成功: {order_id}")
                # 状态更新由回调处理
                return True
            else:
                logger.error(f"订单撤销失败: {order_id}")
                return False
            
        except Exception as e:
            logger.error(f"撤销订单失败: {e}", exc_info=True)
            return False
    
    def query_account(self) -> Dict[str, Any]:
        """
        查询账户信息
        
        Returns:
            账户信息字典
        """
        if not self._connected:
            logger.warning("CTP交易接口未连接，返回空账户信息")
            return {}
        
        try:
            
            # 真实CTP查询
            if not self._ctp_api:
                logger.error("CTP API未初始化")
                return {}
            
            # 重置事件
            self._account_query_event.clear()
            
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"K","location":"ctp_trader.py:query_account","message":"Calling query_account","data":{"user_id":self.user_id,"has_ctp_api":self._ctp_api is not None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 查询账户
            self._ctp_api.query_account()
            
            # 等待查询结果（最多等待5秒）
            if self._account_query_event.wait(timeout=5):
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"K","location":"ctp_trader.py:query_account","message":"Account query success","data":{"account_info":self.account_info},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return self.account_info.copy()
            else:
                logger.warning("账户查询超时")
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"K","location":"ctp_trader.py:query_account","message":"Account query timeout","data":{"account_info":self.account_info},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return self.account_info.copy() if self.account_info else {}
            
        except Exception as e:
            logger.error(f"查询账户信息失败: {e}", exc_info=True)
            return {}
    
    def query_positions(self) -> List[Position]:
        """
        查询持仓
        
        Returns:
            持仓列表
        """
        if not self._connected:
            logger.warning("CTP交易接口未连接，返回空持仓列表")
            return []
        
        try:
            
            # 真实CTP查询
            if not self._ctp_api:
                logger.error("CTP API未初始化")
                return []
            
            # 重置事件
            self._position_query_event.clear()
            
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"M","location":"ctp_trader.py:query_positions","message":"Calling query_position","data":{"has_ctp_api":self._ctp_api is not None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 查询持仓
            self._ctp_api.query_position()
            
            # 等待查询结果（最多等待5秒）
            if self._position_query_event.wait(timeout=5):
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"M","location":"ctp_trader.py:query_positions","message":"Position query success","data":{"position_count":len(self.positions)},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return list(self.positions.values())
            else:
                logger.warning("持仓查询超时")
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"M","location":"ctp_trader.py:query_positions","message":"Position query timeout","data":{"position_count":len(self.positions)},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return list(self.positions.values())
            
        except Exception as e:
            logger.error(f"查询持仓失败: {e}", exc_info=True)
            return []
    
    def query_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        查询订单
        
        Args:
            symbol: 合约代码，如果为None则查询所有订单
            
        Returns:
            订单列表
        """
        if not self._connected:
            logger.warning("CTP交易接口未连接，返回空订单列表")
            return []
        
        try:
            
            # 真实CTP查询
            if not self._ctp_api:
                logger.error("CTP API未初始化")
                return []
            
            # 重置事件
            self._order_query_event.clear()
            
            # 查询订单
            req = {}
            if symbol:
                req['symbol'] = symbol
            self._ctp_api.query_order(req)
            
            # 等待查询结果（最多等待5秒）
            if self._order_query_event.wait(timeout=5):
                if symbol:
                    orders = [o for o in self.orders.values() if o.symbol == symbol]
                else:
                    orders = list(self.orders.values())
                return orders
            else:
                logger.warning("订单查询超时")
                # 返回本地缓存的订单
                if symbol:
                    orders = [o for o in self.orders.values() if o.symbol == symbol]
                else:
                    orders = list(self.orders.values())
                return orders
            
        except Exception as e:
            logger.error(f"查询订单失败: {e}", exc_info=True)
            return []
    
    def register_order_callback(self, callback: Callable[[Order], None]):
        """注册订单回调"""
        self.on_order_callback = callback
    
    def register_trade_callback(self, callback: Callable[[Order], None]):
        """注册成交回调"""
        self.on_trade_callback = callback
    
    def register_position_callback(self, callback: Callable[[Position], None]):
        """注册持仓回调"""
        self.on_position_callback = callback
    
    def register_account_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """注册账户回调"""
        self.on_account_callback = callback
    
    def _convert_order_type(self, order_type: OrderType) -> str:
        """转换订单类型为CTP格式"""
        # TODO: 根据实际CTP库的订单类型进行转换
        type_map = {
            OrderType.LIMIT: '2',  # 限价单
            OrderType.MARKET: '1',  # 市价单
        }
        return type_map.get(order_type, '2')
    
    def _convert_direction(self, direction: OrderDirection) -> str:
        """转换订单方向为CTP格式"""
        # CTP方向定义：0-买, 1-卖, 2-ETF申购, 3-ETF赎回, 4-融资, 5-融券
        # 期货：0-买开, 1-卖平, 2-卖开, 3-买平
        direction_map = {
            OrderDirection.BUY: '0',   # 买开
            OrderDirection.SELL: '1',   # 卖平
            OrderDirection.SHORT: '2',  # 卖开
            OrderDirection.COVER: '3', # 买平
        }
        return direction_map.get(direction, '0')
    
    def _on_tick_callback(self, tick_data: Dict):
        """vnpy-ctp Tick数据回调（行情数据，交易接口不需要）"""
        pass
    
    def _on_trade_callback(self, event):
        """vnpy-ctp 成交通知回调"""
        try:
            trade_data = event.data
            order_ref = getattr(trade_data, 'order_ref', '') if hasattr(trade_data, 'order_ref') else trade_data.get('order_ref', '') if isinstance(trade_data, dict) else ''
            order_id = self._order_ref_map.get(order_ref)
            
            if not order_id or order_id not in self.orders:
                logger.warning(f"收到未知订单的成交: {order_ref}")
                return
            
            order = self.orders[order_id]
            fill_volume = int(getattr(trade_data, 'volume', 0) if hasattr(trade_data, 'volume') else trade_data.get('volume', 0) if isinstance(trade_data, dict) else 0)
            fill_price = float(getattr(trade_data, 'price', 0.0) if hasattr(trade_data, 'price') else trade_data.get('price', 0.0) if isinstance(trade_data, dict) else 0.0)
            
            # 更新订单成交信息
            order.update_fill(fill_volume, fill_price)
            
            # 调用成交回调
            if self.on_trade_callback:
                try:
                    self.on_trade_callback(order)
                except Exception as e:
                    logger.error(f"成交回调执行失败: {e}")
            
            logger.info(f"订单成交: {order_id}, {fill_volume}手@{fill_price}")
            
        except Exception as e:
            logger.error(f"处理成交通知失败: {e}", exc_info=True)
    
    def _on_order_callback(self, event):
        """vnpy-ctp 订单状态回调"""
        try:
            order_data = event.data
            order_ref = getattr(order_data, 'order_ref', '') if hasattr(order_data, 'order_ref') else order_data.get('order_ref', '') if isinstance(order_data, dict) else ''
            order_id = self._order_ref_map.get(order_ref)
            
            if not order_id:
                # 可能是查询返回的订单，需要创建或更新
                order_id = getattr(order_data, 'orderid', '') if hasattr(order_data, 'orderid') else order_data.get('orderid', '') if isinstance(order_data, dict) else ''
                if not order_id or order_id not in self.orders:
                    # 创建新订单对象
                    order = self._create_order_from_ctp_data(order_data)
                    if order:
                        self.orders[order.order_id] = order
                        if order_ref:
                            self._order_ref_map[order_ref] = order.order_id
                else:
                    order = self.orders[order_id]
            else:
                order = self.orders[order_id]
            
            # 更新订单状态
            status = getattr(order_data, 'status', '') if hasattr(order_data, 'status') else order_data.get('status', '') if isinstance(order_data, dict) else ''
            self._update_order_status_from_ctp(order, status, order_data)
            
            # 设置查询事件（如果是查询返回的）
            if isinstance(order_data, dict) and 'query' in order_data.get('type', ''):
                self._order_query_event.set()
            
            # 调用订单回调
            if self.on_order_callback:
                try:
                    self.on_order_callback(order)
                except Exception as e:
                    logger.error(f"订单回调执行失败: {e}")
            
        except Exception as e:
            logger.error(f"处理订单状态失败: {e}", exc_info=True)
    
    def _on_position_callback(self, event):
        """vnpy-ctp 持仓更新回调"""
        try:
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"L","location":"ctp_trader.py:_on_position_callback","message":"Position callback triggered","data":{"event_type":type(event).__name__,"has_data":hasattr(event,'data')},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            position_data = event.data
            symbol = getattr(position_data, 'symbol', '') if hasattr(position_data, 'symbol') else position_data.get('symbol', '') if isinstance(position_data, dict) else ''
            if not symbol:
                return
            
            # 转换为Position对象
            pos = self._create_position_from_ctp_data(position_data)
            if pos:
                self.positions[symbol] = pos
                self._position_query_event.set()
                
                # 调用持仓回调
                if self.on_position_callback:
                    try:
                        self.on_position_callback(pos)
                    except Exception as e:
                        logger.error(f"持仓回调执行失败: {e}")
            
        except Exception as e:
            logger.error(f"处理持仓更新失败: {e}", exc_info=True)
    
    def _on_account_callback(self, event):
        """vnpy-ctp 账户更新回调"""
        try:
            # #region agent log
            import json
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"J","location":"ctp_trader.py:_on_account_callback","message":"Account callback triggered","data":{"event_type":type(event).__name__,"has_data":hasattr(event,'data'),"data_type":type(event.data).__name__ if hasattr(event,'data') else None},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            account_data = event.data
            
            # #region agent log
            try:
                account_attrs = [attr for attr in dir(account_data) if not attr.startswith('_')] if hasattr(account_data, '__dict__') else []
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"J","location":"ctp_trader.py:_on_account_callback","message":"Account data attributes","data":{"attrs":account_attrs[:10]},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            self.account_info = {
                'balance': float(account_data.balance) if hasattr(account_data, 'balance') else 0.0,
                'available': float(account_data.available) if hasattr(account_data, 'available') else 0.0,
                'margin': float(account_data.margin) if hasattr(account_data, 'margin') else 0.0,
                'frozen_margin': float(account_data.frozen) if hasattr(account_data, 'frozen') else 0.0,
                'commission': float(account_data.commission) if hasattr(account_data, 'commission') else 0.0,
                'profit': float(account_data.profit) if hasattr(account_data, 'profit') else 0.0,
            }
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"J","location":"ctp_trader.py:_on_account_callback","message":"Account info updated","data":{"account_info":self.account_info},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            # 调用账户回调
            if self.on_account_callback:
                try:
                    self.on_account_callback(self.account_info.copy())
                except Exception as e:
                    logger.error(f"账户回调执行失败: {e}")
            
            self._account_query_event.set()
            
        except Exception as e:
            logger.error(f"处理账户更新失败: {e}", exc_info=True)
    
    def _on_log_callback(self, event):
        """vnpy-ctp 日志事件回调"""
        try:
            log_data = event.data
            log_msg = log_data.get('msg', '') if isinstance(log_data, dict) else str(log_data)
            log_level = log_data.get('level', 'INFO') if isinstance(log_data, dict) else 'INFO'
            
            # 处理连接状态
            if '连接成功' in log_msg or '登录成功' in log_msg:
                self._connected = True
                logger.info(f"SimNow连接成功: {log_msg}")
            elif '连接失败' in log_msg or '登录失败' in log_msg:
                self._connected = False
                logger.error(f"SimNow连接失败: {log_msg}")
            
        except Exception as e:
            logger.debug(f"处理日志事件失败: {e}")
    
    def _create_order_from_ctp_data(self, order_data) -> Optional[Order]:
        """从CTP订单数据创建Order对象"""
        try:
            # 处理vnpy-ctp数据格式
            if hasattr(order_data, 'symbol'):
                symbol = order_data.symbol.split('.')[0] if '.' in order_data.symbol else order_data.symbol
                direction_str = str(getattr(order_data, 'direction', '0'))
                price = float(getattr(order_data, 'price', 0))
                volume = int(getattr(order_data, 'volume', 0))
                order_id = getattr(order_data, 'orderid', '')
            elif isinstance(order_data, dict):
                symbol = order_data.get('symbol', '').split('.')[0] if '.' in order_data.get('symbol', '') else order_data.get('symbol', '')
                direction_str = str(order_data.get('direction', '0'))
                price = float(order_data.get('price', 0))
                volume = int(order_data.get('volume', 0))
                order_id = order_data.get('orderid', '')
            else:
                return None
            
            # 转换方向
            direction_map = {
                '0': OrderDirection.BUY,
                '1': OrderDirection.SELL,
                '2': OrderDirection.SHORT,
                '3': OrderDirection.COVER,
            }
            direction = direction_map.get(direction_str, OrderDirection.BUY)
            
            # 创建订单
            order = Order(
                symbol=symbol,
                direction=direction,
                price=price,
                volume=volume,
                order_type=OrderType.LIMIT
            )
            
            # 设置订单ID
            if order_id:
                order.order_id = order_id
            
            return order
            
        except Exception as e:
            logger.error(f"创建订单对象失败: {e}", exc_info=True)
            return None
    
    def _update_order_status_from_ctp(self, order: Order, status: str, order_data):
        """从CTP状态更新订单状态"""
        # CTP订单状态：全部成交、部分成交、未成交、已撤销、拒单等
        # vnpy-ctp使用Status枚举
        try:
            from vnpy.trader.constant import Status
            if hasattr(status, 'value'):
                status_value = status.value
            elif isinstance(status, Status):
                status_value = status.name
            else:
                status_value = str(status)
        except:
            status_value = str(status)
        
        status_map = {
            'ALLTRADED': OrderStatus.FILLED,
            'PARTIALTRADED': OrderStatus.PARTIAL,
            'NOTTRADED': OrderStatus.SUBMITTED,
            'CANCELLED': OrderStatus.CANCELLED,
            'REJECTED': OrderStatus.REJECTED,
            '全部成交': OrderStatus.FILLED,
            '部分成交': OrderStatus.PARTIAL,
            '未成交': OrderStatus.SUBMITTED,
            '已撤销': OrderStatus.CANCELLED,
            '拒单': OrderStatus.REJECTED,
        }
        
        new_status = status_map.get(status_value, OrderStatus.SUBMITTED)
        order.status = new_status
        
        # 更新成交信息
        if hasattr(order_data, 'traded'):
            order.filled_volume = int(order_data.traded)
        elif isinstance(order_data, dict) and 'traded' in order_data:
            order.filled_volume = int(order_data.get('traded', 0))
        
        order.update_time = datetime.now()
    
    def _create_position_from_ctp_data(self, position_data) -> Optional[Position]:
        """从CTP持仓数据创建Position对象"""
        try:
            # 处理vnpy-ctp数据格式
            if hasattr(position_data, 'symbol'):
                symbol = position_data.symbol.split('.')[0] if '.' in position_data.symbol else position_data.symbol
                volume = int(getattr(position_data, 'volume', 0))
                price = float(getattr(position_data, 'price', 0))
                direction_str = str(getattr(position_data, 'direction', ''))
            elif isinstance(position_data, dict):
                symbol = position_data.get('symbol', '').split('.')[0] if '.' in position_data.get('symbol', '') else position_data.get('symbol', '')
                volume = int(position_data.get('volume', 0))
                price = float(position_data.get('price', 0))
                direction_str = str(position_data.get('direction', ''))
            else:
                return None
            
            # 转换方向
            if direction_str in ['多', 'long', 'LONG', '1', 'Long']:
                direction = Direction.LONG
            elif direction_str in ['空', 'short', 'SHORT', '-1', 'Short']:
                direction = Direction.SHORT
            else:
                direction = Direction.LONG if volume > 0 else Direction.NONE
            
            multiplier = get_contract_multiplier(symbol)
            
            pos = Position(
                symbol=symbol,
                direction=direction,
                volume=abs(volume),
                entry_price=price,
                entry_time=datetime.now(),
                current_price=price,
                multiplier=multiplier
            )
            
            return pos
            
        except Exception as e:
            logger.error(f"创建持仓对象失败: {e}", exc_info=True)
            return None
    
    def _get_exchange_from_symbol(self, symbol: str) -> str:
        """从合约代码获取交易所代码"""
        # 根据合约代码前缀判断交易所
        if symbol.startswith('rb') or symbol.startswith('cu') or symbol.startswith('au'):
            return 'SHFE'  # 上海期货交易所
        elif symbol.startswith('i') or symbol.startswith('j') or symbol.startswith('jm'):
            return 'DCE'  # 大连商品交易所
        elif symbol.startswith('c') or symbol.startswith('cs') or symbol.startswith('m'):
            return 'CZCE'  # 郑州商品交易所
        elif symbol.startswith('IF') or symbol.startswith('IC') or symbol.startswith('IH'):
            return 'CFFEX'  # 中国金融期货交易所
        else:
            return 'SHFE'  # 默认
    
    def _get_offset_from_direction(self, direction: OrderDirection) -> str:
        """从订单方向获取开平标志"""
        # CTP开平标志：0-开仓, 1-平仓
        if direction in [OrderDirection.BUY, OrderDirection.SHORT]:
            return 'OPEN'  # 开仓
        else:
            return 'CLOSE'  # 平仓

