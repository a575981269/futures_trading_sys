"""
实盘账户适配器
将LiveAccount转换为Portfolio格式，供风控模块使用
"""
from typing import Dict, List
from datetime import datetime

from trading.live_account import LiveAccount
from backtest.portfolio import Portfolio, Position, Direction
from config.contracts import get_contract_multiplier
from utils.logger import get_logger

logger = get_logger(__name__)


class LiveAccountAdapter:
    """实盘账户适配器"""
    
    def __init__(self, live_account: LiveAccount):
        """
        初始化适配器
        
        Args:
            live_account: 实盘账户对象
        """
        self.live_account = live_account
    
    def to_portfolio(self) -> Portfolio:
        """
        将LiveAccount转换为Portfolio对象
        
        Returns:
            Portfolio对象
        """
        # 获取账户信息
        account_info = self.live_account.get_account_info()
        balance = account_info.get('balance', 0.0)
        available = account_info.get('available', 0.0)
        margin = account_info.get('margin', 0.0)
        
        # 创建Portfolio对象
        # 使用可用资金作为当前资金，总权益 = 可用资金 + 占用保证金 + 浮动盈亏
        portfolio = Portfolio(initial_capital=balance)
        portfolio.current_capital = available
        
        # 转换持仓
        positions = self.live_account.get_positions()
        for pos in positions:
            # 创建Portfolio的Position对象
            portfolio_pos = Position(
                symbol=pos.symbol,
                direction=pos.direction,
                volume=pos.volume,
                entry_price=pos.entry_price,
                entry_time=pos.entry_time,
                current_price=pos.current_price,
                multiplier=pos.multiplier
            )
            portfolio.positions[pos.symbol] = portfolio_pos
        
        # 计算总权益（资金 + 持仓浮动盈亏）
        total_equity = balance
        for pos in portfolio.positions.values():
            total_equity += pos.get_pnl()
        
        # 更新初始资金为总权益（用于计算比例）
        portfolio.initial_capital = max(total_equity, balance)
        
        logger.debug(f"账户适配完成: 资金={balance}, 可用={available}, 持仓数={len(positions)}")
        
        return portfolio
    
    def get_account_metrics(self) -> Dict:
        """
        获取账户指标
        
        Returns:
            账户指标字典
        """
        account_info = self.live_account.get_account_info()
        positions = self.live_account.get_positions()
        
        # 计算总持仓价值
        total_position_value = 0.0
        for pos in positions:
            multiplier = get_contract_multiplier(pos.symbol)
            total_position_value += pos.current_price * pos.volume * multiplier
        
        # 计算总权益
        total_equity = account_info.get('balance', 0.0)
        for pos in positions:
            total_equity += pos.get_pnl()
        
        metrics = {
            'balance': account_info.get('balance', 0.0),
            'available': account_info.get('available', 0.0),
            'margin': account_info.get('margin', 0.0),
            'total_equity': total_equity,
            'total_position_value': total_position_value,
            'position_count': len(positions),
            'position_ratio': total_position_value / total_equity if total_equity > 0 else 0.0,
        }
        
        return metrics

