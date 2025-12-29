"""
回测窗口 - 回测配置、结果展示
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QPushButton, QLineEdit, QComboBox, QDateEdit,
    QDoubleSpinBox, QSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import pyqtgraph as pg

from gui.utils.signal_bridge import SignalBridge
from utils.logger import get_logger

logger = get_logger(__name__)


class BacktestWidget(QWidget):
    """回测窗口"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：回测配置
        config_group = QGroupBox("回测配置")
        config_layout = QVBoxLayout()
        
        # 策略选择
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("策略:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["策略1", "策略2", "策略3"])
        strategy_layout.addWidget(self.strategy_combo)
        config_layout.addLayout(strategy_layout)
        
        # 合约代码
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("合约代码:"))
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("例如: rb2501")
        symbol_layout.addWidget(self.symbol_edit)
        config_layout.addLayout(symbol_layout)
        
        # 时间范围
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("开始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        config_layout.addLayout(date_layout)
        
        # 初始资金
        capital_layout = QHBoxLayout()
        capital_layout.addWidget(QLabel("初始资金:"))
        self.initial_capital = QDoubleSpinBox()
        self.initial_capital.setMinimum(10000)
        self.initial_capital.setMaximum(100000000)
        self.initial_capital.setValue(1000000)
        self.initial_capital.setDecimals(0)
        capital_layout.addWidget(self.initial_capital)
        config_layout.addLayout(capital_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("开始回测")
        self.run_btn.clicked.connect(self.run_backtest)
        button_layout.addWidget(self.run_btn)
        
        config_layout.addLayout(button_layout)
        config_group.setLayout(config_layout)
        splitter.addWidget(config_group)
        
        # 右侧：回测结果
        result_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 性能指标
        metrics_group = QGroupBox("性能指标")
        metrics_layout = QVBoxLayout()
        
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["指标", "数值"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.metrics_table.setAlternatingRowColors(True)
        
        metrics_layout.addWidget(self.metrics_table)
        metrics_group.setLayout(metrics_layout)
        result_splitter.addWidget(metrics_group)
        
        # 收益曲线
        curve_group = QGroupBox("收益曲线")
        curve_layout = QVBoxLayout()
        
        self.curve_chart = pg.GraphicsLayoutWidget()
        self.curve_plot = self.curve_chart.addPlot()
        self.curve_plot.setLabel('left', '资金')
        self.curve_plot.setLabel('bottom', '时间')
        self.curve_plot.showGrid(x=True, y=True, alpha=0.3)
        
        curve_layout.addWidget(self.curve_chart)
        curve_group.setLayout(curve_layout)
        result_splitter.addWidget(curve_group)
        
        result_splitter.setStretchFactor(0, 1)
        result_splitter.setStretchFactor(1, 2)
        
        splitter.addWidget(result_splitter)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def run_backtest(self):
        """运行回测"""
        logger.info("开始回测")
        # 回测逻辑将在后续集成业务逻辑时实现


