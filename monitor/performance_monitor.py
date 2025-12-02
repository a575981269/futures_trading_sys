"""
性能监控
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque

from backtest.portfolio import Portfolio
from trading.order import Order
from utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """性能监控"""
    
    def __init__(self, portfolio: Optional[Portfolio] = None):
        """
        初始化性能监控
        
        Args:
            portfolio: 组合对象
        """
        self.portfolio = portfolio
        
        # 权益曲线
        self.equity_history: deque = deque(maxlen=10000)
        self.equity_times: deque = deque(maxlen=10000)
        
        # 交易统计
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        
        # 实时指标
        self.current_equity = 0.0
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_equity = 0.0
        
        logger.info("性能监控初始化完成")
    
    def update_equity(self, equity: float, timestamp: datetime = None):
        """
        更新权益
        
        Args:
            equity: 当前权益
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.current_equity = equity
        self.equity_history.append(equity)
        self.equity_times.append(timestamp)
        
        # 更新峰值权益
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        # 计算最大回撤
        if self.peak_equity > 0:
            drawdown = (equity - self.peak_equity) / self.peak_equity * 100
            if drawdown < self.max_drawdown:
                self.max_drawdown = drawdown
    
    def record_trade(self, order: Order, pnl: float):
        """
        记录交易
        
        Args:
            order: 订单对象
            pnl: 盈亏
        """
        if order.is_filled():
            self.trade_count += 1
            
            if pnl > 0:
                self.win_count += 1
                self.total_profit += pnl
            elif pnl < 0:
                self.loss_count += 1
                self.total_loss += abs(pnl)
    
    def get_win_rate(self) -> float:
        """获取胜率"""
        if self.trade_count == 0:
            return 0.0
        return self.win_count / self.trade_count * 100
    
    def get_profit_factor(self) -> float:
        """获取盈亏比"""
        if self.total_loss == 0:
            return float('inf') if self.total_profit > 0 else 0.0
        return self.total_profit / self.total_loss
    
    def get_daily_return(self) -> float:
        """获取今日收益率"""
        if len(self.equity_history) < 2:
            return 0.0
        
        # 获取今日开始时的权益
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_equity = self.current_equity
        
        # 查找今日第一个权益记录
        for i, t in enumerate(self.equity_times):
            if t >= today_start:
                if i > 0:
                    start_equity = self.equity_history[i - 1]
                break
        
        if start_equity > 0:
            return (self.current_equity - start_equity) / start_equity * 100
        return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            指标字典
        """
        metrics = {
            'current_equity': self.current_equity,
            'daily_return': self.get_daily_return(),
            'max_drawdown': abs(self.max_drawdown),
            'trade_count': self.trade_count,
            'win_rate': self.get_win_rate(),
            'profit_factor': self.get_profit_factor(),
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
        }
        
        if self.portfolio:
            metrics['total_positions'] = len(self.portfolio.get_all_positions())
        
        return metrics
    
    def reset_daily_stats(self):
        """重置每日统计"""
        self.daily_pnl = 0.0
        logger.info("性能监控每日统计已重置")

