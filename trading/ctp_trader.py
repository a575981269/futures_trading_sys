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

logger = get_logger(__name__)

# 尝试导入vnpy-ctp
try:
    from vnpy.gateway.ctp import CtpGateway
    VNPY_CTP_AVAILABLE = True
except ImportError:
    VNPY_CTP_AVAILABLE = False
    logger.warning("vnpy-ctp未安装，将使用模拟模式")


class CTPTrader(TradingInterface):
    """CTP交易接口封装"""
    
    def __init__(self,
                 broker_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 trade_address: Optional[str] = None):
        """
        初始化CTP交易接口
        
        Args:
            broker_id: 经纪商代码
            user_id: 用户代码
            password: 密码
            trade_address: 交易服务器地址
        """
        self.broker_id = broker_id or settings.CTP_BROKER_ID
        self.user_id = user_id or settings.CTP_USER_ID
        self.password = password or settings.CTP_PASSWORD
        self.trade_address = trade_address or settings.CTP_TRADE_ADDRESS
        
        # 连接状态
        self._connected = False
        self._lock = Lock()
        
        # CTP API对象（vnpy-ctp或模拟模式）
        self._ctp_api = None
        self._use_simulation = not VNPY_CTP_AVAILABLE
        
        # 订单管理
        self.orders: Dict[str, Order] = {}  # {order_id: Order}
        self.positions: Dict[str, Position] = {}  # {symbol: Position}
        
        # 账户信息
        self.account_info: Dict[str, Any] = {}
        
        # 回调函数
        self.on_order_callback: Optional[Callable[[Order], None]] = None
        self.on_trade_callback: Optional[Callable[[Order], None]] = None
        self.on_position_callback: Optional[Callable[[Position], None]] = None
        
        # 订单引用映射（用于CTP回调）
        self._order_ref_map: Dict[str, str] = {}  # {order_ref: order_id}
        self._order_ref_counter = 0
        
        # 查询等待事件
        self._account_query_event = Event()
        self._position_query_event = Event()
        self._order_query_event = Event()
        
        logger.info(f"CTP交易接口初始化完成 (模拟模式={'是' if self._use_simulation else '否'})")
    
    def connect(self) -> bool:
        """
        连接CTP交易接口
        
        Returns:
            是否连接成功
        """
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_trader.py:80","message":"connect() called","data":{"_connected":self._connected,"_use_simulation":self._use_simulation,"trade_address":self.trade_address},"timestamp":int(time.time()*1000)})+'\n')
        except: pass
        # #endregion
        
        with self._lock:
            if self._connected:
                logger.warning("CTP交易接口已连接")
                return True
            
            try:
                if self._use_simulation:
                    # 模拟模式：直接连接成功
                    logger.info("使用模拟模式连接CTP交易接口")
                    # #region agent log
                    try:
                        with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_trader.py:93","message":"Using simulation mode","data":{"_use_simulation":self._use_simulation},"timestamp":int(time.time()*1000)})+'\n')
                    except: pass
                    # #endregion
                    self._connected = True
                    
                    # 初始化模拟账户信息
                    self.account_info = {
                        'balance': 1000000.0,
                        'available': 1000000.0,
                        'margin': 0.0,
                        'frozen_margin': 0.0,
                        'commission': 0.0,
                        'profit': 0.0,
                    }
                    # #region agent log
                    try:
                        with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_trader.py:108","message":"Simulation mode connected successfully","data":{"account_info":self.account_info},"timestamp":int(time.time()*1000)})+'\n')
                    except: pass
                    # #endregion
                    
                    logger.info("模拟模式连接成功")
                    return True
                
                # 真实CTP连接（使用vnpy-ctp）
                if not VNPY_CTP_AVAILABLE:
                    # #region agent log
                    try:
                        with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"ctp_trader.py:112","message":"VNPY_CTP_AVAILABLE is False","data":{"VNPY_CTP_AVAILABLE":VNPY_CTP_AVAILABLE},"timestamp":int(time.time()*1000)})+'\n')
                    except: pass
                    # #endregion
                    logger.error("vnpy-ctp未安装，无法连接真实CTP接口")
                    return False
                
                logger.info(f"连接CTP交易接口: {self.trade_address}")
                
                # 创建vnpy-ctp网关
                self._ctp_api = CtpGateway()
                
                # 配置CTP参数
                ctp_config = {
                    "用户名": self.user_id,
                    "密码": self.password,
                    "经纪商代码": self.broker_id,
                    "交易服务器": self.trade_address,
                    "行情服务器": settings.CTP_MD_ADDRESS,
                    "产品名称": settings.CTP_APP_ID,
                    "授权编码": settings.CTP_AUTH_CODE,
                }
                
                # 注册回调
                # vnpy-ctp使用事件驱动，需要注册事件处理器
                # 注意：vnpy-ctp的实际API可能不同，这里是一个通用实现
                # 实际使用时需要根据vnpy-ctp的具体API调整
                
                # 连接
                self._ctp_api.connect(ctp_config)
                
                # 等待登录完成（最多等待10秒）
                # vnpy-ctp连接是异步的，需要等待登录回调
                timeout = 10
                start_time = time.time()
                login_event = Event()
                
                # 临时保存登录事件
                original_on_login = getattr(self._ctp_api, 'on_login', None)
                
                def on_login_callback(data):
                    if data.get('status', False):
                        self._connected = True
                        login_event.set()
                    if original_on_login:
                        original_on_login(data)
                
                # 设置登录回调
                if hasattr(self._ctp_api, 'on_login'):
                    self._ctp_api.on_login = on_login_callback
                
                # 等待登录
                if login_event.wait(timeout=timeout):
                    logger.info("CTP登录成功")
                else:
                    logger.error("CTP登录超时")
                    return False
                
                # 查询账户和持仓
                self.query_account()
                self.query_positions()
                
                logger.info("CTP交易接口连接成功")
                return True
                
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
                
                if self._ctp_api and not self._use_simulation:
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
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ctp_trader.py:submit_order","message":"submit_order() called","data":{"_connected":self._connected,"symbol":order.symbol,"direction":order.direction.value,"price":order.price,"volume":order.volume},"timestamp":int(time.time()*1000)})+'\n')
        except: pass
        # #endregion
        
        if not self._connected:
            logger.error("CTP交易接口未连接")
            return None
        
        try:
            if self._use_simulation:
                # 模拟模式：直接接受订单
                logger.info(f"模拟模式提交订单: {order}")
                order.status = OrderStatus.SUBMITTED
                self.orders[order.order_id] = order
                
                # 模拟成交（延迟执行）
                def simulate_fill():
                    time.sleep(0.5)
                    if order.order_id in self.orders:
                        order.update_fill(order.volume, order.price)
                        if self.on_trade_callback:
                            try:
                                self.on_trade_callback(order)
                            except Exception as e:
                                logger.error(f"成交回调执行失败: {e}")
                
                Thread(target=simulate_fill, daemon=True).start()
                
                if self.on_order_callback:
                    try:
                        self.on_order_callback(order)
                    except Exception as e:
                        logger.error(f"订单回调执行失败: {e}")
                
                return order.order_id
            
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
            if self._use_simulation:
                # 模拟模式：直接撤销
                logger.info(f"模拟模式撤销订单: {order_id}")
                order.cancel()
                
                if self.on_order_callback:
                    try:
                        self.on_order_callback(order)
                    except Exception as e:
                        logger.error(f"订单回调执行失败: {e}")
                
                return True
            
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
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"ctp_trader.py:query_account","message":"query_account() called","data":{"_connected":self._connected,"_use_simulation":self._use_simulation},"timestamp":int(time.time()*1000)})+'\n')
        except: pass
        # #endregion
        
        if not self._connected:
            logger.warning("CTP交易接口未连接，返回空账户信息")
            return {}
        
        try:
            if self._use_simulation:
                # 模拟模式：返回模拟账户信息
                if not self.account_info:
                    self.account_info = {
                        'balance': 1000000.0,
                        'available': 1000000.0,
                        'margin': 0.0,
                        'frozen_margin': 0.0,
                        'commission': 0.0,
                        'profit': 0.0,
                    }
                # #region agent log
                try:
                    with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"ctp_trader.py:query_account","message":"Returning account info","data":{"account_info":self.account_info},"timestamp":int(time.time()*1000)})+'\n')
                except: pass
                # #endregion
                return self.account_info.copy()
            
            # 真实CTP查询
            if not self._ctp_api:
                logger.error("CTP API未初始化")
                return {}
            
            # 重置事件
            self._account_query_event.clear()
            
            # 查询账户
            self._ctp_api.query_account()
            
            # 等待查询结果（最多等待5秒）
            if self._account_query_event.wait(timeout=5):
                return self.account_info.copy()
            else:
                logger.warning("账户查询超时")
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
            if self._use_simulation:
                # 模拟模式：返回空持仓列表
                return list(self.positions.values())
            
            # 真实CTP查询
            if not self._ctp_api:
                logger.error("CTP API未初始化")
                return []
            
            # 重置事件
            self._position_query_event.clear()
            
            # 查询持仓
            self._ctp_api.query_position()
            
            # 等待查询结果（最多等待5秒）
            if self._position_query_event.wait(timeout=5):
                return list(self.positions.values())
            else:
                logger.warning("持仓查询超时")
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
            if self._use_simulation:
                # 模拟模式：返回本地缓存的订单
                if symbol:
                    orders = [o for o in self.orders.values() if o.symbol == symbol]
                else:
                    orders = list(self.orders.values())
                return orders
            
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
    
    def _on_trade_callback(self, trade_data: Dict):
        """vnpy-ctp 成交通知回调"""
        try:
            order_ref = trade_data.get('order_ref', '')
            order_id = self._order_ref_map.get(order_ref)
            
            if not order_id or order_id not in self.orders:
                logger.warning(f"收到未知订单的成交: {order_ref}")
                return
            
            order = self.orders[order_id]
            fill_volume = trade_data.get('volume', 0)
            fill_price = trade_data.get('price', 0.0)
            
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
    
    def _on_order_callback(self, order_data: Dict):
        """vnpy-ctp 订单状态回调"""
        try:
            order_ref = order_data.get('order_ref', '')
            order_id = self._order_ref_map.get(order_ref)
            
            if not order_id:
                # 可能是查询返回的订单，需要创建或更新
                order_id = order_data.get('orderid', '')
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
            status = order_data.get('status', '')
            self._update_order_status_from_ctp(order, status, order_data)
            
            # 设置查询事件（如果是查询返回的）
            if 'query' in order_data.get('type', ''):
                self._order_query_event.set()
            
            # 调用订单回调
            if self.on_order_callback:
                try:
                    self.on_order_callback(order)
                except Exception as e:
                    logger.error(f"订单回调执行失败: {e}")
            
        except Exception as e:
            logger.error(f"处理订单状态失败: {e}", exc_info=True)
    
    def _on_position_callback(self, position_data: Dict):
        """vnpy-ctp 持仓更新回调"""
        try:
            symbol = position_data.get('symbol', '')
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
    
    def _on_account_callback(self, account_data: Dict):
        """vnpy-ctp 账户更新回调"""
        try:
            self.account_info = {
                'balance': account_data.get('balance', 0.0),
                'available': account_data.get('available', 0.0),
                'margin': account_data.get('margin', 0.0),
                'frozen_margin': account_data.get('frozen', 0.0),
                'commission': account_data.get('commission', 0.0),
                'profit': account_data.get('profit', 0.0),
            }
            self._account_query_event.set()
            
        except Exception as e:
            logger.error(f"处理账户更新失败: {e}", exc_info=True)
    
    def _create_order_from_ctp_data(self, order_data: Dict) -> Optional[Order]:
        """从CTP订单数据创建Order对象"""
        try:
            symbol = order_data.get('symbol', '')
            direction_str = order_data.get('direction', '')
            price = float(order_data.get('price', 0))
            volume = int(order_data.get('volume', 0))
            
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
            order.order_id = order_data.get('orderid', order.order_id)
            
            return order
            
        except Exception as e:
            logger.error(f"创建订单对象失败: {e}")
            return None
    
    def _update_order_status_from_ctp(self, order: Order, status: str, order_data: Dict):
        """从CTP状态更新订单状态"""
        # CTP订单状态：全部成交、部分成交、未成交、已撤销、拒单等
        status_map = {
            '全部成交': OrderStatus.FILLED,
            '部分成交': OrderStatus.PARTIAL,
            '未成交': OrderStatus.SUBMITTED,
            '已撤销': OrderStatus.CANCELLED,
            '拒单': OrderStatus.REJECTED,
        }
        
        new_status = status_map.get(status, OrderStatus.SUBMITTED)
        order.status = new_status
        
        # 更新成交信息
        if 'traded' in order_data:
            order.filled_volume = int(order_data.get('traded', 0))
        
        order.update_time = datetime.now()
    
    def _create_position_from_ctp_data(self, position_data: Dict) -> Optional[Position]:
        """从CTP持仓数据创建Position对象"""
        try:
            symbol = position_data.get('symbol', '')
            volume = int(position_data.get('volume', 0))
            price = float(position_data.get('price', 0))
            direction_str = position_data.get('direction', '')
            
            # 转换方向
            if direction_str in ['多', 'long', 'LONG', '1']:
                direction = Direction.LONG
            elif direction_str in ['空', 'short', 'SHORT', '-1']:
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
            logger.error(f"创建持仓对象失败: {e}")
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

