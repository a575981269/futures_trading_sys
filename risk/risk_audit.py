"""
风控审计日志
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
from threading import Lock

from risk.risk_rules import RiskResult
from trading.order import Order
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskAuditRecord:
    """风控审计记录"""
    timestamp: datetime
    order_id: Optional[str]
    symbol: Optional[str]
    risk_type: str  # 'order_risk', 'position_risk', 'capital_risk'
    result: str  # 'passed', 'blocked', 'warning'
    message: str
    reason: Optional[str] = None
    risk_level: Optional[str] = None
    order_details: Optional[Dict[str, Any]] = None
    account_metrics: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换datetime为字符串
        data['timestamp'] = self.timestamp.isoformat()
        return data


class RiskAuditLogger:
    """风控审计日志记录器"""
    
    def __init__(self, log_file: Optional[str] = None, max_records: int = 10000):
        """
        初始化审计日志记录器
        
        Args:
            log_file: 日志文件路径，如果为None则使用默认路径
            max_records: 最大记录数
        """
        if log_file is None:
            log_file = os.path.join('logs', 'risk_audit.jsonl')
        
        self.log_file = log_file
        self.max_records = max_records
        self._lock = Lock()
        self._records: List[RiskAuditRecord] = []
        
        # 确保日志目录存在
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"风控审计日志初始化: {self.log_file}")
    
    def log_order_risk(self,
                      order: Order,
                      result: RiskResult,
                      account_metrics: Optional[Dict[str, Any]] = None):
        """
        记录订单风控检查
        
        Args:
            order: 订单对象
            result: 风控检查结果
            account_metrics: 账户指标
        """
        record = RiskAuditRecord(
            timestamp=datetime.now(),
            order_id=order.order_id,
            symbol=order.symbol,
            risk_type='order_risk',
            result='passed' if result.passed else 'blocked',
            message=result.message,
            reason=result.reason,
            risk_level=result.level.value if result.level else None,
            order_details={
                'direction': order.direction.value,
                'price': order.price,
                'volume': order.volume,
                'order_type': order.order_type.value,
            },
            account_metrics=account_metrics,
        )
        
        self._add_record(record)
    
    def log_position_risk(self,
                         symbol: str,
                         volume: int,
                         result: RiskResult,
                         account_metrics: Optional[Dict[str, Any]] = None):
        """
        记录持仓风控检查
        
        Args:
            symbol: 合约代码
            volume: 持仓数量
            result: 风控检查结果
            account_metrics: 账户指标
        """
        record = RiskAuditRecord(
            timestamp=datetime.now(),
            order_id=None,
            symbol=symbol,
            risk_type='position_risk',
            result='passed' if result.passed else 'blocked',
            message=result.message,
            reason=result.reason,
            risk_level=result.level.value if result.level else None,
            order_details={'volume': volume},
            account_metrics=account_metrics,
        )
        
        self._add_record(record)
    
    def log_capital_risk(self,
                        order_amount: float,
                        result: RiskResult,
                        account_metrics: Optional[Dict[str, Any]] = None):
        """
        记录资金风控检查
        
        Args:
            order_amount: 订单金额
            result: 风控检查结果
            account_metrics: 账户指标
        """
        record = RiskAuditRecord(
            timestamp=datetime.now(),
            order_id=None,
            symbol=None,
            risk_type='capital_risk',
            result='passed' if result.passed else 'blocked',
            message=result.message,
            reason=result.reason,
            risk_level=result.level.value if result.level else None,
            order_details={'order_amount': order_amount},
            account_metrics=account_metrics,
        )
        
        self._add_record(record)
    
    def _add_record(self, record: RiskAuditRecord):
        """添加记录"""
        with self._lock:
            self._records.append(record)
            
            # 限制内存中的记录数
            if len(self._records) > self.max_records:
                self._records = self._records[-self.max_records:]
            
            # 写入文件
            self._write_record(record)
    
    def _write_record(self, record: RiskAuditRecord):
        """写入记录到文件"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"写入审计日志失败: {e}")
    
    def get_recent_records(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的记录
        
        Args:
            count: 记录数量
        
        Returns:
            记录列表
        """
        with self._lock:
            records = self._records[-count:] if self._records else []
            return [r.to_dict() for r in records]
    
    def get_records_by_result(self, result: str) -> List[Dict[str, Any]]:
        """
        按结果筛选记录
        
        Args:
            result: 结果类型 ('passed', 'blocked', 'warning')
        
        Returns:
            记录列表
        """
        with self._lock:
            records = [r for r in self._records if r.result == result]
            return [r.to_dict() for r in records]
    
    def get_records_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        按合约筛选记录
        
        Args:
            symbol: 合约代码
        
        Returns:
            记录列表
        """
        with self._lock:
            records = [r for r in self._records if r.symbol == symbol]
            return [r.to_dict() for r in records]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            total = len(self._records)
            passed = sum(1 for r in self._records if r.result == 'passed')
            blocked = sum(1 for r in self._records if r.result == 'blocked')
            warning = sum(1 for r in self._records if r.result == 'warning')
            
            return {
                'total_records': total,
                'passed': passed,
                'blocked': blocked,
                'warning': warning,
                'pass_rate': passed / total if total > 0 else 0.0,
                'block_rate': blocked / total if total > 0 else 0.0,
            }

