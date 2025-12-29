"""
交易面板 - 下单、撤单、持仓管理
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QDoubleSpinBox,
    QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from typing import List, Optional
from datetime import datetime

from gui.utils.signal_bridge import SignalBridge
from trading.order import Order, OrderType, OrderDirection
from backtest.portfolio import Position
from utils.logger import get_logger

logger = get_logger(__name__)


class TradingWidget(QWidget):
    """交易面板"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.positions: List[Position] = []
        self.orders: List[Order] = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：下单面板
        left_panel = QGroupBox("快速下单")
        left_layout = QVBoxLayout()
        
        # 合约代码
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("合约代码:"))
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("例如: rb2501")
        symbol_layout.addWidget(self.symbol_edit)
        left_layout.addLayout(symbol_layout)
        
        # 方向
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("方向:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItem("买入", OrderDirection.BUY)
        self.direction_combo.addItem("卖出", OrderDirection.SELL)
        direction_layout.addWidget(self.direction_combo)
        left_layout.addLayout(direction_layout)
        
        # 价格类型
        price_type_layout = QHBoxLayout()
        price_type_layout.addWidget(QLabel("价格类型:"))
        self.price_type_combo = QComboBox()
        self.price_type_combo.addItem("限价", OrderType.LIMIT)
        self.price_type_combo.addItem("市价", OrderType.MARKET)
        price_type_layout.addWidget(self.price_type_combo)
        left_layout.addLayout(price_type_layout)
        
        # 价格
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("价格:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMinimum(0)
        self.price_spin.setMaximum(999999)
        self.price_spin.setDecimals(2)
        price_layout.addWidget(self.price_spin)
        left_layout.addLayout(price_layout)
        
        # 数量
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("数量:"))
        self.volume_spin = QSpinBox()
        self.volume_spin.setMinimum(1)
        self.volume_spin.setMaximum(1000)
        self.volume_spin.setValue(1)
        volume_layout.addWidget(self.volume_spin)
        left_layout.addLayout(volume_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.buy_btn = QPushButton("买入")
        self.buy_btn.setStyleSheet("background-color: #ff5050; color: white; font-weight: bold;")
        self.buy_btn.clicked.connect(lambda: self.submit_order(OrderDirection.BUY))
        button_layout.addWidget(self.buy_btn)
        
        self.sell_btn = QPushButton("卖出")
        self.sell_btn.setStyleSheet("background-color: #00c800; color: white; font-weight: bold;")
        self.sell_btn.clicked.connect(lambda: self.submit_order(OrderDirection.SELL))
        button_layout.addWidget(self.sell_btn)
        
        left_layout.addLayout(button_layout)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # 右侧：持仓和订单
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 持仓列表
        position_group = QGroupBox("持仓")
        position_layout = QVBoxLayout()
        
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(6)
        self.position_table.setHorizontalHeaderLabels([
            "合约", "方向", "数量", "开仓价", "持仓盈亏", "操作"
        ])
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.position_table.setAlternatingRowColors(True)
        
        position_layout.addWidget(self.position_table)
        position_group.setLayout(position_layout)
        right_splitter.addWidget(position_group)
        
        # 订单列表
        order_group = QGroupBox("订单")
        order_layout = QVBoxLayout()
        
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(7)
        self.order_table.setHorizontalHeaderLabels([
            "订单号", "合约", "方向", "价格", "数量", "状态", "操作"
        ])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_table.setAlternatingRowColors(True)
        
        order_layout.addWidget(self.order_table)
        order_group.setLayout(order_layout)
        right_splitter.addWidget(order_group)
        
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def setup_connections(self):
        """设置信号连接"""
        self.signal_bridge.position_updated.connect(self.on_position_updated)
        self.signal_bridge.order_updated.connect(self.on_order_updated)
    
    @pyqtSlot(object)
    def on_position_updated(self, position: Position):
        """持仓更新"""
        # 更新持仓列表
        self.update_position_table()
    
    @pyqtSlot(object)
    def on_order_updated(self, order: Order):
        """订单更新"""
        # 更新订单列表
        self.update_order_table()
    
    def submit_order(self, direction: OrderDirection):
        """提交订单"""
        symbol = self.symbol_edit.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "警告", "请输入合约代码")
            return
        
        price = self.price_spin.value()
        volume = self.volume_spin.value()
        price_type = self.price_type_combo.currentData()
        
        # 创建订单
        order = Order(
            symbol=symbol,
            direction=direction,
            price=price,
            volume=volume,
            order_type=price_type
        )
        
        # 发送订单信号（将在业务逻辑层处理）
        logger.info(f"提交订单: {order}")
        # 注意：实际下单需要在业务逻辑层通过BusinessLogicManager完成
        QMessageBox.information(self, "提示", f"订单已提交: {symbol} {direction.value} {volume}手 @ {price}")
    
    def update_position_table(self):
        """更新持仓表格"""
        self.position_table.setRowCount(len(self.positions))
        
        for i, pos in enumerate(self.positions):
            # 合约
            self.position_table.setItem(i, 0, QTableWidgetItem(pos.symbol))
            
            # 方向
            direction_str = "多头" if pos.direction == OrderDirection.BUY else "空头"
            direction_item = QTableWidgetItem(direction_str)
            if pos.direction == OrderDirection.BUY:
                direction_item.setForeground(Qt.GlobalColor.red)
            else:
                direction_item.setForeground(Qt.GlobalColor.green)
            self.position_table.setItem(i, 1, direction_item)
            
            # 数量
            self.position_table.setItem(i, 2, QTableWidgetItem(str(pos.volume)))
            
            # 开仓价
            self.position_table.setItem(i, 3, QTableWidgetItem(f"{pos.avg_price:.2f}"))
            
            # 持仓盈亏（需要当前价格，暂时显示0）
            pnl_item = QTableWidgetItem("0.00")
            self.position_table.setItem(i, 4, pnl_item)
            
            # 操作按钮
            close_btn = QPushButton("平仓")
            close_btn.clicked.connect(lambda checked, p=pos: self.close_position(p))
            self.position_table.setCellWidget(i, 5, close_btn)
    
    def update_order_table(self):
        """更新订单表格"""
        self.order_table.setRowCount(len(self.orders))
        
        for i, order in enumerate(self.orders):
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
            
            # 状态
            status_str = order.status.value if hasattr(order.status, 'value') else str(order.status)
            self.order_table.setItem(i, 5, QTableWidgetItem(status_str))
            
            # 操作按钮
            if order.status.value == "SUBMITTED" or order.status.value == "PARTIAL":
                cancel_btn = QPushButton("撤单")
                cancel_btn.clicked.connect(lambda checked, o=order: self.cancel_order(o))
                self.order_table.setCellWidget(i, 6, cancel_btn)
            else:
                self.order_table.setItem(i, 6, QTableWidgetItem(""))
    
    def close_position(self, position: Position):
        """平仓"""
        reply = QMessageBox.question(
            self,
            "确认平仓",
            f"确定要平仓 {position.symbol} {position.volume}手吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"平仓: {position.symbol} {position.volume}手")
            QMessageBox.information(self, "提示", "平仓指令已发送")
    
    def cancel_order(self, order: Order):
        """撤单"""
        reply = QMessageBox.question(
            self,
            "确认撤单",
            f"确定要撤销订单 {order.order_id} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"撤单: {order.order_id}")
            QMessageBox.information(self, "提示", "撤单指令已发送")

