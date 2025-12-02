"""
合约配置
"""
from typing import Dict, Optional
from database.models import ContractInfo


# 常见期货合约配置
CONTRACT_CONFIGS: Dict[str, Dict] = {
    # 上期所
    'rb': {'exchange': 'SHFE', 'name': '螺纹钢', 'size': 10, 'price_tick': 1.0},
    'hc': {'exchange': 'SHFE', 'name': '热卷', 'size': 10, 'price_tick': 1.0},
    'cu': {'exchange': 'SHFE', 'name': '铜', 'size': 5, 'price_tick': 10.0},
    'al': {'exchange': 'SHFE', 'name': '铝', 'size': 5, 'price_tick': 5.0},
    'zn': {'exchange': 'SHFE', 'name': '锌', 'size': 5, 'price_tick': 5.0},
    'au': {'exchange': 'SHFE', 'name': '黄金', 'size': 1000, 'price_tick': 0.05},
    'ag': {'exchange': 'SHFE', 'name': '白银', 'size': 15, 'price_tick': 1.0},
    
    # 大商所
    'i': {'exchange': 'DCE', 'name': '铁矿石', 'size': 100, 'price_tick': 0.5},
    'j': {'exchange': 'DCE', 'name': '焦炭', 'size': 100, 'price_tick': 0.5},
    'jm': {'exchange': 'DCE', 'name': '焦煤', 'size': 60, 'price_tick': 0.5},
    'c': {'exchange': 'DCE', 'name': '玉米', 'size': 10, 'price_tick': 1.0},
    'cs': {'exchange': 'DCE', 'name': '玉米淀粉', 'size': 10, 'price_tick': 1.0},
    
    # 郑商所
    'CF': {'exchange': 'CZCE', 'name': '棉花', 'size': 5, 'price_tick': 5.0},
    'TA': {'exchange': 'CZCE', 'name': 'PTA', 'size': 5, 'price_tick': 2.0},
    'MA': {'exchange': 'CZCE', 'name': '甲醇', 'size': 10, 'price_tick': 1.0},
    
    # 中金所
    'IF': {'exchange': 'CFFEX', 'name': '沪深300', 'size': 300, 'price_tick': 0.2},
    'IC': {'exchange': 'CFFEX', 'name': '中证500', 'size': 200, 'price_tick': 0.2},
    'IH': {'exchange': 'CFFEX', 'name': '上证50', 'size': 300, 'price_tick': 0.2},
}


def get_contract_config(symbol: str) -> Optional[Dict]:
    """
    获取合约配置
    
    Args:
        symbol: 合约代码，如 'rb2501'
    
    Returns:
        合约配置字典，如果不存在返回None
    """
    # 提取品种代码（去掉数字部分）
    import re
    product_code = re.sub(r'\d+', '', symbol)
    
    # 先尝试小写
    config = CONTRACT_CONFIGS.get(product_code.lower())
    if config:
        return config.copy()
    
    # 再尝试大写
    config = CONTRACT_CONFIGS.get(product_code)
    if config:
        return config.copy()
    
    return None


def create_contract_info(symbol: str) -> Optional[ContractInfo]:
    """
    根据合约代码创建ContractInfo对象
    
    Args:
        symbol: 合约代码
    
    Returns:
        ContractInfo对象，如果配置不存在返回None
    """
    config = get_contract_config(symbol)
    if not config:
        return None
    
    contract = ContractInfo(
        symbol=symbol,
        exchange=config['exchange'],
        name=config['name'],
        size=config['size'],
        price_tick=config['price_tick'],
    )
    
    return contract


def get_contract_multiplier(symbol: str) -> int:
    """
    获取合约乘数
    
    Args:
        symbol: 合约代码
    
    Returns:
        合约乘数，默认返回1
    """
    config = get_contract_config(symbol)
    if config:
        return config.get('size', 1)
    return 1


def get_price_tick(symbol: str) -> float:
    """
    获取最小变动价位
    
    Args:
        symbol: 合约代码
    
    Returns:
        最小变动价位，默认返回1.0
    """
    config = get_contract_config(symbol)
    if config:
        return config.get('price_tick', 1.0)
    return 1.0

