"""
绩效分析模块
"""
from typing import List, Optional
import numpy as np
from datetime import datetime

from backtest.portfolio import Portfolio, Trade
from utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, portfolio: Portfolio):
        """
        初始化绩效分析器
        
        Args:
            portfolio: 组合对象
        """
        self.portfolio = portfolio
    
    def calculate_total_return(self) -> float:
        """
        计算总收益率
        
        Returns:
            总收益率（百分比）
        """
        initial = self.portfolio.initial_capital
        final = self.portfolio.get_total_equity()
        return (final - initial) / initial * 100
    
    def calculate_annual_return(self, days: int) -> float:
        """
        计算年化收益率
        
        Args:
            days: 回测天数
        
        Returns:
            年化收益率（百分比）
        """
        total_return = self.calculate_total_return() / 100
        if days <= 0:
            return 0.0
        years = days / 252  # 假设一年252个交易日
        if years <= 0:
            return 0.0
        annual_return = (1 + total_return) ** (1 / years) - 1
        return annual_return * 100
    
    def calculate_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns:
            最大回撤（百分比）
        """
        equity_curve = np.array(self.portfolio.equity_curve)
        if len(equity_curve) == 0:
            return 0.0
        
        # 计算累计最高值
        cummax = np.maximum.accumulate(equity_curve)
        
        # 计算回撤
        drawdown = (equity_curve - cummax) / cummax * 100
        
        # 最大回撤
        max_dd = np.min(drawdown)
        return abs(max_dd)
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        计算夏普比率
        
        Args:
            risk_free_rate: 无风险利率（年化）
        
        Returns:
            夏普比率
        """
        equity_curve = np.array(self.portfolio.equity_curve)
        if len(equity_curve) < 2:
            return 0.0
        
        # 计算收益率序列
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        # 年化收益率
        mean_return = np.mean(returns) * 252
        
        # 年化波动率
        std_return = np.std(returns) * np.sqrt(252)
        
        # 夏普比率
        sharpe = (mean_return - risk_free_rate) / std_return
        return sharpe
    
    def calculate_win_rate(self) -> float:
        """
        计算胜率
        
        Returns:
            胜率（百分比）
        """
        trades = self.portfolio.get_trades()
        if len(trades) == 0:
            return 0.0
        
        # 计算每笔交易的盈亏
        # 这里简化处理，实际应该配对开平仓
        winning_trades = 0
        total_trades = 0
        
        # 按合约分组计算
        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)
        
        for symbol, symbol_trade_list in symbol_trades.items():
            # 配对开平仓
            positions = {}
            for trade in symbol_trade_list:
                if trade.volume > 0:  # 开仓
                    key = (trade.symbol, trade.direction)
                    if key not in positions:
                        positions[key] = []
                    positions[key].append(trade)
                else:  # 平仓
                    key = (trade.symbol, trade.direction)
                    if key in positions and len(positions[key]) > 0:
                        open_trade = positions[key].pop(0)
                        # 计算盈亏
                        if trade.direction.value == 1:  # 多仓
                            pnl = (trade.price - open_trade.price) * abs(trade.volume)
                        else:  # 空仓
                            pnl = (open_trade.price - trade.price) * abs(trade.volume)
                        
                        total_trades += 1
                        if pnl > 0:
                            winning_trades += 1
        
        if total_trades == 0:
            return 0.0
        
        return winning_trades / total_trades * 100
    
    def calculate_profit_factor(self) -> float:
        """
        计算盈亏比
        
        Returns:
            盈亏比
        """
        trades = self.portfolio.get_trades()
        if len(trades) == 0:
            return 0.0
        
        total_profit = 0.0
        total_loss = 0.0
        
        # 按合约分组计算（简化处理）
        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)
        
        for symbol, symbol_trade_list in symbol_trades.items():
            positions = {}
            for trade in symbol_trade_list:
                if trade.volume > 0:  # 开仓
                    key = (trade.symbol, trade.direction)
                    if key not in positions:
                        positions[key] = []
                    positions[key].append(trade)
                else:  # 平仓
                    key = (trade.symbol, trade.direction)
                    if key in positions and len(positions[key]) > 0:
                        open_trade = positions[key].pop(0)
                        # 计算盈亏
                        if trade.direction.value == 1:  # 多仓
                            pnl = (trade.price - open_trade.price) * abs(trade.volume)
                        else:  # 空仓
                            pnl = (open_trade.price - trade.price) * abs(trade.volume)
                        
                        if pnl > 0:
                            total_profit += pnl
                        else:
                            total_loss += abs(pnl)
        
        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0
        
        return total_profit / total_loss
    
    def get_statistics(self, days: int = 0) -> dict:
        """
        获取完整的绩效统计
        
        Args:
            days: 回测天数
        
        Returns:
            统计字典
        """
        stats = {
            'initial_capital': self.portfolio.initial_capital,
            'final_equity': self.portfolio.get_total_equity(),
            'total_return': self.calculate_total_return(),
            'max_drawdown': self.calculate_max_drawdown(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'win_rate': self.calculate_win_rate(),
            'profit_factor': self.calculate_profit_factor(),
            'total_trades': len(self.portfolio.get_trades()),
            'total_positions': len(self.portfolio.get_all_positions()),
        }
        
        if days > 0:
            stats['annual_return'] = self.calculate_annual_return(days)
        
        return stats
    
    def print_statistics(self, days: int = 0):
        """
        打印绩效统计
        
        Args:
            days: 回测天数
        """
        stats = self.get_statistics(days)
        
        print("\n" + "=" * 50)
        print("回测绩效统计")
        print("=" * 50)
        print(f"初始资金: {stats['initial_capital']:,.2f}")
        print(f"最终权益: {stats['final_equity']:,.2f}")
        print(f"总收益率: {stats['total_return']:.2f}%")
        if days > 0:
            print(f"年化收益率: {stats['annual_return']:.2f}%")
        print(f"最大回撤: {stats['max_drawdown']:.2f}%")
        print(f"夏普比率: {stats['sharpe_ratio']:.2f}")
        print(f"胜率: {stats['win_rate']:.2f}%")
        print(f"盈亏比: {stats['profit_factor']:.2f}")
        print(f"总交易次数: {stats['total_trades']}")
        print(f"当前持仓数: {stats['total_positions']}")
        print("=" * 50 + "\n")

