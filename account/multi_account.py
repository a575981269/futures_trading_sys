"""
多账户管理
"""
from typing import Dict, List, Optional, Any
from account.account_manager import AccountManager, AccountType
from utils.logger import get_logger

logger = get_logger(__name__)


class MultiAccount:
    """多账户管理"""
    
    def __init__(self):
        """初始化多账户管理"""
        self.account_manager = AccountManager()
        logger.info("多账户管理初始化完成")
    
    def add_sim_account(self,
                       account_id: str,
                       initial_capital: float = 1000000.0,
                       commission_rate: float = 0.0001,
                       slippage: float = 0.0,
                       is_default: bool = False):
        """
        添加模拟账户
        
        Args:
            account_id: 账户ID
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
            is_default: 是否设为默认账户
        """
        from trading.sim_account import SimAccount
        
        account = SimAccount(
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage=slippage
        )
        
        self.account_manager.add_account(account_id, account, is_default)
        logger.info(f"模拟账户已添加: {account_id}")
    
    def add_live_account(self,
                        account_id: str,
                        trading_interface: Any,
                        is_default: bool = False):
        """
        添加实盘账户
        
        Args:
            account_id: 账户ID
            trading_interface: 交易接口
            is_default: 是否设为默认账户
        """
        from trading.live_account import LiveAccount
        
        account = LiveAccount(trading_interface)
        self.account_manager.add_account(account_id, account, is_default)
        logger.info(f"实盘账户已添加: {account_id}")
    
    def switch_account(self, account_id: str) -> bool:
        """
        切换账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            是否成功
        """
        return self.account_manager.set_current_account(account_id)
    
    def get_total_capital(self) -> float:
        """获取总资金（所有账户）"""
        total = 0.0
        for account_id, account in self.account_manager.get_all_accounts().items():
            info = self.account_manager.get_account_info(account_id)
            if info:
                total += info.get('balance', 0.0) or info.get('equity', 0.0)
        return total
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """
        获取账户统计
        
        Returns:
            统计字典
        """
        accounts = self.account_manager.get_all_accounts()
        stats = {
            'total_accounts': len(accounts),
            'current_account': self.account_manager.current_account_id,
            'total_capital': self.get_total_capital(),
            'accounts': []
        }
        
        for account_id, account in accounts.items():
            info = self.account_manager.get_account_info(account_id)
            if info:
                stats['accounts'].append({
                    'account_id': account_id,
                    'info': info
                })
        
        return stats

