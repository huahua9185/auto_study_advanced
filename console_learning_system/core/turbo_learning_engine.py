"""
倍速学习引擎
实现单课程的高效倍速学习功能
"""

import asyncio
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
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


@dataclass
class TurboLearningConfig:
    """倍速学习配置"""
    max_speed_multiplier: float = 5.0    # 最大倍速倍数
    min_speed_multiplier: float = 1.0    # 最小倍速倍数
    adaptive_speed: bool = True          # 自适应速度调节
    progress_check_interval: int = 3     # 进度检查间隔(秒)
    virtual_interaction_rate: float = 0.8  # 虚拟交互率
    safety_margin: float = 0.95         # 安全边际(学习到视频的95%)


class TurboLearningSession:
    """倍速学习会话"""

    def __init__(self, course: Course, target_speed: float = 2.0):
        self.course = course
        self.target_speed = target_speed
        self.current_speed = 1.0
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

        # 学习进度
        self.initial_progress = course.progress
        self.current_progress = course.progress
        self.target_progress = 100.0

        # 时间统计
        self.real_time_spent = 0.0       # 实际耗时
        self.virtual_time_learned = 0.0  # 虚拟学习时间
        self.efficiency_ratio = 0.0      # 效率比率

        # 状态管理
        self.status = "preparing"  # preparing, learning, accelerating, completed, failed
        self.is_active = True
        self.logs: List[str] = []

        # 倍速学习相关
        self.speed_changes: List[Dict] = []  # 速度变化记录
        self.interaction_points: List[Dict] = []  # 交互点记录

    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}][倍速] {message}"
        self.logs.append(log_entry)

    def change_speed(self, new_speed: float, reason: str = ""):
        """改变学习速度"""
        old_speed = self.current_speed
        self.current_speed = new_speed

        change_record = {
            'timestamp': datetime.now(),
            'old_speed': old_speed,
            'new_speed': new_speed,
            'reason': reason
        }
        self.speed_changes.append(change_record)

        self.add_log(f"速度调整: {old_speed:.1f}x → {new_speed:.1f}x ({reason})")

    def add_interaction_point(self, virtual_position: float, interaction_type: str):
        """添加交互点"""
        interaction = {
            'timestamp': datetime.now(),
            'virtual_position': virtual_position,
            'interaction_type': interaction_type,
            'speed_at_time': self.current_speed
        }
        self.interaction_points.append(interaction)

    def calculate_efficiency(self) -> float:
        """计算学习效率"""
        if self.real_time_spent <= 0:
            return 0.0

        progress_gained = self.current_progress - self.initial_progress
        time_minutes = self.real_time_spent / 60

        return progress_gained / time_minutes if time_minutes > 0 else 0.0

    def get_speed_stability(self) -> float:
        """获取速度稳定性（0-1，1表示最稳定）"""
        if len(self.speed_changes) <= 1:
            return 1.0

        speed_variations = []
        for i in range(1, len(self.speed_changes)):
            prev_speed = self.speed_changes[i-1]['new_speed']
            curr_speed = self.speed_changes[i]['new_speed']
            variation = abs(curr_speed - prev_speed) / prev_speed
            speed_variations.append(variation)

        avg_variation = sum(speed_variations) / len(speed_variations)
        return max(0.0, 1.0 - avg_variation)

    def complete(self):
        """完成倍速学习"""
        self.end_time = datetime.now()
        self.status = "completed"
        self.is_active = False

        total_duration = (self.end_time - self.start_time).total_seconds()
        self.real_time_spent = total_duration
        self.efficiency_ratio = self.calculate_efficiency()

        self.add_log(f"倍速学习完成 - 耗时: {total_duration:.0f}s, 效率: {self.efficiency_ratio:.1f}%/min")


class TurboLearningEngine:
    """倍速学习引擎"""

    def __init__(self, config_manager: ConfigManager, course_manager: CourseManager):
        self.config_manager = config_manager
        self.course_manager = course_manager

        # 倍速学习配置
        self.config = TurboLearningConfig()
        self.load_config()

        # 当前会话
        self.current_session: Optional[TurboLearningSession] = None

        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.speed_callback: Optional[Callable] = None

    def load_config(self):
        """加载配置"""
        try:
            turbo_config = self.config_manager.get('turbo_learning', {})

            self.config.max_speed_multiplier = turbo_config.get('max_speed_multiplier', 5.0)
            self.config.min_speed_multiplier = turbo_config.get('min_speed_multiplier', 1.0)
            self.config.adaptive_speed = turbo_config.get('adaptive_speed', True)
            self.config.progress_check_interval = turbo_config.get('progress_check_interval', 3)
            self.config.virtual_interaction_rate = turbo_config.get('virtual_interaction_rate', 0.8)
            self.config.safety_margin = turbo_config.get('safety_margin', 0.95)

        except Exception:
            # 使用默认配置
            pass

    def save_config(self):
        """保存配置"""
        turbo_config = {
            'max_speed_multiplier': self.config.max_speed_multiplier,
            'min_speed_multiplier': self.config.min_speed_multiplier,
            'adaptive_speed': self.config.adaptive_speed,
            'progress_check_interval': self.config.progress_check_interval,
            'virtual_interaction_rate': self.config.virtual_interaction_rate,
            'safety_margin': self.config.safety_margin
        }
        self.config_manager.set('turbo_learning', turbo_config)
        self.config_manager.save()

    def set_progress_callback(self, callback: Callable):
        """设置进度回调"""
        self.progress_callback = callback

    def set_speed_callback(self, callback: Callable):
        """设置速度回调"""
        self.speed_callback = callback

    def calculate_optimal_speed(self, course: Course, target_time: Optional[int] = None) -> float:
        """计算最优学习速度"""
        try:
            # 获取课程信息
            api_client = self.course_manager.login_manager.get_api_client()
            if not api_client:
                return 2.0  # 默认2倍速

            course_info = run_async_in_sync(api_client.get_course_info(course.user_course_id))
            if not course_info:
                return 2.0

            video_duration = float(course_info.get('video_duration', 1800))
            current_progress = course.progress
            remaining_progress = 100.0 - current_progress

            # 计算剩余时间
            remaining_time = video_duration * (remaining_progress / 100.0)

            if target_time:
                # 根据目标时间计算速度
                required_speed = remaining_time / target_time
                # 限制在合理范围内
                return max(
                    self.config.min_speed_multiplier,
                    min(self.config.max_speed_multiplier, required_speed)
                )
            else:
                # 根据剩余时间推荐速度
                if remaining_time > 3600:  # 超过1小时
                    return 3.0
                elif remaining_time > 1800:  # 超过30分钟
                    return 2.5
                elif remaining_time > 600:   # 超过10分钟
                    return 2.0
                else:
                    return 1.5

        except Exception:
            return 2.0  # 默认值

    async def learn_course_turbo(self,
                                course: Course,
                                target_speed: float = None,
                                target_time: int = None,
                                auto_adjust: bool = True) -> TurboLearningSession:
        """倍速学习单门课程"""

        # 计算最优速度
        if target_speed is None:
            target_speed = self.calculate_optimal_speed(course, target_time)

        # 限制速度范围
        target_speed = max(
            self.config.min_speed_multiplier,
            min(self.config.max_speed_multiplier, target_speed)
        )

        # 创建倍速学习会话
        session = TurboLearningSession(course, target_speed)
        self.current_session = session

        session.add_log(f"开始倍速学习: {course.course_name}")
        session.add_log(f"目标速度: {target_speed:.1f}x")

        try:
            # 获取API客户端
            api_client = self.course_manager.login_manager.get_api_client()
            if not api_client:
                session.add_log("无法获取API客户端")
                session.status = "failed"
                return session

            # 获取课程信息
            course_info = await api_client.get_course_info(course.user_course_id)
            if not course_info:
                session.add_log("无法获取课程信息")
                session.status = "failed"
                return session

            video_duration = float(course_info.get('video_duration', 1800))
            session.add_log(f"视频总时长: {video_duration:.0f}秒")

            # 开始倍速学习
            await self._perform_turbo_learning(session, api_client, video_duration, auto_adjust)

        except Exception as e:
            session.add_log(f"倍速学习异常: {str(e)}")
            session.status = "failed"
        finally:
            session.complete()
            self.current_session = None

        return session

    async def _perform_turbo_learning(self,
                                    session: TurboLearningSession,
                                    api_client,
                                    video_duration: float,
                                    auto_adjust: bool):
        """执行倍速学习"""
        session.status = "learning"

        # 计算学习参数
        current_progress = session.initial_progress
        current_position = current_progress * video_duration / 100.0
        target_position = video_duration * self.config.safety_margin

        session.add_log(f"学习范围: {current_position:.0f}s → {target_position:.0f}s")

        # 设置初始速度
        session.change_speed(session.target_speed, "初始设置")

        # 学习循环
        start_time = time.time()
        last_progress_update = start_time
        last_interaction_time = start_time

        virtual_position = current_position
        learning_segments = self._generate_learning_segments(
            current_position, target_position, session.target_speed
        )

        for segment_idx, segment in enumerate(learning_segments):
            if not session.is_active:
                break

            session.add_log(f"执行学习片段 {segment_idx + 1}/{len(learning_segments)}")

            # 执行学习片段
            await self._execute_learning_segment(
                session, api_client, segment, video_duration, auto_adjust
            )

        # 最终检查
        if session.current_progress >= 99.0:
            session.add_log("达到学习目标")
        else:
            session.add_log(f"学习结束，当前进度: {session.current_progress:.1f}%")

    def _generate_learning_segments(self,
                                  start_position: float,
                                  end_position: float,
                                  speed: float) -> List[Dict]:
        """生成学习片段"""
        segments = []
        total_duration = end_position - start_position

        # 根据速度和总时长分割成合理的片段
        segment_count = max(3, min(10, int(total_duration / 300)))  # 每片段约5分钟
        segment_duration = total_duration / segment_count

        for i in range(segment_count):
            segment_start = start_position + i * segment_duration
            segment_end = min(end_position, segment_start + segment_duration)

            # 添加一些随机性以模拟真实学习
            speed_variation = 0.8 + (i % 3) * 0.1  # 0.8-1.0的速度变化

            segment = {
                'start_position': segment_start,
                'end_position': segment_end,
                'duration': segment_end - segment_start,
                'base_speed': speed,
                'speed_variation': speed_variation,
                'interaction_points': self._generate_interaction_points(segment_start, segment_end)
            }

            segments.append(segment)

        return segments

    def _generate_interaction_points(self, start: float, end: float) -> List[Dict]:
        """生成交互点"""
        interactions = []
        segment_duration = end - start

        # 每30-60秒生成一个交互点
        interval = max(30, min(60, segment_duration / 5))
        current_pos = start

        while current_pos < end:
            interaction_type = self._choose_interaction_type()
            interactions.append({
                'position': current_pos,
                'type': interaction_type,
                'duration': 1 + (hash(str(current_pos)) % 3)  # 1-3秒
            })

            current_pos += interval + (hash(str(current_pos)) % 20)  # 添加随机性

        return interactions

    def _choose_interaction_type(self) -> str:
        """选择交互类型"""
        import random
        interactions = ['pause', 'seek', 'volume', 'speed_adjust', 'continue']
        return random.choice(interactions)

    async def _execute_learning_segment(self,
                                      session: TurboLearningSession,
                                      api_client,
                                      segment: Dict,
                                      video_duration: float,
                                      auto_adjust: bool):
        """执行学习片段"""
        start_pos = segment['start_position']
        end_pos = segment['end_position']
        base_speed = segment['base_speed']

        session.add_log(f"片段学习: {start_pos:.0f}s → {end_pos:.0f}s (速度: {base_speed:.1f}x)")

        # 片段开始时间
        segment_start_time = time.time()
        virtual_position = start_pos

        # 执行交互点
        for interaction in segment['interaction_points']:
            if not session.is_active:
                break

            # 学习到交互点
            target_pos = interaction['position']
            await self._learn_to_position(
                session, api_client, virtual_position, target_pos,
                video_duration, base_speed
            )

            # 执行交互
            await self._execute_interaction(session, interaction)

            virtual_position = target_pos

        # 完成片段剩余部分
        if session.is_active and virtual_position < end_pos:
            await self._learn_to_position(
                session, api_client, virtual_position, end_pos,
                video_duration, base_speed
            )

    async def _learn_to_position(self,
                               session: TurboLearningSession,
                               api_client,
                               start_pos: float,
                               end_pos: float,
                               video_duration: float,
                               speed: float):
        """学习到指定位置"""
        duration = end_pos - start_pos
        real_time_needed = duration / speed

        session.add_log(f"学习: {start_pos:.0f}s → {end_pos:.0f}s (实际耗时: {real_time_needed:.0f}s)")

        # 模拟学习过程
        steps = max(3, int(real_time_needed / 5))  # 每5秒更新一次
        step_time = real_time_needed / steps
        step_progress = duration / steps

        current_pos = start_pos

        for step in range(steps):
            if not session.is_active:
                break

            # 更新位置
            current_pos += step_progress
            new_progress = min(100.0, (current_pos / video_duration) * 100.0)
            session.current_progress = new_progress

            # 提交进度
            await self._submit_turbo_progress(session, api_client, current_pos, real_time_needed)

            # 调用回调
            if self.progress_callback:
                self.progress_callback(session.course, new_progress)

            # 等待
            await asyncio.sleep(step_time)

    async def _execute_interaction(self, session: TurboLearningSession, interaction: Dict):
        """执行交互"""
        interaction_type = interaction['type']
        duration = interaction['duration']

        session.add_interaction_point(interaction['position'], interaction_type)

        if interaction_type == 'pause':
            session.add_log(f"模拟暂停 {duration}秒")
        elif interaction_type == 'seek':
            session.add_log(f"模拟跳转操作")
        elif interaction_type == 'speed_adjust':
            # 临时调整速度
            old_speed = session.current_speed
            new_speed = old_speed * (0.9 + (hash(str(interaction['position'])) % 20) / 100)
            session.change_speed(new_speed, "用户调整")

        # 等待交互时间
        await asyncio.sleep(duration)

    async def _submit_turbo_progress(self,
                                   session: TurboLearningSession,
                                   api_client,
                                   position: float,
                                   session_time: float):
        """提交倍速学习进度"""
        try:
            # 构建SCORM数据
            serialize_sco = {
                "res01": {
                    "lesson_location": str(int(position)),
                    "session_time": str(int(session_time)),
                    "last_learn_time": datetime.now().strftime("%Y-%m-%d+%H:%M:%S")
                },
                "last_study_sco": "res01"
            }

            # 提交进度
            result = await api_client.submit_learning_progress(
                user_course_id=session.course.user_course_id,
                serialize_sco=serialize_sco
            )

            if result:
                session.add_log(f"倍速进度提交成功 - 位置: {position:.0f}s, 进度: {session.current_progress:.1f}%")
                return True
            else:
                session.add_log("倍速进度提交失败")
                return False

        except Exception as e:
            session.add_log(f"倍速进度提交异常: {str(e)}")
            return False

    def get_speed_recommendations(self, course: Course) -> Dict[str, float]:
        """获取速度推荐"""
        try:
            api_client = self.course_manager.login_manager.get_api_client()
            if not api_client:
                return {'conservative': 1.5, 'balanced': 2.0, 'aggressive': 3.0}

            course_info = run_async_in_sync(api_client.get_course_info(course.user_course_id))
            if not course_info:
                return {'conservative': 1.5, 'balanced': 2.0, 'aggressive': 3.0}

            video_duration = float(course_info.get('video_duration', 1800))
            remaining_progress = 100.0 - course.progress
            remaining_time = video_duration * (remaining_progress / 100.0)

            # 根据剩余时间推荐
            if remaining_time > 3600:  # 超过1小时
                return {
                    'conservative': 2.0,
                    'balanced': 3.0,
                    'aggressive': 4.0
                }
            elif remaining_time > 1800:  # 超过30分钟
                return {
                    'conservative': 1.5,
                    'balanced': 2.5,
                    'aggressive': 3.5
                }
            else:  # 30分钟内
                return {
                    'conservative': 1.2,
                    'balanced': 2.0,
                    'aggressive': 3.0
                }

        except Exception:
            return {'conservative': 1.5, 'balanced': 2.0, 'aggressive': 3.0}

    def estimate_completion_time(self, course: Course, speed: float) -> Dict[str, Any]:
        """估算完成时间"""
        try:
            api_client = self.course_manager.login_manager.get_api_client()
            if not api_client:
                return {'error': '无法获取API客户端'}

            course_info = run_async_in_sync(api_client.get_course_info(course.user_course_id))
            if not course_info:
                return {'error': '无法获取课程信息'}

            video_duration = float(course_info.get('video_duration', 1800))
            remaining_progress = 100.0 - course.progress
            remaining_video_time = video_duration * (remaining_progress / 100.0)

            # 考虑倍速和交互时间
            real_learning_time = remaining_video_time / speed
            interaction_overhead = real_learning_time * 0.1  # 10%的交互开销
            total_estimated_time = real_learning_time + interaction_overhead

            return {
                'remaining_video_time': remaining_video_time,
                'real_learning_time': real_learning_time,
                'total_estimated_time': total_estimated_time,
                'time_saved': remaining_video_time - total_estimated_time,
                'efficiency_gain': ((remaining_video_time - total_estimated_time) / remaining_video_time) * 100
            }

        except Exception as e:
            return {'error': f'估算失败: {str(e)}'}

    def stop_current_session(self):
        """停止当前会话"""
        if self.current_session:
            self.current_session.is_active = False
            self.current_session.add_log("用户停止倍速学习")

    def get_current_session_status(self) -> Optional[Dict]:
        """获取当前会话状态"""
        if not self.current_session:
            return None

        return {
            'course_name': self.current_session.course.course_name,
            'current_speed': self.current_session.current_speed,
            'progress': self.current_session.current_progress,
            'status': self.current_session.status,
            'efficiency': self.current_session.calculate_efficiency(),
            'time_spent': (datetime.now() - self.current_session.start_time).total_seconds()
        }