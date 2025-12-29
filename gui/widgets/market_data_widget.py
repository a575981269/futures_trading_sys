"""
行情显示窗口 - K线图和Tick数据
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from typing import List, Optional
from datetime import datetime

from gui.utils.signal_bridge import SignalBridge
from gui.charts.kline_chart import KlineChartWidget
from database.models import TickData, KlineData
from utils.logger import get_logger

logger = get_logger(__name__)


class MarketDataWidget(QWidget):
    """行情显示窗口"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.main_window = parent  # 保存主窗口引用
        self.current_symbol: str = ""
        self.tick_data: List[TickData] = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("合约代码:"))
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("例如: rb2501")
        self.symbol_edit.returnPressed.connect(self.on_subscribe)
        toolbar.addWidget(self.symbol_edit)
        
        self.subscribe_btn = QPushButton("订阅")
        self.subscribe_btn.clicked.connect(self.on_subscribe)
        toolbar.addWidget(self.subscribe_btn)
        
        self.unsubscribe_btn = QPushButton("取消订阅")
        self.unsubscribe_btn.clicked.connect(self.on_unsubscribe)
        toolbar.addWidget(self.unsubscribe_btn)
        
        toolbar.addStretch()
        
        # K线周期选择
        toolbar.addWidget(QLabel("周期:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1m", "5m", "15m", "30m", "1h", "1d"])
        self.interval_combo.setCurrentText("1m")
        toolbar.addWidget(self.interval_combo)
        
        layout.addLayout(toolbar)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # K线图
        self.kline_chart = KlineChartWidget()
        splitter.addWidget(self.kline_chart)
        
        # Tick数据表格
        tick_group = QGroupBox("实时Tick数据")
        tick_layout = QVBoxLayout()
        
        self.tick_table = QTableWidget()
        self.tick_table.setColumnCount(8)
        self.tick_table.setHorizontalHeaderLabels([
            "时间", "最新价", "涨跌", "涨跌幅", "成交量", "买一价", "卖一价", "持仓量"
        ])
        self.tick_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tick_table.setAlternatingRowColors(True)
        self.tick_table.setMaximumHeight(200)
        
        tick_layout.addWidget(self.tick_table)
        tick_group.setLayout(tick_layout)
        splitter.addWidget(tick_group)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
    
    def setup_connections(self):
        """设置信号连接"""
        self.signal_bridge.tick_received.connect(self.on_tick_received)
        self.signal_bridge.bar_received.connect(self.on_bar_received)
    
    @pyqtSlot(object)
    def on_tick_received(self, tick: TickData):
        """接收Tick数据"""
        if not tick or tick.symbol != self.current_symbol:
            return
        
        # 添加到列表（保留最近100条）
        self.tick_data.insert(0, tick)
        if len(self.tick_data) > 100:
            self.tick_data.pop()
        
        # 更新表格
        self.update_tick_table()
    
    @pyqtSlot(object)
    def on_bar_received(self, bar: KlineData):
        """接收K线数据"""
        if not bar or bar.symbol != self.current_symbol:
            return
        
        # 更新K线图
        self.kline_chart.add_kline(bar)
    
    def on_subscribe(self):
        """订阅合约"""
        symbol = self.symbol_edit.text().strip().upper()
        if not symbol:
            return
        
        self.current_symbol = symbol
        self.kline_chart.current_symbol = symbol
        self.tick_data.clear()
        self.tick_table.setRowCount(0)
        self.kline_chart.clear()
        
        # 通过主窗口获取business_logic并订阅
        logger.info(f"订阅合约: {symbol}")
        try:
            if self.main_window and hasattr(self.main_window, 'business_logic'):
                success = self.main_window.business_logic.subscribe_symbol(symbol)
                if success:
                    logger.info(f"订阅成功: {symbol}")
                else:
                    logger.error(f"订阅失败: {symbol}")
            else:
                logger.warning("无法找到business_logic，订阅请求未发送")
        except Exception as e:
            logger.error(f"订阅时出错: {e}", exc_info=True)
    
    def on_unsubscribe(self):
        """取消订阅"""
        if self.current_symbol:
            logger.info(f"取消订阅合约: {self.current_symbol}")
            self.current_symbol = ""
            self.tick_data.clear()
            self.tick_table.setRowCount(0)
            self.kline_chart.clear()
    
    def update_tick_table(self):
        """更新Tick数据表格"""
        if not self.tick_data:
            return
        
        # 只显示最新的20条
        display_count = min(20, len(self.tick_data))
        self.tick_table.setRowCount(display_count)
        
        for i, tick in enumerate(self.tick_data[:display_count]):
            # 时间
            time_str = tick.datetime.strftime("%H:%M:%S") if tick.datetime else ""
            self.tick_table.setItem(i, 0, QTableWidgetItem(time_str))
            
            # 最新价
            price_item = QTableWidgetItem(f"{tick.last_price:.2f}")
            self.tick_table.setItem(i, 1, price_item)
            
            # 涨跌（需要与上一个价格比较）
            if i < len(self.tick_data) - 1:
                prev_tick = self.tick_data[i + 1]
                price_change = tick.last_price - prev_tick.last_price
                price_change_pct = (price_change / prev_tick.last_price * 100) if prev_tick.last_price > 0 else 0
            else:
                price_change = 0
                price_change_pct = 0
            
            # 涨跌
            change_item = QTableWidgetItem(f"{price_change:+.2f}")
            if price_change > 0:
                change_item.setForeground(Qt.GlobalColor.red)
            elif price_change < 0:
                change_item.setForeground(Qt.GlobalColor.green)
            self.tick_table.setItem(i, 2, change_item)
            
            # 涨跌幅
            change_pct_item = QTableWidgetItem(f"{price_change_pct:+.2f}%")
            if price_change_pct > 0:
                change_pct_item.setForeground(Qt.GlobalColor.red)
            elif price_change_pct < 0:
                change_pct_item.setForeground(Qt.GlobalColor.green)
            self.tick_table.setItem(i, 3, change_pct_item)
            
            # 成交量
            self.tick_table.setItem(i, 4, QTableWidgetItem(str(tick.volume)))
            
            # 买一价
            bid_price = tick.bid_price1 if tick.bid_price1 else 0
            self.tick_table.setItem(i, 5, QTableWidgetItem(f"{bid_price:.2f}"))
            
            # 卖一价
            ask_price = tick.ask_price1 if tick.ask_price1 else 0
            self.tick_table.setItem(i, 6, QTableWidgetItem(f"{ask_price:.2f}"))
            
            # 持仓量
            self.tick_table.setItem(i, 7, QTableWidgetItem(str(tick.open_interest)))
        
        # 自动滚动到顶部
        self.tick_table.scrollToTop()

