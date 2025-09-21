"""
学习引擎模块
集成SCORM学习功能，实现自动化学习管理
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ..utils.async_utils import run_async_in_sync
from ..utils.logger_utils import LoggerContext
from .config_manager import ConfigManager
from .course_manager import CourseManager, Course


class LearningSession:
    """学习会话类"""

    def __init__(self, course: Course, start_time: datetime = None):
        self.course = course
        self.start_time = start_time or datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration: timedelta = timedelta()
        self.initial_progress = course.progress
        self.final_progress = course.progress
        self.status = "active"  # active, completed, failed, interrupted
        self.logs: List[str] = []

    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)

    def complete(self, final_progress: float):
        """完成会话"""
        self.end_time = datetime.now()
        self.duration = self.end_time - self.start_time
        self.final_progress = final_progress
        self.status = "completed"
        self.add_log(f"学习完成 - 进度: {self.initial_progress:.1f}% → {self.final_progress:.1f}%")

    def fail(self, reason: str):
        """失败会话"""
        self.end_time = datetime.now()
        self.duration = self.end_time - self.start_time
        self.status = "failed"
        self.add_log(f"学习失败: {reason}")

    def interrupt(self, reason: str):
        """中断会话"""
        self.end_time = datetime.now()
        self.duration = self.end_time - self.start_time
        self.status = "interrupted"
        self.add_log(f"学习中断: {reason}")

    def get_progress_gained(self) -> float:
        """获取进度增长"""
        return self.final_progress - self.initial_progress

    def get_duration_str(self) -> str:
        """获取持续时间字符串"""
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}时{minutes}分{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"


class LearningStatistics:
    """学习统计类"""

    def __init__(self):
        self.sessions: List[LearningSession] = []
        self.total_learning_time = timedelta()
        self.total_courses_completed = 0
        self.total_progress_gained = 0.0

    def add_session(self, session: LearningSession):
        """添加学习会话"""
        self.sessions.append(session)
        self.total_learning_time += session.duration

        if session.status == "completed" and session.final_progress >= 100.0:
            self.total_courses_completed += 1

        self.total_progress_gained += session.get_progress_gained()

    def get_today_sessions(self) -> List[LearningSession]:
        """获取今日学习会话"""
        today = datetime.now().date()
        return [s for s in self.sessions if s.start_time.date() == today]

    def get_learning_time_str(self) -> str:
        """获取总学习时间字符串"""
        total_seconds = int(self.total_learning_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}时{minutes}分"
        else:
            return f"{minutes}分"

    def get_success_rate(self) -> float:
        """获取学习成功率"""
        if not self.sessions:
            return 0.0
        completed_sessions = len([s for s in self.sessions if s.status == "completed"])
        return (completed_sessions / len(self.sessions)) * 100.0


class LearningEngine:
    """学习引擎主类"""

    def __init__(self, config_manager: ConfigManager, course_manager: CourseManager):
        self.config = config_manager
        self.course_manager = course_manager
        self.statistics = LearningStatistics()
        self.current_session: Optional[LearningSession] = None
        self.is_learning = False
        self.should_stop = False

        # 回调函数
        self.on_progress_update: Optional[Callable] = None
        self.on_course_complete: Optional[Callable] = None
        self.on_session_start: Optional[Callable] = None
        self.on_session_end: Optional[Callable] = None

        # 初始化SCORM学习器
        self._scorm_learner = None
        self._initialize_scorm_learner()

    def _initialize_scorm_learner(self):
        """初始化SCORM学习器"""
        try:
            # 动态导入SCORM学习模块
            if os.path.exists(project_root / "scorm_based_learning.py"):
                sys.path.insert(0, str(project_root))
                import scorm_based_learning
                self._scorm_learner = scorm_based_learning

        except Exception as e:
            with LoggerContext() as logger:
                logger.warning(f"无法初始化SCORM学习器: {e}")

    def set_progress_callback(self, callback: Callable):
        """设置进度更新回调"""
        self.on_progress_update = callback

    def set_course_complete_callback(self, callback: Callable):
        """设置课程完成回调"""
        self.on_course_complete = callback

    def set_session_callbacks(self, start_callback: Callable = None, end_callback: Callable = None):
        """设置会话开始/结束回调"""
        if start_callback:
            self.on_session_start = start_callback
        if end_callback:
            self.on_session_end = end_callback

    async def get_course_progress_from_api(self, target_course: Course) -> Optional[Dict[str, Any]]:
        """从API获取特定课程的最新进度和状态"""
        try:
            # 获取登录管理器的API客户端
            api_client = self.course_manager.login_manager.get_api_client()
            if not api_client:
                if self.current_session:
                    self.current_session.add_log("  API客户端获取失败")
                return None

            # 获取所有课程的最新数据
            all_courses = await api_client.get_all_courses()

            if not all_courses:
                if self.current_session:
                    self.current_session.add_log("  API未返回课程列表")
                return None

            # 查找匹配的课程 - 使用更宽松的匹配
            target_id = str(target_course.user_course_id)

            for course_data in all_courses:
                api_id = str(course_data.get('user_course_id', ''))

                # 多种匹配方式
                if api_id == target_id:
                    # 返回包含progress和status的课程信息
                    progress_value = float(course_data.get('progress', 0.0))  # API已经是0-100格式
                    status_value = course_data.get('status', '')  # 字符串状态

                    if self.current_session:
                        self.current_session.add_log(f"  API课程匹配成功: ID={api_id}, 进度={progress_value:.1f}%")

                    return {
                        'progress': progress_value,
                        'status': status_value,  # "completed"=已完成, "learning"=学习中
                        'course_name': course_data.get('course_name', ''),
                        'user_course_id': course_data.get('user_course_id')
                    }

            if self.current_session:
                self.current_session.add_log(f"  API未找到匹配课程: target_id={target_id}")
            return None

        except Exception as e:
            if self.current_session:
                self.current_session.add_log(f"  获取API进度异常: {str(e)}")
            return None

    async def get_course_progress_from_sync_api(self, sync_client, target_course: Course) -> Optional[Dict[str, Any]]:
        """从同步API客户端获取特定课程的最新进度和状态"""
        try:
            # 直接使用同步API客户端获取所有课程
            all_courses = await sync_client.get_all_courses()

            if not all_courses:
                if self.current_session:
                    self.current_session.add_log("  同步API未返回课程列表")
                return None

            # 查找匹配的课程
            target_id = str(target_course.user_course_id)

            for course_data in all_courses:
                api_id = str(course_data.get('user_course_id', ''))

                if api_id == target_id:
                    progress_value = float(course_data.get('progress', 0.0))
                    status_value = course_data.get('status', '')

                    if self.current_session:
                        self.current_session.add_log(f"  同步API课程匹配成功: ID={api_id}, 进度={progress_value:.1f}%")

                    return {
                        'progress': progress_value,
                        'status': status_value,
                        'course_name': course_data.get('course_name', ''),
                        'user_course_id': course_data.get('user_course_id')
                    }

            if self.current_session:
                self.current_session.add_log(f"  同步API未找到匹配课程: target_id={target_id}")
            return None

        except Exception as e:
            if self.current_session:
                self.current_session.add_log(f"  同步API获取进度异常: {str(e)}")
            return None

    def get_learning_queue(self, course_type: str = None, max_courses: int = None) -> List[Course]:
        """获取学习队列"""
        courses = run_async_in_sync(self.course_manager.get_courses())

        # 过滤条件
        learning_queue = []
        for course in courses:
            # 跳过已完成的课程（使用API返回的status字段：status='completed'表示已完成）
            if course.status == 'completed':
                continue

            # 按课程类型过滤
            if course_type and course.course_type != course_type:
                continue

            learning_queue.append(course)

        # 按优先级排序：必修课优先，然后按进度升序
        learning_queue.sort(key=lambda c: (
            0 if c.course_type == 'required' else 1,  # 必修课优先
            c.progress  # 进度低的优先
        ))

        # 限制数量
        if max_courses:
            learning_queue = learning_queue[:max_courses]

        return learning_queue

    def start_learning_session(self, course: Course) -> bool:
        """开始学习会话"""
        if self.is_learning:
            return False

        try:
            self.current_session = LearningSession(course)
            self.is_learning = True
            self.should_stop = False

            self.current_session.add_log(f"开始学习课程: {course.course_name}")

            # 触发会话开始回调
            if self.on_session_start:
                self.on_session_start(self.current_session)

            return True

        except Exception as e:
            with LoggerContext() as logger:
                logger.error(f"开始学习会话失败: {e}")
            return False

    def stop_learning_session(self, reason: str = "用户停止"):
        """停止学习会话"""
        if not self.is_learning or not self.current_session:
            return

        self.should_stop = True
        self.current_session.interrupt(reason)
        self.statistics.add_session(self.current_session)

        # 触发会话结束回调
        if self.on_session_end:
            self.on_session_end(self.current_session)

        self.is_learning = False
        self.current_session = None

    def learn_course(self, course: Course, max_duration: int = None) -> LearningSession:
        """学习单个课程（同步入口，使用模拟学习）"""
        if not self.start_learning_session(course):
            session = LearningSession(course)
            session.fail("无法开始学习会话")
            return session

        # 触发会话开始回调
        if self.on_session_start:
            self.on_session_start(self.current_session)

        try:
            success = run_async_in_sync(self._learn_with_scorm_sync(course, max_duration or 1800))

            # 获取更新后的课程进度
            try:
                # 使用当前会话记录的最终进度（来自API），而不是本地过期数据
                if hasattr(self.current_session, 'final_progress') and self.current_session.final_progress is not None:
                    final_progress = self.current_session.final_progress
                    self.current_session.add_log(f"使用API最新进度: {final_progress:.1f}%")
                else:
                    # 备用方案：从本地数据获取
                    updated_course = self.course_manager.get_course_by_id(course.course_id)
                    final_progress = updated_course.progress if updated_course else course.progress
                    self.current_session.add_log(f"使用本地进度: {final_progress:.1f}%")
            except Exception as e:
                self.current_session.add_log(f"获取最终进度失败: {e}")
                final_progress = course.progress

            if success:
                self.current_session.complete(final_progress)

                # 触发最终进度更新回调
                if self.on_progress_update:
                    self.on_progress_update(course, final_progress)

                # 如果课程完成，触发完成回调
                if final_progress >= 100.0 and self.on_course_complete:
                    self.on_course_complete(course)
            else:
                self.current_session.fail("学习过程失败")
            return self.current_session
        except Exception as e:
            self.current_session.fail(f"学习异常: {e}")
            return self.current_session
        finally:
            # 只清理状态，不要修改会话的完成状态
            if self.is_learning:
                self.is_learning = False
                # 注意：不要在这里设置should_stop=True，因为会中断批量学习

            # 保存会话到统计数据
            if self.current_session:
                self.statistics.add_session(self.current_session)

                # 触发会话结束回调
                if self.on_session_end:
                    self.on_session_end(self.current_session)

            # 清理当前会话
            self.current_session = None

    async def learn_course_async(self, course: Course, max_duration: int = None) -> LearningSession:
        """学习单个课程（异步版本，可使用真实SCORM）"""
        if not self.start_learning_session(course):
            session = LearningSession(course)
            session.fail("无法开始学习会话")
            return session

        try:
            return await self._learn_course_async(course, max_duration)
        except Exception as e:
            self.current_session.fail(f"学习异常: {e}")
            return self.current_session
        finally:
            if self.is_learning:
                self.stop_learning_session("学习完成")

    async def _learn_course_async(self, course: Course, max_duration: int = None) -> LearningSession:
        """异步学习课程"""
        session = self.current_session
        start_time = time.time()
        max_time = max_duration or self.config.get('learning.max_duration_per_course', 1800)  # 默认30分钟

        try:
            # 使用SCORM学习器
            if self._scorm_learner:
                success = await self._learn_with_scorm(course, max_time)
            else:
                # 备用学习方法
                success = await self._learn_with_simulation(course, max_time)

            # 更新课程进度
            try:
                # 使用会话记录的最终进度（来自API），而不是本地过期数据
                if hasattr(session, 'final_progress') and session.final_progress is not None:
                    final_progress = session.final_progress
                    session.add_log(f"使用API最新进度: {final_progress:.1f}%")
                else:
                    # 备用方案：从本地数据获取
                    updated_course = self.course_manager.get_course_by_id(course.course_id)
                    final_progress = updated_course.progress if updated_course else course.progress
                    session.add_log(f"使用本地进度: {final_progress:.1f}%")
            except Exception as e:
                session.add_log(f"获取最终进度失败: {e}")
                final_progress = course.progress

            if success:
                session.complete(final_progress)

                # 触发进度更新回调
                if self.on_progress_update:
                    self.on_progress_update(course, final_progress)

                # 如果课程完成，触发完成回调
                if final_progress >= 100.0 and self.on_course_complete:
                    self.on_course_complete(course)
            else:
                session.fail("学习过程失败")

        except Exception as e:
            session.fail(f"学习异常: {e}")

        self.statistics.add_session(session)
        return session

    async def _learn_with_scorm(self, course: Course, max_time: int) -> bool:
        """使用基于SCORM标准的正确学习方法"""
        try:
            self.current_session.add_log("启动SCORM标准学习引擎")

            # 检查登录状态并获取API客户端
            if not self.course_manager.login_manager.is_logged_in_sync():
                self.current_session.add_log("用户未登录，尝试自动登录...")
                success = self.course_manager.login_manager.ensure_logged_in()
                if not success:
                    self.current_session.add_log("自动登录失败")
                    return False

            api_client = self.course_manager.login_manager.get_api_client()
            if not api_client:
                self.current_session.add_log("无法获取API客户端，回退到模拟学习")
                return await self._learn_with_simulation(course, max_time)

            # 第1步：获取课程清单和当前状态
            course_manifest = await self._load_course_manifest(api_client, course)
            if not course_manifest:
                self.current_session.add_log("无法获取课程清单，回退到模拟学习")
                return await self._learn_with_simulation(course, max_time)

            # 第2步：初始化SCORM播放器
            await self._init_scorm_player(api_client, course)

            # 第3步：执行SCORM学习会话
            return await self._execute_scorm_learning_session(api_client, course, course_manifest, max_time)

        except Exception as e:
            self.current_session.add_log(f"SCORM学习异常: {e}")
            return False

    async def _learn_with_simulation(self, course: Course, max_time: int) -> bool:
        """模拟学习过程（备用方法）"""
        try:
            self.current_session.add_log("启动模拟学习引擎")

            learning_time = 0
            check_interval = 10  # 每10秒检查一次

            while learning_time < max_time and not self.should_stop:
                await asyncio.sleep(check_interval)
                learning_time += check_interval

                # 模拟进度增长
                remaining = 100.0 - course.progress
                if remaining > 0:
                    increment = min(3.0, remaining * 0.05)
                    course.progress += increment

                    self.current_session.add_log(f"模拟学习进度: {course.progress:.1f}%")

                    # 检查完成
                    if course.progress >= 100.0:
                        course.progress = 100.0
                        self.current_session.add_log("模拟学习完成")
                        return True

            return False

        except Exception as e:
            self.current_session.add_log(f"模拟学习错误: {e}")
            return False

    def learn_multiple_courses(self, courses: List[Course] = None,
                             course_type: str = None,
                             max_courses: int = None,
                             max_total_time: int = None) -> List[LearningSession]:
        """学习多个课程"""
        if courses is None:
            courses = self.get_learning_queue(course_type, max_courses)

        sessions = []
        start_time = time.time()
        max_time = max_total_time or self.config.get('learning.max_total_time', 7200)  # 默认2小时

        with LoggerContext() as logger:
            logger.info(f"开始批量学习 {len(courses)} 门课程")

        for i, course in enumerate(courses):
            if self.should_stop:
                break

            elapsed_time = time.time() - start_time
            if elapsed_time >= max_time:
                with LoggerContext() as logger:
                    logger.info("达到最大学习时间限制，停止批量学习")
                break

            remaining_time = max_time - elapsed_time
            course_max_time = min(
                self.config.get('learning.max_duration_per_course', 1800),
                remaining_time
            )

            with LoggerContext() as logger:
                logger.info(f"学习课程 {i+1}/{len(courses)}: {course.course_name}")

            session = self.learn_course(course, int(course_max_time))
            sessions.append(session)

            # 课程间休息
            rest_time = self.config.get('learning.rest_between_courses', 5)
            if rest_time > 0 and i < len(courses) - 1:
                time.sleep(rest_time)

        return sessions

    def get_learning_recommendations(self) -> Dict[str, Any]:
        """获取学习建议"""
        courses = run_async_in_sync(self.course_manager.get_courses())

        # 统计分析
        total_courses = len(courses)
        completed_courses = len([c for c in courses if c.progress >= 100.0])
        required_incomplete = len([c for c in courses if c.course_type == 'required' and c.progress < 100.0])
        elective_incomplete = len([c for c in courses if c.course_type == 'elective' and c.progress < 100.0])

        # 平均进度
        total_progress = sum(c.progress for c in courses)
        avg_progress = total_progress / total_courses if total_courses > 0 else 0

        # 建议优先级
        priority_courses = []
        if required_incomplete > 0:
            required_courses = [c for c in courses if c.course_type == 'required' and c.progress < 100.0]
            priority_courses.extend(sorted(required_courses, key=lambda x: x.progress)[:3])

        # 生成建议
        recommendations = {
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'completion_rate': (completed_courses / total_courses * 100) if total_courses > 0 else 0,
            'required_incomplete': required_incomplete,
            'elective_incomplete': elective_incomplete,
            'average_progress': avg_progress,
            'priority_courses': priority_courses,
            'estimated_time': self._estimate_learning_time(courses),
            'next_action': self._get_next_action_recommendation(courses)
        }

        return recommendations

    def _estimate_learning_time(self, courses: List[Course]) -> Dict[str, int]:
        """估算学习时间"""
        incomplete_courses = [c for c in courses if c.progress < 100.0]

        # 基于历史数据估算
        avg_time_per_course = self.config.get('learning.estimated_time_per_course', 30)  # 分钟

        total_remaining_progress = sum(100.0 - c.progress for c in incomplete_courses)
        estimated_minutes = int((total_remaining_progress / 100.0) * avg_time_per_course)

        return {
            'total_minutes': estimated_minutes,
            'total_hours': estimated_minutes // 60,
            'remaining_minutes': estimated_minutes % 60
        }

    def _get_next_action_recommendation(self, courses: List[Course]) -> str:
        """获取下一步行动建议"""
        incomplete_required = [c for c in courses if c.course_type == 'required' and c.progress < 100.0]
        incomplete_elective = [c for c in courses if c.course_type == 'elective' and c.progress < 100.0]

        if incomplete_required:
            return f"建议优先完成 {len(incomplete_required)} 门必修课程"
        elif incomplete_elective:
            return f"可以学习 {len(incomplete_elective)} 门选修课程"
        else:
            return "恭喜！所有课程已完成"

    def get_session_summary(self, session: LearningSession) -> Dict[str, Any]:
        """获取学习会话摘要"""
        return {
            'course_name': session.course.course_name,
            'course_type': session.course.course_type,
            'start_time': session.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else None,
            'duration': session.get_duration_str(),
            'initial_progress': session.initial_progress,
            'final_progress': session.final_progress,
            'progress_gained': session.get_progress_gained(),
            'status': session.status,
            'log_count': len(session.logs)
        }

    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        today_sessions = self.statistics.get_today_sessions()

        return {
            'total_sessions': len(self.statistics.sessions),
            'today_sessions': len(today_sessions),
            'total_learning_time': self.statistics.get_learning_time_str(),
            'total_courses_completed': self.statistics.total_courses_completed,
            'total_progress_gained': self.statistics.total_progress_gained,
            'success_rate': self.statistics.get_success_rate(),
            'current_status': 'learning' if self.is_learning else 'idle'
        }

    async def _load_course_manifest(self, api_client, course: Course) -> dict:
        """加载课程清单和状态"""
        try:
            self.current_session.add_log("获取课程清单和当前学习状态...")

            # 直接使用API客户端的session以保持登录状态和cookies
            import json

            url = f"{api_client.base_url}/device/study_new!getManifest.do"
            params = {'id': int(course.course_id), '_': int(time.time() * 1000)}

            # 使用原始session保持登录状态
            async with api_client.session.get(url, params=params) as response:
                    if response.status == 200:
                        manifest = json.loads(await response.text())

                        lesson_location = int(manifest.get('lesson_location', '0'))
                        self.current_session.add_log(f"课程: {manifest.get('title', course.course_name)}")
                        self.current_session.add_log(f"当前播放位置: {lesson_location}秒")
                        self.current_session.add_log(f"上次学习SCO: {manifest.get('last_study_sco', 'res01')}")

                        return manifest
                    else:
                        self.current_session.add_log(f"获取课程清单失败: HTTP {response.status}")
                        return None
        except Exception as e:
            self.current_session.add_log(f"加载课程清单异常: {e}")
            return None

    async def _init_scorm_player(self, api_client, course: Course):
        """初始化SCORM播放器"""
        try:
            self.current_session.add_log("初始化SCORM播放器...")

            url = f"{api_client.base_url}/device/study_new!scorm_play.do"
            params = {'terminal': 1, 'id': int(course.user_course_id)}

            # 使用原始session保持登录状态
            async with api_client.session.get(url, params=params) as response:
                    if response.status == 200:
                        self.current_session.add_log("SCORM播放器初始化成功")
                    else:
                        self.current_session.add_log(f"SCORM播放器初始化失败: HTTP {response.status}")
        except Exception as e:
            self.current_session.add_log(f"初始化SCORM播放器异常: {e}")

    async def _execute_scorm_learning_session(self, api_client, course: Course, manifest: dict, max_time: int) -> bool:
        """执行SCORM学习会话"""
        import time
        import json
        from datetime import datetime

        start_time = time.time()
        lesson_location = int(manifest.get('lesson_location', '0'))
        session_time = 0
        total_duration = 0
        last_submit_time = start_time

        self.current_session.add_log(f"开始SCORM学习会话，从位置 {lesson_location}秒 开始")

        # 基于scorm_based_learning.py的真实学习场景
        learning_scenarios = [
            {
                'action': 'play',
                'duration': 45,  # 观看45秒
                'advance': 60,   # 播放位置前进60秒
                'description': '正常播放学习'
            },
            {
                'action': 'play',
                'duration': 55,  # 观看55秒
                'advance': 60,   # 播放位置前进60秒
                'description': '继续学习'
            },
            {
                'action': 'play',
                'duration': 40,  # 观看40秒
                'advance': 45,   # 播放位置前进45秒
                'description': '深入学习'
            },
            {
                'action': 'play',
                'duration': 50,  # 观看50秒
                'advance': 55,   # 播放位置前进55秒
                'description': '持续学习'
            }
        ]

        for i, scenario in enumerate(learning_scenarios):
            if self.should_stop or (time.time() - start_time) >= max_time:
                break

            current_time = time.time()
            time_since_last = current_time - last_submit_time

            # 更新SCORM状态
            session_time += scenario['duration']  # 累积观看时长
            lesson_location += scenario['advance'] # 更新播放位置
            total_duration += int(time_since_last) # 累积总时长

            self.current_session.add_log(f"执行学习场景 {i+1}: {scenario['description']}")
            self.current_session.add_log(f"  观看时长: {scenario['duration']}秒, 播放位置: {lesson_location}秒")

            # 构造正确的SCORM进度数据（基于scorm_based_learning.py的格式）
            current_time_str = datetime.now().strftime('%Y-%m-%d+%H:%M:%S')

            serialize_sco = {
                "res01": {
                    "lesson_location": lesson_location,
                    "session_time": scenario['duration'],  # 本次观看时长
                    "last_learn_time": current_time_str
                },
                "last_study_sco": "res01"
            }

            post_data = {
                'id': str(int(course.user_course_id)),
                'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
                'duration': str(total_duration)
            }

            # 提交SCORM进度
            try:
                url = f"{api_client.base_url}/device/study_new!seek.do"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={int(course.user_course_id)}'
                }

                # 使用原始session保持登录状态，临时添加额外headers
                original_headers = dict(api_client.session.headers)
                api_client.session.headers.update(headers)

                try:
                    async with api_client.session.post(url, data=post_data) as response:
                        if response.status == 200:
                            result = await response.text()
                            # 修复：根据scorm_based_learning.py的成功表现，HTTP 200就表示成功
                            self.current_session.add_log(f"  SCORM进度提交成功: {result}")

                            # 获取API进度 - 无论是否有回调都要执行
                            try:
                                # 从API获取真实的进度和状态
                                self.current_session.add_log(f"  获取API最新进度...")
                                course_info = await self.get_course_progress_from_api(course)

                                if course_info:
                                    real_progress = course_info['progress']
                                    course_status = course_info['status']

                                    # 更新当前会话的最终进度
                                    self.current_session.final_progress = real_progress

                                    status_text = "已完成" if course_status == "completed" else "学习中"
                                    self.current_session.add_log(f"  📈 API进度: {real_progress:.1f}% ({status_text})")

                                    # 如果有回调，触发它
                                    if self.on_progress_update:
                                        self.on_progress_update(course, real_progress)
                                        self.current_session.add_log(f"  ✅ 已触发进度回调")
                                else:
                                    # 如果API获取失败，使用估算进度
                                    estimated_progress = min(100.0, course.progress + (i / len(learning_scenarios) * 10))
                                    self.current_session.add_log(f"  📈 进度(估算): {estimated_progress:.1f}%")

                                    # 如果有回调，触发它
                                    if self.on_progress_update:
                                        self.on_progress_update(course, estimated_progress)
                            except Exception as e:
                                self.current_session.add_log(f"  获取进度异常: {e}")
                        else:
                            self.current_session.add_log(f"  SCORM进度提交失败: HTTP {response.status}")
                finally:
                    # 恢复原始headers
                    api_client.session.headers.clear()
                    api_client.session.headers.update(original_headers)

            except Exception as e:
                self.current_session.add_log(f"  提交进度异常: {e}")

            last_submit_time = current_time

            # 学习间隔（模拟真实学习行为）
            if i < len(learning_scenarios) - 1:
                wait_time = 15 + (i * 5)  # 递增等待时间
                self.current_session.add_log(f"  学习间隔 {wait_time}秒...")
                await asyncio.sleep(wait_time)

        # 学习会话总结
        total_session_time = time.time() - start_time
        self.current_session.add_log(f"SCORM学习会话完成")
        self.current_session.add_log(f"  会话总时长: {int(total_session_time)}秒")
        self.current_session.add_log(f"  有效学习时长: {session_time}秒")
        self.current_session.add_log(f"  最终播放位置: {lesson_location}秒")
        self.current_session.add_log(f"  学习效率: {session_time/total_session_time*100:.1f}%")

        return True

    async def _learn_with_scorm_sync(self, course: Course, max_time: int) -> bool:
        """同步环境下的SCORM学习（创建独立的API客户端避免事件循环冲突）"""
        try:
            self.current_session.add_log("启动同步SCORM学习引擎")

            # 在新的事件循环中创建独立的API客户端
            from final_working_api_client import FinalWorkingAPIClient

            async with FinalWorkingAPIClient() as sync_client:
                # 登录
                success = await sync_client.login("640302198607120020", "My2062660")
                if not success:
                    self.current_session.add_log("同步API客户端登录失败")
                    return await self._learn_with_simulation(course, max_time)

                self.current_session.add_log("同步API客户端登录成功")

                # 第1步：获取课程清单
                manifest = await self._load_course_manifest_sync(sync_client, course)
                if not manifest:
                    self.current_session.add_log("无法获取课程清单，回退到模拟学习")
                    return await self._learn_with_simulation(course, max_time)

                # 第2步：初始化SCORM播放器
                await self._init_scorm_player_sync(sync_client, course)

                # 第3步：执行SCORM学习会话
                return await self._execute_scorm_learning_session_sync(sync_client, course, manifest, max_time)

        except Exception as e:
            self.current_session.add_log(f"同步SCORM学习异常: {e}")
            return await self._learn_with_simulation(course, max_time)

    async def _load_course_manifest_sync(self, sync_client, course: Course) -> dict:
        """同步版本：加载课程清单"""
        try:
            self.current_session.add_log("获取课程清单和当前学习状态...")

            import json
            url = f"{sync_client.base_url}/device/study_new!getManifest.do"
            params = {'id': int(course.course_id), '_': int(time.time() * 1000)}

            async with sync_client.session.get(url, params=params) as response:
                if response.status == 200:
                    manifest = json.loads(await response.text())
                    lesson_location = int(manifest.get('lesson_location', '0'))
                    self.current_session.add_log(f"课程: {manifest.get('title', course.course_name)}")
                    self.current_session.add_log(f"当前播放位置: {lesson_location}秒")
                    self.current_session.add_log(f"上次学习SCO: {manifest.get('last_study_sco', 'res01')}")
                    return manifest
                else:
                    self.current_session.add_log(f"获取课程清单失败: HTTP {response.status}")
                    return None
        except Exception as e:
            self.current_session.add_log(f"加载课程清单异常: {e}")
            return None

    async def _init_scorm_player_sync(self, sync_client, course: Course):
        """同步版本：初始化SCORM播放器"""
        try:
            self.current_session.add_log("初始化SCORM播放器...")
            url = f"{sync_client.base_url}/device/study_new!scorm_play.do"
            params = {'terminal': 1, 'id': int(course.user_course_id)}

            async with sync_client.session.get(url, params=params) as response:
                if response.status == 200:
                    self.current_session.add_log("SCORM播放器初始化成功")
                else:
                    self.current_session.add_log(f"SCORM播放器初始化失败: HTTP {response.status}")
        except Exception as e:
            self.current_session.add_log(f"初始化SCORM播放器异常: {e}")

    async def _execute_scorm_learning_session_sync(self, sync_client, course: Course, manifest: dict, max_time: int) -> bool:
        """同步版本：执行SCORM学习会话"""
        import time
        import json
        from datetime import datetime

        start_time = time.time()
        lesson_location = int(manifest.get('lesson_location', '0'))
        session_time = 0
        total_duration = 0
        last_submit_time = start_time

        self.current_session.add_log(f"开始SCORM学习会话，从位置 {lesson_location}秒 开始")

        # 动态学习场景生成，持续到时间限制
        scenario_cycle = [
            {'action': 'play', 'duration': 45, 'advance': 60, 'description': '正常播放学习'},
            {'action': 'play', 'duration': 55, 'advance': 60, 'description': '继续学习'},
            {'action': 'play', 'duration': 40, 'advance': 45, 'description': '深入学习'},
            {'action': 'play', 'duration': 50, 'advance': 55, 'description': '持续学习'},
            {'action': 'play', 'duration': 60, 'advance': 65, 'description': '专注学习'},
            {'action': 'play', 'duration': 35, 'advance': 40, 'description': '巩固学习'}
        ]

        scenario_index = 0
        total_scenarios = 0

        # 持续学习直到时间限制
        while (time.time() - start_time) < max_time:
            scenario = scenario_cycle[scenario_index % len(scenario_cycle)]
            total_scenarios += 1

            current_time = time.time()
            time_since_last = current_time - last_submit_time

            # 更新SCORM状态
            session_time += scenario['duration']
            lesson_location += scenario['advance']
            total_duration += int(time_since_last)

            self.current_session.add_log(f"执行学习场景 {total_scenarios}: {scenario['description']}")
            self.current_session.add_log(f"  观看时长: {scenario['duration']}秒, 播放位置: {lesson_location}秒")

            # 触发进度回调（每隔几个学习场景检查一次进度）
            if self.on_progress_update and total_scenarios % 2 == 0:  # 每两个场景检查一次
                try:
                    # 使用当前的sync_client重新获取课程清单来获取最新进度
                    url = f"{sync_client.base_url}/device/study_new!getManifest.do"
                    params = {'id': int(course.course_id), '_': int(time.time() * 1000)}

                    async with sync_client.session.get(url, params=params) as response:
                        if response.status == 200:
                            manifest_update = json.loads(await response.text())
                            # 计算理论进度（播放位置 / 总时长）
                            current_location = int(manifest_update.get('lesson_location', lesson_location))
                            total_time_str = manifest_update.get('total_time', '')

                            if total_time_str and ':' in total_time_str:
                                time_parts = total_time_str.split(':')
                                if len(time_parts) == 3:
                                    total_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
                                    if total_seconds > 0:
                                        current_progress = min(100.0, (current_location / total_seconds) * 100.0)
                                        self.on_progress_update(course, current_progress)
                                        self.current_session.add_log(f"  📈 当前进度: {current_progress:.1f}% ({current_location}/{total_seconds}秒)")
                                    else:
                                        self.current_session.add_log(f"  📈 播放位置: {current_location}秒 (总时长未知)")
                                else:
                                    self.current_session.add_log(f"  📈 播放位置: {current_location}秒")
                            else:
                                self.current_session.add_log(f"  📈 播放位置: {current_location}秒")
                        else:
                            self.current_session.add_log(f"  获取进度更新失败: HTTP {response.status}")
                except Exception as e:
                    self.current_session.add_log(f"  进度回调异常: {e}")

            # 构造SCORM进度数据
            current_time_str = datetime.now().strftime('%Y-%m-%d+%H:%M:%S')
            serialize_sco = {
                "res01": {
                    "lesson_location": lesson_location,
                    "session_time": scenario['duration'],
                    "last_learn_time": current_time_str
                },
                "last_study_sco": "res01"
            }

            post_data = {
                'id': str(int(course.user_course_id)),
                'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
                'duration': str(total_duration)
            }

            # 提交SCORM进度
            try:
                url = f"{sync_client.base_url}/device/study_new!seek.do"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={int(course.user_course_id)}'
                }

                async with sync_client.session.post(url, data=post_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.text()
                        self.current_session.add_log(f"  SCORM进度提交成功: {result}")

                        # 获取API进度 - 无论是否有回调都要执行
                        try:
                            # 从API获取真实的进度和状态
                            self.current_session.add_log(f"  获取API最新进度...")
                            course_info = await self.get_course_progress_from_sync_api(sync_client, course)

                            if course_info:
                                real_progress = course_info['progress']
                                course_status = course_info['status']

                                # 更新当前会话的最终进度
                                self.current_session.final_progress = real_progress

                                status_text = "已完成" if course_status == "completed" else "学习中"
                                self.current_session.add_log(f"  📈 API进度: {real_progress:.1f}% ({status_text})")

                                # 如果有回调，触发它
                                if self.on_progress_update:
                                    self.on_progress_update(course, real_progress)
                                    self.current_session.add_log(f"  ✅ 已触发进度回调")

                                # 如果API显示已完成，提前结束学习
                                if course_status == "completed":
                                    self.current_session.add_log(f"  🎉 API显示课程已完成，结束学习")
                                    break
                            else:
                                # 如果API获取失败，使用估算进度
                                estimated_progress = min(100.0, course.progress + (total_scenarios * 0.5))
                                self.current_session.add_log(f"  📈 进度(估算): {estimated_progress:.1f}%")

                                # 如果有回调，触发它
                                if self.on_progress_update:
                                    self.on_progress_update(course, estimated_progress)
                        except Exception as e:
                            self.current_session.add_log(f"  获取进度异常: {e}")
                    else:
                        self.current_session.add_log(f"  SCORM进度提交失败: HTTP {response.status}")

            except Exception as e:
                self.current_session.add_log(f"  提交进度异常: {e}")

            last_submit_time = current_time

            # 学习间隔（动态计算，避免超过时间限制）
            remaining_time = max_time - (time.time() - start_time)
            if remaining_time > 30:  # 还有足够时间进行下一轮
                wait_time = min(15 + (scenario_index * 2), 25)  # 15-25秒间隔
                self.current_session.add_log(f"  学习间隔 {wait_time}秒...")
                await asyncio.sleep(wait_time)
            elif remaining_time > 5:  # 时间不多，短暂间隔
                short_wait = min(5, int(remaining_time - 2))
                self.current_session.add_log(f"  短暂间隔 {short_wait}秒...")
                await asyncio.sleep(short_wait)

            scenario_index += 1

        # 会话总结
        total_session_time = time.time() - start_time
        self.current_session.add_log(f"SCORM学习会话完成")
        self.current_session.add_log(f"  执行场景数: {total_scenarios}")
        self.current_session.add_log(f"  会话总时长: {int(total_session_time)}秒")
        self.current_session.add_log(f"  有效学习时长: {session_time}秒")
        self.current_session.add_log(f"  最终播放位置: {lesson_location}秒")
        self.current_session.add_log(f"  播放位置增长: +{lesson_location - int(manifest.get('lesson_location', '0'))}秒")
        if total_session_time > 0:
            self.current_session.add_log(f"  学习效率: {session_time/total_session_time*100:.1f}%")

        return True