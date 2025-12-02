"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class KlineData(Base):
    """K线数据模型"""
    __tablename__ = 'kline_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, comment='合约代码')
    exchange = Column(String(10), nullable=False, comment='交易所')
    datetime = Column(DateTime, nullable=False, comment='K线时间')
    interval = Column(String(10), nullable=False, comment='K线周期(1m, 5m, 15m, 1h, 1d等)')
    open = Column(Float, nullable=False, comment='开盘价')
    high = Column(Float, nullable=False, comment='最高价')
    low = Column(Float, nullable=False, comment='最低价')
    close = Column(Float, nullable=False, comment='收盘价')
    volume = Column(Integer, default=0, comment='成交量')
    open_interest = Column(Integer, default=0, comment='持仓量')
    turnover = Column(Float, default=0.0, comment='成交额')
    
    # 创建复合索引，优化查询性能
    __table_args__ = (
        Index('idx_symbol_interval_datetime', 'symbol', 'interval', 'datetime'),
        Index('idx_datetime', 'datetime'),
    )
    
    def __repr__(self):
        return f"<KlineData(symbol={self.symbol}, datetime={self.datetime}, close={self.close})>"


class TickData(Base):
    """Tick数据模型"""
    __tablename__ = 'tick_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, comment='合约代码')
    exchange = Column(String(10), nullable=False, comment='交易所')
    datetime = Column(DateTime, nullable=False, comment='Tick时间')
    last_price = Column(Float, nullable=False, comment='最新价')
    volume = Column(Integer, default=0, comment='成交量')
    open_interest = Column(Integer, default=0, comment='持仓量')
    bid_price1 = Column(Float, comment='买一价')
    bid_volume1 = Column(Integer, comment='买一量')
    ask_price1 = Column(Float, comment='卖一价')
    ask_volume1 = Column(Integer, comment='卖一量')
    turnover = Column(Float, default=0.0, comment='成交额')
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_symbol_datetime', 'symbol', 'datetime'),
        Index('idx_datetime', 'datetime'),
    )
    
    def __repr__(self):
        return f"<TickData(symbol={self.symbol}, datetime={self.datetime}, price={self.last_price})>"


class ContractInfo(Base):
    """合约信息模型"""
    __tablename__ = 'contract_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, comment='合约代码')
    exchange = Column(String(10), nullable=False, comment='交易所')
    name = Column(String(50), comment='合约名称')
    product_type = Column(String(10), comment='产品类型')
    size = Column(Integer, comment='合约乘数')
    price_tick = Column(Float, comment='最小变动价位')
    margin_rate = Column(Float, comment='保证金率')
    commission_rate = Column(Float, comment='手续费率')
    is_active = Column(Integer, default=1, comment='是否活跃(1:是, 0:否)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<ContractInfo(symbol={self.symbol}, name={self.name})>"

