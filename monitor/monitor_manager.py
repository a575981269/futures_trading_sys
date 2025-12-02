"""
监控管理器
"""
from typing import Dict, Any, Optional, Callable
from threading import Thread, Event
import time

from monitor.performance_monitor import PerformanceMonitor
from monitor.system_monitor import SystemMonitor
from monitor.alert import AlertManager, AlertLevel
from backtest.portfolio import Portfolio
from utils.logger import get_logger

logger = get_logger(__name__)


class MonitorManager:
    """监控管理器"""
    
    def __init__(self,
                 portfolio: Optional[Portfolio] = None,
                 enable_performance_monitor: bool = True,
                 enable_system_monitor: bool = True,
                 monitor_interval: int = 60):
        """
        初始化监控管理器
        
        Args:
            portfolio: 组合对象
            enable_performance_monitor: 是否启用性能监控
            enable_system_monitor: 是否启用系统监控
            monitor_interval: 监控间隔（秒）
        """
        # 性能监控
        self.performance_monitor: Optional[PerformanceMonitor] = None
        if enable_performance_monitor:
            self.performance_monitor = PerformanceMonitor(portfolio)
        
        # 系统监控
        self.system_monitor: Optional[SystemMonitor] = None
        if enable_system_monitor:
            self.system_monitor = SystemMonitor()
        
        # 告警管理器
        self.alert_manager = AlertManager()
        
        # 监控线程
        self.monitor_interval = monitor_interval
        self._monitoring = False
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None
        
        # 指标注册
        self.metrics: Dict[str, Callable] = {}
        
        logger.info("监控管理器初始化完成")
    
    def start_monitoring(self):
        """启动监控"""
        if self._monitoring:
            logger.warning("监控已在运行")
            return
        
        self._monitoring = True
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                # 性能监控
                if self.performance_monitor:
                    self._check_performance()
                
                # 系统监控
                if self.system_monitor:
                    self._check_system()
                
                # 等待下次监控
                self._stop_event.wait(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"监控循环执行失败: {e}")
                self.alert_manager.trigger_alert(
                    AlertLevel.ERROR,
                    f"监控循环执行失败: {e}",
                    source="MonitorManager"
                )
    
    def _check_performance(self):
        """检查性能指标"""
        if not self.performance_monitor:
            return
        
        metrics = self.performance_monitor.get_metrics()
        
        # 检查最大回撤
        max_drawdown = metrics.get('max_drawdown', 0)
        if max_drawdown > 20.0:  # 回撤超过20%
            self.alert_manager.trigger_alert(
                AlertLevel.WARNING,
                f"最大回撤超过20%: {max_drawdown:.2f}%",
                source="PerformanceMonitor",
                details=metrics
            )
        
        # 检查日收益率
        daily_return = metrics.get('daily_return', 0)
        if daily_return < -10.0:  # 日亏损超过10%
            self.alert_manager.trigger_alert(
                AlertLevel.WARNING,
                f"日亏损超过10%: {daily_return:.2f}%",
                source="PerformanceMonitor",
                details=metrics
            )
    
    def _check_system(self):
        """检查系统资源"""
        if not self.system_monitor:
            return
        
        resource_check = self.system_monitor.check_resources()
        
        if not resource_check.get('cpu_ok', True):
            self.alert_manager.trigger_alert(
                AlertLevel.WARNING,
                "CPU使用率过高",
                source="SystemMonitor"
            )
        
        if not resource_check.get('memory_ok', True):
            self.alert_manager.trigger_alert(
                AlertLevel.WARNING,
                "内存使用率过高",
                source="SystemMonitor"
            )
        
        if not resource_check.get('disk_ok', True):
            self.alert_manager.trigger_alert(
                AlertLevel.WARNING,
                "磁盘使用率过高",
                source="SystemMonitor"
            )
    
    def register_metric(self, name: str, callback: Callable):
        """
        注册指标
        
        Args:
            name: 指标名称
            callback: 指标计算回调函数
        """
        self.metrics[name] = callback
        logger.info(f"指标已注册: {name}")
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标
        
        Returns:
            指标字典
        """
        all_metrics = {}
        
        if self.performance_monitor:
            all_metrics['performance'] = self.performance_monitor.get_metrics()
        
        if self.system_monitor:
            all_metrics['system'] = self.system_monitor.get_all_metrics()
        
        # 自定义指标
        for name, callback in self.metrics.items():
            try:
                all_metrics[name] = callback()
            except Exception as e:
                logger.error(f"指标计算失败: {name}, {e}")
        
        return all_metrics
    
    def trigger_alert(self, level: AlertLevel, message: str,
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
        self.alert_manager.trigger_alert(level, message, source, details)
    
    def register_alert_handler(self, handler: Callable):
        """注册告警处理器"""
        self.alert_manager.register_handler(handler)

