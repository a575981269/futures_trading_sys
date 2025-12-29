"""
连接配置窗口 - CTP连接和环境选择
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional

from gui.utils.signal_bridge import SignalBridge
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionWidget(QDialog):
    """连接配置窗口"""
    
    # 信号
    connection_requested = pyqtSignal(dict)  # 连接参数
    
    def __init__(self, signal_bridge: SignalBridge, parent=None):
        super().__init__(parent)
        self.signal_bridge = signal_bridge
        self.setWindowTitle("CTP连接配置")
        self.setModal(True)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 环境选择组
        env_group = QGroupBox("环境选择")
        env_layout = QVBoxLayout()
        
        self.env_combo = QComboBox()
        self.env_combo.addItem("CTP主席系统（正常交易时间，端口30001/30011）", "normal")
        self.env_combo.addItem("7x24环境（全天候，端口40001/40011）", "7x24")
        env_layout.addWidget(self.env_combo)
        
        env_group.setLayout(env_layout)
        layout.addWidget(env_group)
        
        # 连接参数组
        params_group = QGroupBox("连接参数")
        params_layout = QFormLayout()
        
        # 经纪商代码
        self.broker_id_edit = QLineEdit()
        self.broker_id_edit.setPlaceholderText("例如: 9999")
        params_layout.addRow("经纪商代码:", self.broker_id_edit)
        
        # 用户代码
        self.user_id_edit = QLineEdit()
        self.user_id_edit.setPlaceholderText("SimNow用户代码")
        params_layout.addRow("用户代码:", self.user_id_edit)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("SimNow密码")
        params_layout.addRow("密码:", self.password_edit)
        
        # 显示密码复选框
        self.show_password_check = QCheckBox("显示密码")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        params_layout.addRow("", self.show_password_check)
        
        # APP ID
        self.app_id_edit = QLineEdit()
        self.app_id_edit.setPlaceholderText("例如: simnow_client_test")
        params_layout.addRow("APP ID:", self.app_id_edit)
        
        # 授权编码
        self.auth_code_edit = QLineEdit()
        self.auth_code_edit.setPlaceholderText("例如: 0000000000000000")
        params_layout.addRow("授权编码:", self.auth_code_edit)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # 服务器地址（只读显示）
        server_group = QGroupBox("服务器地址（自动选择）")
        server_layout = QFormLayout()
        
        self.md_address_label = QLabel()
        self.trade_address_label = QLabel()
        server_layout.addRow("行情服务器:", self.md_address_label)
        server_layout.addRow("交易服务器:", self.trade_address_label)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # 环境变化时更新服务器地址
        self.env_combo.currentIndexChanged.connect(self.update_server_addresses)
        self.update_server_addresses()
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setDefault(True)
        self.connect_btn.clicked.connect(self.on_connect)
        button_layout.addWidget(self.connect_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def toggle_password_visibility(self, checked: bool):
        """切换密码显示"""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def update_server_addresses(self):
        """更新服务器地址显示"""
        env_type = self.env_combo.currentData()
        addresses = settings.get_server_addresses(env_type)
        self.md_address_label.setText(addresses['md_address'])
        self.trade_address_label.setText(addresses['trade_address'])
    
    def load_settings(self):
        """加载配置"""
        # 从settings加载
        self.broker_id_edit.setText(settings.CTP_BROKER_ID or "")
        self.user_id_edit.setText(settings.CTP_USER_ID or "")
        self.password_edit.setText(settings.CTP_PASSWORD or "")
        self.app_id_edit.setText(settings.CTP_APP_ID or "simnow_client_test")
        self.auth_code_edit.setText(settings.CTP_AUTH_CODE or "0000000000000000")
        
        # 设置环境
        env_type = settings.CTP_ENVIRONMENT or "normal"
        index = self.env_combo.findData(env_type)
        if index >= 0:
            self.env_combo.setCurrentIndex(index)
    
    def on_connect(self):
        """连接按钮点击"""
        # 验证输入
        broker_id = self.broker_id_edit.text().strip()
        user_id = self.user_id_edit.text().strip()
        password = self.password_edit.text().strip()
        app_id = self.app_id_edit.text().strip()
        auth_code = self.auth_code_edit.text().strip()
        env_type = self.env_combo.currentData()
        
        if not broker_id:
            QMessageBox.warning(self, "警告", "请输入经纪商代码")
            return
        
        if not user_id:
            QMessageBox.warning(self, "警告", "请输入用户代码")
            return
        
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码")
            return
        
        # 获取服务器地址
        addresses = settings.get_server_addresses(env_type)
        
        # 构建连接参数
        connection_params = {
            'broker_id': broker_id,
            'user_id': user_id,
            'password': password,
            'app_id': app_id or 'simnow_client_test',
            'auth_code': auth_code or '0000000000000000',
            'md_address': addresses['md_address'],
            'trade_address': addresses['trade_address'],
            'environment': env_type
        }
        
        # 发送连接请求信号
        self.connection_requested.emit(connection_params)
        self.accept()


