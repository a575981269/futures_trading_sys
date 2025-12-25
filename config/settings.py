"""
系统配置
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
# 指定 UTF-8 编码以避免中文注释导致的编码错误
try:
    load_dotenv(encoding='utf-8')
except UnicodeDecodeError as e:
    # 如果遇到编码错误，尝试修复 .env 文件编码
    try:
        import codecs
        # 尝试以不同编码读取并转换为 UTF-8
        for encoding in ['gbk', 'gb2312', 'latin1']:
            try:
                with codecs.open('.env', 'r', encoding=encoding) as f:
                    content = f.read()
                with codecs.open('.env', 'w', encoding='utf-8') as f:
                    f.write(content)
                load_dotenv(encoding='utf-8')
                break
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue
        else:
            raise Exception(f"无法读取 .env 文件，请确保文件编码为 UTF-8: {e}")
    except Exception as ex:
        raise Exception(f"无法修复 .env 文件编码: {ex}")
except Exception as e:
    # 其他错误，尝试默认方式
    load_dotenv()


class Settings:
    """系统配置类"""
    
    # 环境类型常量
    CTP_ENV_NORMAL = "normal"  # CTP主席系统（正常交易时间）
    CTP_ENV_7X24 = "7x24"      # 7x24环境（全天候）
    
    # CTP连接配置 - SimNow 模拟环境
    # BrokerID统一为：9999
    # 支持上期所期权、能源中心期权、中金所期权、广期所期权、郑商所期权、大商所期权
    # 
    # 服务器地址配置（可在 .env 文件中设置）：
    # CTP主席系统（正常交易时间）：
    #   - 第一组: Trade 182.254.243.31:30001, Market 182.254.243.31:30011
    #   - 第二组: Trade 182.254.243.31:30002, Market 182.254.243.31:30012
    #   - 第三组: Trade 182.254.243.31:30003, Market 182.254.243.31:30013
    # 7x24环境（全天候）：
    #   - Trade 182.254.243.31:40001, Market 182.254.243.31:40011
    # 
    # 环境变量说明：
    # - CTP_MD_ADDRESS_NORMAL / CTP_TRADE_ADDRESS_NORMAL: CTP主席系统地址（优先）
    # - CTP_MD_ADDRESS_7X24 / CTP_TRADE_ADDRESS_7X24: 7x24环境地址（优先）
    # - CTP_MD_ADDRESS / CTP_TRADE_ADDRESS: 通用地址（如果环境特定变量未设置则使用）
    CTP_BROKER_ID: str = os.getenv('CTP_BROKER_ID', '9999')
    CTP_USER_ID: str = os.getenv('CTP_USER_ID', '')
    CTP_PASSWORD: str = os.getenv('CTP_PASSWORD', '')
    CTP_ENVIRONMENT: str = os.getenv('CTP_ENVIRONMENT', CTP_ENV_NORMAL)  # 环境类型：normal 或 7x24
    CTP_APP_ID: str = os.getenv('CTP_APP_ID', 'simnow_client_test')
    CTP_AUTH_CODE: str = os.getenv('CTP_AUTH_CODE', '0000000000000000')
    
    # 注意：以下变量已废弃，请使用环境特定的变量（CTP_MD_ADDRESS_NORMAL/7X24等）
    # 保留这些变量仅用于向后兼容
    CTP_MD_ADDRESS: str = os.getenv('CTP_MD_ADDRESS', '')  # 已废弃，请使用环境特定变量
    CTP_TRADE_ADDRESS: str = os.getenv('CTP_TRADE_ADDRESS', '')  # 已废弃，请使用环境特定变量
    
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
    def is_7x24_environment(cls, env_type: Optional[str] = None) -> bool:
        """检查是否为7x24环境"""
        if env_type is None:
            env_type = cls.CTP_ENVIRONMENT
        return env_type == cls.CTP_ENV_7X24
    
    @classmethod
    def get_server_addresses(cls, env_type: Optional[str] = None) -> dict:
        """
        根据环境类型获取服务器地址
        
        Args:
            env_type: 环境类型（normal 或 7x24），如果为None则使用配置中的环境类型
        
        Returns:
            包含 md_address 和 trade_address 的字典
        """
        if env_type is None:
            env_type = cls.CTP_ENVIRONMENT
        
        # #region agent log
        import json
        import time
        try:
            with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"settings.py:get_server_addresses","message":"Getting server addresses","data":{"env_type":env_type,"CTP_ENV_7X24":cls.CTP_ENV_7X24,"CTP_ENV_NORMAL":cls.CTP_ENV_NORMAL,"env_var_md":os.getenv('CTP_MD_ADDRESS'),"env_var_trade":os.getenv('CTP_TRADE_ADDRESS'),"env_var_md_7x24":os.getenv('CTP_MD_ADDRESS_7X24'),"env_var_trade_7x24":os.getenv('CTP_TRADE_ADDRESS_7X24'),"env_var_md_normal":os.getenv('CTP_MD_ADDRESS_NORMAL'),"env_var_trade_normal":os.getenv('CTP_TRADE_ADDRESS_NORMAL')},"timestamp":int(time.time()*1000)})+'\n')
        except: pass
        # #endregion
        
        if env_type == cls.CTP_ENV_7X24:
            # 7x24环境服务器地址
            # 优先使用环境特定的变量，如果没有则使用通用变量，最后使用默认值
            md_address = os.getenv('CTP_MD_ADDRESS_7X24') or os.getenv('CTP_MD_ADDRESS') or 'tcp://182.254.243.31:40011'
            trade_address = os.getenv('CTP_TRADE_ADDRESS_7X24') or os.getenv('CTP_TRADE_ADDRESS') or 'tcp://182.254.243.31:40001'
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"settings.py:get_server_addresses","message":"7x24 addresses selected","data":{"md_address":md_address,"trade_address":trade_address},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            return {
                'md_address': md_address,
                'trade_address': trade_address,
            }
        else:
            # CTP主席系统（正常交易时间）服务器地址
            # 优先使用环境特定的变量，如果没有则使用通用变量，最后使用默认值
            md_address = os.getenv('CTP_MD_ADDRESS_NORMAL') or os.getenv('CTP_MD_ADDRESS') or 'tcp://182.254.243.31:30011'
            trade_address = os.getenv('CTP_TRADE_ADDRESS_NORMAL') or os.getenv('CTP_TRADE_ADDRESS') or 'tcp://182.254.243.31:30001'
            
            # #region agent log
            try:
                with open(r'c:\Users\lenovo\Desktop\futures_trading_sys\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"settings.py:get_server_addresses","message":"Normal addresses selected","data":{"md_address":md_address,"trade_address":trade_address},"timestamp":int(time.time()*1000)})+'\n')
            except: pass
            # #endregion
            
            return {
                'md_address': md_address,
                'trade_address': trade_address,
            }
    
    @classmethod
    def get_ctp_config(cls, env_type: Optional[str] = None) -> dict:
        """
        获取CTP配置字典
        
        Args:
            env_type: 环境类型（normal 或 7x24），如果为None则使用配置中的环境类型
        """
        addresses = cls.get_server_addresses(env_type)
        return {
            'broker_id': cls.CTP_BROKER_ID,
            'user_id': cls.CTP_USER_ID,
            'password': cls.CTP_PASSWORD,
            'md_address': addresses['md_address'],
            'trade_address': addresses['trade_address'],
            'app_id': cls.CTP_APP_ID,
            'auth_code': cls.CTP_AUTH_CODE,
            'environment': env_type or cls.CTP_ENVIRONMENT,
        }


# 全局配置实例
settings = Settings()

