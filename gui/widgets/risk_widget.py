"""
风控监控窗口 - 风控指标、告警信息
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSlot
from typing import List, Dict

from gui.utils.signal_bridge import SignalBridge
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskWidget(QWidget):
    """风控监控窗口"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.alerts: List[Dict[str, str]] = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：风控指标
        metrics_group = QGroupBox("风控指标")
        metrics_layout = QGridLayout()
        
        self.position_limit_label = QLabel("持仓限制: --")
        self.capital_limit_label = QLabel("资金限制: --")
        self.order_limit_label = QLabel("订单限制: --")
        self.daily_loss_label = QLabel("日亏损: --")
        self.risk_ratio_label = QLabel("风险比例: --")
        
        metrics_layout.addWidget(self.position_limit_label, 0, 0)
        metrics_layout.addWidget(self.capital_limit_label, 0, 1)
        metrics_layout.addWidget(self.order_limit_label, 1, 0)
        metrics_layout.addWidget(self.daily_loss_label, 1, 1)
        metrics_layout.addWidget(self.risk_ratio_label, 2, 0)
        
        metrics_group.setLayout(metrics_layout)
        splitter.addWidget(metrics_group)
        
        # 右侧：告警信息
        alert_group = QGroupBox("告警信息")
        alert_layout = QVBoxLayout()
        
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(4)
        self.alert_table.setHorizontalHeaderLabels([
            "时间", "类型", "级别", "消息"
        ])
        self.alert_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alert_table.setAlternatingRowColors(True)
        
        alert_layout.addWidget(self.alert_table)
        alert_group.setLayout(alert_layout)
        
        splitter.addWidget(alert_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def setup_connections(self):
        """设置信号连接"""
        self.signal_bridge.risk_alert.connect(self.on_risk_alert)
    
    @pyqtSlot(str, str)
    def on_risk_alert(self, alert_type: str, message: str):
        """接收风控告警"""
        from datetime import datetime
        alert = {
            'time': datetime.now().strftime("%H:%M:%S"),
            'type': alert_type,
            'level': 'WARNING',
            'message': message
        }
        self.alerts.insert(0, alert)
        if len(self.alerts) > 100:
            self.alerts.pop()
        
        self.update_alert_table()
    
    def update_alert_table(self):
        """更新告警表格"""
        self.alert_table.setRowCount(len(self.alerts))
        
        for i, alert in enumerate(self.alerts):
            # 时间
            self.alert_table.setItem(i, 0, QTableWidgetItem(alert['time']))
            
            # 类型
            self.alert_table.setItem(i, 1, QTableWidgetItem(alert['type']))
            
            # 级别
            level_item = QTableWidgetItem(alert['level'])
            if alert['level'] == 'ERROR':
                level_item.setForeground(Qt.GlobalColor.red)
            elif alert['level'] == 'WARNING':
                level_item.setForeground(Qt.GlobalColor.yellow)
            self.alert_table.setItem(i, 2, level_item)
            
            # 消息
            self.alert_table.setItem(i, 3, QTableWidgetItem(alert['message']))

