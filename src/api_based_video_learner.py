#!/usr/bin/env python3
"""
基于API的智能视频学习引擎
绕过前端UI，直接与后端API交互，实现高效自动学习
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin
import threading
from datetime import datetime

@dataclass
class VideoInfo:
    """视频信息"""
    sco_id: str
    course_id: str
    user_course_id: str
    sco_name: str
    duration_minutes: int
    video_url: str
    file_path: str
    file_name: str
    course_no: str

@dataclass
class StudyProgress:
    """学习进度"""
    current_position: int  # 当前播放位置(秒)
    total_duration: int   # 总时长(秒)
    completion_rate: float  # 完成率(0-1)
    study_times: int      # 学习次数
    last_study_time: str  # 最后学习时间

class APIBasedVideoLearner:
    """基于API的视频学习引擎"""

    def __init__(self, cookies: Dict[str, str], token: str = "3ee5648315e911e7b2f200fff6167960"):
        self.cookies = cookies
        self.token = token
        self.base_url = "https://edu.nxgbjy.org.cn"
        self.logger = self._setup_logger()

        # API会话
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://edu.nxgbjy.org.cn/nxxzxy/index.html',
            'token': token,
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })

        # 学习状态
        self.current_video: Optional[VideoInfo] = None
        self.current_progress: Optional[StudyProgress] = None
        self.is_studying = False
        self.study_thread: Optional[threading.Thread] = None

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger('APIVideoLearner')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def check_course_permission(self, user_course_id: str, study_times: int = 1) -> bool:
        """检查课程学习权限"""
        try:
            url = f"{self.base_url}/device/course!check_course.do"
            params = {
                'user_course_id': user_course_id,
                'study_times': study_times,
                'terminal': 1
            }

            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                play_status = data.get('play_status', 0)
                status = data.get('status', 0)
                self.logger.info(f"课程权限检查: user_course_id={user_course_id}, play_status={play_status}, status={status}")

                # play_status含义分析:
                # 1 = 可以播放
                # 3 = 可能是已完成或其他可播放状态
                # 0 = 不可播放
                allowed_statuses = [1, 3]  # 扩展允许的状态码

                if play_status in allowed_statuses:
                    self.logger.info(f"课程权限检查通过: play_status={play_status}")
                    return True
                else:
                    self.logger.warning(f"课程权限不足: play_status={play_status}")
                    return False
            else:
                self.logger.error(f"权限检查失败: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"权限检查异常: {e}")
            return False

    def get_course_manifest(self, course_id: str) -> Optional[Dict]:
        """获取课程清单信息"""
        try:
            url = f"{self.base_url}/device/study_new!getManifest.do"
            params = {
                'id': course_id,
                '_': int(time.time() * 1000)
            }

            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"获取课程清单成功: {data.get('title', 'Unknown')}")
                return data
            else:
                self.logger.error(f"获取课程清单失败: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"获取课程清单异常: {e}")
            return None

    def parse_video_info_from_manifest(self, manifest: Dict, user_course_id: str) -> Optional[VideoInfo]:
        """从课程清单解析视频信息"""
        try:
            if 'chapter' not in manifest or not manifest['chapter']:
                return None

            chapter = manifest['chapter'][0]  # 取第一个章节

            # 解析视频URL，提取路径和文件名
            video_url = chapter.get('url', '')
            if not video_url:
                return None

            # 从URL提取文件信息: https://edu.nxgbjy.org.cn/course/nx202505/sco1/1.mp4
            parts = video_url.split('/')
            if len(parts) >= 3:
                course_no = manifest.get('course_no', parts[-3])
                file_path = parts[-2]  # sco1
                file_name = parts[-1]  # 1.mp4
            else:
                course_no = manifest.get('course_no', '')
                file_path = 'sco1'
                file_name = '1.mp4'

            video_info = VideoInfo(
                sco_id=chapter.get('sco_id', ''),
                course_id=chapter.get('course_id', ''),
                user_course_id=user_course_id,
                sco_name=chapter.get('sco_name', ''),
                duration_minutes=int(chapter.get('duration', 0)),
                video_url=video_url,
                file_path=file_path,
                file_name=file_name,
                course_no=course_no
            )

            self.logger.info(f"解析视频信息成功: {video_info.sco_name} ({video_info.duration_minutes}分钟)")
            return video_info

        except Exception as e:
            self.logger.error(f"解析视频信息失败: {e}")
            return None

    def get_video_real_url(self, video_info: VideoInfo) -> Optional[str]:
        """获取视频真实URL"""
        try:
            # 尝试多种文件名格式
            file_variants = [
                f"{video_info.file_name}",  # 1.mp4
                f"{video_info.file_name.replace('.mp4', '_L.mp4')}",  # 1_L.mp4
                "1.mp4",  # 默认文件名
                "1_L.mp4"  # 默认低质量文件名
            ]

            for file_name in file_variants:
                try:
                    url = f"{self.base_url}/device/study_new!getUrlBypf.do"
                    params = {
                        'path': video_info.file_path,
                        'fileName': file_name,
                        'course_no': video_info.course_no,
                        'is_gkk': 'false',
                        '_': int(time.time() * 1000)
                    }

                    response = self.session.get(url, params=params)
                    if response.status_code == 200:
                        real_url = response.text.strip()
                        if real_url and real_url.startswith('http'):
                            self.logger.info(f"获取到视频真实URL: {real_url}")
                            return real_url

                except Exception as e:
                    continue

            # 如果API方式失败，尝试直接构造URL
            direct_url = f"{self.base_url}/course/{video_info.course_no}/{video_info.file_path}/1.mp4"
            self.logger.info(f"使用直接构造的URL: {direct_url}")
            return direct_url

        except Exception as e:
            self.logger.error(f"获取视频真实URL失败: {e}")
            return None

    def init_scorm_player(self, user_course_id: str) -> bool:
        """初始化SCORM播放器"""
        try:
            url = f"{self.base_url}/device/study_new!scorm_play.do"
            params = {
                'terminal': 1,
                'id': user_course_id
            }

            response = self.session.get(url, params=params)
            success = response.status_code == 200

            if success:
                self.logger.info("SCORM播放器初始化成功")
            else:
                self.logger.error(f"SCORM播放器初始化失败: {response.status_code}")

            return success

        except Exception as e:
            self.logger.error(f"SCORM播放器初始化异常: {e}")
            return False

    def report_study_progress(self, video_info: VideoInfo, position_seconds: int) -> bool:
        """上报学习进度"""
        try:
            url = f"{self.base_url}/device/study_new!seek.do"

            # 构造SCORM格式的进度数据
            progress_data = {
                'user_course_id': video_info.user_course_id,
                'course_id': video_info.course_id,
                'sco_id': video_info.sco_id,
                'lesson_location': position_seconds,
                'session_time': position_seconds,
                'completion_status': 'incomplete' if position_seconds < video_info.duration_minutes * 60 * 0.9 else 'completed'
            }

            response = self.session.post(url, json=progress_data)
            success = response.status_code == 200

            if success:
                self.logger.debug(f"进度上报成功: {position_seconds}秒 ({position_seconds//60}:{position_seconds%60:02d})")
            else:
                self.logger.error(f"进度上报失败: {response.status_code}")

            return success

        except Exception as e:
            self.logger.error(f"进度上报异常: {e}")
            return False

    def simulate_video_study(self, video_info: VideoInfo,
                           speed_multiplier: float = 1.0,
                           report_interval: int = 30) -> bool:
        """模拟视频学习过程"""
        try:
            total_seconds = video_info.duration_minutes * 60
            current_position = 0

            self.logger.info(f"开始学习视频: {video_info.sco_name}")
            self.logger.info(f"视频时长: {video_info.duration_minutes}分钟 ({total_seconds}秒)")
            self.logger.info(f"学习倍速: {speed_multiplier}x")
            self.logger.info(f"进度上报间隔: {report_interval}秒")

            self.is_studying = True
            start_time = time.time()
            last_report_position = 0

            while current_position < total_seconds and self.is_studying:
                # 计算实际等待时间（考虑倍速）
                sleep_duration = min(report_interval, total_seconds - current_position) / speed_multiplier
                time.sleep(sleep_duration)

                # 更新当前位置
                current_position += report_interval
                current_position = min(current_position, total_seconds)

                # 计算完成率
                completion_rate = current_position / total_seconds

                # 更新进度状态
                self.current_progress = StudyProgress(
                    current_position=current_position,
                    total_duration=total_seconds,
                    completion_rate=completion_rate,
                    study_times=1,
                    last_study_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                # 显示进度
                progress_bar = "█" * int(completion_rate * 50) + "░" * (50 - int(completion_rate * 50))
                elapsed_time = time.time() - start_time
                estimated_total = elapsed_time / completion_rate if completion_rate > 0 else 0
                remaining_time = estimated_total - elapsed_time if estimated_total > 0 else 0

                print(f"\r🎬 学习进度: [{progress_bar}] {completion_rate:.1%} "
                      f"({current_position//60:02d}:{current_position%60:02d}/"
                      f"{total_seconds//60:02d}:{total_seconds%60:02d}) "
                      f"剩余: {remaining_time//60:.0f}:{remaining_time%60:02.0f}", end="", flush=True)

                # 上报进度（避免过于频繁）
                if current_position - last_report_position >= report_interval or current_position >= total_seconds:
                    self.report_study_progress(video_info, current_position)
                    last_report_position = current_position

                # 检查课程权限（防止会话过期）
                if current_position % (report_interval * 3) == 0:  # 每3个周期检查一次
                    if not self.check_course_permission(video_info.user_course_id):
                        self.logger.warning("课程权限检查失败，可能需要重新登录")

            print()  # 换行

            if current_position >= total_seconds:
                self.logger.info("✅ 视频学习完成！")
                return True
            else:
                self.logger.info("⏹️ 视频学习被中断")
                return False

        except Exception as e:
            self.logger.error(f"视频学习异常: {e}")
            return False
        finally:
            self.is_studying = False

    def start_course_study(self, user_course_id: str, course_id: str,
                          speed_multiplier: float = 2.0,
                          async_mode: bool = False) -> bool:
        """开始课程学习"""
        try:
            self.logger.info(f"准备开始学习课程: user_course_id={user_course_id}, course_id={course_id}")

            # 1. 检查课程权限
            if not self.check_course_permission(user_course_id):
                self.logger.error("课程学习权限检查失败")
                return False

            # 2. 初始化SCORM播放器
            if not self.init_scorm_player(user_course_id):
                self.logger.error("SCORM播放器初始化失败")
                return False

            # 3. 获取课程清单
            manifest = self.get_course_manifest(course_id)
            if not manifest:
                self.logger.error("获取课程清单失败")
                return False

            # 4. 解析视频信息
            video_info = self.parse_video_info_from_manifest(manifest, user_course_id)
            if not video_info:
                self.logger.error("解析视频信息失败")
                return False

            self.current_video = video_info

            # 5. 获取视频真实URL（可选，用于验证）
            real_url = self.get_video_real_url(video_info)
            if real_url:
                self.logger.info(f"视频文件URL: {real_url}")

            # 6. 开始学习
            if async_mode:
                # 异步模式：在后台线程中学习
                self.study_thread = threading.Thread(
                    target=self.simulate_video_study,
                    args=(video_info, speed_multiplier),
                    daemon=True
                )
                self.study_thread.start()
                self.logger.info("已启动后台学习线程")
                return True
            else:
                # 同步模式：阻塞学习
                return self.simulate_video_study(video_info, speed_multiplier)

        except Exception as e:
            self.logger.error(f"开始课程学习失败: {e}")
            return False

    def stop_study(self):
        """停止学习"""
        self.is_studying = False
        if self.study_thread and self.study_thread.is_alive():
            self.study_thread.join(timeout=5)
        self.logger.info("学习已停止")

    def get_current_progress(self) -> Optional[StudyProgress]:
        """获取当前学习进度"""
        return self.current_progress

    def batch_study_courses(self, course_list: List[Tuple[str, str]],
                          speed_multiplier: float = 2.0) -> Dict[str, bool]:
        """批量学习课程"""
        results = {}

        self.logger.info(f"开始批量学习 {len(course_list)} 门课程")

        for i, (user_course_id, course_id) in enumerate(course_list, 1):
            self.logger.info(f"\n📚 开始学习第 {i}/{len(course_list)} 门课程")

            success = self.start_course_study(
                user_course_id=user_course_id,
                course_id=course_id,
                speed_multiplier=speed_multiplier,
                async_mode=False
            )

            results[f"{user_course_id}_{course_id}"] = success

            if success:
                self.logger.info(f"✅ 第 {i} 门课程学习完成")
            else:
                self.logger.error(f"❌ 第 {i} 门课程学习失败")

            # 课程间休息
            if i < len(course_list):
                self.logger.info("课程间休息 10 秒...")
                time.sleep(10)

        completed_count = sum(1 for success in results.values() if success)
        self.logger.info(f"\n🎯 批量学习完成: {completed_count}/{len(course_list)} 门课程成功")

        return results