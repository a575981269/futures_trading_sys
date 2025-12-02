"""
系统监控
"""
import psutil
import platform
from typing import Dict, Any, Optional
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class SystemMonitor:
    """系统监控"""
    
    def __init__(self):
        """初始化系统监控"""
        self.start_time = datetime.now()
        logger.info("系统监控初始化完成")
    
    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"获取CPU使用率失败: {e}")
            return 0.0
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
        except Exception as e:
            logger.error(f"获取内存使用情况失败: {e}")
            return {}
    
    def get_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """获取磁盘使用情况"""
        try:
            disk = psutil.disk_usage(path)
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        except Exception as e:
            logger.error(f"获取磁盘使用情况失败: {e}")
            return {}
    
    def get_network_io(self) -> Dict[str, Any]:
        """获取网络IO"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
            }
        except Exception as e:
            logger.error(f"获取网络IO失败: {e}")
            return {}
    
    def get_process_info(self) -> Dict[str, Any]:
        """获取进程信息"""
        try:
            process = psutil.Process()
            return {
                'pid': process.pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()),
            }
        except Exception as e:
            logger.error(f"获取进程信息失败: {e}")
            return {}
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'uptime': str(datetime.now() - self.start_time),
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有系统指标
        
        Returns:
            指标字典
        """
        return {
            'cpu': {
                'usage': self.get_cpu_usage(),
            },
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_io(),
            'process': self.get_process_info(),
            'system': self.get_system_info(),
        }
    
    def check_resources(self,
                       max_cpu_percent: float = 90.0,
                       max_memory_percent: float = 90.0,
                       max_disk_percent: float = 90.0) -> Dict[str, bool]:
        """
        检查系统资源
        
        Args:
            max_cpu_percent: 最大CPU使用率
            max_memory_percent: 最大内存使用率
            max_disk_percent: 最大磁盘使用率
            
        Returns:
            检查结果字典
        """
        cpu_usage = self.get_cpu_usage()
        memory_usage = self.get_memory_usage()
        disk_usage = self.get_disk_usage()
        
        return {
            'cpu_ok': cpu_usage < max_cpu_percent,
            'memory_ok': memory_usage.get('percent', 0) < max_memory_percent,
            'disk_ok': disk_usage.get('percent', 0) < max_disk_percent,
        }

