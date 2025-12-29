"""
K线图表组件 - 基于PyQtGraph
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPen, QBrush

from database.models import KlineData
from indicators.ma import MA, EMA
from utils.logger import get_logger

logger = get_logger(__name__)


class KlineChartWidget(QWidget):
    """K线图表组件"""
    
    # 信号
    symbol_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.klines: List[KlineData] = []
        self.current_symbol: str = ""
        self.indicators: Dict[str, bool] = {
            'MA5': False,
            'MA10': False,
            'MA20': False,
            'MA60': False,
            'EMA12': False,
            'EMA26': False,
        }
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("指标:"))
        
        # 指标选择
        self.ma5_btn = QPushButton("MA5")
        self.ma5_btn.setCheckable(True)
        self.ma5_btn.clicked.connect(lambda: self.toggle_indicator('MA5'))
        toolbar.addWidget(self.ma5_btn)
        
        self.ma10_btn = QPushButton("MA10")
        self.ma10_btn.setCheckable(True)
        self.ma10_btn.clicked.connect(lambda: self.toggle_indicator('MA10'))
        toolbar.addWidget(self.ma10_btn)
        
        self.ma20_btn = QPushButton("MA20")
        self.ma20_btn.setCheckable(True)
        self.ma20_btn.clicked.connect(lambda: self.toggle_indicator('MA20'))
        toolbar.addWidget(self.ma20_btn)
        
        self.ma60_btn = QPushButton("MA60")
        self.ma60_btn.setCheckable(True)
        self.ma60_btn.clicked.connect(lambda: self.toggle_indicator('MA60'))
        toolbar.addWidget(self.ma60_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 图表区域
        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_widget.setBackground('black')
        layout.addWidget(self.graphics_widget)
        
        # 创建K线图
        self.kline_plot = self.graphics_widget.addPlot(row=0, col=0)
        self.kline_plot.setLabel('left', '价格')
        self.kline_plot.setLabel('bottom', '时间')
        self.kline_plot.showGrid(x=True, y=True, alpha=0.3)
        self.kline_plot.setMouseEnabled(x=True, y=True)
        
        # 创建成交量图
        self.volume_plot = self.graphics_widget.addPlot(row=1, col=0)
        self.volume_plot.setLabel('left', '成交量')
        self.volume_plot.setLabel('bottom', '时间')
        self.volume_plot.showGrid(x=True, y=True, alpha=0.3)
        self.volume_plot.setMouseEnabled(x=True, y=True)
        self.volume_plot.setXLink(self.kline_plot)
        
        # 存储绘图项
        self.kline_items = []
        self.volume_items = []
        self.indicator_items = []
        
        # 十字光标
        self.crosshair_v = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('white', width=1, style=Qt.PenStyle.DashLine))
        self.crosshair_h = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('white', width=1, style=Qt.PenStyle.DashLine))
        self.kline_plot.addItem(self.crosshair_v, ignoreBounds=True)
        self.kline_plot.addItem(self.crosshair_h, ignoreBounds=True)
        self.crosshair_v.setVisible(False)
        self.crosshair_h.setVisible(False)
        
        # 鼠标跟踪 - 使用proxy对象来捕获鼠标事件
        self._mouse_in_plot = False
        self.kline_plot.scene().sigMouseMoved.connect(self.on_mouse_moved)
        
        # 使用定时器来检测鼠标是否在图表区域内
        from PyQt6.QtCore import QTimer
        self._mouse_timer = QTimer()
        self._mouse_timer.timeout.connect(self._check_mouse_position)
        self._mouse_timer.start(100)  # 每100ms检查一次
    
    def toggle_indicator(self, indicator_name: str):
        """切换指标显示"""
        self.indicators[indicator_name] = not self.indicators[indicator_name]
        self.update_chart()
    
    def set_crosshair_visible(self, visible: bool):
        """设置十字光标可见性"""
        self.crosshair_v.setVisible(visible)
        self.crosshair_h.setVisible(visible)
    
    def on_mouse_moved(self, pos):
        """鼠标移动事件"""
        if self.kline_plot.sceneBoundingRect().contains(pos):
            if not self._mouse_in_plot:
                self._mouse_in_plot = True
                self.set_crosshair_visible(True)
            mouse_point = self.kline_plot.vb.mapSceneToView(pos)
            self.crosshair_v.setPos(mouse_point.x())
            self.crosshair_h.setPos(mouse_point.y())
        else:
            if self._mouse_in_plot:
                self._mouse_in_plot = False
                self.set_crosshair_visible(False)
    
    def _check_mouse_position(self):
        """检查鼠标位置（备用方法）"""
        # 这个方法作为备用，如果sigMouseMoved不工作
        pass
    
    def update_data(self, klines: List[KlineData], symbol: str = ""):
        """更新K线数据"""
        if not klines:
            return
        
        self.klines = klines
        if symbol:
            self.current_symbol = symbol
        
        self.update_chart()
    
    def add_kline(self, kline: KlineData):
        """添加单根K线"""
        self.klines.append(kline)
        self.update_chart()
    
    def update_chart(self):
        """更新图表"""
        if not self.klines:
            return
        
        # 清除旧数据
        for item in self.kline_items:
            self.kline_plot.removeItem(item)
        for item in self.volume_items:
            self.volume_plot.removeItem(item)
        for item in self.indicator_items:
            self.kline_plot.removeItem(item)
        
        self.kline_items.clear()
        self.volume_items.clear()
        self.indicator_items.clear()
        
        # 准备数据
        n = len(self.klines)
        if n == 0:
            return
        
        # 时间轴（使用索引）
        x = np.arange(n)
        
        # K线数据
        opens = np.array([k.open for k in self.klines])
        highs = np.array([k.high for k in self.klines])
        lows = np.array([k.low for k in self.klines])
        closes = np.array([k.close for k in self.klines])
        volumes = np.array([k.volume for k in self.klines])
        
        # 绘制K线
        for i in range(n):
            open_price = opens[i]
            high_price = highs[i]
            low_price = lows[i]
            close_price = closes[i]
            
            # 判断涨跌
            is_up = close_price >= open_price
            color = QColor(255, 80, 80) if is_up else QColor(0, 200, 0)  # 红涨绿跌
            
            # 绘制实体
            body_top = max(open_price, close_price)
            body_bottom = min(open_price, close_price)
            body_height = body_top - body_bottom if body_top != body_bottom else 0.01
            
            # 实体矩形
            rect = QGraphicsRectItem(
                i - 0.3, body_bottom, 0.6, body_height
            )
            rect.setPen(pg.mkPen(color, width=1))
            rect.setBrush(pg.mkBrush(color))
            self.kline_plot.addItem(rect)
            self.kline_items.append(rect)
            
            # 上影线
            if high_price > body_top:
                line = pg.PlotDataItem(
                    [i, i], [body_top, high_price],
                    pen=pg.mkPen(color, width=1)
                )
                self.kline_plot.addItem(line)
                self.kline_items.append(line)
            
            # 下影线
            if low_price < body_bottom:
                line = pg.PlotDataItem(
                    [i, i], [low_price, body_bottom],
                    pen=pg.mkPen(color, width=1)
                )
                self.kline_plot.addItem(line)
                self.kline_items.append(line)
        
        # 绘制技术指标
        closes_list = closes.tolist()
        
        if self.indicators['MA5']:
            ma5_values = MA(closes_list, 5)
            ma5_array = np.array([v if v is not None else np.nan for v in ma5_values])
            ma5_line = pg.PlotDataItem(x, ma5_array, pen=pg.mkPen('yellow', width=1), name='MA5')
            self.kline_plot.addItem(ma5_line)
            self.indicator_items.append(ma5_line)
        
        if self.indicators['MA10']:
            ma10_values = MA(closes_list, 10)
            ma10_array = np.array([v if v is not None else np.nan for v in ma10_values])
            ma10_line = pg.PlotDataItem(x, ma10_array, pen=pg.mkPen('cyan', width=1), name='MA10')
            self.kline_plot.addItem(ma10_line)
            self.indicator_items.append(ma10_line)
        
        if self.indicators['MA20']:
            ma20_values = MA(closes_list, 20)
            ma20_array = np.array([v if v is not None else np.nan for v in ma20_values])
            ma20_line = pg.PlotDataItem(x, ma20_array, pen=pg.mkPen('magenta', width=1), name='MA20')
            self.kline_plot.addItem(ma20_line)
            self.indicator_items.append(ma20_line)
        
        if self.indicators['MA60']:
            ma60_values = MA(closes_list, 60)
            ma60_array = np.array([v if v is not None else np.nan for v in ma60_values])
            ma60_line = pg.PlotDataItem(x, ma60_array, pen=pg.mkPen('orange', width=1), name='MA60')
            self.kline_plot.addItem(ma60_line)
            self.indicator_items.append(ma60_line)
        
        # 绘制成交量
        volume_colors = [QColor(255, 80, 80) if closes[i] >= opens[i] else QColor(0, 200, 0) for i in range(n)]
        volume_bars = pg.BarGraphItem(x=x, height=volumes, width=0.8, brushes=volume_colors)
        self.volume_plot.addItem(volume_bars)
        self.volume_items.append(volume_bars)
        
        # 自动调整范围
        if n > 0:
            price_min = min(lows)
            price_max = max(highs)
            price_range = price_max - price_min
            self.kline_plot.setYRange(price_min - price_range * 0.1, price_max + price_range * 0.1)
            
            volume_max = max(volumes) if len(volumes) > 0 else 1
            self.volume_plot.setYRange(0, volume_max * 1.1)
            
            self.kline_plot.setXRange(0, max(n - 1, 0))
            self.volume_plot.setXRange(0, max(n - 1, 0))
    
    def clear(self):
        """清除图表"""
        self.klines.clear()
        for item in self.kline_items:
            self.kline_plot.removeItem(item)
        for item in self.volume_items:
            self.volume_plot.removeItem(item)
        for item in self.indicator_items:
            self.kline_plot.removeItem(item)
        self.kline_items.clear()
        self.volume_items.clear()
        self.indicator_items.clear()

