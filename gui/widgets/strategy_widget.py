"""
策略管理窗口 - 策略列表、参数配置、启停控制
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QPushButton, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from typing import Dict, Any, List

from gui.utils.signal_bridge import SignalBridge
from utils.logger import get_logger

logger = get_logger(__name__)


class StrategyWidget(QWidget):
    """策略管理窗口"""
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.strategies: List[Dict[str, Any]] = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("添加策略")
        add_btn.clicked.connect(self.add_strategy)
        toolbar.addWidget(add_btn)
        
        remove_btn = QPushButton("移除策略")
        remove_btn.clicked.connect(self.remove_strategy)
        toolbar.addWidget(remove_btn)
        
        config_btn = QPushButton("配置参数")
        config_btn.clicked.connect(self.config_strategy)
        toolbar.addWidget(config_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 策略列表
        strategy_group = QGroupBox("策略列表")
        strategy_layout = QVBoxLayout()
        
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(5)
        self.strategy_table.setHorizontalHeaderLabels([
            "策略ID", "策略名称", "状态", "参数", "操作"
        ])
        self.strategy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.strategy_table.setAlternatingRowColors(True)
        
        strategy_layout.addWidget(self.strategy_table)
        strategy_group.setLayout(strategy_layout)
        
        layout.addWidget(strategy_group)
    
    def setup_connections(self):
        """设置信号连接"""
        self.signal_bridge.strategy_status_changed.connect(self.on_strategy_status_changed)
    
    @pyqtSlot(str, str)
    def on_strategy_status_changed(self, strategy_id: str, status: str):
        """策略状态变化"""
        self.update_strategy_table()
    
    def add_strategy(self):
        """添加策略"""
        QMessageBox.information(self, "提示", "添加策略功能将在后续实现")
    
    def remove_strategy(self):
        """移除策略"""
        current_row = self.strategy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要移除的策略")
            return
        
        reply = QMessageBox.question(
            self,
            "确认移除",
            "确定要移除该策略吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.strategies.pop(current_row)
            self.update_strategy_table()
    
    def config_strategy(self):
        """配置策略参数"""
        current_row = self.strategy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要配置的策略")
            return
        
        QMessageBox.information(self, "提示", "策略参数配置功能将在后续实现")
    
    def update_strategy_table(self):
        """更新策略表格"""
        self.strategy_table.setRowCount(len(self.strategies))
        
        for i, strategy in enumerate(self.strategies):
            # 策略ID
            self.strategy_table.setItem(i, 0, QTableWidgetItem(strategy.get('id', '')))
            
            # 策略名称
            self.strategy_table.setItem(i, 1, QTableWidgetItem(strategy.get('name', '')))
            
            # 状态
            status = strategy.get('status', 'STOPPED')
            status_item = QTableWidgetItem(status)
            if status == 'RUNNING':
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.strategy_table.setItem(i, 2, status_item)
            
            # 参数
            params = strategy.get('params', {})
            params_str = ', '.join([f"{k}={v}" for k, v in params.items()])
            self.strategy_table.setItem(i, 3, QTableWidgetItem(params_str))
            
            # 操作按钮
            if status == 'RUNNING':
                stop_btn = QPushButton("停止")
                stop_btn.clicked.connect(lambda checked, s=strategy: self.stop_strategy(s))
                self.strategy_table.setCellWidget(i, 4, stop_btn)
            else:
                start_btn = QPushButton("启动")
                start_btn.clicked.connect(lambda checked, s=strategy: self.start_strategy(s))
                self.strategy_table.setCellWidget(i, 4, start_btn)
    
    def start_strategy(self, strategy: Dict[str, Any]):
        """启动策略"""
        logger.info(f"启动策略: {strategy.get('id')}")
        strategy['status'] = 'RUNNING'
        self.update_strategy_table()
    
    def stop_strategy(self, strategy: Dict[str, Any]):
        """停止策略"""
        logger.info(f"停止策略: {strategy.get('id')}")
        strategy['status'] = 'STOPPED'
        self.update_strategy_table()


