#!/usr/bin/env python3
"""
智能学习调度器 - 优化学习任务的分配和执行策略
"""

import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import logging
import json
from pathlib import Path

from src.concurrent_learning_engine import ConcurrentLearningEngine, TaskPriority, TaskStatus
from src.pure_api_learner import PureAPILearner, CourseInfo


@dataclass
class LearningPlan:
    """学习计划"""
    total_courses: int
    estimated_total_time: float  # 小时
    estimated_completion_date: datetime
    priority_distribution: Dict[TaskPriority, int]
    daily_learning_target: float  # 小时/天


@dataclass
class LearningProgress:
    """学习进度报告"""
    completed_courses: int
    total_courses: int
    completion_rate: float
    total_learning_time: float  # 小时
    average_daily_time: float   # 小时/天
    estimated_remaining_time: float  # 小时
    current_efficiency: float   # 课程/小时


class SmartLearningScheduler:
    """智能学习调度器"""

    def __init__(self, username: str, password: str, max_workers: int = 3):
        """
        初始化智能调度器

        Args:
            username: 登录用户名
            password: 登录密码
            max_workers: 最大并发线程数
        """
        self.username = username
        self.password = password
        self.max_workers = max_workers

        # 核心组件
        self.engine = ConcurrentLearningEngine(max_workers, username, password)
        self.api_learner = PureAPILearner(username, password)

        # 调度配置
        self.auto_retry_failed = True
        self.max_retry_count = 3
        self.retry_delay_minutes = 5

        # 学习计划和进度
        self.learning_plan: Optional[LearningPlan] = None
        self.start_time: Optional[datetime] = None

        # 监控和统计
        self.monitoring_thread: Optional[threading.Thread] = None
        self.should_monitor = False
        self.progress_history: List[LearningProgress] = []

        # 回调函数
        self.on_course_completed: Optional[Callable] = None
        self.on_plan_completed: Optional[Callable] = None
        self.on_progress_report: Optional[Callable] = None

        # 日志
        self.logger = self._setup_logger()

        # 数据持久化
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.progress_file = self.data_dir / "learning_progress.json"

        # 设置引擎回调
        self.engine.on_task_completed = self._on_task_completed
        self.engine.on_task_failed = self._on_task_failed
        self.engine.on_progress_update = self._on_progress_update

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("SmartLearningScheduler")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def create_learning_plan(self, daily_target_hours: float = 4.0) -> LearningPlan:
        """
        创建学习计划

        Args:
            daily_target_hours: 每日学习目标小时数

        Returns:
            LearningPlan: 学习计划
        """
        self.logger.info("🎯 正在创建学习计划...")

        # 登录并获取课程信息
        if not self.api_learner.login():
            raise Exception("登录失败，无法创建学习计划")

        # 获取所有未完成课程
        elective_courses = self.api_learner.get_elective_courses()
        required_courses = self.api_learner.get_required_courses()

        all_courses = elective_courses + required_courses
        incomplete_courses = [course for course in all_courses if course.progress < 100]

        if not incomplete_courses:
            self.logger.info("🎉 所有课程已完成！")
            return LearningPlan(
                total_courses=0,
                estimated_total_time=0,
                estimated_completion_date=datetime.now(),
                priority_distribution={},
                daily_learning_target=daily_target_hours
            )

        # 计算时间估算
        total_estimated_time = 0
        priority_distribution = {priority: 0 for priority in TaskPriority}

        for course in incomplete_courses:
            # 估算剩余学习时间（分钟转小时）
            remaining_progress = (100 - course.progress) / 100
            estimated_minutes = course.duration_minutes * remaining_progress
            total_estimated_time += estimated_minutes / 60

            # 计算优先级分布
            if course.course_type == 'required':
                if course.progress >= 80:
                    priority = TaskPriority.URGENT
                else:
                    priority = TaskPriority.HIGH
            else:
                if course.progress >= 90:
                    priority = TaskPriority.URGENT
                elif course.progress >= 50:
                    priority = TaskPriority.NORMAL
                else:
                    priority = TaskPriority.LOW

            priority_distribution[priority] += 1

        # 估算完成日期
        estimated_days = max(1, total_estimated_time / daily_target_hours)
        estimated_completion = datetime.now() + timedelta(days=estimated_days)

        self.learning_plan = LearningPlan(
            total_courses=len(incomplete_courses),
            estimated_total_time=total_estimated_time,
            estimated_completion_date=estimated_completion,
            priority_distribution=priority_distribution,
            daily_learning_target=daily_target_hours
        )

        self.logger.info(f"📋 学习计划创建完成:")
        self.logger.info(f"  📚 总课程数: {self.learning_plan.total_courses}")
        self.logger.info(f"  ⏱️ 预估学习时间: {self.learning_plan.estimated_total_time:.1f} 小时")
        self.logger.info(f"  📅 预期完成日期: {self.learning_plan.estimated_completion_date.strftime('%Y-%m-%d')}")
        self.logger.info(f"  🎯 每日学习目标: {self.learning_plan.daily_learning_target:.1f} 小时")

        # 显示优先级分布
        for priority, count in self.learning_plan.priority_distribution.items():
            if count > 0:
                self.logger.info(f"  {priority.name}: {count} 门课程")

        return self.learning_plan

    def start_auto_learning(self, daily_target_hours: float = 4.0):
        """
        启动自动学习

        Args:
            daily_target_hours: 每日学习目标小时数
        """
        self.logger.info("🚀 启动智能学习调度器...")

        # 创建学习计划
        if not self.learning_plan:
            self.create_learning_plan(daily_target_hours)

        if self.learning_plan.total_courses == 0:
            self.logger.info("🎉 没有需要学习的课程！")
            return

        # 获取课程并添加到引擎
        if not self.api_learner.login():
            raise Exception("登录失败，无法开始学习")

        elective_courses = self.api_learner.get_elective_courses()
        required_courses = self.api_learner.get_required_courses()
        all_courses = elective_courses + required_courses
        incomplete_courses = [course for course in all_courses if course.progress < 100]

        # 批量添加任务
        task_ids = self.engine.add_courses(incomplete_courses, auto_prioritize=True)
        self.logger.info(f"📝 已添加 {len(task_ids)} 个学习任务")

        # 启动引擎
        self.engine.start()
        self.start_time = datetime.now()

        # 启动监控
        self._start_monitoring()

        self.logger.info("✅ 智能学习调度器已启动")

    def stop_learning(self):
        """停止学习"""
        self.logger.info("⏹️ 停止智能学习调度器...")

        # 停止监控
        self._stop_monitoring()

        # 停止引擎
        self.engine.stop()

        # 保存进度
        self._save_progress()

        self.logger.info("✅ 智能学习调度器已停止")

    def _start_monitoring(self):
        """启动监控线程"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self.should_monitor = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def _stop_monitoring(self):
        """停止监控线程"""
        self.should_monitor = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)

    def _monitoring_loop(self):
        """监控循环"""
        self.logger.info("📊 启动进度监控...")

        last_report_time = datetime.now()
        report_interval = timedelta(minutes=10)  # 每10分钟报告一次

        while self.should_monitor:
            try:
                current_time = datetime.now()

                # 定期生成进度报告
                if current_time - last_report_time >= report_interval:
                    progress = self._generate_progress_report()
                    self.progress_history.append(progress)

                    self.logger.info(f"📊 学习进度报告:")
                    self.logger.info(f"  完成课程: {progress.completed_courses}/{progress.total_courses}")
                    self.logger.info(f"  完成率: {progress.completion_rate:.1f}%")
                    self.logger.info(f"  学习时间: {progress.total_learning_time:.1f} 小时")
                    self.logger.info(f"  预估剩余: {progress.estimated_remaining_time:.1f} 小时")

                    if self.on_progress_report:
                        try:
                            self.on_progress_report(progress)
                        except Exception as e:
                            self.logger.error(f"进度报告回调异常: {e}")

                    last_report_time = current_time

                # 检查失败任务重试
                if self.auto_retry_failed:
                    self._check_retry_failed_tasks()

                # 检查是否完成所有任务
                status = self.engine.get_status()
                if (status['tasks']['pending'] == 0 and
                    status['tasks']['running'] == 0 and
                    status['tasks']['completed'] > 0):

                    self.logger.info("🎉 所有学习任务已完成！")
                    if self.on_plan_completed:
                        try:
                            self.on_plan_completed()
                        except Exception as e:
                            self.logger.error(f"计划完成回调异常: {e}")
                    break

                time.sleep(30)  # 每30秒检查一次

            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(60)

        self.logger.info("📊 进度监控已停止")

    def _generate_progress_report(self) -> LearningProgress:
        """生成进度报告"""
        status = self.engine.get_status()

        completed_courses = status['performance']['courses_completed']
        total_courses = self.learning_plan.total_courses if self.learning_plan else 1
        completion_rate = (completed_courses / max(1, total_courses)) * 100

        total_learning_time = status['performance']['total_learning_time'] / 3600  # 转换为小时

        # 计算平均每日学习时间
        if self.start_time:
            days_elapsed = max(1, (datetime.now() - self.start_time).total_seconds() / 86400)
            average_daily_time = total_learning_time / days_elapsed
        else:
            average_daily_time = 0

        # 计算学习效率
        current_efficiency = (completed_courses / max(0.1, total_learning_time)) if total_learning_time > 0 else 0

        # 估算剩余时间
        remaining_courses = max(0, total_courses - completed_courses)
        estimated_remaining_time = (remaining_courses / max(0.1, current_efficiency)) if current_efficiency > 0 else 0

        return LearningProgress(
            completed_courses=completed_courses,
            total_courses=total_courses,
            completion_rate=completion_rate,
            total_learning_time=total_learning_time,
            average_daily_time=average_daily_time,
            estimated_remaining_time=estimated_remaining_time,
            current_efficiency=current_efficiency
        )

    def _check_retry_failed_tasks(self):
        """检查并重试失败的任务"""
        status = self.engine.get_status()
        current_time = datetime.now()

        with self.engine.task_lock:
            for task_id, task in self.engine.tasks.items():
                if (task.status == TaskStatus.FAILED and
                    task.error_count < self.max_retry_count and
                    task.end_time and
                    current_time - task.end_time > timedelta(minutes=self.retry_delay_minutes)):

                    self.logger.info(f"🔄 重试失败任务: {task.course.course_name} (第{task.error_count + 1}次)")

                    # 重置任务状态
                    task.status = TaskStatus.PENDING
                    task.start_time = None
                    task.end_time = None
                    task.worker_thread_id = None

                    # 重新加入队列
                    self.engine.task_queue.put((task.priority.value, task_id))

    def _on_task_completed(self, task):
        """任务完成回调"""
        self.logger.info(f"✅ 课程完成: {task.course.course_name}")

        if self.on_course_completed:
            try:
                self.on_course_completed(task.course)
            except Exception as e:
                self.logger.error(f"课程完成回调异常: {e}")

    def _on_task_failed(self, task):
        """任务失败回调"""
        self.logger.warning(f"❌ 课程学习失败: {task.course.course_name} (错误: {task.last_error})")

    def _on_progress_update(self, task, progress):
        """进度更新回调"""
        # 这里可以添加进度更新的处理逻辑
        pass

    def get_detailed_status(self) -> Dict:
        """获取详细状态信息"""
        engine_status = self.engine.get_status()

        current_progress = None
        if self.start_time:
            current_progress = self._generate_progress_report()

        return {
            "scheduler": {
                "is_running": self.engine.is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "auto_retry_enabled": self.auto_retry_failed,
                "max_retry_count": self.max_retry_count
            },
            "learning_plan": {
                "total_courses": self.learning_plan.total_courses if self.learning_plan else 0,
                "estimated_total_time": self.learning_plan.estimated_total_time if self.learning_plan else 0,
                "daily_target": self.learning_plan.daily_learning_target if self.learning_plan else 0,
                "estimated_completion": (
                    self.learning_plan.estimated_completion_date.isoformat()
                    if self.learning_plan else None
                )
            },
            "current_progress": {
                "completed_courses": current_progress.completed_courses if current_progress else 0,
                "completion_rate": current_progress.completion_rate if current_progress else 0,
                "total_learning_time": current_progress.total_learning_time if current_progress else 0,
                "average_daily_time": current_progress.average_daily_time if current_progress else 0,
                "efficiency": current_progress.current_efficiency if current_progress else 0
            },
            "engine": engine_status
        }

    def _save_progress(self):
        """保存学习进度到文件"""
        try:
            if not self.progress_history:
                return

            data = {
                "last_update": datetime.now().isoformat(),
                "learning_plan": {
                    "total_courses": self.learning_plan.total_courses if self.learning_plan else 0,
                    "estimated_total_time": self.learning_plan.estimated_total_time if self.learning_plan else 0,
                    "daily_target": self.learning_plan.daily_learning_target if self.learning_plan else 0
                },
                "progress_history": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "completed_courses": p.completed_courses,
                        "completion_rate": p.completion_rate,
                        "total_learning_time": p.total_learning_time,
                        "efficiency": p.current_efficiency
                    }
                    for p in self.progress_history[-10:]  # 只保留最近10条记录
                ],
                "engine_status": self.engine.get_status()
            }

            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"进度已保存到: {self.progress_file}")

        except Exception as e:
            self.logger.error(f"保存进度失败: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_learning()