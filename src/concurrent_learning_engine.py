#!/usr/bin/env python3
"""
并发学习引擎 - 高性能多线程课程学习系统
支持同时学习多门课程，智能调度和性能优化
"""

import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import Queue, PriorityQueue
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from enum import Enum
from threading import Lock, RLock
import weakref

from src.pure_api_learner import PureAPILearner, CourseInfo, LearningSession


class TaskPriority(Enum):
    """任务优先级"""
    URGENT = 1      # 紧急任务（快完成的课程）
    HIGH = 2        # 高优先级（必修课程）
    NORMAL = 3      # 普通优先级（选修课程）
    LOW = 4         # 低优先级（已完成较多的课程）


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"         # 等待执行
    RUNNING = "running"         # 正在执行
    PAUSED = "paused"          # 已暂停
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 执行失败
    CANCELLED = "cancelled"     # 已取消


@dataclass
class LearningTask:
    """学习任务"""
    task_id: str
    course: CourseInfo
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    estimated_duration: int = 0  # 预估分钟数
    worker_thread_id: Optional[str] = None

    def __post_init__(self):
        if self.estimated_duration == 0:
            # 基于课程时长估算
            self.estimated_duration = max(1, self.course.duration_minutes - int(self.course.progress / 100 * self.course.duration_minutes))


@dataclass
class WorkerStats:
    """工作线程统计"""
    thread_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_learning_time: float = 0.0
    current_task: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class EngineStats:
    """引擎统计信息"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    total_learning_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    courses_completed: int = 0
    average_completion_rate: float = 0.0


class ConcurrentLearningEngine:
    """并发学习引擎"""

    def __init__(self, max_workers: int = 3, username: str = None, password: str = None):
        """
        初始化并发学习引擎

        Args:
            max_workers: 最大工作线程数（建议1-5个，避免过多请求）
            username: 登录用户名
            password: 登录密码
        """
        self.max_workers = min(max_workers, 5)  # 限制最大线程数
        self.username = username
        self.password = password

        # 任务管理
        self.task_queue = PriorityQueue()
        self.tasks: Dict[str, LearningTask] = {}
        self.running_tasks: Set[str] = set()

        # 线程管理
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.workers: Dict[str, WorkerStats] = {}

        # 同步控制
        self.task_lock = RLock()
        self.stats_lock = Lock()

        # 统计信息
        self.stats = EngineStats()

        # 控制标志
        self.is_running = False
        self.should_stop = False

        # 回调函数
        self.on_task_completed: Optional[Callable] = None
        self.on_task_failed: Optional[Callable] = None
        self.on_progress_update: Optional[Callable] = None

        # 日志
        self.logger = self._setup_logger()

        # API学习器池
        self.learner_pool: List[PureAPILearner] = []
        self.pool_lock = Lock()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("ConcurrentLearningEngine")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _get_learner(self) -> PureAPILearner:
        """从池中获取API学习器实例"""
        with self.pool_lock:
            if self.learner_pool:
                return self.learner_pool.pop()
            else:
                # 创建新的学习器实例
                learner = PureAPILearner(self.username, self.password)
                return learner

    def _return_learner(self, learner: PureAPILearner):
        """归还API学习器到池中"""
        with self.pool_lock:
            if len(self.learner_pool) < self.max_workers * 2:
                self.learner_pool.append(learner)

    def add_task(self, course: CourseInfo, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """
        添加学习任务

        Args:
            course: 课程信息
            priority: 任务优先级

        Returns:
            str: 任务ID
        """
        task_id = f"{course.course_type}_{course.course_id}_{int(time.time())}"

        task = LearningTask(
            task_id=task_id,
            course=course,
            priority=priority
        )

        with self.task_lock:
            self.tasks[task_id] = task
            # 使用优先级值作为队列优先级（数值越小优先级越高）
            self.task_queue.put((priority.value, task_id))
            self.stats.total_tasks += 1

        self.logger.info(f"已添加任务: {course.course_name} (优先级: {priority.name})")
        return task_id

    def add_courses(self, courses: List[CourseInfo], auto_prioritize: bool = True) -> List[str]:
        """
        批量添加课程任务

        Args:
            courses: 课程列表
            auto_prioritize: 是否自动设置优先级

        Returns:
            List[str]: 任务ID列表
        """
        task_ids = []

        for course in courses:
            if course.progress >= 100:
                self.logger.info(f"跳过已完成课程: {course.course_name}")
                continue

            if auto_prioritize:
                priority = self._calculate_priority(course)
            else:
                priority = TaskPriority.NORMAL

            task_id = self.add_task(course, priority)
            task_ids.append(task_id)

        return task_ids

    def _calculate_priority(self, course: CourseInfo) -> TaskPriority:
        """根据课程信息自动计算优先级"""
        # 必修课优先级较高
        if course.course_type == 'required':
            if course.progress >= 80:
                return TaskPriority.URGENT  # 接近完成的必修课最优先
            else:
                return TaskPriority.HIGH
        else:
            # 选修课根据进度决定
            if course.progress >= 90:
                return TaskPriority.URGENT  # 接近完成的优先
            elif course.progress >= 50:
                return TaskPriority.NORMAL
            else:
                return TaskPriority.LOW

    def start(self):
        """启动并发学习引擎"""
        if self.is_running:
            self.logger.warning("学习引擎已在运行")
            return

        self.is_running = True
        self.should_stop = False
        self.stats.start_time = datetime.now()

        self.logger.info(f"🚀 启动并发学习引擎 (工作线程数: {self.max_workers})")

        # 提交所有工作线程
        for i in range(self.max_workers):
            future = self.executor.submit(self._worker_thread, f"worker_{i}")
            # 不需要存储future，让它们自由运行

    def stop(self, timeout: float = 30.0):
        """停止并发学习引擎"""
        if not self.is_running:
            return

        self.logger.info("⏹️ 正在停止并发学习引擎...")
        self.should_stop = True

        # 等待所有任务完成或超时
        self.executor.shutdown(wait=True, timeout=timeout)

        self.is_running = False
        self.logger.info("✅ 并发学习引擎已停止")

    def _worker_thread(self, thread_id: str):
        """工作线程主循环"""
        with self.stats_lock:
            self.workers[thread_id] = WorkerStats(thread_id=thread_id)

        worker_stats = self.workers[thread_id]
        self.logger.info(f"🔄 工作线程 {thread_id} 已启动")

        try:
            # 获取学习器实例
            learner = self._get_learner()

            # 登录
            if not learner.login():
                self.logger.error(f"工作线程 {thread_id} 登录失败")
                return

            while not self.should_stop:
                try:
                    # 从队列获取任务（超时1秒）
                    priority, task_id = self.task_queue.get(timeout=1.0)

                    with self.task_lock:
                        if task_id not in self.tasks:
                            continue

                        task = self.tasks[task_id]
                        if task.status != TaskStatus.PENDING:
                            continue

                        # 标记任务为运行状态
                        task.status = TaskStatus.RUNNING
                        task.start_time = datetime.now()
                        task.worker_thread_id = thread_id
                        self.running_tasks.add(task_id)
                        worker_stats.current_task = task_id
                        self.stats.running_tasks += 1

                    self.logger.info(f"🎓 [{thread_id}] 开始学习: {task.course.course_name}")

                    # 执行学习任务
                    success = self._execute_learning_task(learner, task, worker_stats)

                    # 更新任务状态
                    with self.task_lock:
                        task.end_time = datetime.now()
                        self.running_tasks.discard(task_id)
                        worker_stats.current_task = None
                        self.stats.running_tasks -= 1

                        if success:
                            task.status = TaskStatus.COMPLETED
                            worker_stats.tasks_completed += 1
                            self.stats.completed_tasks += 1

                            if task.course.progress >= 100:
                                self.stats.courses_completed += 1

                            self.logger.info(f"✅ [{thread_id}] 完成学习: {task.course.course_name}")

                            if self.on_task_completed:
                                try:
                                    self.on_task_completed(task)
                                except Exception as e:
                                    self.logger.error(f"任务完成回调异常: {e}")
                        else:
                            task.status = TaskStatus.FAILED
                            task.error_count += 1
                            worker_stats.tasks_failed += 1
                            self.stats.failed_tasks += 1

                            self.logger.error(f"❌ [{thread_id}] 学习失败: {task.course.course_name}")

                            if self.on_task_failed:
                                try:
                                    self.on_task_failed(task)
                                except Exception as e:
                                    self.logger.error(f"任务失败回调异常: {e}")

                        worker_stats.last_activity = datetime.now()

                except Exception as e:
                    if "Empty" not in str(e):  # 忽略队列为空的异常
                        self.logger.debug(f"工作线程 {thread_id} 等待任务: {e}")
                    time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"工作线程 {thread_id} 异常: {e}")
        finally:
            # 归还学习器
            try:
                self._return_learner(learner)
            except:
                pass
            self.logger.info(f"⏹️ 工作线程 {thread_id} 已停止")

    def _execute_learning_task(self, learner: PureAPILearner, task: LearningTask, worker_stats: WorkerStats) -> bool:
        """执行学习任务"""
        try:
            start_time = time.time()

            # 开始学习课程
            success = learner.learn_course(task.course)

            end_time = time.time()
            learning_time = end_time - start_time

            worker_stats.total_learning_time += learning_time
            self.stats.total_learning_time += learning_time

            return success

        except Exception as e:
            task.last_error = str(e)
            self.logger.error(f"学习任务执行异常: {e}")
            return False

    def _on_progress_update(self, task: LearningTask, progress: float):
        """处理学习进度更新"""
        task.progress = progress
        task.course.progress = progress

        if self.on_progress_update:
            try:
                self.on_progress_update(task, progress)
            except Exception as e:
                self.logger.error(f"进度更新回调异常: {e}")

    def get_status(self) -> Dict:
        """获取引擎状态"""
        with self.task_lock:
            pending_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
            running_tasks = len(self.running_tasks)
            completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
            failed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        runtime = datetime.now() - self.stats.start_time

        return {
            "engine": {
                "is_running": self.is_running,
                "runtime_seconds": runtime.total_seconds(),
                "max_workers": self.max_workers
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": pending_tasks,
                "running": running_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks
            },
            "workers": {
                worker_id: {
                    "tasks_completed": stats.tasks_completed,
                    "tasks_failed": stats.tasks_failed,
                    "total_learning_time": stats.total_learning_time,
                    "current_task": stats.current_task,
                    "last_activity": stats.last_activity.isoformat()
                }
                for worker_id, stats in self.workers.items()
            },
            "performance": {
                "courses_completed": self.stats.courses_completed,
                "total_learning_time": self.stats.total_learning_time,
                "average_task_time": (
                    self.stats.total_learning_time / max(1, completed_tasks)
                    if completed_tasks > 0 else 0
                )
            }
        }

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取特定任务状态"""
        with self.task_lock:
            if task_id not in self.tasks:
                return None

            task = self.tasks[task_id]
            return {
                "task_id": task_id,
                "course_name": task.course.course_name,
                "status": task.status.value,
                "progress": task.progress,
                "priority": task.priority.name,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "error_count": task.error_count,
                "last_error": task.last_error,
                "worker_thread_id": task.worker_thread_id
            }

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.task_lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]

            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False

            if task.status == TaskStatus.RUNNING:
                # 正在运行的任务无法直接取消，只能标记
                task.status = TaskStatus.CANCELLED
                self.logger.warning(f"任务 {task_id} 将在完成当前操作后取消")
                return True
            else:
                task.status = TaskStatus.CANCELLED
                self.logger.info(f"已取消任务: {task_id}")
                return True

    def pause_task(self, task_id: str) -> bool:
        """暂停任务（实际上是取消，因为任务无法真正暂停）"""
        return self.cancel_task(task_id)

    def clear_completed_tasks(self):
        """清理已完成的任务"""
        with self.task_lock:
            completed_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]

            for task_id in completed_tasks:
                del self.tasks[task_id]

        self.logger.info(f"已清理 {len(completed_tasks)} 个完成的任务")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()