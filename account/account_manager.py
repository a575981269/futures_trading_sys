"""
账户管理器
"""
from typing import Dict, Optional, Any
from enum import Enum

from trading.sim_account import SimAccount
from trading.live_account import LiveAccount
from utils.logger import get_logger

logger = get_logger(__name__)


class AccountType(Enum):
    """账户类型"""
    SIM = "SIM"      # 模拟账户
    LIVE = "LIVE"    # 实盘账户


class AccountManager:
    """账户管理器"""
    
    def __init__(self):
        """初始化账户管理器"""
        self.accounts: Dict[str, Any] = {}  # {account_id: Account}
        self.current_account_id: Optional[str] = None
        
        logger.info("账户管理器初始化完成")
    
    def add_account(self,
                   account_id: str,
                   account: Any,
                   is_default: bool = False):
        """
        添加账户
        
        Args:
            account_id: 账户ID
            account: 账户对象（SimAccount或LiveAccount）
            is_default: 是否设为默认账户
        """
        self.accounts[account_id] = account
        
        if is_default or self.current_account_id is None:
            self.current_account_id = account_id
        
        logger.info(f"账户已添加: {account_id}, 默认={is_default}")
    
    def remove_account(self, account_id: str) -> bool:
        """
        移除账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            是否成功
        """
        if account_id not in self.accounts:
            return False
        
        # 如果移除的是当前账户，切换到其他账户
        if self.current_account_id == account_id:
            other_accounts = [aid for aid in self.accounts.keys() if aid != account_id]
            if other_accounts:
                self.current_account_id = other_accounts[0]
            else:
                self.current_account_id = None
        
        del self.accounts[account_id]
        logger.info(f"账户已移除: {account_id}")
        return True
    
    def set_current_account(self, account_id: str) -> bool:
        """
        设置当前账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            是否成功
        """
        if account_id not in self.accounts:
            logger.error(f"账户不存在: {account_id}")
            return False
        
        self.current_account_id = account_id
        logger.info(f"当前账户已切换: {account_id}")
        return True
    
    def get_current_account(self) -> Optional[Any]:
        """获取当前账户"""
        if self.current_account_id:
            return self.accounts.get(self.current_account_id)
        return None
    
    def get_account(self, account_id: str) -> Optional[Any]:
        """获取指定账户"""
        return self.accounts.get(account_id)
    
    def get_all_accounts(self) -> Dict[str, Any]:
        """获取所有账户"""
        return self.accounts.copy()
    
    def get_account_info(self, account_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取账户信息
        
        Args:
            account_id: 账户ID，如果为None则获取当前账户
            
        Returns:
            账户信息字典
        """
        if account_id is None:
            account = self.get_current_account()
        else:
            account = self.get_account(account_id)
        
        if account is None:
            return None
        
        # 根据账户类型获取信息
        if isinstance(account, SimAccount):
            return account.get_account_info()
        elif isinstance(account, LiveAccount):
            return account.get_account_info()
        
        return None

