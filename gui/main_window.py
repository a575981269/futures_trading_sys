"""
主窗口 - 期货交易系统GUI主界面
"""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QIcon
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Thread

from gui.utils.signal_bridge import SignalBridge
from gui.utils.theme import Theme
from gui.business_logic import BusinessLogicManager
from utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.signal_bridge = SignalBridge()
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_timer()
        
        # 业务逻辑组件（将在后续集成）
        self.market_data_widget = None
        self.trading_widget = None
        self.account_widget = None
        self.strategy_widget = None
        self.backtest_widget = None
        self.risk_widget = None
        self.order_widget = None
        self.log_widget = None
        self.connection_widget = None
        
        # 业务逻辑管理器
        self.business_logic = BusinessLogicManager(self.signal_bridge)
        
        # 连接信号
        self.signal_bridge.connection_status_changed.connect(self.update_connection_status)
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("期货量化交易系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # 应用主题
        Theme.apply_dark_theme(self)
        
        # 创建中心部件 - 使用标签页布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        layout.addWidget(self.tab_widget)
    
    def setup_menus(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        connect_action = QAction("连接CTP(&C)", self)
        connect_action.setShortcut("Ctrl+C")
        connect_action.triggered.connect(self.show_connection_dialog)
        file_menu.addAction(connect_action)
        
        disconnect_action = QAction("断开连接(&D)", self)
        disconnect_action.setShortcut("Ctrl+D")
        disconnect_action.triggered.connect(self.disconnect_ctp)
        file_menu.addAction(disconnect_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        market_data_action = QAction("行情(&M)", self)
        market_data_action.setShortcut("Ctrl+M")
        market_data_action.triggered.connect(self.show_market_data)
        view_menu.addAction(market_data_action)
        
        trading_action = QAction("交易(&T)", self)
        trading_action.setShortcut("Ctrl+T")
        trading_action.triggered.connect(self.show_trading)
        view_menu.addAction(trading_action)
        
        account_action = QAction("账户(&A)", self)
        account_action.setShortcut("Ctrl+A")
        account_action.triggered.connect(self.show_account)
        view_menu.addAction(account_action)
        
        strategy_action = QAction("策略(&S)", self)
        strategy_action.setShortcut("Ctrl+S")
        strategy_action.triggered.connect(self.show_strategy)
        view_menu.addAction(strategy_action)
        
        backtest_action = QAction("回测(&B)", self)
        backtest_action.setShortcut("Ctrl+B")
        backtest_action.triggered.connect(self.show_backtest)
        view_menu.addAction(backtest_action)
        
        risk_action = QAction("风控(&R)", self)
        risk_action.setShortcut("Ctrl+R")
        risk_action.triggered.connect(self.show_risk)
        view_menu.addAction(risk_action)
        
        order_action = QAction("订单(&O)", self)
        order_action.setShortcut("Ctrl+O")
        order_action.triggered.connect(self.show_order)
        view_menu.addAction(order_action)
        
        log_action = QAction("日志(&L)", self)
        log_action.setShortcut("Ctrl+L")
        log_action.triggered.connect(self.show_log)
        view_menu.addAction(log_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        settings_action = QAction("设置(&S)", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 连接按钮
        connect_btn = QAction("连接", self)
        connect_btn.triggered.connect(self.show_connection_dialog)
        toolbar.addAction(connect_btn)
        
        toolbar.addSeparator()
        
        # 行情按钮
        market_btn = QAction("行情", self)
        market_btn.triggered.connect(self.show_market_data)
        toolbar.addAction(market_btn)
        
        # 交易按钮
        trading_btn = QAction("交易", self)
        trading_btn.triggered.connect(self.show_trading)
        toolbar.addAction(trading_btn)
        
        # 账户按钮
        account_btn = QAction("账户", self)
        account_btn.triggered.connect(self.show_account)
        toolbar.addAction(account_btn)
    
    def setup_statusbar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 连接状态标签
        self.connection_label = QLabel("未连接")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_bar.addWidget(self.connection_label)
        
        self.status_bar.addPermanentWidget(QLabel("|"))
        
        # 账户信息标签
        self.account_label = QLabel("账户: --")
        self.status_bar.addPermanentWidget(self.account_label)
        
        self.status_bar.addPermanentWidget(QLabel("|"))
        
        # 时间标签
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
    
    def setup_timer(self):
        """设置定时器"""
        # 更新时间
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新
        self.update_time()
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
    
    def show_connection_dialog(self):
        """显示连接配置对话框"""
        if self.connection_widget is None:
            from gui.widgets.connection_widget import ConnectionWidget
            self.connection_widget = ConnectionWidget(self.signal_bridge, self)
            self.connection_widget.connection_requested.connect(self.on_connection_requested)
        self.connection_widget.show()
    
    def on_connection_requested(self, connection_params: Dict[str, Any]):
        """处理连接请求"""
        # 在后台线程中连接
        def connect_thread():
            success = self.business_logic.connect_ctp(connection_params)
            if success:
                logger.info("CTP连接成功")
            else:
                logger.error("CTP连接失败")
        
        thread = Thread(target=connect_thread, daemon=True)
        thread.start()
    
    def disconnect_ctp(self):
        """断开CTP连接"""
        if self.business_logic.is_connected:
            self.business_logic.disconnect_ctp()
        else:
            QMessageBox.information(self, "提示", "当前未连接")
    
    def show_market_data(self):
        """显示行情窗口"""
        if self.market_data_widget is None:
            from gui.widgets.market_data_widget import MarketDataWidget
            self.market_data_widget = MarketDataWidget(self.signal_bridge, self)
            self.tab_widget.addTab(self.market_data_widget, "行情")
        self.tab_widget.setCurrentWidget(self.market_data_widget)
    
    def show_trading(self):
        """显示交易窗口"""
        if self.trading_widget is None:
            from gui.widgets.trading_widget import TradingWidget
            self.trading_widget = TradingWidget(self.signal_bridge)
            self.tab_widget.addTab(self.trading_widget, "交易")
        self.tab_widget.setCurrentWidget(self.trading_widget)
    
    def show_account(self):
        """显示账户窗口"""
        if self.account_widget is None:
            from gui.widgets.account_widget import AccountWidget
            self.account_widget = AccountWidget(self.signal_bridge)
            self.tab_widget.addTab(self.account_widget, "账户")
        self.tab_widget.setCurrentWidget(self.account_widget)
    
    def show_strategy(self):
        """显示策略窗口"""
        if self.strategy_widget is None:
            from gui.widgets.strategy_widget import StrategyWidget
            self.strategy_widget = StrategyWidget(self.signal_bridge)
            self.tab_widget.addTab(self.strategy_widget, "策略")
        self.tab_widget.setCurrentWidget(self.strategy_widget)
    
    def show_backtest(self):
        """显示回测窗口"""
        if self.backtest_widget is None:
            from gui.widgets.backtest_widget import BacktestWidget
            self.backtest_widget = BacktestWidget(self.signal_bridge)
            self.tab_widget.addTab(self.backtest_widget, "回测")
        self.tab_widget.setCurrentWidget(self.backtest_widget)
    
    def show_risk(self):
        """显示风控窗口"""
        if self.risk_widget is None:
            from gui.widgets.risk_widget import RiskWidget
            self.risk_widget = RiskWidget(self.signal_bridge)
            self.tab_widget.addTab(self.risk_widget, "风控")
        self.tab_widget.setCurrentWidget(self.risk_widget)
    
    def show_order(self):
        """显示订单窗口"""
        if self.order_widget is None:
            from gui.widgets.order_widget import OrderWidget
            self.order_widget = OrderWidget(self.signal_bridge)
            self.tab_widget.addTab(self.order_widget, "订单")
        self.tab_widget.setCurrentWidget(self.order_widget)
    
    def show_log(self):
        """显示日志窗口"""
        if self.log_widget is None:
            from gui.widgets.log_widget import LogWidget
            self.log_widget = LogWidget(self.signal_bridge)
            self.tab_widget.addTab(self.log_widget, "日志")
        self.tab_widget.setCurrentWidget(self.log_widget)
    
    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "提示", "设置功能将在后续实现")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "期货量化交易系统\n\n"
            "版本: 1.0.0\n"
            "基于CTP接口的期货量化交易系统\n"
            "支持实时行情、策略回测、实盘交易"
        )
    
    @pyqtSlot(bool, str)
    def update_connection_status(self, connected: bool, message: str = ""):
        """更新连接状态"""
        if connected:
            self.connection_label.setText("已连接")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_label.setText("未连接")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        
        if message:
            self.status_bar.showMessage(message, 3000)
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 断开连接等清理工作
            event.accept()
        else:
            event.ignore()

