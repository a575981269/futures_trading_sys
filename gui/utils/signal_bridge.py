"""
信号桥接 - 将CTP接口回调转换为Qt信号，确保线程安全
"""
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any, List, Optional
from database.models import TickData, KlineData
from trading.order import Order
from backtest.portfolio import Position


class SignalBridge(QObject):
    """信号桥接类，用于线程安全的数据传递"""
    
    # 行情数据信号
    tick_received = pyqtSignal(object)  # TickData
    bar_received = pyqtSignal(object)    # KlineData
    
    # 交易数据信号
    order_updated = pyqtSignal(object)   # Order
    trade_updated = pyqtSignal(object)   # Trade
    position_updated = pyqtSignal(object)  # Position
    account_updated = pyqtSignal(dict)   # account_info dict
    
    # 连接状态信号
    connection_status_changed = pyqtSignal(bool, str)  # (connected, message)
    
    # 日志信号
    log_received = pyqtSignal(str, int)  # (message, level)
    
    # 策略信号
    strategy_status_changed = pyqtSignal(str, str)  # (strategy_id, status)
    
    # 风控信号
    risk_alert = pyqtSignal(str, str)  # (alert_type, message)
    
    def __init__(self):
        super().__init__()
    
    def emit_tick(self, tick: TickData):
        """发送Tick数据信号"""
        self.tick_received.emit(tick)
    
    def emit_bar(self, bar: KlineData):
        """发送K线数据信号"""
        self.bar_received.emit(bar)
    
    def emit_order(self, order: Order):
        """发送订单更新信号"""
        self.order_updated.emit(order)
    
    def emit_position(self, position: Position):
        """发送持仓更新信号"""
        self.position_updated.emit(position)
    
    def emit_account(self, account_info: Dict[str, Any]):
        """发送账户更新信号"""
        self.account_updated.emit(account_info)
    
    def emit_connection_status(self, connected: bool, message: str = ""):
        """发送连接状态信号"""
        self.connection_status_changed.emit(connected, message)
    
    def emit_log(self, message: str, level: int = 20):
        """发送日志信号"""
        self.log_received.emit(message, level)
    
    def emit_strategy_status(self, strategy_id: str, status: str):
        """发送策略状态信号"""
        self.strategy_status_changed.emit(strategy_id, status)
    
    def emit_risk_alert(self, alert_type: str, message: str):
        """发送风控告警信号"""
        self.risk_alert.emit(alert_type, message)


