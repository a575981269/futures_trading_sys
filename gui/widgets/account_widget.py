"""
账户信息窗口 - 资金、持仓、盈亏
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSlot
from typing import Dict, Any, List
import pyqtgraph as pg

from gui.utils.signal_bridge import SignalBridge
from backtest.portfolio import Position
from utils.logger import get_logger

logger = get_logger(__name__)


class AccountWidget(QWidget):
    """账户信息窗口"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.account_info: Dict[str, Any] = {}
        self.positions: List[Position] = []
        self.equity_history = []  # 资金曲线历史
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：账户信息
        left_panel = QGroupBox("账户信息")
        left_layout = QGridLayout()
        
        # 账户资金信息
        self.balance_label = QLabel("总资产: --")
        self.available_label = QLabel("可用资金: --")
        self.margin_label = QLabel("占用保证金: --")
        self.frozen_label = QLabel("冻结资金: --")
        self.commission_label = QLabel("手续费: --")
        self.profit_label = QLabel("持仓盈亏: --")
        
        left_layout.addWidget(self.balance_label, 0, 0)
        left_layout.addWidget(self.available_label, 0, 1)
        left_layout.addWidget(self.margin_label, 1, 0)
        left_layout.addWidget(self.frozen_label, 1, 1)
        left_layout.addWidget(self.commission_label, 2, 0)
        left_layout.addWidget(self.profit_label, 2, 1)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # 右侧：持仓明细和资金曲线
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 持仓明细
        position_group = QGroupBox("持仓明细")
        position_layout = QVBoxLayout()
        
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(7)
        self.position_table.setHorizontalHeaderLabels([
            "合约", "方向", "数量", "开仓价", "当前价", "持仓盈亏", "盈亏比例"
        ])
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.position_table.setAlternatingRowColors(True)
        
        position_layout.addWidget(self.position_table)
        position_group.setLayout(position_layout)
        right_splitter.addWidget(position_group)
        
        # 资金曲线
        equity_group = QGroupBox("资金曲线")
        equity_layout = QVBoxLayout()
        
        self.equity_chart = pg.GraphicsLayoutWidget()
        self.equity_plot = self.equity_chart.addPlot()
        self.equity_plot.setLabel('left', '资金')
        self.equity_plot.setLabel('bottom', '时间')
        self.equity_plot.showGrid(x=True, y=True, alpha=0.3)
        
        equity_layout.addWidget(self.equity_chart)
        equity_group.setLayout(equity_layout)
        right_splitter.addWidget(equity_group)
        
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)
        
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def setup_connections(self):
        """设置信号连接"""
        self.signal_bridge.account_updated.connect(self.on_account_updated)
        self.signal_bridge.position_updated.connect(self.on_position_updated)
    
    @pyqtSlot(dict)
    def on_account_updated(self, account_info: Dict[str, Any]):
        """账户更新"""
        self.account_info = account_info
        self.update_account_info()
    
    @pyqtSlot(object)
    def on_position_updated(self, position: Position):
        """持仓更新"""
        self.update_position_table()
    
    def update_account_info(self):
        """更新账户信息显示"""
        balance = self.account_info.get('balance', 0.0)
        available = self.account_info.get('available', 0.0)
        margin = self.account_info.get('margin', 0.0)
        frozen = self.account_info.get('frozen_margin', 0.0)
        commission = self.account_info.get('commission', 0.0)
        profit = self.account_info.get('profit', 0.0)
        
        self.balance_label.setText(f"总资产: {balance:,.2f}")
        self.available_label.setText(f"可用资金: {available:,.2f}")
        self.margin_label.setText(f"占用保证金: {margin:,.2f}")
        self.frozen_label.setText(f"冻结资金: {frozen:,.2f}")
        self.commission_label.setText(f"手续费: {commission:,.2f}")
        
        profit_text = f"持仓盈亏: {profit:,.2f}"
        if profit > 0:
            self.profit_label.setText(profit_text)
            self.profit_label.setStyleSheet("color: red;")
        elif profit < 0:
            self.profit_label.setText(profit_text)
            self.profit_label.setStyleSheet("color: green;")
        else:
            self.profit_label.setText(profit_text)
            self.profit_label.setStyleSheet("color: white;")
        
        # 更新资金曲线
        self.equity_history.append(balance)
        if len(self.equity_history) > 1000:
            self.equity_history.pop(0)
        
        self.update_equity_curve()
    
    def update_position_table(self):
        """更新持仓表格"""
        self.position_table.setRowCount(len(self.positions))
        
        for i, pos in enumerate(self.positions):
            # 合约
            self.position_table.setItem(i, 0, QTableWidgetItem(pos.symbol))
            
            # 方向
            direction_str = "多头" if pos.direction.value == "BUY" else "空头"
            direction_item = QTableWidgetItem(direction_str)
            if pos.direction.value == "BUY":
                direction_item.setForeground(Qt.GlobalColor.red)
            else:
                direction_item.setForeground(Qt.GlobalColor.green)
            self.position_table.setItem(i, 1, direction_item)
            
            # 数量
            self.position_table.setItem(i, 2, QTableWidgetItem(str(pos.volume)))
            
            # 开仓价
            self.position_table.setItem(i, 3, QTableWidgetItem(f"{pos.avg_price:.2f}"))
            
            # 当前价（需要从行情获取，暂时显示开仓价）
            current_price = pos.avg_price
            self.position_table.setItem(i, 4, QTableWidgetItem(f"{current_price:.2f}"))
            
            # 持仓盈亏
            pnl = (current_price - pos.avg_price) * pos.volume if pos.direction.value == "BUY" else (pos.avg_price - current_price) * pos.volume
            pnl_item = QTableWidgetItem(f"{pnl:,.2f}")
            if pnl > 0:
                pnl_item.setForeground(Qt.GlobalColor.red)
            elif pnl < 0:
                pnl_item.setForeground(Qt.GlobalColor.green)
            self.position_table.setItem(i, 5, pnl_item)
            
            # 盈亏比例
            pnl_pct = (pnl / (pos.avg_price * pos.volume) * 100) if pos.avg_price * pos.volume > 0 else 0
            pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
            if pnl_pct > 0:
                pnl_pct_item.setForeground(Qt.GlobalColor.red)
            elif pnl_pct < 0:
                pnl_pct_item.setForeground(Qt.GlobalColor.green)
            self.position_table.setItem(i, 6, pnl_pct_item)
    
    def update_equity_curve(self):
        """更新资金曲线"""
        if not self.equity_history:
            return
        
        import numpy as np
        x = np.arange(len(self.equity_history))
        y = np.array(self.equity_history)
        
        self.equity_plot.clear()
        self.equity_plot.plot(x, y, pen=pg.mkPen('cyan', width=2))


