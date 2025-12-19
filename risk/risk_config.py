"""
风控规则配置管理
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

from risk.position_limit import PositionLimit
from risk.capital_limit import CapitalLimit
from risk.order_limit import OrderLimit
from risk.risk_manager import RiskManager
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskConfig:
    """风控配置"""
    # 持仓限制
    max_position_per_symbol: Optional[int] = None
    max_total_positions: Optional[int] = None
    max_position_value_ratio: Optional[float] = None
    
    # 资金限制
    max_order_amount: Optional[float] = None
    max_daily_loss: Optional[float] = None
    max_daily_loss_ratio: Optional[float] = None
    min_available_ratio: Optional[float] = None
    
    # 订单限制
    max_orders_per_minute: Optional[int] = None
    max_orders_per_symbol_per_minute: Optional[int] = None
    max_price_deviation_ratio: Optional[float] = None
    
    # 是否启用风控
    enable_risk_control: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskConfig':
        """从字典创建"""
        return cls(**data)
    
    def create_risk_manager(self) -> RiskManager:
        """创建风控管理器"""
        position_limit = None
        if any([self.max_position_per_symbol, self.max_total_positions, self.max_position_value_ratio]):
            position_limit = PositionLimit(
                max_position_per_symbol=self.max_position_per_symbol,
                max_total_positions=self.max_total_positions,
                max_position_value_ratio=self.max_position_value_ratio,
            )
        
        capital_limit = None
        if any([self.max_order_amount, self.max_daily_loss, self.max_daily_loss_ratio, self.min_available_ratio]):
            capital_limit = CapitalLimit(
                max_order_amount=self.max_order_amount,
                max_daily_loss=self.max_daily_loss,
                max_daily_loss_ratio=self.max_daily_loss_ratio,
                min_available_ratio=self.min_available_ratio,
            )
        
        order_limit = None
        if any([self.max_orders_per_minute, self.max_orders_per_symbol_per_minute, self.max_price_deviation_ratio]):
            order_limit = OrderLimit(
                max_orders_per_minute=self.max_orders_per_minute,
                max_orders_per_symbol_per_minute=self.max_orders_per_symbol_per_minute,
                max_price_deviation_ratio=self.max_price_deviation_ratio,
            )
        
        return RiskManager(
            position_limit=position_limit,
            capital_limit=capital_limit,
            order_limit=order_limit,
            enable_risk_control=self.enable_risk_control,
        )


class RiskConfigManager:
    """风控配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            config_file = os.path.join('config', 'risk_config.json')
        
        self.config_file = config_file
        self.configs: Dict[str, RiskConfig] = {}  # {name: RiskConfig}
        self.default_config_name = 'default'
        
        # 加载配置
        self._load_configs()
    
    def _load_configs(self):
        """从文件加载配置"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
            self._create_default_config()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载所有配置
            for name, config_data in data.items():
                self.configs[name] = RiskConfig.from_dict(config_data)
            
            logger.info(f"加载风控配置: {len(self.configs)}个配置")
            
        except Exception as e:
            logger.error(f"加载风控配置失败: {e}", exc_info=True)
            self._create_default_config()
    
    def _save_configs(self):
        """保存配置到文件"""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {name: config.to_dict() for name, config in self.configs.items()}
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"保存风控配置: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存风控配置失败: {e}", exc_info=True)
    
    def _create_default_config(self):
        """创建默认配置"""
        default_config = RiskConfig(
            max_position_per_symbol=10,
            max_total_positions=5,
            max_position_value_ratio=0.3,
            max_order_amount=100000.0,
            max_daily_loss=50000.0,
            max_daily_loss_ratio=0.1,
            min_available_ratio=0.2,
            max_orders_per_minute=10,
            max_orders_per_symbol_per_minute=5,
            max_price_deviation_ratio=0.05,
            enable_risk_control=True,
        )
        
        self.configs[self.default_config_name] = default_config
        self._save_configs()
    
    def get_config(self, name: Optional[str] = None) -> RiskConfig:
        """
        获取配置
        
        Args:
            name: 配置名称，如果为None则返回默认配置
        
        Returns:
            风控配置对象
        """
        config_name = name or self.default_config_name
        
        if config_name not in self.configs:
            logger.warning(f"配置不存在: {config_name}，使用默认配置")
            config_name = self.default_config_name
        
        return self.configs.get(config_name, self.configs[self.default_config_name])
    
    def set_config(self, name: str, config: RiskConfig):
        """
        设置配置
        
        Args:
            name: 配置名称
            config: 风控配置对象
        """
        self.configs[name] = config
        self._save_configs()
        logger.info(f"更新风控配置: {name}")
    
    def update_config(self, name: str, **kwargs):
        """
        更新配置
        
        Args:
            name: 配置名称
            **kwargs: 要更新的配置项
        """
        config = self.get_config(name)
        
        # 更新配置项
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                logger.warning(f"未知的配置项: {key}")
        
        self.set_config(name, config)
    
    def create_risk_manager(self, name: Optional[str] = None) -> RiskManager:
        """
        创建风控管理器
        
        Args:
            name: 配置名称，如果为None则使用默认配置
        
        Returns:
            风控管理器对象
        """
        config = self.get_config(name)
        return config.create_risk_manager()
    
    def list_configs(self) -> List[str]:
        """列出所有配置名称"""
        return list(self.configs.keys())
    
    def delete_config(self, name: str) -> bool:
        """
        删除配置
        
        Args:
            name: 配置名称
        
        Returns:
            是否成功
        """
        if name == self.default_config_name:
            logger.warning("不能删除默认配置")
            return False
        
        if name in self.configs:
            del self.configs[name]
            self._save_configs()
            logger.info(f"删除风控配置: {name}")
            return True
        
        return False

