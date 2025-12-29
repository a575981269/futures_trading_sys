"""
日志查看窗口 - 系统日志、交易日志
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPlainTextEdit, QComboBox, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from datetime import datetime

from gui.utils.signal_bridge import SignalBridge
from utils.logger import get_logger

logger = get_logger(__name__)


class LogWidget(QWidget):
    """日志查看窗口"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.log_buffer = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("日志级别:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_filter.currentTextChanged.connect(self.filter_logs)
        toolbar.addWidget(self.level_filter)
        
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.clear_logs)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 日志显示
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        layout.addWidget(log_group)
    
    def setup_connections(self):
        """设置信号连接"""
        self.signal_bridge.log_received.connect(self.on_log_received)
    
    @pyqtSlot(str, int)
    def on_log_received(self, message: str, level: int):
        """接收日志"""
        level_names = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR"}
        level_name = level_names.get(level, "INFO")
        
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] [{level_name}] {message}"
        self.log_buffer.append((level_name, log_entry))
        
        if len(self.log_buffer) > 1000:
            self.log_buffer.pop(0)
        
        self.update_log_display()
    
    def filter_logs(self):
        """筛选日志"""
        self.update_log_display()
    
    def update_log_display(self):
        """更新日志显示"""
        filter_level = self.level_filter.currentText()
        
        if filter_level == "全部":
            filtered_logs = [entry[1] for entry in self.log_buffer]
        else:
            filtered_logs = [entry[1] for entry in self.log_buffer if entry[0] == filter_level]
        
        self.log_text.setPlainText("\n".join(filtered_logs))
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """清空日志"""
        self.log_buffer.clear()
        self.log_text.clear()


