"""
系统配置
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """系统配置类"""
    
    # CTP连接配置 - SimNow 模拟环境
    # BrokerID统一为：9999
    # 支持上期所期权、能源中心期权、中金所期权、广期所期权、郑商所期权、大商所期权
    # 三组服务器（看穿式前置，使用监控中心生产秘钥）：
    # 第一组: Trade 182.254.243.31:30001, Market 182.254.243.31:30011
    # 第二组: Trade 182.254.243.31:30002, Market 182.254.243.31:30012
    # 第三组: Trade 182.254.243.31:30003, Market 182.254.243.31:30013
    CTP_BROKER_ID: str = os.getenv('CTP_BROKER_ID', '9999')
    CTP_USER_ID: str = os.getenv('CTP_USER_ID', '')
    CTP_PASSWORD: str = os.getenv('CTP_PASSWORD', '')
    CTP_MD_ADDRESS: str = os.getenv('CTP_MD_ADDRESS', 'tcp://182.254.243.31:30011')  # 第一组行情服务器
    CTP_TRADE_ADDRESS: str = os.getenv('CTP_TRADE_ADDRESS', 'tcp://182.254.243.31:30001')  # 第一组交易服务器
    CTP_APP_ID: str = os.getenv('CTP_APP_ID', 'simnow_client_test')
    CTP_AUTH_CODE: str = os.getenv('CTP_AUTH_CODE', '0000000000000000')
    
    # 数据库配置
    DB_URL: Optional[str] = os.getenv('DB_URL', None)  # 如果为None，使用默认SQLite
    DB_ECHO: bool = os.getenv('DB_ECHO', 'False').lower() == 'true'
    
    # 日志配置
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')
    
    # 回测配置
    BACKTEST_INITIAL_CAPITAL: float = float(os.getenv('BACKTEST_INITIAL_CAPITAL', '1000000.0'))
    BACKTEST_COMMISSION_RATE: float = float(os.getenv('BACKTEST_COMMISSION_RATE', '0.0001'))
    BACKTEST_SLIPPAGE: float = float(os.getenv('BACKTEST_SLIPPAGE', '0.0'))
    
    # 数据存储配置
    DATA_DIR: str = os.getenv('DATA_DIR', 'data')
    
    @classmethod
    def validate_ctp_config(cls) -> bool:
        """验证CTP配置是否完整"""
        required_fields = [
            cls.CTP_BROKER_ID,
            cls.CTP_USER_ID,
            cls.CTP_PASSWORD,
        ]
        return all(field for field in required_fields)
    
    @classmethod
    def get_ctp_config(cls) -> dict:
        """获取CTP配置字典"""
        return {
            'broker_id': cls.CTP_BROKER_ID,
            'user_id': cls.CTP_USER_ID,
            'password': cls.CTP_PASSWORD,
            'md_address': cls.CTP_MD_ADDRESS,
            'trade_address': cls.CTP_TRADE_ADDRESS,
            'app_id': cls.CTP_APP_ID,
            'auth_code': cls.CTP_AUTH_CODE,
        }


# 全局配置实例
settings = Settings()

