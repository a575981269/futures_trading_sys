"""
风控规则定义
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    """风险级别"""
    SAFE = "SAFE"          # 安全
    WARNING = "WARNING"    # 警告
    BLOCK = "BLOCK"        # 阻止


@dataclass
class RiskResult:
    """风控检查结果"""
    passed: bool           # 是否通过
    level: RiskLevel       # 风险级别
    message: str          # 提示信息
    reason: Optional[str] = None  # 拒绝原因
    
    @classmethod
    def safe(cls, message: str = "风控检查通过") -> 'RiskResult':
        """创建安全结果"""
        return cls(
            passed=True,
            level=RiskLevel.SAFE,
            message=message
        )
    
    @classmethod
    def warning(cls, message: str, reason: Optional[str] = None) -> 'RiskResult':
        """创建警告结果"""
        return cls(
            passed=True,
            level=RiskLevel.WARNING,
            message=message,
            reason=reason
        )
    
    @classmethod
    def block(cls, message: str, reason: str) -> 'RiskResult':
        """创建阻止结果"""
        return cls(
            passed=False,
            level=RiskLevel.BLOCK,
            message=message,
            reason=reason
        )

