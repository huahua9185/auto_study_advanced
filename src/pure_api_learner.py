#!/usr/bin/env python3
"""
Pure API学习器 - 完全基于API的高性能学习系统
无需浏览器，直接调用后端API实现自动化学习
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
from urllib.parse import urljoin
import io
import base64
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
import binascii

# 导入现有的验证码识别
from src.captcha_solver import CaptchaSolver

@dataclass
class UserInfo:
    """用户信息"""
    user_id: int
    username: str
    realname: str
    org_name: str
    uuid: str
    avatar: str = ""

@dataclass
class CourseInfo:
    """课程信息"""
    course_id: str
    user_course_id: str
    course_name: str
    course_type: str  # 'required' or 'elective'
    progress: float
    duration_minutes: int
    study_times: int
    status: int
    course_no: str = ""
    credit: float = 0.0
    need_exam: bool = False

@dataclass
class LearningSession:
    """学习会话"""
    course_info: CourseInfo
    start_time: datetime
    current_position: int = 0
    total_duration: int = 0
    completion_rate: float = 0.0
    status: str = "pending"  # pending, learning, completed, failed

class APISession:
    """API会话管理"""

    def __init__(self, base_url: str = "https://edu.nxgbjy.org.cn"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user_info: Optional[UserInfo] = None
        self.logger = self._setup_logger()

        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger('APISession')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def update_token(self, token: str):
        """更新token"""
        self.token = token
        self.session.headers.update({
            'token': token,
            'Referer': f'{self.base_url}/nxxzxy/index.html'
        })

    def get(self, endpoint: str, params: Dict = None, **kwargs) -> requests.Response:
        """GET请求"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, **kwargs)
        self.logger.debug(f"GET {url} -> {response.status_code}")
        return response

    def post(self, endpoint: str, data: Dict = None, json_data: Dict = None, **kwargs) -> requests.Response:
        """POST请求"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, data=data, json=json_data, **kwargs)
        self.logger.debug(f"POST {url} -> {response.status_code}")
        return response

    def get_cookies_dict(self) -> Dict[str, str]:
        """获取cookies字典"""
        return {cookie.name: cookie.value for cookie in self.session.cookies}

class PureAPILearner:
    """纯API学习器 - 完全脱离浏览器的高性能学习系统"""

    def __init__(self, username: str, password: str, base_url: str = "https://edu.nxgbjy.org.cn"):
        self.username = username
        self.password = password
        self.api_session = APISession(base_url)
        self.captcha_solver = CaptchaSolver()
        self.logger = self._setup_logger()

        # 学习状态
        self.current_sessions: List[LearningSession] = []
        self.is_logged_in = False

        # API端点配置（修正后）
        self.endpoints = {
            'captcha': '/device/login!get_auth_code.do',
            'login': '/device/login.do',
            'elective_courses': '/device/course!optional_course_list.do',
            'required_courses': '/device/course!list.do',  # 需要验证
            'course_detail': '/device/course!pc_detail.do',
            'check_course': '/device/course!check_course.do',
            'scorm_play': '/device/study_new!scorm_play.do',
            'get_manifest': '/device/study_new!getManifest.do',
            'get_video_url': '/device/study_new!getUrlBypf.do',
            'report_progress': '/device/study_new!seek.do',
            'user_info': '/device/user!study_center_stat.do'
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger('PureAPILearner')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _encrypt_password(self, password: str, key: str = "CCR!@#$%") -> str:
        """
        使用DES加密密码（Base64版本）

        根据浏览器实际行为，使用Base64编码输出

        Args:
            password: 明文密码
            key: 加密密钥

        Returns:
            str: Base64编码的加密密码
        """
        try:
            # 确保密钥是8字节
            if len(key) > 8:
                key = key[:8]
            elif len(key) < 8:
                key = key.ljust(8, '\0')

            key_bytes = key.encode('utf-8')

            # 创建DES密码对象
            cipher = DES.new(key_bytes, DES.MODE_ECB)

            # 将密码按照DES要求进行填充（使用标准PKCS5填充）
            password_bytes = password.encode('utf-8')
            padded_password = pad(password_bytes, DES.block_size)

            # 加密
            encrypted = cipher.encrypt(padded_password)

            # 转换为Base64字符串
            base64_result = base64.b64encode(encrypted).decode('utf-8')

            self.logger.info(f"密码加密成功: {password[:3]}*** -> {base64_result}")
            return base64_result

        except Exception as e:
            self.logger.error(f"密码加密失败: {e}")
            import traceback
            traceback.print_exc()
            return password  # 失败时返回原密码

    def get_captcha(self) -> Optional[str]:
        """获取验证码"""
        try:
            # 添加必要的参数和请求头
            headers = {
                'Referer': f'{self.api_session.base_url}/nxxzxy/index.html'
            }

            response = self.api_session.get(self.endpoints['captcha'], headers=headers)
            if response.status_code == 200:
                # 使用现有的验证码识别器
                captcha_result = self.captcha_solver.solve_captcha_from_bytes(response.content)

                if captcha_result and len(captcha_result) == 4 and captcha_result.isdigit():
                    self.logger.info(f"验证码识别成功: {captcha_result}")
                    return captcha_result
                else:
                    self.logger.warning(f"验证码识别失败或格式错误: {captcha_result}")
                    return None
            else:
                self.logger.error(f"获取验证码失败: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"获取验证码异常: {e}")
            return None

    def login(self, max_retries: int = 3) -> bool:
        """纯API登录"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"开始第 {attempt + 1}/{max_retries} 次登录尝试")

                # 1. 获取验证码
                captcha = self.get_captcha()
                if not captcha:
                    self.logger.warning("验证码获取失败，使用默认值")
                    captcha = "1234"  # 备用验证码

                # 2. 准备登录数据（使用修复后的加密密码）
                encrypted_password = self._encrypt_password(self.password)
                login_data = {
                    'username': self.username,
                    'password': encrypted_password,
                    'randomCode': captcha,
                    'terminal': '1'
                }

                self.logger.info(f"登录数据: username={self.username}, password=[encrypted:{len(encrypted_password)} chars], captcha={captcha}")

                # 设置正确的请求头
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f'{self.api_session.base_url}/nxxzxy/index.html'
                }

                # 3. 发送登录请求
                response = self.api_session.post(self.endpoints['login'], data=login_data, headers=headers)

                # 详细日志登录响应
                self.logger.info(f"登录响应状态码: {response.status_code}")
                self.logger.info(f"登录响应头: {dict(response.headers)}")
                self.logger.info(f"登录响应内容: {response.text}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        self.logger.info(f"登录响应JSON: {result}")

                        if result.get('status') == 1:
                            # 登录成功
                            user_data = result.get('user', {})
                            self.api_session.user_info = UserInfo(
                                user_id=result.get('user_id'),
                                username=self.username,
                                realname=user_data.get('realname', ''),
                                org_name=user_data.get('org_name', ''),
                                uuid=user_data.get('uuid', ''),
                                avatar=user_data.get('avatar', '')
                            )

                            # 更新token
                            token = result.get('system_uuid')
                            if token:
                                self.api_session.update_token(token)

                            self.is_logged_in = True
                            self.logger.info(f"✅ 登录成功: {self.api_session.user_info.realname} ({self.api_session.user_info.org_name})")
                            return True
                        else:
                            # 登录失败
                            error_msg = result.get('message', '未知错误')
                            self.logger.warning(f"登录失败: {error_msg}")
                            if "验证码" in error_msg or "校验码" in error_msg:
                                continue  # 重试
                            else:
                                break  # 用户名密码错误，不重试
                    except json.JSONDecodeError as e:
                        self.logger.error(f"登录响应JSON解析失败: {e}")
                        self.logger.error(f"原始响应: {response.text}")
                        break
                else:
                    self.logger.error(f"登录请求失败: {response.status_code}")
                    self.logger.error(f"错误响应: {response.text}")

            except Exception as e:
                self.logger.error(f"登录异常: {e}")

        self.logger.error("❌ 登录失败")
        return False

    def get_elective_courses(self) -> List[CourseInfo]:
        """获取选修课列表"""
        try:
            params = {
                'course_type': 1,
                'current': 1,
                'limit': 99999,
                'terminal': 1
            }

            response = self.api_session.get(self.endpoints['elective_courses'], params=params)

            if response.status_code == 200:
                data = response.json()
                if 'courses' in data:
                    courses = []
                    for course_data in data['courses']:
                        course = CourseInfo(
                            course_id=str(course_data.get('course_id', '')),
                            user_course_id=str(course_data.get('id', '')),
                            course_name=course_data.get('course_name', ''),
                            course_type='elective',
                            progress=float(course_data.get('process', 0.0)),
                            duration_minutes=int(course_data.get('duration', 0)),
                            study_times=int(course_data.get('study_times', 0)),
                            status=int(course_data.get('status', 0)),
                            course_no=course_data.get('course_no', ''),
                            credit=float(course_data.get('credit', 0.0)),
                            need_exam=bool(course_data.get('need_exam', False))
                        )
                        courses.append(course)

                    self.logger.info(f"获取到 {len(courses)} 门选修课程")
                    return courses
                else:
                    self.logger.warning("选修课数据结构异常")
                    return []
            else:
                self.logger.error(f"获取选修课失败: {response.status_code}")
                return []
        except Exception as e:
            self.logger.error(f"获取选修课异常: {e}")
            return []

    def get_required_courses(self) -> List[CourseInfo]:
        """获取必修课列表 - 需要发现正确的API"""
        self.logger.warning("必修课API尚未实现，需要进一步发现")
        return []

    def get_all_courses(self) -> Dict[str, List[CourseInfo]]:
        """获取所有课程"""
        return {
            'elective': self.get_elective_courses(),
            'required': self.get_required_courses()
        }

    def check_course_permission(self, user_course_id: str, study_times: int = 1) -> bool:
        """检查课程学习权限"""
        try:
            params = {
                'user_course_id': user_course_id,
                'study_times': study_times,
                'terminal': 1
            }

            response = self.api_session.get(self.endpoints['check_course'], params=params)
            if response.status_code == 200:
                data = response.json()
                play_status = data.get('play_status', 0)

                # 允许的状态: 1=可播放, 3=已完成但可播放
                allowed_statuses = [1, 3]
                is_allowed = play_status in allowed_statuses

                self.logger.info(f"课程权限检查: user_course_id={user_course_id}, play_status={play_status}, 允许={is_allowed}")
                return is_allowed
            else:
                self.logger.error(f"权限检查失败: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"权限检查异常: {e}")
            return False

    def init_scorm_player(self, user_course_id: str) -> bool:
        """初始化SCORM播放器"""
        try:
            params = {
                'terminal': 1,
                'id': user_course_id
            }

            response = self.api_session.get(self.endpoints['scorm_play'], params=params)
            success = response.status_code == 200

            if success:
                self.logger.info("SCORM播放器初始化成功")
            else:
                self.logger.error(f"SCORM播放器初始化失败: {response.status_code}")

            return success
        except Exception as e:
            self.logger.error(f"SCORM播放器初始化异常: {e}")
            return False

    def get_course_manifest(self, course_id: str) -> Optional[Dict]:
        """获取课程清单"""
        try:
            params = {
                'id': course_id,
                '_': int(time.time() * 1000)
            }

            response = self.api_session.get(self.endpoints['get_manifest'], params=params)
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

    def get_video_url(self, course_no: str, file_path: str, file_name: str) -> Optional[str]:
        """获取视频真实URL"""
        try:
            params = {
                'path': file_path,
                'fileName': file_name,
                'course_no': course_no,
                'is_gkk': 'false',
                '_': int(time.time() * 1000)
            }

            response = self.api_session.get(self.endpoints['get_video_url'], params=params)
            if response.status_code == 200:
                video_url = response.text.strip()
                if video_url and video_url.startswith('http'):
                    self.logger.info(f"获取视频URL成功: {video_url}")
                    return video_url
                else:
                    # 构造直接URL
                    direct_url = f"{self.api_session.base_url}/course/{course_no}/{file_path}/{file_name}"
                    self.logger.info(f"使用直接构造URL: {direct_url}")
                    return direct_url
            else:
                self.logger.error(f"获取视频URL失败: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"获取视频URL异常: {e}")
            return None

    def report_learning_progress(self, course_info: CourseInfo, position_seconds: int) -> bool:
        """上报学习进度"""
        try:
            # 构造进度数据
            progress_data = {
                'user_course_id': course_info.user_course_id,
                'course_id': course_info.course_id,
                'lesson_location': position_seconds,
                'session_time': position_seconds,
                'completion_status': 'incomplete' if position_seconds < course_info.duration_minutes * 60 * 0.9 else 'completed'
            }

            response = self.api_session.post(self.endpoints['report_progress'], json_data=progress_data)
            success = response.status_code == 200

            if success:
                self.logger.debug(f"进度上报成功: {position_seconds}秒")
            else:
                self.logger.error(f"进度上报失败: {response.status_code}")

            return success
        except Exception as e:
            self.logger.error(f"进度上报异常: {e}")
            return False

    def simulate_course_learning(self, course_info: CourseInfo, speed_multiplier: float = 1.0) -> bool:
        """模拟课程学习过程"""
        try:
            session = LearningSession(
                course_info=course_info,
                start_time=datetime.now(),
                total_duration=course_info.duration_minutes * 60,
                status="learning"
            )

            self.current_sessions.append(session)

            self.logger.info(f"🎬 开始学习: {course_info.course_name}")
            self.logger.info(f"⏱️  时长: {course_info.duration_minutes}分钟, 倍速: {speed_multiplier}x")

            total_seconds = course_info.duration_minutes * 60
            report_interval = 30  # 每30秒上报一次

            for current_position in range(0, total_seconds + 1, report_interval):
                current_position = min(current_position, total_seconds)

                # 计算完成率
                completion_rate = current_position / total_seconds if total_seconds > 0 else 1.0
                session.current_position = current_position
                session.completion_rate = completion_rate

                # 显示进度
                progress_bar = "█" * int(completion_rate * 50) + "░" * (50 - int(completion_rate * 50))
                print(f"\r🎬 学习进度: [{progress_bar}] {completion_rate:.1%} "
                      f"({current_position//60:02d}:{current_position%60:02d}/"
                      f"{total_seconds//60:02d}:{total_seconds%60:02d})", end="", flush=True)

                # 上报进度
                self.report_learning_progress(course_info, current_position)

                # 等待（考虑倍速）
                if current_position < total_seconds:
                    sleep_time = min(report_interval, total_seconds - current_position) / speed_multiplier
                    time.sleep(sleep_time)

            print()  # 换行
            session.status = "completed"
            self.logger.info(f"✅ 课程学习完成: {course_info.course_name}")
            return True

        except Exception as e:
            self.logger.error(f"课程学习异常: {e}")
            if self.current_sessions:
                self.current_sessions[-1].status = "failed"
            return False

    def learn_course(self, course_info: CourseInfo, speed_multiplier: float = 2.0) -> bool:
        """学习单门课程的完整流程"""
        try:
            # 1. 检查权限
            if not self.check_course_permission(course_info.user_course_id):
                self.logger.error(f"课程权限检查失败: {course_info.course_name}")
                return False

            # 2. 初始化SCORM播放器
            if not self.init_scorm_player(course_info.user_course_id):
                self.logger.error(f"SCORM播放器初始化失败: {course_info.course_name}")
                return False

            # 3. 获取课程清单
            manifest = self.get_course_manifest(course_info.course_id)
            if not manifest:
                self.logger.error(f"获取课程清单失败: {course_info.course_name}")
                return False

            # 4. 模拟学习过程
            return self.simulate_course_learning(course_info, speed_multiplier)

        except Exception as e:
            self.logger.error(f"学习课程失败: {e}")
            return False

    def batch_learn(self, courses: List[CourseInfo], speed_multiplier: float = 2.0,
                   progress_threshold: float = 100.0) -> Dict[str, bool]:
        """批量学习课程"""
        results = {}

        # 过滤未完成课程
        incomplete_courses = [c for c in courses if c.progress < progress_threshold]

        self.logger.info(f"🎯 开始批量学习 {len(incomplete_courses)} 门未完成课程")

        for i, course in enumerate(incomplete_courses, 1):
            self.logger.info(f"\n📚 ({i}/{len(incomplete_courses)}) 开始学习: {course.course_name}")

            success = self.learn_course(course, speed_multiplier)
            results[course.user_course_id] = success

            if success:
                self.logger.info(f"✅ 第 {i} 门课程完成")
            else:
                self.logger.error(f"❌ 第 {i} 门课程失败")

            # 课程间休息
            if i < len(incomplete_courses):
                time.sleep(5)

        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"\n🎉 批量学习完成: {success_count}/{len(incomplete_courses)} 门课程成功")

        return results

    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计"""
        total_sessions = len(self.current_sessions)
        completed_sessions = len([s for s in self.current_sessions if s.status == "completed"])
        failed_sessions = len([s for s in self.current_sessions if s.status == "failed"])

        return {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'failed_sessions': failed_sessions,
            'success_rate': completed_sessions / total_sessions if total_sessions > 0 else 0,
            'user_info': asdict(self.api_session.user_info) if self.api_session.user_info else None
        }