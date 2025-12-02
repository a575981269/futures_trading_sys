"""
技术指标库（统一接口）
"""
from typing import List, Optional, Dict, Any
from database.models import KlineData

from indicators.ma import MA, EMA, SMA, calculate_ma_from_klines
from indicators.macd import MACD
from indicators.rsi import RSI
from indicators.bollinger import BollingerBands

from utils.logger import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def ma(klines: List[KlineData], period: int, price_type: str = 'close') -> List[Optional[float]]:
        """
        计算移动平均线
        
        Args:
            klines: K线数据列表
            period: 周期
            price_type: 价格类型
            
        Returns:
            MA值列表
        """
        return calculate_ma_from_klines(klines, period, price_type, 'SMA')
    
    @staticmethod
    def ema(klines: List[KlineData], period: int, price_type: str = 'close') -> List[Optional[float]]:
        """
        计算指数移动平均线
        
        Args:
            klines: K线数据列表
            period: 周期
            price_type: 价格类型
            
        Returns:
            EMA值列表
        """
        return calculate_ma_from_klines(klines, period, price_type, 'EMA')
    
    @staticmethod
    def macd(klines: List[KlineData],
            fast_period: int = 12,
            slow_period: int = 26,
            signal_period: int = 9) -> Dict[str, List[Optional[float]]]:
        """
        计算MACD指标
        
        Args:
            klines: K线数据列表
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            {'dif': [...], 'dea': [...], 'macd': [...]}
        """
        prices = [k.close for k in klines]
        dif, dea, macd = MACD(prices, fast_period, slow_period, signal_period)
        return {
            'dif': dif,
            'dea': dea,
            'macd': macd
        }
    
    @staticmethod
    def rsi(klines: List[KlineData], period: int = 14) -> List[Optional[float]]:
        """
        计算RSI指标
        
        Args:
            klines: K线数据列表
            period: 周期
            
        Returns:
            RSI值列表
        """
        prices = [k.close for k in klines]
        return RSI(prices, period)
    
    @staticmethod
    def bollinger(klines: List[KlineData],
                 period: int = 20,
                 num_std: float = 2.0) -> Dict[str, List[Optional[float]]]:
        """
        计算布林带指标
        
        Args:
            klines: K线数据列表
            period: 周期
            num_std: 标准差倍数
            
        Returns:
            {'upper': [...], 'middle': [...], 'lower': [...]}
        """
        prices = [k.close for k in klines]
        upper, middle, lower = BollingerBands(prices, period, num_std)
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    @staticmethod
    def calculate_all(klines: List[KlineData],
                     ma_periods: List[int] = [5, 10, 20, 60],
                     macd_params: Dict = None,
                     rsi_period: int = 14,
                     bollinger_params: Dict = None) -> Dict[str, Any]:
        """
        计算所有指标
        
        Args:
            klines: K线数据列表
            ma_periods: MA周期列表
            macd_params: MACD参数
            rsi_period: RSI周期
            bollinger_params: 布林带参数
            
        Returns:
            所有指标字典
        """
        result = {}
        
        # MA指标
        for period in ma_periods:
            result[f'ma{period}'] = TechnicalIndicators.ma(klines, period)
            result[f'ema{period}'] = TechnicalIndicators.ema(klines, period)
        
        # MACD指标
        if macd_params is None:
            macd_params = {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        result['macd'] = TechnicalIndicators.macd(klines, **macd_params)
        
        # RSI指标
        result['rsi'] = TechnicalIndicators.rsi(klines, rsi_period)
        
        # 布林带指标
        if bollinger_params is None:
            bollinger_params = {'period': 20, 'num_std': 2.0}
        result['bollinger'] = TechnicalIndicators.bollinger(klines, **bollinger_params)
        
        return result

