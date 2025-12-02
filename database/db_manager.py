"""
数据库管理器
"""
import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import Base, KlineData, TickData, ContractInfo
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_url: 数据库连接URL，默认使用SQLite
                   格式: sqlite:///path/to/db.sqlite
                   或: mysql+pymysql://user:pass@host/dbname
        """
        if db_url is None:
            # 默认使用SQLite
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'futures.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db_url = f'sqlite:///{db_path}'
        
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 创建表
        self.create_tables()
        logger.info(f"数据库连接成功: {db_url}")
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
        except SQLAlchemyError as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    # ========== K线数据操作 ==========
    
    def save_kline(self, kline_data: KlineData) -> bool:
        """保存单条K线数据"""
        session = self.get_session()
        try:
            session.add(kline_data)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"保存K线数据失败: {e}")
            return False
        finally:
            session.close()
    
    def save_klines_batch(self, kline_list: List[KlineData]) -> bool:
        """批量保存K线数据"""
        session = self.get_session()
        try:
            session.bulk_save_objects(kline_list)
            session.commit()
            logger.info(f"批量保存K线数据成功，共{len(kline_list)}条")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"批量保存K线数据失败: {e}")
            return False
        finally:
            session.close()
    
    def get_klines(self, symbol: str, interval: str, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[KlineData]:
        """
        查询K线数据
        
        Args:
            symbol: 合约代码
            interval: K线周期
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制返回条数
        """
        session = self.get_session()
        try:
            query = session.query(KlineData).filter(
                KlineData.symbol == symbol,
                KlineData.interval == interval
            )
            
            if start_time:
                query = query.filter(KlineData.datetime >= start_time)
            if end_time:
                query = query.filter(KlineData.datetime <= end_time)
            
            query = query.order_by(KlineData.datetime.asc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"查询K线数据失败: {e}")
            return []
        finally:
            session.close()
    
    def get_latest_kline(self, symbol: str, interval: str) -> Optional[KlineData]:
        """获取最新一条K线数据"""
        session = self.get_session()
        try:
            return session.query(KlineData).filter(
                KlineData.symbol == symbol,
                KlineData.interval == interval
            ).order_by(KlineData.datetime.desc()).first()
        except SQLAlchemyError as e:
            logger.error(f"查询最新K线数据失败: {e}")
            return None
        finally:
            session.close()
    
    # ========== Tick数据操作 ==========
    
    def save_tick(self, tick_data: TickData) -> bool:
        """保存单条Tick数据"""
        session = self.get_session()
        try:
            session.add(tick_data)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"保存Tick数据失败: {e}")
            return False
        finally:
            session.close()
    
    def save_ticks_batch(self, tick_list: List[TickData]) -> bool:
        """批量保存Tick数据"""
        session = self.get_session()
        try:
            session.bulk_save_objects(tick_list)
            session.commit()
            logger.info(f"批量保存Tick数据成功，共{len(tick_list)}条")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"批量保存Tick数据失败: {e}")
            return False
        finally:
            session.close()
    
    def get_ticks(self, symbol: str,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  limit: Optional[int] = None) -> List[TickData]:
        """
        查询Tick数据
        
        Args:
            symbol: 合约代码
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制返回条数
        """
        session = self.get_session()
        try:
            query = session.query(TickData).filter(
                TickData.symbol == symbol
            )
            
            if start_time:
                query = query.filter(TickData.datetime >= start_time)
            if end_time:
                query = query.filter(TickData.datetime <= end_time)
            
            query = query.order_by(TickData.datetime.asc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"查询Tick数据失败: {e}")
            return []
        finally:
            session.close()
    
    # ========== 合约信息操作 ==========
    
    def save_contract(self, contract: ContractInfo) -> bool:
        """保存合约信息"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(ContractInfo).filter(
                ContractInfo.symbol == contract.symbol
            ).first()
            
            if existing:
                # 更新现有记录
                for key, value in contract.__dict__.items():
                    if not key.startswith('_') and key != 'id':
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
            else:
                session.add(contract)
            
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"保存合约信息失败: {e}")
            return False
        finally:
            session.close()
    
    def get_contract(self, symbol: str) -> Optional[ContractInfo]:
        """获取合约信息"""
        session = self.get_session()
        try:
            return session.query(ContractInfo).filter(
                ContractInfo.symbol == symbol
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"查询合约信息失败: {e}")
            return None
        finally:
            session.close()
    
    def get_all_contracts(self, is_active: Optional[int] = None) -> List[ContractInfo]:
        """获取所有合约信息"""
        session = self.get_session()
        try:
            query = session.query(ContractInfo)
            if is_active is not None:
                query = query.filter(ContractInfo.is_active == is_active)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"查询合约信息失败: {e}")
            return []
        finally:
            session.close()

