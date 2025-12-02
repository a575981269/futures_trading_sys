"""
任务调度器
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from threading import Thread, Event, Lock
import time

from scheduler.tasks import Task, TaskStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        """初始化任务调度器"""
        self.tasks: Dict[str, Task] = {}  # {task_id: Task}
        self.task_queue: List[Task] = []  # 任务队列
        
        # 定时任务 {task_id: (task, interval, next_run_time)}
        self.scheduled_tasks: Dict[str, tuple] = {}
        
        # 线程控制
        self._running = False
        self._stop_event = Event()
        self._scheduler_thread: Optional[Thread] = None
        self._lock = Lock()
        
        logger.info("任务调度器初始化完成")
    
    def add_task(self,
                name: str,
                func: Callable,
                args: tuple = (),
                kwargs: Optional[Dict] = None) -> str:
        """
        添加任务
        
        Args:
            name: 任务名称
            func: 任务函数
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            任务ID
        """
        task = Task(
            name=name,
            func=func,
            args=args or (),
            kwargs=kwargs or {}
        )
        
        with self._lock:
            self.tasks[task.task_id] = task
            self.task_queue.append(task)
        
        logger.info(f"任务已添加: {name} ({task.task_id})")
        return task.task_id
    
    def add_periodic_task(self,
                         name: str,
                         func: Callable,
                         interval: int,
                         args: tuple = (),
                         kwargs: Optional[Dict] = None) -> str:
        """
        添加定时任务
        
        Args:
            name: 任务名称
            func: 任务函数
            interval: 执行间隔（秒）
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            任务ID
        """
        task = Task(
            name=name,
            func=func,
            args=args or (),
            kwargs=kwargs or {}
        )
        
        next_run_time = datetime.now() + timedelta(seconds=interval)
        
        with self._lock:
            self.tasks[task.task_id] = task
            self.scheduled_tasks[task.task_id] = (task, interval, next_run_time)
        
        logger.info(f"定时任务已添加: {name} ({task.task_id}), 间隔={interval}秒")
        return task.task_id
    
    def remove_task(self, task_id: str) -> bool:
        """
        移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
            
            # 从队列中移除
            self.task_queue = [t for t in self.task_queue if t.task_id != task_id]
            
            # 从定时任务中移除
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
            
            logger.info(f"任务已移除: {task_id}")
            return True
        
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """
        获取任务列表
        
        Args:
            status: 任务状态，如果为None则返回所有任务
            
        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行")
            return
        
        self._running = True
        self._stop_event.clear()
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("任务调度器已停止")
    
    def _scheduler_loop(self):
        """调度器循环"""
        while not self._stop_event.is_set():
            try:
                # 处理队列中的任务
                self._process_queue()
                
                # 处理定时任务
                self._process_scheduled_tasks()
                
                # 等待1秒
                self._stop_event.wait(1)
                
            except Exception as e:
                logger.error(f"调度器循环执行失败: {e}")
                time.sleep(1)
    
    def _process_queue(self):
        """处理任务队列"""
        with self._lock:
            if not self.task_queue:
                return
            
            # 取出第一个任务
            task = self.task_queue.pop(0)
        
        # 执行任务
        self._execute_task(task)
    
    def _process_scheduled_tasks(self):
        """处理定时任务"""
        now = datetime.now()
        to_run = []
        
        with self._lock:
            for task_id, (task, interval, next_run_time) in list(self.scheduled_tasks.items()):
                if now >= next_run_time:
                    to_run.append((task_id, task, interval))
        
        # 执行到期的定时任务
        for task_id, task, interval in to_run:
            # 创建新任务实例执行
            new_task = Task(
                name=task.name,
                func=task.func,
                args=task.args,
                kwargs=task.kwargs
            )
            self._execute_task(new_task)
            
            # 更新下次执行时间
            with self._lock:
                if task_id in self.scheduled_tasks:
                    next_run_time = datetime.now() + timedelta(seconds=interval)
                    self.scheduled_tasks[task_id] = (task, interval, next_run_time)
    
    def _execute_task(self, task: Task):
        """执行任务"""
        task.start()
        logger.info(f"执行任务: {task.name} ({task.task_id})")
        
        try:
            result = task.func(*task.args, **task.kwargs)
            task.success(result)
            logger.info(f"任务执行成功: {task.name} ({task.task_id})")
        except Exception as e:
            error_msg = str(e)
            task.fail(error_msg)
            logger.error(f"任务执行失败: {task.name} ({task.task_id}), 错误: {error_msg}")

