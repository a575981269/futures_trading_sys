"""
组合管理模块
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from utils.logger import get_logger
from config.contracts import get_contract_multiplier
from utils.helpers import calculate_pnl

logger = get_logger(__name__)


class Direction(Enum):
    """持仓方向"""
    LONG = 1   # 多头
    SHORT = -1  # 空头
    NONE = 0    # 无持仓


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    direction: Direction
    volume: int  # 持仓手数
    entry_price: float  # 开仓价
    entry_time: datetime  # 开仓时间
    current_price: float = 0.0  # 当前价格
    multiplier: int = 1  # 合约乘数
    
    def get_pnl(self) -> float:
        """计算浮动盈亏"""
        if self.direction == Direction.NONE:
            return 0.0
        return calculate_pnl(
            self.entry_price,
            self.current_price,
            self.volume,
            self.direction.value,
            self.multiplier
        )
    
    def update_price(self, price: float):
        """更新当前价格"""
        self.current_price = price


@dataclass
class Trade:
    """交易记录"""
    symbol: str
    direction: Direction
    volume: int
    price: float
    time: datetime
    trade_id: str
    commission: float = 0.0  # 手续费


class Portfolio:
    """组合管理类"""
    
    def __init__(self, initial_capital: float = 1000000.0,
                 commission_rate: float = 0.0001,
                 slippage: float = 0.0):
        """
        初始化组合
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点（按价格比例）
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 持仓字典 {symbol: Position}
        self.positions: Dict[str, Position] = {}
        
        # 交易记录
        self.trades: List[Trade] = []
        
        # 资金曲线
        self.equity_curve: List[float] = [initial_capital]
        self.equity_times: List[datetime] = [datetime.now()]
        
        logger.info(f"组合初始化: 初始资金={initial_capital}, 手续费率={commission_rate}")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())
    
    def open_long(self, symbol: str, price: float, volume: int,
                  time: datetime) -> bool:
        """
        开多仓
        
        Args:
            symbol: 合约代码
            price: 开仓价
            volume: 数量
            time: 时间
        
        Returns:
            是否成功
        """
        # 计算实际价格（考虑滑点）
        actual_price = price * (1 + self.slippage)
        
        # 计算手续费
        multiplier = get_contract_multiplier(symbol)
        commission = actual_price * volume * multiplier * self.commission_rate
        
        # 检查资金是否足够
        required_capital = actual_price * volume * multiplier + commission
        if required_capital > self.current_capital:
            logger.warning(f"资金不足，无法开多仓: {symbol}, 需要={required_capital}, 可用={self.current_capital}")
            return False
        
        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            if pos.direction == Direction.SHORT:
                # 如果已有空仓，先平空
                self.close_short(symbol, actual_price, min(volume, pos.volume), time)
                volume -= min(volume, pos.volume)
                if volume <= 0:
                    return True
            
            if pos.direction == Direction.LONG:
                # 加仓
                total_volume = pos.volume + volume
                total_cost = pos.entry_price * pos.volume + actual_price * volume
                pos.entry_price = total_cost / total_volume
                pos.volume = total_volume
            else:
                # 新建多仓
                pos = Position(
                    symbol=symbol,
                    direction=Direction.LONG,
                    volume=volume,
                    entry_price=actual_price,
                    entry_time=time,
                    current_price=actual_price,
                    multiplier=multiplier
                )
                self.positions[symbol] = pos
        else:
            # 新建多仓
            pos = Position(
                symbol=symbol,
                direction=Direction.LONG,
                volume=volume,
                entry_price=actual_price,
                entry_time=time,
                current_price=actual_price,
                multiplier=multiplier
            )
            self.positions[symbol] = pos
        
        # 扣除资金
        self.current_capital -= required_capital
        
        # 记录交易
        trade = Trade(
            symbol=symbol,
            direction=Direction.LONG,
            volume=volume,
            price=actual_price,
            time=time,
            trade_id=f"{symbol}_{time.strftime('%Y%m%d%H%M%S')}",
            commission=commission
        )
        self.trades.append(trade)
        
        logger.info(f"开多仓: {symbol}, 价格={actual_price}, 数量={volume}, 资金={self.current_capital:.2f}")
        return True
    
    def close_long(self, symbol: str, price: float, volume: int,
                   time: datetime) -> bool:
        """
        平多仓
        
        Args:
            symbol: 合约代码
            price: 平仓价
            volume: 数量
            time: 时间
        
        Returns:
            是否成功
        """
        if symbol not in self.positions:
            logger.warning(f"无持仓，无法平多仓: {symbol}")
            return False
        
        pos = self.positions[symbol]
        if pos.direction != Direction.LONG:
            logger.warning(f"持仓方向不匹配，无法平多仓: {symbol}")
            return False
        
        if volume > pos.volume:
            volume = pos.volume
        
        # 计算实际价格
        actual_price = price * (1 - self.slippage)
        
        # 计算盈亏和手续费
        multiplier = pos.multiplier
        pnl = calculate_pnl(pos.entry_price, actual_price, volume, 1, multiplier)
        commission = actual_price * volume * multiplier * self.commission_rate
        
        # 更新资金
        self.current_capital += actual_price * volume * multiplier - commission + pnl
        
        # 更新持仓
        pos.volume -= volume
        if pos.volume == 0:
            del self.positions[symbol]
        
        # 记录交易
        trade = Trade(
            symbol=symbol,
            direction=Direction.LONG,
            volume=-volume,
            price=actual_price,
            time=time,
            trade_id=f"{symbol}_{time.strftime('%Y%m%d%H%M%S')}",
            commission=commission
        )
        self.trades.append(trade)
        
        logger.info(f"平多仓: {symbol}, 价格={actual_price}, 数量={volume}, 盈亏={pnl:.2f}, 资金={self.current_capital:.2f}")
        return True
    
    def open_short(self, symbol: str, price: float, volume: int,
                   time: datetime) -> bool:
        """
        开空仓
        
        Args:
            symbol: 合约代码
            price: 开仓价
            volume: 数量
            time: 时间
        
        Returns:
            是否成功
        """
        # 计算实际价格
        actual_price = price * (1 - self.slippage)
        
        # 计算手续费
        multiplier = get_contract_multiplier(symbol)
        commission = actual_price * volume * multiplier * self.commission_rate
        
        # 检查资金是否足够
        required_capital = actual_price * volume * multiplier + commission
        if required_capital > self.current_capital:
            logger.warning(f"资金不足，无法开空仓: {symbol}")
            return False
        
        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            if pos.direction == Direction.LONG:
                # 如果已有多仓，先平多
                self.close_long(symbol, actual_price, min(volume, pos.volume), time)
                volume -= min(volume, pos.volume)
                if volume <= 0:
                    return True
            
            if pos.direction == Direction.SHORT:
                # 加仓
                total_volume = pos.volume + volume
                total_cost = pos.entry_price * pos.volume + actual_price * volume
                pos.entry_price = total_cost / total_volume
                pos.volume = total_volume
            else:
                # 新建空仓
                pos = Position(
                    symbol=symbol,
                    direction=Direction.SHORT,
                    volume=volume,
                    entry_price=actual_price,
                    entry_time=time,
                    current_price=actual_price,
                    multiplier=multiplier
                )
                self.positions[symbol] = pos
        else:
            # 新建空仓
            pos = Position(
                symbol=symbol,
                direction=Direction.SHORT,
                volume=volume,
                entry_price=actual_price,
                entry_time=time,
                current_price=actual_price,
                multiplier=multiplier
            )
            self.positions[symbol] = pos
        
        # 扣除资金
        self.current_capital -= required_capital
        
        # 记录交易
        trade = Trade(
            symbol=symbol,
            direction=Direction.SHORT,
            volume=volume,
            price=actual_price,
            time=time,
            trade_id=f"{symbol}_{time.strftime('%Y%m%d%H%M%S')}",
            commission=commission
        )
        self.trades.append(trade)
        
        logger.info(f"开空仓: {symbol}, 价格={actual_price}, 数量={volume}, 资金={self.current_capital:.2f}")
        return True
    
    def close_short(self, symbol: str, price: float, volume: int,
                    time: datetime) -> bool:
        """
        平空仓
        
        Args:
            symbol: 合约代码
            price: 平仓价
            volume: 数量
            time: 时间
        
        Returns:
            是否成功
        """
        if symbol not in self.positions:
            logger.warning(f"无持仓，无法平空仓: {symbol}")
            return False
        
        pos = self.positions[symbol]
        if pos.direction != Direction.SHORT:
            logger.warning(f"持仓方向不匹配，无法平空仓: {symbol}")
            return False
        
        if volume > pos.volume:
            volume = pos.volume
        
        # 计算实际价格
        actual_price = price * (1 + self.slippage)
        
        # 计算盈亏和手续费
        multiplier = pos.multiplier
        pnl = calculate_pnl(pos.entry_price, actual_price, volume, -1, multiplier)
        commission = actual_price * volume * multiplier * self.commission_rate
        
        # 更新资金
        self.current_capital += actual_price * volume * multiplier - commission + pnl
        
        # 更新持仓
        pos.volume -= volume
        if pos.volume == 0:
            del self.positions[symbol]
        
        # 记录交易
        trade = Trade(
            symbol=symbol,
            direction=Direction.SHORT,
            volume=-volume,
            price=actual_price,
            time=time,
            trade_id=f"{symbol}_{time.strftime('%Y%m%d%H%M%S')}",
            commission=commission
        )
        self.trades.append(trade)
        
        logger.info(f"平空仓: {symbol}, 价格={actual_price}, 数量={volume}, 盈亏={pnl:.2f}, 资金={self.current_capital:.2f}")
        return True
    
    def update_price(self, symbol: str, price: float):
        """更新持仓价格"""
        if symbol in self.positions:
            self.positions[symbol].update_price(price)
    
    def get_total_equity(self) -> float:
        """获取总权益（资金 + 持仓浮动盈亏）"""
        total_pnl = sum(pos.get_pnl() for pos in self.positions.values())
        return self.current_capital + total_pnl
    
    def record_equity(self, time: datetime):
        """记录权益曲线"""
        equity = self.get_total_equity()
        self.equity_curve.append(equity)
        self.equity_times.append(time)
    
    def get_trades(self) -> List[Trade]:
        """获取所有交易记录"""
        return self.trades.copy()

