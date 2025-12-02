"""
定时任务定义
"""
from datetime import datetime, time as dt_time
from typing import Callable

from scheduler.task_scheduler import TaskScheduler
from utils.logger import get_logger

logger = get_logger(__name__)


def create_daily_job(scheduler: TaskScheduler,
                    name: str,
                    func: Callable,
                    time: dt_time,
                    args: tuple = (),
                    kwargs: dict = None):
    """
    创建每日定时任务
    
    Args:
        scheduler: 任务调度器
        name: 任务名称
        func: 任务函数
        time: 执行时间
        args: 位置参数
        kwargs: 关键字参数
    """
    def wrapper():
        now = datetime.now().time()
        if now >= time:
            func(*args, **(kwargs or {}))
    
    # 每分钟检查一次
    scheduler.add_periodic_task(
        name=f"{name}_daily",
        func=wrapper,
        interval=60,
        args=(),
        kwargs={}
    )
    logger.info(f"每日定时任务已创建: {name}, 执行时间: {time}")


def create_hourly_job(scheduler: TaskScheduler,
                      name: str,
                      func: Callable,
                      minute: int = 0,
                      args: tuple = (),
                      kwargs: dict = None):
    """
    创建每小时定时任务
    
    Args:
        scheduler: 任务调度器
        name: 任务名称
        func: 任务函数
        minute: 执行分钟（0-59）
        args: 位置参数
        kwargs: 关键字参数
    """
    def wrapper():
        now = datetime.now()
        if now.minute == minute:
            func(*args, **(kwargs or {}))
    
    # 每分钟检查一次
    scheduler.add_periodic_task(
        name=f"{name}_hourly",
        func=wrapper,
        interval=60,
        args=(),
        kwargs={}
    )
    logger.info(f"每小时定时任务已创建: {name}, 执行分钟: {minute}")

