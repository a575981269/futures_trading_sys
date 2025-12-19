"""
风控管理器
"""
from typing import Optional, Dict, Any
from datetime import datetime
from risk.risk_rules import RiskResult, RiskLevel
from risk.position_limit import PositionLimit
from risk.capital_limit import CapitalLimit
from risk.order_limit import OrderLimit
from trading.order import Order, OrderDirection
from backtest.portfolio import Portfolio, Direction
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskManager:
    """风控管理器"""
    
    def __init__(self,
                 position_limit: Optional[PositionLimit] = None,
                 capital_limit: Optional[CapitalLimit] = None,
                 order_limit: Optional[OrderLimit] = None,
                 enable_risk_control: bool = True):
        """
        初始化风控管理器
        
        Args:
            position_limit: 持仓限制
            capital_limit: 资金限制
            order_limit: 订单限制
            enable_risk_control: 是否启用风控
        """
        self.position_limit = position_limit
        self.capital_limit = capital_limit
        self.order_limit = order_limit
        self.enable_risk_control = enable_risk_control
        
        logger.info(f"风控管理器初始化: 启用={enable_risk_control}")
    
    def check_order_risk(self,
                        order: Order,
                        portfolio: Portfolio,
                        current_price: Optional[float] = None) -> RiskResult:
        """
        检查订单风险（综合检查）
        
        Args:
            order: 订单对象
            portfolio: 组合对象
            current_price: 当前价格
            
        Returns:
            风控结果
        """
        # #region agent log
        import json
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"risk_manager.py:check_order_risk","message":"Risk check started","data":{"symbol":order.symbol,"enable_risk_control":self.enable_risk_control,"has_order_limit":self.order_limit is not None,"has_capital_limit":self.capital_limit is not None,"has_position_limit":self.position_limit is not None,"current_price":current_price},"timestamp":int(__import__('time').time()*1000)})+'\n')
        except: pass
        # #endregion
        
        if not self.enable_risk_control:
            return RiskResult.safe("风控已禁用")
        
        # 订单限制检查
        if self.order_limit:
            result = self.order_limit.check_order_risk(order, current_price)
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"risk_manager.py:check_order_risk","message":"Order limit check result","data":{"passed":result.passed,"reason":result.reason},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
            if not result.passed:
                logger.warning(f"订单风控失败: {result.reason}")
                return result
        
        # 计算订单金额
        from config.contracts import get_contract_multiplier
        multiplier = get_contract_multiplier(order.symbol)
        order_amount = order.price * order.volume * multiplier
        
        # 资金限制检查
        if self.capital_limit:
            result = self.capital_limit.check_capital_risk(order_amount, portfolio)
            if not result.passed:
                logger.warning(f"资金风控失败: {result.reason}")
                return result
            
            # 检查单日亏损
            result = self.capital_limit.check_daily_loss(portfolio)
            if not result.passed:
                logger.warning(f"单日亏损风控失败: {result.reason}")
                return result
        
        # 持仓限制检查
        if self.position_limit and current_price:
            # 确定持仓方向
            # 买入开仓或平空 -> 多仓
            # 卖出开仓或平多 -> 空仓
            if order.direction in [OrderDirection.BUY, OrderDirection.COVER]:
                direction = Direction.LONG
            else:
                direction = Direction.SHORT
            
            if order.direction in [OrderDirection.SELL, OrderDirection.COVER]:
                # 平仓操作，检查持仓是否存在
                pos = portfolio.get_position(order.symbol)
                if not pos:
                    return RiskResult.block(
                        f"无持仓无法平仓: {order.symbol}",
                        "持仓风控检查失败"
                    )
            else:
                # 开仓操作
                result = self.position_limit.check_position_risk(
                    order.symbol,
                    order.volume,
                    direction,
                    portfolio,
                    current_price
                )
                if not result.passed:
                    logger.warning(f"持仓风控失败: {result.reason}")
                    return result
        
        return RiskResult.safe("订单风控检查通过")
    
    def check_position_risk(self,
                           symbol: str,
                           volume: int,
                           direction: Direction,
                           portfolio: Portfolio,
                           current_price: float) -> RiskResult:
        """
        检查持仓风险
        
        Args:
            symbol: 合约代码
            volume: 持仓数量
            direction: 持仓方向
            portfolio: 组合对象
            current_price: 当前价格
            
        Returns:
            风控结果
        """
        if not self.enable_risk_control:
            return RiskResult.safe("风控已禁用")
        
        if self.position_limit:
            return self.position_limit.check_position_risk(
                symbol, volume, direction, portfolio, current_price
            )
        
        return RiskResult.safe("持仓风控检查通过")
    
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
        if not self.enable_risk_control:
            return RiskResult.safe("风控已禁用")
        
        if self.capital_limit:
            result = self.capital_limit.check_capital_risk(order_amount, portfolio)
            if not result.passed:
                return result
            
            return self.capital_limit.check_daily_loss(portfolio)
        
        return RiskResult.safe("资金风控检查通过")
    
    def get_risk_metrics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        获取风险指标
        
        Args:
            portfolio: 组合对象
            
        Returns:
            风险指标字典
        """
        metrics = {
            'total_equity': portfolio.get_total_equity(),
            'available_capital': portfolio.current_capital,
            'total_positions': len(portfolio.get_all_positions()),
            'position_symbols': [pos.symbol for pos in portfolio.get_all_positions()],
        }
        
        # 计算总持仓价值
        total_position_value = 0.0
        for pos in portfolio.get_all_positions():
            from config.contracts import get_contract_multiplier
            multiplier = get_contract_multiplier(pos.symbol)
            total_position_value += pos.current_price * pos.volume * multiplier
        
        metrics['total_position_value'] = total_position_value
        
        if portfolio.get_total_equity() > 0:
            metrics['position_ratio'] = total_position_value / portfolio.get_total_equity()
        else:
            metrics['position_ratio'] = 0.0
        
        # 单日盈亏
        if self.capital_limit:
            today = datetime.now().strftime('%Y-%m-%d')
            metrics['daily_pnl'] = self.capital_limit.daily_pnl.get(today, 0.0)
        
        return metrics
    
    def reset_daily_stats(self):
        """重置每日统计"""
        if self.capital_limit:
            self.capital_limit.reset_daily_stats()
        logger.info("风控每日统计已重置")

