"""
资金限制风控
"""
from typing import Optional, Dict
from datetime import datetime, timedelta
from risk.risk_rules import RiskResult, RiskLevel
from backtest.portfolio import Portfolio
from utils.logger import get_logger

logger = get_logger(__name__)


class CapitalLimit:
    """资金限制"""
    
    def __init__(self,
                 max_order_amount: Optional[float] = None,
                 max_daily_loss: Optional[float] = None,
                 max_daily_loss_ratio: Optional[float] = None,
                 min_available_ratio: Optional[float] = None):
        """
        初始化资金限制
        
        Args:
            max_order_amount: 单笔订单最大金额
            max_daily_loss: 单日最大亏损金额
            max_daily_loss_ratio: 单日最大亏损比例（0-1）
            min_available_ratio: 账户可用资金最小比例（0-1）
        """
        self.max_order_amount = max_order_amount
        self.max_daily_loss = max_daily_loss
        self.max_daily_loss_ratio = max_daily_loss_ratio
        self.min_available_ratio = min_available_ratio
        
        # 记录每日盈亏
        self.daily_pnl: Dict[str, float] = {}  # {date: pnl}
        self.daily_start_equity: Dict[str, float] = {}  # {date: start_equity}
        
        logger.info(f"资金限制初始化: 单笔最大={max_order_amount}, "
                   f"日亏损限制={max_daily_loss}, 日亏损比例={max_daily_loss_ratio}")
    
    def check_capital_risk(self,
                          order_amount: float,
                          portfolio: Portfolio) -> RiskResult:
        """
        检查资金风险
        
        Args:
            order_amount: 订单金额
            portfolio: 组合对象
            
        Returns:
            风控结果
        """
        total_equity = portfolio.get_total_equity()
        
        # 检查单笔订单最大金额
        if self.max_order_amount is not None:
            if order_amount > self.max_order_amount:
                return RiskResult.block(
                    f"单笔订单金额超限",
                    f"订单金额{order_amount:,.2f}，超过限制{self.max_order_amount:,.2f}"
                )
        
        # 检查账户可用资金比例
        if self.min_available_ratio is not None:
            available_capital = portfolio.current_capital
            available_ratio = available_capital / total_equity if total_equity > 0 else 0
            
            if available_ratio < self.min_available_ratio:
                return RiskResult.block(
                    f"账户可用资金比例不足",
                    f"可用资金比例{available_ratio*100:.2f}%，"
                    f"低于限制{self.min_available_ratio*100:.2f}%"
                )
        
        return RiskResult.safe("资金风控检查通过")
    
    def check_daily_loss(self, portfolio: Portfolio) -> RiskResult:
        """
        检查单日亏损
        
        Args:
            portfolio: 组合对象
            
        Returns:
            风控结果
        """
        today = datetime.now().strftime('%Y-%m-%d')
        total_equity = portfolio.get_total_equity()
        
        # 初始化今日记录
        if today not in self.daily_start_equity:
            self.daily_start_equity[today] = total_equity
            self.daily_pnl[today] = 0.0
        
        # 计算今日盈亏
        start_equity = self.daily_start_equity[today]
        daily_pnl = total_equity - start_equity
        self.daily_pnl[today] = daily_pnl
        
        # 检查单日最大亏损金额
        if self.max_daily_loss is not None:
            if daily_pnl < -self.max_daily_loss:
                return RiskResult.block(
                    f"单日亏损超限",
                    f"今日亏损{abs(daily_pnl):,.2f}，超过限制{self.max_daily_loss:,.2f}"
                )
        
        # 检查单日最大亏损比例
        if self.max_daily_loss_ratio is not None and start_equity > 0:
            loss_ratio = abs(daily_pnl) / start_equity
            if daily_pnl < 0 and loss_ratio > self.max_daily_loss_ratio:
                return RiskResult.block(
                    f"单日亏损比例超限",
                    f"今日亏损比例{loss_ratio*100:.2f}%，"
                    f"超过限制{self.max_daily_loss_ratio*100:.2f}%"
                )
        
        # 警告级别检查
        if daily_pnl < 0:
            if self.max_daily_loss and abs(daily_pnl) > self.max_daily_loss * 0.8:
                return RiskResult.warning(
                    f"单日亏损接近限制",
                    f"今日亏损{abs(daily_pnl):,.2f}，接近限制{self.max_daily_loss:,.2f}"
                )
        
        return RiskResult.safe("单日亏损检查通过")
    
    def reset_daily_stats(self):
        """重置每日统计（通常在交易日开始时调用）"""
        today = datetime.now().strftime('%Y-%m-%d')
        # 清理旧数据（保留最近7天）
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        self.daily_pnl = {k: v for k, v in self.daily_pnl.items() if k >= cutoff_date}
        self.daily_start_equity = {k: v for k, v in self.daily_start_equity.items() if k >= cutoff_date}
        
        logger.info(f"每日统计已重置: {today}")

