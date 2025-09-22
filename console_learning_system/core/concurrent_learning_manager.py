"""
并发学习管理器
实现多课程并发学习和单课程倍速学习功能
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ..utils.async_utils import run_async_in_sync
from ..utils.logger_utils import LoggerContext
from .config_manager import ConfigManager
from .course_manager import CourseManager, Course
from .learning_engine import LearningEngine, LearningSession


class LearningMode(Enum):
    """学习模式枚举"""
    SEQUENTIAL = "sequential"  # 顺序学习
    CONCURRENT = "concurrent"  # 并发学习
    TURBO = "turbo"          # 倍速学习


@dataclass
class ConcurrentLearningConfig:
    """并发学习配置"""
    max_concurrent_courses: int = 3  # 最大并发课程数
    speed_multiplier: float = 1.0    # 学习速度倍数
    progress_update_interval: int = 5 # 进度更新间隔(秒)
    auto_balance_load: bool = True   # 自动负载均衡
    resource_limit_per_course: float = 0.3  # 每门课程资源限制(0-1)


class ConcurrentLearningSession:
    """并发学习会话"""

    def __init__(self, course: Course, session_id: str, speed_multiplier: float = 1.0):
        self.course = course
        self.session_id = session_id
        self.speed_multiplier = speed_multiplier
        self.start_time = datetime.now()
        self.last_update_time = self.start_time
        self.total_learning_time = 0.0  # 总学习时间(秒)
        self.effective_learning_time = 0.0  # 有效学习时间(考虑倍速)
        self.initial_progress = course.progress
        self.current_progress = course.progress
        self.target_progress = 100.0
        self.status = "starting"  # starting, learning, paused, completed, failed
        self.logs: List[str] = []
        self.is_active = True

        # 倍速学习相关
        self.virtual_position = 0.0  # 虚拟播放位置
        self.real_duration = 0.0     # 实际学习时长

    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}][{self.session_id}] {message}"
        self.logs.append(log_entry)

    def update_progress(self, new_progress: float):
        """更新学习进度"""
        self.current_progress = new_progress
        self.last_update_time = datetime.now()

    def calculate_effective_time(self, real_time: float) -> float:
        """计算有效学习时间（考虑倍速）"""
        return real_time * self.speed_multiplier

    def get_progress_rate(self) -> float:
        """获取学习进度率（每分钟进度增长）"""
        elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        if elapsed_minutes <= 0:
            return 0.0
        progress_gained = self.current_progress - self.initial_progress
        return progress_gained / elapsed_minutes

    def is_stalled(self, threshold_minutes: int = 5) -> bool:
        """检查是否停滞"""
        time_since_update = (datetime.now() - self.last_update_time).total_seconds() / 60
        return time_since_update > threshold_minutes

    def complete(self):
        """完成学习"""
        self.status = "completed"
        self.is_active = False
        self.add_log(f"学习完成 - 进度: {self.initial_progress:.1f}% → {self.current_progress:.1f}%")


class ConcurrentLearningManager:
    """并发学习管理器"""

    def __init__(self, config_manager: ConfigManager, course_manager: CourseManager):
        self.config_manager = config_manager
        self.course_manager = course_manager
        self.learning_engine = LearningEngine(config_manager, course_manager)

        # 并发学习配置
        self.config = ConcurrentLearningConfig()
        self.load_config()

        # 活动会话管理
        self.active_sessions: Dict[str, ConcurrentLearningSession] = {}
        self.completed_sessions: List[ConcurrentLearningSession] = []
        self.failed_sessions: List[ConcurrentLearningSession] = []

        # 控制标志
        self.is_running = False
        self.should_stop = False

        # 统计信息
        self.total_courses_processed = 0
        self.total_learning_time = 0.0
        self.session_counter = 0

        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.session_callback: Optional[Callable] = None

    def load_config(self):
        """加载配置"""
        try:
            # 从配置文件加载并发学习设置
            concurrent_config = self.config_manager.get('concurrent_learning', {})

            self.config.max_concurrent_courses = concurrent_config.get('max_concurrent_courses', 3)
            self.config.speed_multiplier = concurrent_config.get('default_speed_multiplier', 1.0)
            self.config.progress_update_interval = concurrent_config.get('progress_update_interval', 5)
            self.config.auto_balance_load = concurrent_config.get('auto_balance_load', True)
            self.config.resource_limit_per_course = concurrent_config.get('resource_limit_per_course', 0.3)

        except Exception:
            # 使用默认配置
            pass

    def save_config(self):
        """保存配置"""
        concurrent_config = {
            'max_concurrent_courses': self.config.max_concurrent_courses,
            'default_speed_multiplier': self.config.speed_multiplier,
            'progress_update_interval': self.config.progress_update_interval,
            'auto_balance_load': self.config.auto_balance_load,
            'resource_limit_per_course': self.config.resource_limit_per_course
        }
        self.config_manager.set('concurrent_learning', concurrent_config)
        self.config_manager.save()

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self.progress_callback = callback

    def set_session_callback(self, callback: Callable):
        """设置会话回调函数"""
        self.session_callback = callback

    def generate_session_id(self) -> str:
        """生成会话ID"""
        self.session_counter += 1
        return f"session_{self.session_counter}_{int(time.time())}"

    async def start_course_learning(self, course: Course, speed_multiplier: float = 1.0) -> str:
        """开始单门课程学习"""
        session_id = self.generate_session_id()
        session = ConcurrentLearningSession(course, session_id, speed_multiplier)

        self.active_sessions[session_id] = session
        session.add_log(f"开始学习课程: {course.course_name}")

        if speed_multiplier > 1.0:
            session.add_log(f"启用倍速学习: {speed_multiplier}x")

        # 启动学习任务
        asyncio.create_task(self._learning_worker(session))

        return session_id

    async def _learning_worker(self, session: ConcurrentLearningSession):
        """学习工作协程"""
        try:
            session.status = "learning"
            session.add_log("开始学习工作进程")

            # 获取API客户端
            api_client = self.course_manager.login_manager.get_api_client()
            if not api_client:
                session.add_log("无法获取API客户端")
                session.status = "failed"
                return

            # 使用学习引擎的SCORM学习功能
            await self._perform_scorm_learning(session, api_client)

        except Exception as e:
            session.add_log(f"学习过程异常: {str(e)}")
            session.status = "failed"
        finally:
            # 清理会话
            await self._cleanup_session(session)

    async def _perform_scorm_learning(self, session: ConcurrentLearningSession, api_client):
        """执行SCORM学习"""
        course = session.course
        session.add_log(f"开始SCORM学习: {course.course_name}")

        # 获取课程信息
        course_info = await api_client.get_course_info(course.user_course_id)
        if not course_info:
            session.add_log("无法获取课程信息")
            session.status = "failed"
            return

        session.add_log(f"课程信息获取成功，视频时长: {course_info.get('video_duration', 0)}秒")

        # 计算学习参数
        video_duration = float(course_info.get('video_duration', 1800))
        current_position = course.progress * video_duration / 100.0
        target_position = video_duration * 0.95  # 学习到95%

        if session.speed_multiplier > 1.0:
            # 倍速学习：减少实际学习时间
            effective_duration = (target_position - current_position) / session.speed_multiplier
            session.add_log(f"倍速学习: 实际时长 {effective_duration:.0f}秒 (原{target_position - current_position:.0f}秒)")
        else:
            effective_duration = target_position - current_position

        # 执行学习循环
        start_time = time.time()
        last_progress_update = start_time

        while session.is_active and not self.should_stop:
            current_time = time.time()
            elapsed_time = current_time - start_time

            # 计算虚拟进度
            if session.speed_multiplier > 1.0:
                # 倍速学习：虚拟时间 = 实际时间 * 倍速
                virtual_elapsed = elapsed_time * session.speed_multiplier
            else:
                virtual_elapsed = elapsed_time

            virtual_position = current_position + virtual_elapsed

            # 限制在目标位置
            if virtual_position >= target_position:
                virtual_position = target_position
                session.is_active = False

            # 计算新进度
            new_progress = min(100.0, (virtual_position / video_duration) * 100.0)
            session.update_progress(new_progress)

            # 定期提交进度到API
            if current_time - last_progress_update >= self.config.progress_update_interval:
                await self._submit_progress(session, api_client, virtual_position, virtual_elapsed)
                last_progress_update = current_time

                # 调用进度回调
                if self.progress_callback:
                    self.progress_callback(session.course, new_progress)

            # 检查是否完成
            if new_progress >= 99.0:
                session.complete()
                break

            # 短暂休眠
            await asyncio.sleep(1)

        # 最终进度提交
        if session.status == "completed":
            await self._submit_progress(session, api_client, virtual_position, virtual_elapsed)
            session.add_log(f"学习完成，最终进度: {session.current_progress:.1f}%")

    async def _submit_progress(self, session: ConcurrentLearningSession, api_client, position: float, duration: float):
        """提交学习进度"""
        try:
            course = session.course

            # 构建SCORM数据
            serialize_sco = {
                "res01": {
                    "lesson_location": str(int(position)),
                    "session_time": str(int(duration)),
                    "last_learn_time": datetime.now().strftime("%Y-%m-%d+%H:%M:%S")
                },
                "last_study_sco": "res01"
            }

            # 提交进度
            result = await api_client.submit_learning_progress(
                user_course_id=course.user_course_id,
                serialize_sco=serialize_sco
            )

            if result:
                session.add_log(f"进度提交成功 - 位置: {position:.0f}s, 进度: {session.current_progress:.1f}%")
            else:
                session.add_log("进度提交失败")

        except Exception as e:
            session.add_log(f"进度提交异常: {str(e)}")

    async def _cleanup_session(self, session: ConcurrentLearningSession):
        """清理会话"""
        session_id = session.session_id

        # 从活动会话中移除
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        # 添加到相应的完成列表
        if session.status == "completed":
            self.completed_sessions.append(session)
        else:
            self.failed_sessions.append(session)

        # 调用会话回调
        if self.session_callback:
            self.session_callback(session)

        session.add_log(f"会话清理完成 - 状态: {session.status}")

    async def learn_courses_concurrently(self,
                                       courses: List[Course],
                                       max_concurrent: int = None,
                                       speed_multiplier: float = 1.0,
                                       max_total_time: int = None) -> List[ConcurrentLearningSession]:
        """并发学习多门课程"""
        if not courses:
            return []

        self.is_running = True
        self.should_stop = False

        max_concurrent = max_concurrent or self.config.max_concurrent_courses
        max_concurrent = min(max_concurrent, len(courses))

        print(f"🚀 开始并发学习 - 课程数:{len(courses)}, 最大并发:{max_concurrent}, 倍速:{speed_multiplier}x")

        start_time = time.time()
        course_queue = courses.copy()
        active_tasks = []

        try:
            # 启动初始批次的课程
            for i in range(min(max_concurrent, len(course_queue))):
                course = course_queue.pop(0)
                session_id = await self.start_course_learning(course, speed_multiplier)
                print(f"  📚 启动课程 {i+1}: {course.course_name}")

            # 监控和管理并发学习
            while (self.active_sessions or course_queue) and not self.should_stop:
                # 检查时间限制
                if max_total_time:
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= max_total_time:
                        print(f"⏰ 达到时间限制 ({max_total_time}秒)，停止学习")
                        break

                # 检查是否有课程完成，启动新课程
                if course_queue and len(self.active_sessions) < max_concurrent:
                    course = course_queue.pop(0)
                    session_id = await self.start_course_learning(course, speed_multiplier)
                    print(f"  📚 启动新课程: {course.course_name}")

                # 显示当前状态
                self._print_concurrent_status()

                # 短暂等待
                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print("\n⏹️ 用户中断学习")
            self.should_stop = True
        finally:
            # 等待所有活动会话完成
            if self.active_sessions:
                print("⏳ 等待活动会话完成...")
                while self.active_sessions and time.time() - start_time < (max_total_time or 3600):
                    await asyncio.sleep(1)

            self.is_running = False

        # 返回所有会话
        all_sessions = self.completed_sessions + self.failed_sessions

        # 打印最终统计
        self._print_final_statistics(start_time)

        return all_sessions

    def _print_concurrent_status(self):
        """打印并发状态"""
        if not self.active_sessions:
            return

        print(f"\n📊 并发学习状态 ({len(self.active_sessions)}个活动会话):")
        for session_id, session in self.active_sessions.items():
            elapsed = (datetime.now() - session.start_time).total_seconds()
            progress_rate = session.get_progress_rate()

            print(f"  🎯 {session.course.course_name[:30]}...")
            print(f"     进度: {session.current_progress:.1f}% (+{session.current_progress - session.initial_progress:.1f}%)")
            print(f"     时长: {elapsed:.0f}s, 速率: {progress_rate:.1f}%/min")

    def _print_final_statistics(self, start_time: float):
        """打印最终统计"""
        total_time = time.time() - start_time
        completed_count = len(self.completed_sessions)
        failed_count = len(self.failed_sessions)

        print(f"\n📈 并发学习统计:")
        print(f"  总用时: {total_time:.0f}秒 ({total_time/60:.1f}分钟)")
        print(f"  完成课程: {completed_count}门")
        print(f"  失败课程: {failed_count}门")

        if self.completed_sessions:
            total_progress_gained = sum(s.current_progress - s.initial_progress for s in self.completed_sessions)
            avg_progress_rate = total_progress_gained / (total_time / 60) if total_time > 0 else 0
            print(f"  平均学习效率: {avg_progress_rate:.1f}%/分钟")

    def get_active_sessions_count(self) -> int:
        """获取活动会话数量"""
        return len(self.active_sessions)

    def get_session_by_id(self, session_id: str) -> Optional[ConcurrentLearningSession]:
        """根据ID获取会话"""
        return self.active_sessions.get(session_id)

    def stop_all_sessions(self):
        """停止所有会话"""
        self.should_stop = True
        for session in self.active_sessions.values():
            session.is_active = False
            session.status = "interrupted"
            session.add_log("用户中断学习")

    def pause_session(self, session_id: str):
        """暂停指定会话"""
        session = self.active_sessions.get(session_id)
        if session:
            session.status = "paused"
            session.add_log("学习已暂停")

    def resume_session(self, session_id: str):
        """恢复指定会话"""
        session = self.active_sessions.get(session_id)
        if session and session.status == "paused":
            session.status = "learning"
            session.add_log("学习已恢复")

    def get_recommended_concurrent_count(self, total_courses: int) -> int:
        """获取推荐的并发数量"""
        if total_courses <= 2:
            return 1
        elif total_courses <= 5:
            return 2
        else:
            return min(3, self.config.max_concurrent_courses)

    def get_recommended_speed_multiplier(self, course_duration: float) -> float:
        """获取推荐的倍速倍数"""
        # 根据课程时长推荐倍速
        if course_duration > 3600:  # 超过1小时
            return 2.0
        elif course_duration > 1800:  # 超过30分钟
            return 1.5
        else:
            return 1.0