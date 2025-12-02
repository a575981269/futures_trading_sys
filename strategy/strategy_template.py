"""
策略模板（空实现）
"""
from strategy.base_strategy import BaseStrategy
from database.models import KlineData, TickData


class StrategyTemplate(BaseStrategy):
    """
    策略模板类
    用户可以继承此类实现自己的策略
    """
    
    def __init__(self, name: str = "StrategyTemplate", params: dict = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        super().__init__(name, params)
        
        # 在这里初始化策略需要的变量
        # 例如：指标、持仓、信号等
    
    def on_init(self):
        """
        策略初始化
        """
        self.write_log("策略初始化完成")
        
        # TODO: 在这里初始化策略需要的指标、变量等
        # 例如：
        # self.ma_fast = MAIndicator(period=5)
        # self.ma_slow = MAIndicator(period=20)
        # self.position = 0
    
    def on_tick(self, tick: TickData):
        """
        Tick数据回调
        
        Args:
            tick: Tick数据对象
        """
        # TODO: 在这里实现基于Tick数据的策略逻辑
        # 例如：
        # if tick.last_price > self.ma_fast.value:
        #     self.buy(tick.symbol, tick.last_price, 1)
        pass
    
    def on_bar(self, bar: KlineData):
        """
        K线数据回调
        
        Args:
            bar: K线数据对象
        """
        # TODO: 在这里实现基于K线数据的策略逻辑
        # 例如：
        # self.ma_fast.update(bar.close)
        # self.ma_slow.update(bar.close)
        # 
        # if self.ma_fast.value > self.ma_slow.value and self.position == 0:
        #     self.buy(bar.symbol, bar.close, 1)
        # elif self.ma_fast.value < self.ma_slow.value and self.position > 0:
        #     self.sell(bar.symbol, bar.close, self.position)
        pass
    
    def on_exit(self):
        """
        策略退出
        """
        self.write_log("策略退出")
        # TODO: 在这里清理资源、保存数据等

