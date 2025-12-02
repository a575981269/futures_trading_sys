"""
合约配置
"""
from typing import Dict, Optional
from database.models import ContractInfo


# 常见期货合约配置
CONTRACT_CONFIGS: Dict[str, Dict] = {
    # ========== 上海期货交易所 (SHFE) ==========
    'cu': {'exchange': 'SHFE', 'name': '铜', 'size': 5, 'price_tick': 10.0},
    'al': {'exchange': 'SHFE', 'name': '铝', 'size': 5, 'price_tick': 5.0},
    'zn': {'exchange': 'SHFE', 'name': '锌', 'size': 5, 'price_tick': 5.0},
    'pb': {'exchange': 'SHFE', 'name': '铅', 'size': 5, 'price_tick': 5.0},
    'ni': {'exchange': 'SHFE', 'name': '镍', 'size': 1, 'price_tick': 10.0},
    'sn': {'exchange': 'SHFE', 'name': '锡', 'size': 1, 'price_tick': 10.0},
    'au': {'exchange': 'SHFE', 'name': '黄金', 'size': 1000, 'price_tick': 0.05},
    'ag': {'exchange': 'SHFE', 'name': '白银', 'size': 15, 'price_tick': 1.0},
    'rb': {'exchange': 'SHFE', 'name': '螺纹钢', 'size': 10, 'price_tick': 1.0},
    'hc': {'exchange': 'SHFE', 'name': '热轧卷板', 'size': 10, 'price_tick': 1.0},
    'ss': {'exchange': 'SHFE', 'name': '不锈钢', 'size': 5, 'price_tick': 5.0},
    'fu': {'exchange': 'SHFE', 'name': '燃料油', 'size': 10, 'price_tick': 1.0},
    'bu': {'exchange': 'SHFE', 'name': '沥青', 'size': 10, 'price_tick': 2.0},
    'ru': {'exchange': 'SHFE', 'name': '天然橡胶', 'size': 10, 'price_tick': 5.0},
    'nr': {'exchange': 'SHFE', 'name': '20号胶', 'size': 10, 'price_tick': 5.0},
    'sp': {'exchange': 'SHFE', 'name': '纸浆', 'size': 10, 'price_tick': 2.0},
    'lu': {'exchange': 'SHFE', 'name': '低硫燃料油', 'size': 10, 'price_tick': 1.0},
    'bc': {'exchange': 'SHFE', 'name': '国际铜', 'size': 5, 'price_tick': 10.0},
    'ao': {'exchange': 'SHFE', 'name': '氧化铝', 'size': 20, 'price_tick': 1.0},
    'ec': {'exchange': 'SHFE', 'name': '合成橡胶', 'size': 5, 'price_tick': 5.0},
    
    # ========== 大连商品交易所 (DCE) ==========
    'a': {'exchange': 'DCE', 'name': '豆一', 'size': 10, 'price_tick': 1.0},
    'b': {'exchange': 'DCE', 'name': '豆二', 'size': 10, 'price_tick': 1.0},
    'm': {'exchange': 'DCE', 'name': '豆粕', 'size': 10, 'price_tick': 1.0},
    'y': {'exchange': 'DCE', 'name': '豆油', 'size': 10, 'price_tick': 2.0},
    'c': {'exchange': 'DCE', 'name': '玉米', 'size': 10, 'price_tick': 1.0},
    'cs': {'exchange': 'DCE', 'name': '玉米淀粉', 'size': 10, 'price_tick': 1.0},
    'l': {'exchange': 'DCE', 'name': '塑料', 'size': 5, 'price_tick': 5.0},
    'v': {'exchange': 'DCE', 'name': 'PVC', 'size': 5, 'price_tick': 5.0},
    'pp': {'exchange': 'DCE', 'name': '聚丙烯', 'size': 5, 'price_tick': 1.0},
    'j': {'exchange': 'DCE', 'name': '焦炭', 'size': 100, 'price_tick': 0.5},
    'jm': {'exchange': 'DCE', 'name': '焦煤', 'size': 60, 'price_tick': 0.5},
    'i': {'exchange': 'DCE', 'name': '铁矿石', 'size': 100, 'price_tick': 0.5},
    'jd': {'exchange': 'DCE', 'name': '鸡蛋', 'size': 10, 'price_tick': 1.0},
    'fb': {'exchange': 'DCE', 'name': '纤维板', 'size': 10, 'price_tick': 0.5},
    'bb': {'exchange': 'DCE', 'name': '胶合板', 'size': 10, 'price_tick': 0.5},
    'pg': {'exchange': 'DCE', 'name': '液化石油气', 'size': 20, 'price_tick': 1.0},
    'lh': {'exchange': 'DCE', 'name': '生猪', 'size': 16, 'price_tick': 5.0},
    'eb': {'exchange': 'DCE', 'name': '苯乙烯', 'size': 5, 'price_tick': 1.0},
    'eg': {'exchange': 'DCE', 'name': '乙二醇', 'size': 10, 'price_tick': 1.0},
    'pk': {'exchange': 'DCE', 'name': '花生', 'size': 5, 'price_tick': 2.0},
    'lc': {'exchange': 'DCE', 'name': '碳酸锂', 'size': 1, 'price_tick': 50.0},
    'bc': {'exchange': 'DCE', 'name': '丁二烯橡胶', 'size': 5, 'price_tick': 5.0},
    
    # ========== 郑州商品交易所 (CZCE) ==========
    'CF': {'exchange': 'CZCE', 'name': '棉花', 'size': 5, 'price_tick': 5.0},
    'CY': {'exchange': 'CZCE', 'name': '棉纱', 'size': 5, 'price_tick': 5.0},
    'SR': {'exchange': 'CZCE', 'name': '白糖', 'size': 10, 'price_tick': 1.0},
    'TA': {'exchange': 'CZCE', 'name': 'PTA', 'size': 5, 'price_tick': 2.0},
    'MA': {'exchange': 'CZCE', 'name': '甲醇', 'size': 10, 'price_tick': 1.0},
    'FG': {'exchange': 'CZCE', 'name': '玻璃', 'size': 20, 'price_tick': 1.0},
    'RS': {'exchange': 'CZCE', 'name': '菜籽', 'size': 10, 'price_tick': 1.0},
    'RM': {'exchange': 'CZCE', 'name': '菜粕', 'size': 10, 'price_tick': 1.0},
    'OI': {'exchange': 'CZCE', 'name': '菜油', 'size': 10, 'price_tick': 2.0},
    'WH': {'exchange': 'CZCE', 'name': '强麦', 'size': 20, 'price_tick': 1.0},
    'PM': {'exchange': 'CZCE', 'name': '普麦', 'size': 50, 'price_tick': 1.0},
    'RI': {'exchange': 'CZCE', 'name': '早籼稻', 'size': 20, 'price_tick': 1.0},
    'LR': {'exchange': 'CZCE', 'name': '晚籼稻', 'size': 20, 'price_tick': 1.0},
    'JR': {'exchange': 'CZCE', 'name': '粳稻', 'size': 20, 'price_tick': 1.0},
    'ZC': {'exchange': 'CZCE', 'name': '动力煤', 'size': 100, 'price_tick': 0.2},
    'SF': {'exchange': 'CZCE', 'name': '硅铁', 'size': 5, 'price_tick': 2.0},
    'SM': {'exchange': 'CZCE', 'name': '锰硅', 'size': 5, 'price_tick': 2.0},
    'UR': {'exchange': 'CZCE', 'name': '尿素', 'size': 20, 'price_tick': 1.0},
    'SA': {'exchange': 'CZCE', 'name': '纯碱', 'size': 20, 'price_tick': 1.0},
    'PF': {'exchange': 'CZCE', 'name': '短纤', 'size': 5, 'price_tick': 2.0},
    'PK': {'exchange': 'CZCE', 'name': '花生', 'size': 5, 'price_tick': 2.0},
    'PX': {'exchange': 'CZCE', 'name': '对二甲苯', 'size': 5, 'price_tick': 2.0},
    'BR': {'exchange': 'CZCE', 'name': '烧碱', 'size': 30, 'price_tick': 1.0},
    'IM': {'exchange': 'CZCE', 'name': '对二甲苯', 'size': 5, 'price_tick': 2.0},
    
    # ========== 中国金融期货交易所 (CFFEX) ==========
    'IF': {'exchange': 'CFFEX', 'name': '沪深300', 'size': 300, 'price_tick': 0.2},
    'IC': {'exchange': 'CFFEX', 'name': '中证500', 'size': 200, 'price_tick': 0.2},
    'IH': {'exchange': 'CFFEX', 'name': '上证50', 'size': 300, 'price_tick': 0.2},
    'IM': {'exchange': 'CFFEX', 'name': '中证1000', 'size': 200, 'price_tick': 0.2},
    'T': {'exchange': 'CFFEX', 'name': '10年期国债', 'size': 10000, 'price_tick': 0.005},
    'TF': {'exchange': 'CFFEX', 'name': '5年期国债', 'size': 10000, 'price_tick': 0.005},
    'TS': {'exchange': 'CFFEX', 'name': '2年期国债', 'size': 20000, 'price_tick': 0.005},
    'TL': {'exchange': 'CFFEX', 'name': '30年期国债', 'size': 10000, 'price_tick': 0.01},
    '30Y': {'exchange': 'CFFEX', 'name': '30年期国债', 'size': 10000, 'price_tick': 0.01},
    
    # ========== 上海国际能源交易中心 (INE) ==========
    'sc': {'exchange': 'INE', 'name': '原油', 'size': 1000, 'price_tick': 0.1},
    '20': {'exchange': 'INE', 'name': '20号胶', 'size': 10, 'price_tick': 5.0},
    'nr': {'exchange': 'INE', 'name': '20号胶', 'size': 10, 'price_tick': 5.0},
    'lu': {'exchange': 'INE', 'name': '低硫燃料油', 'size': 10, 'price_tick': 1.0},
    'bc': {'exchange': 'INE', 'name': '国际铜', 'size': 5, 'price_tick': 10.0},
    'ec': {'exchange': 'INE', 'name': '合成橡胶', 'size': 5, 'price_tick': 5.0},
    'ao': {'exchange': 'INE', 'name': '氧化铝', 'size': 20, 'price_tick': 1.0},
    'ie': {'exchange': 'INE', 'name': '集运指数(欧线)', 'size': 50, 'price_tick': 0.1},
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

