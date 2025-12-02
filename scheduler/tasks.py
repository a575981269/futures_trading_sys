"""
任务定义
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import uuid


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "PENDING"      # 等待中
    RUNNING = "RUNNING"       # 运行中
    SUCCESS = "SUCCESS"       # 成功
    FAILED = "FAILED"         # 失败
    CANCELLED = "CANCELLED"   # 已取消


@dataclass
class Task:
    """任务对象"""
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    
    def start(self):
        """启动任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
    
    def success(self, result: Any = None):
        """标记任务成功"""
        self.status = TaskStatus.SUCCESS
        self.result = result
        self.completed_at = datetime.now()
    
    def fail(self, error: str):
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()
    
    def cancel(self):
        """取消任务"""
        if self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.CANCELLED
            self.completed_at = datetime.now()

