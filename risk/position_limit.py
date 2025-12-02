"""
持仓限制风控
"""
from typing import Dict, Optional
from risk.risk_rules import RiskResult, RiskLevel
from backtest.portfolio import Portfolio, Position, Direction
from utils.logger import get_logger

logger = get_logger(__name__)


class PositionLimit:
    """持仓限制"""
    
    def __init__(self,
                 max_position_per_symbol: Optional[int] = None,
                 max_total_positions: Optional[int] = None,
                 max_position_value_ratio: Optional[float] = None):
        """
        初始化持仓限制
        
        Args:
            max_position_per_symbol: 单品种最大持仓手数
            max_total_positions: 总持仓品种数限制
            max_position_value_ratio: 单品种持仓价值占账户权益的最大比例（0-1）
        """
        self.max_position_per_symbol = max_position_per_symbol
        self.max_total_positions = max_total_positions
        self.max_position_value_ratio = max_position_value_ratio
        
        logger.info(f"持仓限制初始化: 单品种最大={max_position_per_symbol}, "
                   f"总品种数={max_total_positions}, 价值比例={max_position_value_ratio}")
    
    def check_position_risk(self, 
                           symbol: str,
                           new_volume: int,
                           direction: Direction,
                           portfolio: Portfolio,
                           current_price: float) -> RiskResult:
        """
        检查持仓风险
        
        Args:
            symbol: 合约代码
            new_volume: 新增持仓数量
            direction: 持仓方向
            portfolio: 组合对象
            current_price: 当前价格
            
        Returns:
            风控结果
        """
        # 检查单品种持仓限制
        if self.max_position_per_symbol is not None:
            current_pos = portfolio.get_position(symbol)
            current_volume = current_pos.volume if current_pos else 0
            
            # 计算新持仓数量
            if current_pos and current_pos.direction == direction:
                total_volume = current_volume + new_volume
            elif current_pos:
                # 方向相反，先平仓再开仓
                total_volume = new_volume
            else:
                total_volume = new_volume
            
            if total_volume > self.max_position_per_symbol:
                return RiskResult.block(
                    f"单品种持仓超限: {symbol}",
                    f"当前持仓{current_volume}手，新增{new_volume}手，"
                    f"总计{total_volume}手，超过限制{self.max_position_per_symbol}手"
                )
        
        # 检查总持仓品种数限制
        if self.max_total_positions is not None:
            existing_positions = portfolio.get_all_positions()
            existing_symbols = {pos.symbol for pos in existing_positions}
            
            # 如果新增品种不在现有持仓中，需要检查总数
            if symbol not in existing_symbols:
                if len(existing_symbols) >= self.max_total_positions:
                    return RiskResult.block(
                        f"总持仓品种数超限",
                        f"当前持仓{len(existing_symbols)}个品种，"
                        f"超过限制{self.max_total_positions}个品种"
                    )
        
        # 检查单品种持仓价值比例
        if self.max_position_value_ratio is not None:
            from config.contracts import get_contract_multiplier
            
            multiplier = get_contract_multiplier(symbol)
            position_value = current_price * new_volume * multiplier
            
            total_equity = portfolio.get_total_equity()
            if total_equity > 0:
                value_ratio = position_value / total_equity
                if value_ratio > self.max_position_value_ratio:
                    return RiskResult.block(
                        f"单品种持仓价值比例超限: {symbol}",
                        f"持仓价值{position_value:,.2f}，占账户权益{value_ratio*100:.2f}%，"
                        f"超过限制{self.max_position_value_ratio*100:.2f}%"
                    )
        
        return RiskResult.safe(f"持仓风控检查通过: {symbol}")

