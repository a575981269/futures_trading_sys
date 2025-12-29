"""
主题样式管理
"""
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


class Theme:
    """主题样式类"""
    
    # 颜色定义
    COLOR_BUY = QColor(255, 80, 80)      # 红色（买入）
    COLOR_SELL = QColor(0, 200, 0)        # 绿色（卖出）
    COLOR_UP = QColor(255, 80, 80)       # 上涨红色
    COLOR_DOWN = QColor(0, 200, 0)       # 下跌绿色
    COLOR_BACKGROUND = QColor(30, 30, 30)  # 深色背景
    COLOR_TEXT = QColor(255, 255, 255)    # 白色文字
    COLOR_BORDER = QColor(60, 60, 60)     # 边框颜色
    
    @staticmethod
    def get_dark_style() -> str:
        """获取深色主题样式表"""
        return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: "Microsoft YaHei", "SimHei", Arial;
            font-size: 10pt;
        }
        
        QTabWidget::pane {
            border: 1px solid #3d3d3d;
            background-color: #252525;
        }
        
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 8px 16px;
            border: 1px solid #3d3d3d;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #252525;
            border-bottom: 2px solid #0078d4;
        }
        
        QTabBar::tab:hover {
            background-color: #353535;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #3d3d3d;
            color: #808080;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            padding: 4px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid #0078d4;
        }
        
        QComboBox {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            padding: 4px;
            border-radius: 3px;
        }
        
        QComboBox:hover {
            border: 1px solid #0078d4;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #ffffff;
            margin-right: 4px;
        }
        
        QTableWidget {
            background-color: #252525;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            gridline-color: #3d3d3d;
            selection-background-color: #0078d4;
        }
        
        QTableWidget::item {
            padding: 4px;
        }
        
        QTableWidget::item:selected {
            background-color: #0078d4;
        }
        
        QHeaderView::section {
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 6px;
            border: 1px solid #3d3d3d;
            font-weight: bold;
        }
        
        QMenuBar {
            background-color: #252525;
            color: #ffffff;
            border-bottom: 1px solid #3d3d3d;
        }
        
        QMenuBar::item {
            padding: 6px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #3d3d3d;
        }
        
        QMenu {
            background-color: #252525;
            color: #ffffff;
            border: 1px solid #3d3d3d;
        }
        
        QMenu::item {
            padding: 6px 24px;
        }
        
        QMenu::item:selected {
            background-color: #0078d4;
        }
        
        QToolBar {
            background-color: #252525;
            border: none;
            spacing: 4px;
        }
        
        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            padding: 4px;
            border-radius: 3px;
        }
        
        QToolButton:hover {
            background-color: #3d3d3d;
            border: 1px solid #0078d4;
        }
        
        QStatusBar {
            background-color: #252525;
            color: #ffffff;
            border-top: 1px solid #3d3d3d;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        QScrollBar:vertical {
            background-color: #252525;
            width: 12px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background-color: #3d3d3d;
            min-height: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #4d4d4d;
        }
        
        QScrollBar:horizontal {
            background-color: #252525;
            height: 12px;
            border: none;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #3d3d3d;
            min-width: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #4d4d4d;
        }
        
        QGroupBox {
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 4px;
            color: #ffffff;
        }
        """
    
    @staticmethod
    def apply_dark_theme(app: QApplication):
        """应用深色主题"""
        app.setStyleSheet(Theme.get_dark_style())
    
    @staticmethod
    def get_price_color(price_change: float) -> QColor:
        """根据价格变化获取颜色"""
        if price_change > 0:
            return Theme.COLOR_UP
        elif price_change < 0:
            return Theme.COLOR_DOWN
        else:
            return Theme.COLOR_TEXT
    
    @staticmethod
    def format_price(price: float, precision: int = 2) -> str:
        """格式化价格显示"""
        return f"{price:.{precision}f}"


