"""
业务逻辑集成层 - 连接GUI和业务逻辑
"""
from typing import Optional, Dict, Any
from threading import Thread
import time

from gui.utils.signal_bridge import SignalBridge
from market_data.ctp_realtime import CTPRealtimeData
from trading.ctp_trader import CTPTrader
from trading.live_trader import LiveTrader
from trading.order import Order
from database.models import TickData, KlineData
from utils.logger import get_logger

logger = get_logger(__name__)


class BusinessLogicManager:
    """业务逻辑管理器"""
    
    def __init__(self, signal_bridge: SignalBridge):
        self.signal_bridge = signal_bridge
        self.market_data: Optional[CTPRealtimeData] = None
        self.trader: Optional[CTPTrader] = None
        self.live_trader: Optional[LiveTrader] = None
        self.is_connected = False
    
    def connect_ctp(self, connection_params: Dict[str, Any]) -> bool:
        """连接CTP"""
        try:
            # 创建行情接口
            environment = connection_params.get('environment', 'normal')
            self.market_data = CTPRealtimeData(environment=environment)
            
            # 注册回调
            self.market_data.register_tick_callback(self._on_tick)
            self.market_data.register_kline_callback(self._on_bar)
            
            # 连接行情
            if not self.market_data.connect():
                logger.error("行情连接失败")
                self.signal_bridge.emit_connection_status(False, "行情连接失败")
                return False
            
            # 创建交易接口
            self.trader = CTPTrader(
                broker_id=connection_params['broker_id'],
                user_id=connection_params['user_id'],
                password=connection_params['password'],
                environment=environment
            )
            
            # 注册回调
            self.trader.register_order_callback(self._on_order)
            self.trader.register_trade_callback(self._on_trade)
            self.trader.register_position_callback(self._on_position)
            self.trader.register_account_callback(self._on_account)
            
            # 连接交易
            if not self.trader.connect():
                logger.error("交易连接失败")
                self.signal_bridge.emit_connection_status(False, "交易连接失败")
                return False
            
            self.is_connected = True
            self.signal_bridge.emit_connection_status(True, "CTP连接成功")
            logger.info("CTP连接成功")
            return True
            
        except Exception as e:
            logger.error(f"连接CTP失败: {e}", exc_info=True)
            self.signal_bridge.emit_connection_status(False, f"连接失败: {str(e)}")
            return False
    
    def disconnect_ctp(self):
        """断开CTP连接"""
        try:
            if self.market_data:
                self.market_data.disconnect()
                self.market_data = None
            
            if self.trader:
                self.trader.disconnect()
                self.trader = None
            
            self.is_connected = False
            self.signal_bridge.emit_connection_status(False, "已断开连接")
            logger.info("CTP已断开连接")
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}", exc_info=True)
    
    def subscribe_symbol(self, symbol: str) -> bool:
        """订阅合约"""
        if not self.market_data or not self.is_connected:
            logger.warning("未连接，无法订阅")
            return False
        
        return self.market_data.subscribe(symbol)
    
    def submit_order(self, order: Order) -> Optional[str]:
        """提交订单"""
        if not self.trader or not self.is_connected:
            logger.warning("未连接，无法下单")
            return None
        
        return self.trader.submit_order(order)
    
    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        if not self.trader or not self.is_connected:
            logger.warning("未连接，无法撤单")
            return False
        
        return self.trader.cancel_order(order_id)
    
    def _on_tick(self, tick: TickData):
        """Tick数据回调"""
        self.signal_bridge.emit_tick(tick)
    
    def _on_bar(self, bar: KlineData):
        """K线数据回调"""
        self.signal_bridge.emit_bar(bar)
    
    def _on_order(self, order: Order):
        """订单回调"""
        self.signal_bridge.emit_order(order)
    
    def _on_trade(self, trade):
        """成交回调"""
        # 成交信息可以转换为字典
        if hasattr(trade, '__dict__'):
            trade_dict = trade.__dict__
        else:
            trade_dict = {'order_id': str(trade)}
        # 可以发送成交信号（如果signal_bridge有的话）
        logger.info(f"成交: {trade_dict}")
    
    def _on_position(self, position):
        """持仓回调"""
        self.signal_bridge.emit_position(position)
    
    def _on_account(self, account_info: Dict[str, Any]):
        """账户回调"""
        self.signal_bridge.emit_account(account_info)


