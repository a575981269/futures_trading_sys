"""
实时风控监控
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from threading import Thread, Event, Lock
import time

from risk.risk_manager import RiskManager
from risk.risk_adapter import LiveAccountAdapter
from trading.live_account import LiveAccount
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskMonitor:
    """实时风控监控器"""
    
    def __init__(self,
                 risk_manager: RiskManager,
                 live_account: LiveAccount,
                 check_interval: int = 60,
                 alert_thresholds: Optional[Dict[str, float]] = None):
        """
        初始化风控监控器
        
        Args:
            risk_manager: 风控管理器
            live_account: 实盘账户
            check_interval: 检查间隔（秒）
            alert_thresholds: 告警阈值配置
        """
        self.risk_manager = risk_manager
        self.live_account = live_account
        self.check_interval = check_interval
        self.alert_thresholds = alert_thresholds or {
            'position_ratio_warning': 0.7,  # 持仓比例警告阈值
            'position_ratio_critical': 0.9,  # 持仓比例严重阈值
            'daily_loss_warning': 0.05,  # 单日亏损警告比例
            'daily_loss_critical': 0.08,  # 单日亏损严重比例
        }
        
        # 监控状态
        self._running = False
        self._monitor_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._lock = Lock()
        
        # 风险指标历史
        self.risk_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # 告警记录
        self.alerts: List[Dict[str, Any]] = []
        self.max_alerts_size = 100
        
        logger.info(f"风控监控器初始化完成，检查间隔={check_interval}秒")
    
    def start(self):
        """启动监控"""
        if self._running:
            logger.warning("风控监控器已在运行")
            return
        
        self._running = True
        self._stop_event.clear()
        
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("风控监控器已启动")
    
    def stop(self):
        """停止监控"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("风控监控器已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running and not self._stop_event.is_set():
            try:
                # 执行风险检查
                metrics = self._check_risks()
                
                # 记录风险指标
                self._record_metrics(metrics)
                
                # 检查告警
                self._check_alerts(metrics)
                
                # 等待下次检查
                self._stop_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"风控监控循环出错: {e}", exc_info=True)
                time.sleep(self.check_interval)
    
    def _check_risks(self) -> Dict[str, Any]:
        """
        检查风险指标
        
        Returns:
            风险指标字典
        """
        # 创建账户适配器
        adapter = LiveAccountAdapter(self.live_account)
        portfolio = adapter.to_portfolio()
        account_metrics = adapter.get_account_metrics()
        
        # 获取风控指标
        risk_metrics = self.risk_manager.get_risk_metrics(portfolio)
        
        # 合并指标
        metrics = {
            **account_metrics,
            **risk_metrics,
            'timestamp': datetime.now(),
        }
        
        return metrics
    
    def _record_metrics(self, metrics: Dict[str, Any]):
        """记录风险指标"""
        with self._lock:
            self.risk_history.append(metrics)
            
            # 限制历史记录大小
            if len(self.risk_history) > self.max_history_size:
                self.risk_history = self.risk_history[-self.max_history_size:]
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """检查告警条件"""
        alerts_triggered = []
        
        # 检查持仓比例
        position_ratio = metrics.get('position_ratio', 0.0)
        if position_ratio >= self.alert_thresholds['position_ratio_critical']:
            alerts_triggered.append({
                'level': 'CRITICAL',
                'type': 'position_ratio',
                'message': f'持仓比例严重超限: {position_ratio*100:.2f}%',
                'value': position_ratio,
                'threshold': self.alert_thresholds['position_ratio_critical'],
                'timestamp': datetime.now(),
            })
        elif position_ratio >= self.alert_thresholds['position_ratio_warning']:
            alerts_triggered.append({
                'level': 'WARNING',
                'type': 'position_ratio',
                'message': f'持仓比例警告: {position_ratio*100:.2f}%',
                'value': position_ratio,
                'threshold': self.alert_thresholds['position_ratio_warning'],
                'timestamp': datetime.now(),
            })
        
        # 检查单日亏损
        daily_pnl = metrics.get('daily_pnl', 0.0)
        total_equity = metrics.get('total_equity', 1.0)
        if total_equity > 0:
            daily_loss_ratio = abs(daily_pnl) / total_equity if daily_pnl < 0 else 0.0
            
            if daily_loss_ratio >= self.alert_thresholds['daily_loss_critical']:
                alerts_triggered.append({
                    'level': 'CRITICAL',
                    'type': 'daily_loss',
                    'message': f'单日亏损严重: {daily_loss_ratio*100:.2f}% (亏损{daily_pnl:.2f})',
                    'value': daily_loss_ratio,
                    'threshold': self.alert_thresholds['daily_loss_critical'],
                    'timestamp': datetime.now(),
                })
            elif daily_loss_ratio >= self.alert_thresholds['daily_loss_warning']:
                alerts_triggered.append({
                    'level': 'WARNING',
                    'type': 'daily_loss',
                    'message': f'单日亏损警告: {daily_loss_ratio*100:.2f}% (亏损{daily_pnl:.2f})',
                    'value': daily_loss_ratio,
                    'threshold': self.alert_thresholds['daily_loss_warning'],
                    'timestamp': datetime.now(),
                })
        
        # 记录告警
        for alert in alerts_triggered:
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Dict[str, Any]):
        """触发告警"""
        with self._lock:
            self.alerts.append(alert)
            
            # 限制告警记录大小
            if len(self.alerts) > self.max_alerts_size:
                self.alerts = self.alerts[-self.max_alerts_size:]
        
        # 记录日志
        if alert['level'] == 'CRITICAL':
            logger.critical(f"风控告警: {alert['message']}")
        else:
            logger.warning(f"风控告警: {alert['message']}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前风险指标"""
        return self._check_risks()
    
    def get_recent_metrics(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的风险指标"""
        with self._lock:
            return self.risk_history[-count:] if self.risk_history else []
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        with self._lock:
            return self.alerts[-count:] if self.alerts else []
    
    def get_alerts_by_level(self, level: str) -> List[Dict[str, Any]]:
        """按级别获取告警"""
        with self._lock:
            return [a for a in self.alerts if a['level'] == level]

