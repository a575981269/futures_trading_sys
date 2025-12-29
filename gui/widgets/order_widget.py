"""
订单管理窗口 - 订单列表、成交记录
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from typing import List

from gui.utils.signal_bridge import SignalBridge
from trading.order import Order, OrderDirection
from utils.logger import get_logger

logger = get_logger(__name__)


class OrderWidget(QWidget):
    """订单管理窗口"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.orders: List[Order] = []
        self.trades: List[Dict] = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("状态筛选:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "已提交", "部分成交", "全部成交", "已撤销", "已拒绝"])
        self.status_filter.currentTextChanged.connect(self.filter_orders)
        toolbar.addWidget(self.status_filter)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 订单列表
        order_group = QGroupBox("订单列表")
        order_layout = QVBoxLayout()
        
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(8)
        self.order_table.setHorizontalHeaderLabels([
            "订单号", "合约", "方向", "价格", "数量", "已成交", "状态", "时间"
        ])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_table.setAlternatingRowColors(True)
        
        order_layout.addWidget(self.order_table)
        order_group.setLayout(order_layout)
        splitter.addWidget(order_group)
        
        # 成交记录
        trade_group = QGroupBox("成交记录")
        trade_layout = QVBoxLayout()
        
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(7)
        self.trade_table.setHorizontalHeaderLabels([
            "成交号", "订单号", "合约", "方向", "价格", "数量", "时间"
        ])
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trade_table.setAlternatingRowColors(True)
        
        trade_layout.addWidget(self.trade_table)
        trade_group.setLayout(trade_layout)
        splitter.addWidget(trade_group)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
    
    def setup_connections(self):
        """设置信号连接"""
        self.signal_bridge.order_updated.connect(self.on_order_updated)
    
    @pyqtSlot(object)
    def on_order_updated(self, order: Order):
        """订单更新"""
        self.update_order_table()
    
    def filter_orders(self):
        """筛选订单"""
        self.update_order_table()
    
    def update_order_table(self):
        """更新订单表格"""
        filter_text = self.status_filter.currentText()
        
        if filter_text == "全部":
            filtered_orders = self.orders
        else:
            status_map = {
                "已提交": "SUBMITTED",
                "部分成交": "PARTIAL",
                "全部成交": "FILLED",
                "已撤销": "CANCELLED",
                "已拒绝": "REJECTED"
            }
            target_status = status_map.get(filter_text, "")
            filtered_orders = [o for o in self.orders if o.status.value == target_status]
        
        self.order_table.setRowCount(len(filtered_orders))
        
        for i, order in enumerate(filtered_orders):
            # 订单号
            self.order_table.setItem(i, 0, QTableWidgetItem(order.order_id or ""))
            
            # 合约
            self.order_table.setItem(i, 1, QTableWidgetItem(order.symbol))
            
            # 方向
            direction_str = "买入" if order.direction == OrderDirection.BUY else "卖出"
            direction_item = QTableWidgetItem(direction_str)
            if order.direction == OrderDirection.BUY:
                direction_item.setForeground(Qt.GlobalColor.red)
            else:
                direction_item.setForeground(Qt.GlobalColor.green)
            self.order_table.setItem(i, 2, direction_item)
            
            # 价格
            self.order_table.setItem(i, 3, QTableWidgetItem(f"{order.price:.2f}"))
            
            # 数量
            self.order_table.setItem(i, 4, QTableWidgetItem(str(order.volume)))
            
            # 已成交
            self.order_table.setItem(i, 5, QTableWidgetItem(str(order.filled_volume)))
            
            # 状态
            status_str = order.status.value if hasattr(order.status, 'value') else str(order.status)
            self.order_table.setItem(i, 6, QTableWidgetItem(status_str))
            
            # 时间
            time_str = order.submit_time.strftime("%H:%M:%S") if order.submit_time else ""
            self.order_table.setItem(i, 7, QTableWidgetItem(time_str))
    
    def update_trade_table(self):
        """更新成交记录表格"""
        self.trade_table.setRowCount(len(self.trades))
        
        for i, trade in enumerate(self.trades):
            # 成交号
            self.trade_table.setItem(i, 0, QTableWidgetItem(trade.get('trade_id', '')))
            
            # 订单号
            self.trade_table.setItem(i, 1, QTableWidgetItem(trade.get('order_id', '')))
            
            # 合约
            self.trade_table.setItem(i, 2, QTableWidgetItem(trade.get('symbol', '')))
            
            # 方向
            direction_str = trade.get('direction', '')
            direction_item = QTableWidgetItem(direction_str)
            if direction_str == "买入":
                direction_item.setForeground(Qt.GlobalColor.red)
            else:
                direction_item.setForeground(Qt.GlobalColor.green)
            self.trade_table.setItem(i, 3, direction_item)
            
            # 价格
            self.trade_table.setItem(i, 4, QTableWidgetItem(f"{trade.get('price', 0):.2f}"))
            
            # 数量
            self.trade_table.setItem(i, 5, QTableWidgetItem(str(trade.get('volume', 0))))
            
            # 时间
            self.trade_table.setItem(i, 6, QTableWidgetItem(trade.get('time', '')))

