"""
告警系统
"""
from enum import Enum
from typing import List, Callable, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "INFO"          # 信息
    WARNING = "WARNING"    # 警告
    ERROR = "ERROR"        # 错误
    CRITICAL = "CRITICAL"  # 严重


@dataclass
class Alert:
    """告警对象"""
    level: AlertLevel
    message: str
    timestamp: datetime
    source: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        """初始化告警管理器"""
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_history: List[Alert] = []
        self.max_history_size = 1000
        
        logger.info("告警管理器初始化完成")
    
    def register_handler(self, handler: Callable[[Alert], None]):
        """
        注册告警处理器
        
        Args:
            handler: 告警处理函数
        """
        if handler not in self.alert_handlers:
            self.alert_handlers.append(handler)
            logger.info("告警处理器已注册")
    
    def trigger_alert(self,
                     level: AlertLevel,
                     message: str,
                     source: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None):
        """
        触发告警
        
        Args:
            level: 告警级别
            message: 告警消息
            source: 告警来源
            details: 详细信息
        """
        alert = Alert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            source=source,
            details=details
        )
        
        # 添加到历史
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history_size:
            self.alert_history.pop(0)
        
        # 调用处理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")
        
        # 记录日志
        log_msg = f"[{level.value}] {message}"
        if source:
            log_msg = f"[{source}] {log_msg}"
        
        if level == AlertLevel.CRITICAL:
            logger.critical(log_msg)
        elif level == AlertLevel.ERROR:
            logger.error(log_msg)
        elif level == AlertLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def get_recent_alerts(self, level: Optional[AlertLevel] = None,
                         limit: int = 100) -> List[Alert]:
        """
        获取最近的告警
        
        Args:
            level: 告警级别，如果为None则返回所有级别
            limit: 返回数量限制
            
        Returns:
            告警列表
        """
        alerts = self.alert_history[-limit:]
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts


def email_alert_handler(alert: Alert, recipients: List[str]):
    """
    邮件告警处理器（示例）
    
    Args:
        alert: 告警对象
        recipients: 收件人列表
    """
    # TODO: 实现邮件发送逻辑
    logger.info(f"发送邮件告警: {alert.message} -> {recipients}")


def webhook_alert_handler(alert: Alert, webhook_url: str):
    """
    Webhook告警处理器（示例）
    
    Args:
        alert: 告警对象
        webhook_url: Webhook URL
    """
    # TODO: 实现Webhook发送逻辑
    import requests
    try:
        payload = {
            'level': alert.level.value,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'source': alert.source,
            'details': alert.details
        }
        # requests.post(webhook_url, json=payload)
        logger.info(f"发送Webhook告警: {alert.message} -> {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook告警发送失败: {e}")

