"""
并发学习管理器
实现多课程并发学习功能
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import sys
from ..utils.progress_display import ProgressBar, ConcurrentProgressDisplay

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


@dataclass
class ConcurrentLearningConfig:
    """并发学习配置"""
    max_concurrent_courses: int = 3  # 最大并发课程数
    progress_update_interval: int = 30 # 进度更新间隔(秒) - 默认30秒
    auto_balance_load: bool = True   # 自动负载均衡
    resource_limit_per_course: float = 0.3  # 每门课程资源限制(0-1)


class ConcurrentLearningSession:
    """并发学习会话"""

    def __init__(self, course: Course, session_id: str):
        self.course = course
        self.session_id = session_id
        self.start_time = datetime.now()
        self.last_update_time = self.start_time
        self.total_learning_time = 0.0  # 总学习时间(秒)
        self.initial_progress = course.progress
        self.current_progress = course.progress
        self.target_progress = 100.0
        self.status = "starting"  # starting, learning, paused, completed, failed
        self.logs: List[str] = []
        self.is_active = True

        # 错误处理和重试相关
        self.error_count = 0
        self.max_retries = 3
        self.last_error: Optional[str] = None
        self.retry_delay = 5  # 重试延迟(秒)

        # 客户端管理
        self.assigned_client_id = None  # 分配的客户端ID
        self.api_client = None          # 分配的API客户端

        # API提交统计
        self.api_submissions = 0        # API提交次数
        self.api_success_count = 0      # API成功次数

    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}][{self.session_id}] {message}"
        self.logs.append(log_entry)

    def update_progress(self, new_progress: float):
        """更新学习进度"""
        self.current_progress = new_progress
        self.last_update_time = datetime.now()


    def get_elapsed_time(self) -> float:
        """获取已运行时间（秒）"""
        return (datetime.now() - self.start_time).total_seconds()

    def get_progress_rate(self) -> float:
        """获取学习进度率（每分钟进度增长）"""
        elapsed_minutes = self.get_elapsed_time() / 60
        if elapsed_minutes <= 0:
            return 0.0
        progress_gained = self.current_progress - self.initial_progress
        return progress_gained / elapsed_minutes

    def record_error(self, error_message: str) -> bool:
        """记录错误并判断是否可以重试"""
        self.error_count += 1
        self.last_error = error_message
        self.add_log(f"错误 #{self.error_count}: {error_message}")

        if self.error_count <= self.max_retries:
            self.add_log(f"将在 {self.retry_delay} 秒后重试 ({self.error_count}/{self.max_retries})")
            return True  # 可以重试
        else:
            self.add_log(f"达到最大重试次数 ({self.max_retries})，会话失败")
            self.status = "failed"
            self.is_active = False
            return False  # 不能重试

    def reset_for_retry(self):
        """重置会话状态以准备重试"""
        self.status = "starting"
        self.is_active = True
        self.add_log("重新开始学习会话")

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

        # API客户端池管理
        self.master_client = None  # 主客户端（用于登录）
        self.client_pool: Dict[str, Any] = {}  # 客户端池
        self.available_clients: List[str] = []  # 可用客户端ID列表

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
            self.config.progress_update_interval = concurrent_config.get('progress_update_interval', 30)
            self.config.auto_balance_load = concurrent_config.get('auto_balance_load', True)
            self.config.resource_limit_per_course = concurrent_config.get('resource_limit_per_course', 0.3)

        except Exception:
            # 使用默认配置
            pass

    def save_config(self):
        """保存配置"""
        concurrent_config = {
            'max_concurrent_courses': self.config.max_concurrent_courses,
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

    async def initialize_client_pool(self, pool_size: int = None):
        """初始化客户端池"""
        if pool_size is None:
            pool_size = self.config.max_concurrent_courses

        # 获取主客户端
        self.master_client = self.course_manager.login_manager.get_api_client()
        if not self.master_client:
            raise RuntimeError("无法获取主API客户端，请先登录")

        print(f"🏊‍♂️ 初始化客户端池，大小: {pool_size}")

        # 创建子客户端
        for i in range(pool_size):
            client_id = f"pool_client_{i+1}"
            try:
                child_client = await self.master_client.create_child_client(client_id)
                self.client_pool[client_id] = child_client
                self.available_clients.append(client_id)
                print(f"✅ 创建客户端: {client_id}")
            except Exception as e:
                print(f"❌ 创建客户端失败 {client_id}: {e}")

        print(f"🎯 客户端池初始化完成，可用客户端: {len(self.available_clients)}")

    def get_available_client(self):
        """获取可用的客户端"""
        if self.available_clients:
            client_id = self.available_clients.pop(0)
            return self.client_pool.get(client_id)
        return None

    def return_client(self, client_id: str):
        """归还客户端到池中"""
        if client_id in self.client_pool and client_id not in self.available_clients:
            self.available_clients.append(client_id)

    async def cleanup_client_pool(self):
        """清理客户端池"""
        for client_id, client in self.client_pool.items():
            try:
                await client.close()
            except Exception as e:
                print(f"⚠️ 关闭客户端异常 {client_id}: {e}")

        self.client_pool.clear()
        self.available_clients.clear()
        print("🧹 客户端池已清理")

    def generate_session_id(self) -> str:
        """生成会话ID"""
        self.session_counter += 1
        return f"session_{self.session_counter}_{int(time.time())}"

    async def start_course_learning(self, course: Course) -> str:
        """开始单门课程学习"""
        session_id = self.generate_session_id()
        session = ConcurrentLearningSession(course, session_id)

        self.active_sessions[session_id] = session
        session.add_log(f"开始学习课程: {course.course_name}")

        # 启动学习任务
        asyncio.create_task(self._learning_worker(session))

        return session_id

    async def _learning_worker(self, session: ConcurrentLearningSession):
        """学习工作协程（带重试机制）"""
        while session.is_active and not self.should_stop:
            try:
                await self._perform_learning_attempt(session)
                break  # 成功完成，退出重试循环

            except Exception as e:
                error_message = str(e)
                session.add_log(f"学习尝试失败: {error_message}")

                # 记录错误并判断是否可以重试
                if session.record_error(error_message):
                    # 可以重试，等待后重新尝试
                    await asyncio.sleep(session.retry_delay)
                    session.reset_for_retry()
                else:
                    # 不能重试，会话失败
                    break

        # 清理会话
        await self._cleanup_session(session)

    async def _perform_learning_attempt(self, session: ConcurrentLearningSession):
        """执行单次学习尝试"""
        client_acquired = False
        api_client = None

        try:
            session.status = "learning"
            session.add_log("开始学习工作进程")

            # 从客户端池获取API客户端
            api_client = self.get_available_client()
            if not api_client:
                # 回退到共享客户端
                api_client = self.course_manager.login_manager.get_api_client()
                if not api_client:
                    raise RuntimeError("无法获取API客户端")
                session.add_log("使用共享API客户端")
            else:
                client_acquired = True
                session.assigned_client_id = api_client.client_id
                session.api_client = api_client
                session.add_log(f"分配专用客户端: {api_client.client_id}")

            # 使用学习引擎的SCORM学习功能
            await self._perform_scorm_learning(session, api_client)

        finally:
            # 归还客户端到池中
            if client_acquired and session.assigned_client_id and api_client:
                self.return_client(session.assigned_client_id)
                session.add_log(f"归还客户端: {session.assigned_client_id}")

    async def _perform_scorm_learning(self, session: ConcurrentLearningSession, api_client):
        """执行SCORM学习"""
        course = session.course
        session.add_log(f"开始SCORM学习: {course.course_name}")

        # 使用默认课程参数（因为API客户端没有get_course_info方法）
        session.add_log("使用默认课程参数进行学习")

        # 计算学习参数（智能处理duration）
        raw_duration = getattr(course, 'duration', 0)

        # 如果duration值异常小（小于60秒）或为0，使用默认值
        if raw_duration < 60:
            video_duration = 1800.0  # 默认30分钟
            session.add_log(f"课程duration异常({raw_duration}秒)，使用默认30分钟")
        else:
            # duration可能是分钟，转换为秒
            if raw_duration < 3600:  # 小于60分钟，可能是分钟单位
                video_duration = float(raw_duration * 60)
                session.add_log(f"课程duration: {raw_duration}分钟 → {video_duration}秒")
            else:
                video_duration = float(raw_duration)
                session.add_log(f"课程duration: {video_duration}秒")

        current_position = course.progress * video_duration / 100.0
        target_position = video_duration * 0.95  # 学习到95%
        effective_duration = target_position - current_position

        session.add_log(f"学习参数 - 总时长: {video_duration}秒, 当前: {current_position:.0f}s, 目标: {target_position:.0f}s")

        # 执行学习循环
        start_time = time.time()
        last_progress_update = start_time
        total_virtual_time = 0.0  # 累积的虚拟学习时间
        last_loop_time = start_time

        while session.is_active and not self.should_stop:
            current_time = time.time()
            elapsed_time = current_time - start_time
            loop_interval = current_time - last_loop_time
            last_loop_time = current_time

            # 计算这个循环周期的虚拟学习进度（添加随机波动）
            progress_multiplier = random.uniform(0.9, 1.1)  # 90%-110%的随机速度
            virtual_increment = loop_interval * progress_multiplier
            total_virtual_time += virtual_increment
            virtual_position = current_position + total_virtual_time

            # 限制在目标位置
            if virtual_position >= target_position:
                virtual_position = target_position
                session.is_active = False

            # 计算新进度
            new_progress = min(100.0, (virtual_position / video_duration) * 100.0)
            session.update_progress(new_progress)

            # 定期提交进度到API
            if current_time - last_progress_update >= self.config.progress_update_interval:
                await self._submit_progress(session, api_client, virtual_position, total_virtual_time)
                last_progress_update = current_time
                session.add_log(f"定期进度提交 - 虚拟位置: {virtual_position:.0f}s, 虚拟时长: {total_virtual_time:.0f}s")

                # 调用进度回调
                if self.progress_callback:
                    self.progress_callback(session.course, new_progress)

            # 检查是否完成（基于虚拟进度或实际课程进度）
            if new_progress >= 99.0 or session.course.progress >= 99.0:
                session.complete()
                session.add_log(f"课程学习完成 - 进度: {new_progress:.1f}%, 实际进度: {session.course.progress:.1f}%")
                break

            # 模拟真实学习节奏 - 8-12秒随机间隔
            sleep_time = random.uniform(8, 12)
            await asyncio.sleep(sleep_time)

        # 最终进度提交
        if session.status == "completed":
            await self._submit_progress(session, api_client, virtual_position, total_virtual_time)
            session.add_log(f"最终进度提交 - 虚拟位置: {virtual_position:.0f}s, 总虚拟时长: {total_virtual_time:.0f}s")
            session.add_log(f"学习完成，最终进度: {session.current_progress:.1f}%")

    async def _submit_progress(self, session: ConcurrentLearningSession, api_client, position: float, duration: float):
        """提交学习进度"""
        try:
            course = session.course
            session.api_submissions += 1  # 增加提交次数统计

            session.add_log(f"尝试提交进度 - 课程ID: {course.user_course_id}, 位置: {position:.0f}s, 时长: {duration:.0f}s")

            # 提交进度（使用API客户端的实际方法签名）
            result = await api_client.submit_learning_progress(
                user_course_id=course.user_course_id,
                current_location=str(int(position)),
                session_time=str(int(duration)),
                duration=str(int(duration))
            )

            if result:
                session.api_success_count += 1  # 增加成功次数统计
                session.add_log(f"✅ 进度提交成功 - 位置: {position:.0f}s, 本地进度: {session.current_progress:.1f}%")

                # 更新本地课程进度（基于提交的位置计算）
                try:
                    old_progress = course.progress
                    # 根据当前播放位置计算新的进度百分比
                    if video_duration > 0:
                        new_progress = min((position / video_duration) * 100, 100.0)
                        course.progress = new_progress
                        session.add_log(f"本地进度已更新: {old_progress:.1f}% → {course.progress:.1f}%")
                    else:
                        session.add_log("⚠️ 无法计算进度，视频时长为0")
                except Exception as e:
                    session.add_log(f"本地进度更新失败: {str(e)}")
            else:
                session.add_log("❌ 进度提交失败 - API返回False")

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
                                       max_total_time: int = None) -> List[ConcurrentLearningSession]:
        """并发学习多门课程"""
        if not courses:
            return []

        self.is_running = True
        self.should_stop = False

        max_concurrent = max_concurrent or self.config.max_concurrent_courses
        max_concurrent = min(max_concurrent, len(courses))

        print(f"🚀 开始并发学习 - 课程数:{len(courses)}, 最大并发:{max_concurrent}")

        # 初始化客户端池
        if not self.client_pool:
            print("🏊‍♂️ 初始化客户端池...")
            await self.initialize_client_pool(max_concurrent)

        start_time = time.time()
        self._start_time = start_time  # 保存开始时间供状态显示使用
        course_queue = courses.copy()
        active_tasks = []

        try:
            # 启动初始批次的课程
            for i in range(min(max_concurrent, len(course_queue))):
                course = course_queue.pop(0)
                session_id = await self.start_course_learning(course)
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
                    session_id = await self.start_course_learning(course)
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

            # 清理客户端池
            print("🧹 清理客户端池...")
            await self.cleanup_client_pool()

        # 返回所有会话
        all_sessions = self.completed_sessions + self.failed_sessions

        # 打印最终统计
        self._print_final_statistics(start_time)

        return all_sessions

    def _print_concurrent_status(self):
        """打印并发状态（使用美化的进度条）"""
        if not self.active_sessions:
            return

        # 清屏效果（可选）
        # print("\033[2J\033[H")  # 清屏并移动光标到顶部

        # 使用新的仪表板显示
        total_time = time.time() - getattr(self, '_start_time', time.time())
        dashboard = ConcurrentProgressDisplay.create_summary_dashboard(
            self.active_sessions,
            self.completed_sessions,
            self.failed_sessions,
            total_time,
            self.config.max_concurrent_courses
        )
        print(dashboard)

        # 显示每个活动会话的详细信息
        if self.active_sessions:
            print(f"\n{ProgressBar.create_status_badge('learning')} 活动会话详情:")
            for session_id, session in self.active_sessions.items():
                card = ConcurrentProgressDisplay.create_session_card(session)
                print(card)

    def _print_final_statistics(self, start_time: float):
        """打印最终统计（使用美化显示）"""
        total_time = time.time() - start_time
        completed_count = len(self.completed_sessions)
        failed_count = len(self.failed_sessions)

        # 创建分隔线
        print("\n" + "=" * 70)
        print(f"{'🎉 并发学习完成报告 🎉':^70}")
        print("=" * 70)

        # 完成概览
        total_courses = completed_count + failed_count
        if total_courses > 0:
            success_rate = (completed_count / total_courses) * 100
            progress_bar = ProgressBar.create_bar(success_rate, width=40)
            print(f"\n成功率: {progress_bar}")

        # 状态统计卡片
        print(f"\n📊 学习成果:")
        print(f"  {ProgressBar.create_status_badge('completed')} 完成: {completed_count} 门")
        print(f"  {ProgressBar.create_status_badge('failed')} 失败: {failed_count} 门")

        # 时间统计
        time_display = ProgressBar.create_time_display(total_time)
        print(f"\n⏱️  总用时: {time_display}")

        # 效率分析
        if self.completed_sessions:
            total_progress_gained = sum(s.current_progress - s.initial_progress for s in self.completed_sessions)
            avg_progress_rate = total_progress_gained / (total_time / 60) if total_time > 0 else 0

            efficiency_indicator = ProgressBar.create_speed_indicator(avg_progress_rate)
            print(f"⚡ 平均效率: {efficiency_indicator}")

            # 显示最佳表现
            best_session = max(self.completed_sessions,
                             key=lambda s: s.current_progress - s.initial_progress)
            best_progress = best_session.current_progress - best_session.initial_progress
            print(f"\n🏆 最佳表现:")
            print(f"  课程: {best_session.course.course_name[:40]}")
            print(f"  进度提升: +{best_progress:.1f}%")

        print("=" * 70)

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

