"""
策略管理器
"""
from typing import Dict, List, Optional, Type, Any
from threading import Lock
import uuid

from strategy.base_strategy import BaseStrategy
from utils.logger import get_logger

logger = get_logger(__name__)


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        """初始化策略管理器"""
        self.strategies: Dict[str, BaseStrategy] = {}  # {strategy_id: Strategy}
        self.strategy_classes: Dict[str, Type[BaseStrategy]] = {}  # {name: StrategyClass}
        self._lock = Lock()
        
        logger.info("策略管理器初始化完成")
    
    def register_strategy(self, name: str, strategy_class: Type[BaseStrategy]):
        """
        注册策略类
        
        Args:
            name: 策略名称
            strategy_class: 策略类
        """
        with self._lock:
            self.strategy_classes[name] = strategy_class
            logger.info(f"策略类已注册: {name}")
    
    def create_strategy(self,
                       name: str,
                       params: Optional[Dict[str, Any]] = None) -> str:
        """
        创建策略实例
        
        Args:
            name: 策略名称
            params: 策略参数
            
        Returns:
            策略ID
        """
        with self._lock:
            if name not in self.strategy_classes:
                raise ValueError(f"策略类未注册: {name}")
            
            strategy_class = self.strategy_classes[name]
            strategy_id = str(uuid.uuid4())
            
            strategy = strategy_class(
                name=f"{name}_{strategy_id[:8]}",
                params=params or {}
            )
            
            self.strategies[strategy_id] = strategy
            logger.info(f"策略实例已创建: {name} ({strategy_id})")
            
            return strategy_id
    
    def get_strategy(self, strategy_id: str) -> Optional[BaseStrategy]:
        """获取策略实例"""
        return self.strategies.get(strategy_id)
    
    def get_all_strategies(self) -> List[BaseStrategy]:
        """获取所有策略实例"""
        return list(self.strategies.values())
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """
        移除策略实例
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if strategy_id not in self.strategies:
                return False
            
            strategy = self.strategies[strategy_id]
            
            # 如果策略正在运行，先停止
            if strategy.is_active:
                strategy.on_exit()
                strategy.is_active = False
            
            del self.strategies[strategy_id]
            logger.info(f"策略实例已移除: {strategy_id}")
            return True
    
    def start_strategy(self, strategy_id: str) -> bool:
        """
        启动策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功
        """
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            logger.error(f"策略不存在: {strategy_id}")
            return False
        
        if strategy.is_active:
            logger.warning(f"策略已在运行: {strategy_id}")
            return True
        
        try:
            strategy.on_init()
            strategy.is_active = True
            logger.info(f"策略已启动: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"策略启动失败: {strategy_id}, {e}")
            return False
    
    def stop_strategy(self, strategy_id: str) -> bool:
        """
        停止策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功
        """
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            logger.error(f"策略不存在: {strategy_id}")
            return False
        
        if not strategy.is_active:
            logger.warning(f"策略未运行: {strategy_id}")
            return True
        
        try:
            strategy.on_exit()
            strategy.is_active = False
            logger.info(f"策略已停止: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"策略停止失败: {strategy_id}, {e}")
            return False
    
    def get_strategy_list(self) -> List[Dict[str, Any]]:
        """
        获取策略列表
        
        Returns:
            策略信息列表
        """
        result = []
        for strategy_id, strategy in self.strategies.items():
            result.append({
                'strategy_id': strategy_id,
                'name': strategy.name,
                'is_active': strategy.is_active,
                'params': strategy.params,
                'symbols': strategy.symbols,
            })
        return result
    
    def get_registered_strategies(self) -> List[str]:
        """获取已注册的策略类名称"""
        return list(self.strategy_classes.keys())

