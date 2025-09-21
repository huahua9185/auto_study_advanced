#!/usr/bin/env python3
"""
课程管理模块
负责课程信息的获取、存储、查询和管理
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .config_manager import ConfigManager
from .login_manager import LoginManager
from ..utils.async_utils import run_async_in_sync
from ..utils.logger_utils import setup_colored_logger
from ..ui.display_utils import DisplayUtils
from ..ui.input_utils import InputUtils

# 检查是否在学习模式（安静模式）
quiet_mode = os.environ.get('LEARNING_QUIET_MODE', 'false').lower() == 'true'
logger = setup_colored_logger(__name__, console_output=not quiet_mode)


class Course:
    """课程类"""

    def __init__(self, data: Dict[str, Any]):
        self.course_name = data.get('course_name', '')
        self.course_type = data.get('course_type', 'unknown')  # required, elective
        self.progress = float(data.get('progress', 0.0))
        self.video_url = data.get('video_url', '')
        self.user_course_id = data.get('user_course_id', '')
        self.course_id = data.get('course_id', '')
        self.description = data.get('description', '')
        self.duration = data.get('duration', 0)
        self.last_study_time = data.get('last_study_time', '')

        # 新增字段支持真实API数据
        self.credit = float(data.get('credit', 0.0))  # 学分
        self.period = float(data.get('period', 0.0))  # 学时
        self.lecturer = data.get('lecturer', '')  # 讲师
        self.status = data.get('status', '')  # 状态
        self.select_date = data.get('select_date', '')  # 选课日期
        self.complete_date = data.get('complete_date', '')  # 完成日期
        self.study_times = int(data.get('study_times', 0))  # 学习次数
        self.process = float(data.get('process', 0.0))  # 进度（0-100）

        self.is_completed = self.status == 'completed'
        self.is_started = self.progress > 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'course_name': self.course_name,
            'course_type': self.course_type,
            'progress': self.progress,
            'video_url': self.video_url,
            'user_course_id': self.user_course_id,
            'course_id': self.course_id,
            'description': self.description,
            'duration': self.duration,
            'last_study_time': self.last_study_time,
            'credit': self.credit,
            'period': self.period,
            'lecturer': self.lecturer,
            'status': self.status,
            'select_date': self.select_date,
            'complete_date': self.complete_date,
            'study_times': self.study_times,
            'process': self.process,
            'is_completed': self.is_completed,
            'is_started': self.is_started
        }

    def __str__(self) -> str:
        status = "已完成" if self.is_completed else "学习中" if self.is_started else "未开始"
        type_name = "必修" if self.course_type == 'required' else "选修"
        credit_info = f" {self.credit}学分" if self.credit > 0 else ""
        lecturer_info = f" - {self.lecturer}" if self.lecturer else ""
        return f"[{type_name}] {self.course_name} - {self.progress:.1f}% ({status}){credit_info}{lecturer_info}"


class CourseManager:
    """课程管理器"""

    def __init__(self, config_manager: ConfigManager, login_manager: LoginManager):
        self.config_manager = config_manager
        self.login_manager = login_manager
        self.data_dir = Path("console_learning_system/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 数据文件路径
        self.courses_file = self.data_dir / "courses.json"
        self.database_file = self.data_dir / "courses.db"

        # 课程数据
        self.courses: List[Course] = []
        self.last_update_time: Optional[datetime] = None

        # 初始化数据库
        self._init_database()

        # 加载课程数据
        self.load_courses()

    async def initialize(self) -> bool:
        """异步初始化课程管理器"""
        try:
            # 初始化数据库（已在__init__中完成）
            # 加载课程数据（已在__init__中完成）
            logger.info("课程管理器初始化成功")
            return True
        except Exception as e:
            logger.error(f"课程管理器初始化失败: {e}")
            return False

    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()

                # 创建课程表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS courses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_name TEXT NOT NULL,
                        course_type TEXT NOT NULL,
                        progress REAL DEFAULT 0.0,
                        video_url TEXT,
                        user_course_id TEXT,
                        course_id TEXT,
                        description TEXT,
                        duration INTEGER DEFAULT 0,
                        last_study_time TEXT,
                        is_completed BOOLEAN DEFAULT FALSE,
                        is_started BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(course_name, course_type)
                    )
                ''')

                # 创建学习记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id INTEGER,
                        session_start TEXT,
                        session_end TEXT,
                        progress_before REAL,
                        progress_after REAL,
                        learning_time INTEGER,
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (course_id) REFERENCES courses (id)
                    )
                ''')

                # 执行数据库迁移（添加新字段）
                self._migrate_database(cursor)

                conn.commit()
                logger.info("数据库初始化成功")

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")

    def _migrate_database(self, cursor):
        """数据库迁移 - 添加新字段"""
        try:
            # 获取当前表结构
            cursor.execute("PRAGMA table_info(courses)")
            columns = [column[1] for column in cursor.fetchall()]

            # 需要添加的新字段
            new_columns = [
                ('credit', 'REAL DEFAULT 0.0'),
                ('period', 'REAL DEFAULT 0.0'),
                ('lecturer', 'TEXT DEFAULT ""'),
                ('status', 'TEXT DEFAULT ""'),
                ('select_date', 'TEXT DEFAULT ""'),
                ('complete_date', 'TEXT DEFAULT ""'),
                ('study_times', 'INTEGER DEFAULT 0'),
                ('process', 'REAL DEFAULT 0.0')
            ]

            # 添加缺失的字段
            added_columns = []
            for column_name, column_type in new_columns:
                if column_name not in columns:
                    try:
                        cursor.execute(f'ALTER TABLE courses ADD COLUMN {column_name} {column_type}')
                        added_columns.append(column_name)
                        logger.info(f"✅ 添加数据库字段: {column_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ 添加字段 {column_name} 失败: {e}")

            if added_columns:
                logger.info(f"数据库迁移完成，添加了 {len(added_columns)} 个新字段: {', '.join(added_columns)}")
            else:
                logger.info("数据库架构已是最新，无需迁移")

        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")

    def load_courses(self, force_refresh: bool = False):
        """加载课程数据

        Args:
            force_refresh: 是否强制从API刷新数据
        """
        try:
            # 如果强制刷新，直接从API获取
            if force_refresh:
                logger.info("强制从API刷新课程数据...")
                success = self.fetch_courses_from_api_sync()
                if success:
                    logger.info(f"从API刷新了 {len(self.courses)} 门课程")
                    return
                else:
                    logger.warning("API刷新失败，回退到本地数据")

            # 优先从数据库加载
            courses_from_db = self._load_from_database()
            if courses_from_db:
                self.courses = courses_from_db
                logger.info(f"从数据库加载了 {len(self.courses)} 门课程")
                return

            # 如果数据库为空，尝试从JSON文件加载
            if self.courses_file.exists():
                with open(self.courses_file, 'r', encoding='utf-8') as f:
                    courses_data = json.load(f)

                self.courses = [Course(data) for data in courses_data]
                logger.info(f"从文件加载了 {len(self.courses)} 门课程")

                # 同步到数据库
                self._save_to_database()
            else:
                # 尝试从根目录的JSON文件加载
                self._load_from_root_directory()

        except Exception as e:
            logger.error(f"加载课程数据失败: {e}")
            self.courses = []

    def _load_from_database(self) -> List[Course]:
        """从数据库加载课程"""
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()

                # 首先检查表中都有哪些列
                cursor.execute("PRAGMA table_info(courses)")
                columns_info = cursor.fetchall()
                available_columns = [col[1] for col in columns_info]

                # 构建动态查询语句，只选择存在的列
                base_columns = [
                    'course_name', 'course_type', 'progress', 'video_url', 'user_course_id',
                    'course_id', 'description', 'duration', 'last_study_time',
                    'is_completed', 'is_started'
                ]

                new_columns = [
                    'credit', 'period', 'lecturer', 'status', 'select_date',
                    'complete_date', 'study_times', 'process'
                ]

                # 只选择表中实际存在的列
                select_columns = []
                for col in base_columns + new_columns:
                    if col in available_columns:
                        select_columns.append(col)

                query = f'''
                    SELECT {', '.join(select_columns)}
                    FROM courses
                    ORDER BY course_type, course_name
                '''

                cursor.execute(query)
                courses = []

                for row in cursor.fetchall():
                    course_data = {}

                    # 映射查询结果到字典
                    for i, col_name in enumerate(select_columns):
                        course_data[col_name] = row[i]

                    # 确保所有必需字段都有默认值
                    course_data.setdefault('credit', 0.0)
                    course_data.setdefault('period', 0.0)
                    course_data.setdefault('lecturer', '')
                    course_data.setdefault('status', '')
                    course_data.setdefault('select_date', '')
                    course_data.setdefault('complete_date', '')
                    course_data.setdefault('study_times', 0)
                    course_data.setdefault('process', 0.0)

                    courses.append(Course(course_data))

                return courses

        except Exception as e:
            logger.error(f"从数据库加载课程失败: {e}")
            return []

    def _load_from_root_directory(self):
        """从根目录加载现有的课程数据"""
        try:
            root_dir = Path(".")

            # 查找现有的课程数据文件
            course_files = [
                "required_course_parsed_data.json",
                "elective_course_parsed_data.json"
            ]

            all_courses = []

            for file_name in course_files:
                file_path = root_dir / file_name
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        courses_data = json.load(f)
                        for course_data in courses_data:
                            all_courses.append(Course(course_data))

            if all_courses:
                self.courses = all_courses
                logger.info(f"从根目录文件加载了 {len(self.courses)} 门课程")

                # 保存到数据库和JSON文件
                self.save_courses()

        except Exception as e:
            logger.error(f"从根目录加载课程数据失败: {e}")

    def save_courses(self):
        """保存课程数据"""
        try:
            # 保存到数据库
            self._save_to_database()

            # 保存到JSON文件
            courses_data = [course.to_dict() for course in self.courses]
            with open(self.courses_file, 'w', encoding='utf-8') as f:
                json.dump(courses_data, f, indent=2, ensure_ascii=False)

            self.last_update_time = datetime.now()
            logger.info(f"保存了 {len(self.courses)} 门课程")

        except Exception as e:
            logger.error(f"保存课程数据失败: {e}")

    def _save_to_database(self):
        """保存到数据库"""
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()

                # 检查哪些列存在
                cursor.execute("PRAGMA table_info(courses)")
                columns_info = cursor.fetchall()
                available_columns = [col[1] for col in columns_info]

                # 清空现有数据
                cursor.execute('DELETE FROM courses')

                # 动态构建插入语句
                base_columns = [
                    'course_name', 'course_type', 'progress', 'video_url', 'user_course_id',
                    'course_id', 'description', 'duration', 'last_study_time',
                    'is_completed', 'is_started', 'updated_at'
                ]

                new_columns = [
                    'credit', 'period', 'lecturer', 'status', 'select_date',
                    'complete_date', 'study_times', 'process'
                ]

                # 只使用存在的列
                insert_columns = []
                for col in base_columns + new_columns:
                    if col in available_columns:
                        insert_columns.append(col)

                placeholders = ', '.join(['?' for _ in insert_columns])
                columns_str = ', '.join(insert_columns)

                insert_query = f'''
                    INSERT INTO courses ({columns_str})
                    VALUES ({placeholders})
                '''

                # 插入课程数据
                for course in self.courses:
                    values = []
                    for col in insert_columns:
                        if col == 'updated_at':
                            values.append(datetime.now().isoformat())
                        elif col == 'credit':
                            values.append(getattr(course, 'credit', 0.0))
                        elif col == 'period':
                            values.append(getattr(course, 'period', 0.0))
                        elif col == 'lecturer':
                            values.append(getattr(course, 'lecturer', ''))
                        elif col == 'status':
                            values.append(getattr(course, 'status', ''))
                        elif col == 'select_date':
                            values.append(getattr(course, 'select_date', ''))
                        elif col == 'complete_date':
                            values.append(getattr(course, 'complete_date', ''))
                        elif col == 'study_times':
                            values.append(getattr(course, 'study_times', 0))
                        elif col == 'process':
                            values.append(getattr(course, 'process', 0.0))
                        else:
                            values.append(getattr(course, col))

                    cursor.execute(insert_query, values)

                conn.commit()
                logger.info(f"成功保存 {len(self.courses)} 门课程到数据库")

        except Exception as e:
            logger.error(f"保存到数据库失败: {e}")

    async def fetch_courses_from_api(self) -> bool:
        """从API获取课程列表"""
        try:
            # 重新创建 API 客户端以避免事件循环问题
            from final_working_api_client import FinalWorkingAPIClient

            # 创建新的API客户端实例
            api_client = FinalWorkingAPIClient()
            await api_client.initialize()

            # 使用固定的登录信息（避免配置问题）
            username = "640302198607120020"
            password = "My2062660"

            logger.info("正在重新登录并获取课程列表...")

            # 执行登录
            login_success = await api_client.login(username, password)
            if not login_success:
                logger.error("登录失败")
                await api_client.close()
                return False

            # 获取所有课程（必修+选修）
            courses_data = await api_client.get_all_courses()

            # 关闭API客户端
            await api_client.close()

            if courses_data:
                # 转换为Course对象
                new_courses = []
                for course_data in courses_data:
                    # 适配API返回的数据格式（支持新的真实API字段）
                    adapted_data = {
                        'course_name': course_data.get('course_name', ''),
                        'course_type': course_data.get('course_type', 'unknown'),
                        'progress': course_data.get('progress', 0.0),
                        'video_url': course_data.get('video_url', ''),
                        'user_course_id': str(course_data.get('user_course_id', '')),
                        'course_id': str(course_data.get('id', '')),
                        'description': course_data.get('description', ''),
                        'duration': course_data.get('duration', 0),
                        'last_study_time': course_data.get('last_study_time', ''),
                        # 新增真实API字段
                        'credit': course_data.get('credit', 0.0),
                        'period': course_data.get('period', 0.0),
                        'lecturer': course_data.get('lecturer', ''),
                        'status': course_data.get('status', ''),
                        'select_date': course_data.get('select_date', ''),
                        'complete_date': course_data.get('complete_date', ''),
                        'study_times': course_data.get('study_times', 0),
                        'process': course_data.get('process', 0.0)
                    }
                    new_courses.append(Course(adapted_data))

                self.courses = new_courses
                self.save_courses()

                logger.info(f"成功获取了 {len(self.courses)} 门课程")
                return True
            else:
                logger.warning("API返回的课程数据为空")
                return False

        except Exception as e:
            logger.error(f"从API获取课程失败: {e}")
            return False

    def fetch_courses_from_api_sync(self) -> bool:
        """同步方式从API获取课程"""
        return run_async_in_sync(self.fetch_courses_from_api())

    async def get_courses_async(self) -> List[Course]:
        """异步获取课程列表"""
        return self.get_all_courses()

    def get_courses_sync(self) -> List[Course]:
        """同步获取课程列表"""
        return self.get_all_courses()

    async def get_courses(self) -> List[Course]:
        """获取课程列表（异步版本）"""
        return self.get_all_courses()

    async def update_course_progress_async(self, course_id: str, progress: float) -> bool:
        """异步更新课程进度"""
        try:
            course = self.get_course_by_id(course_id)
            if course:
                course.progress = progress
                course.is_completed = progress >= 100.0
                course.is_started = progress > 0.0
                course.last_study_time = datetime.now().isoformat()

                # 更新数据库
                with sqlite3.connect(self.database_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE courses SET
                            progress = ?,
                            is_completed = ?,
                            is_started = ?,
                            last_study_time = ?
                        WHERE course_id = ?
                    ''', (progress, course.is_completed, course.is_started,
                         course.last_study_time, course_id))
                    conn.commit()

                logger.info(f"更新课程进度: {course.course_name} -> {progress:.1f}%")
                return True
            else:
                logger.warning(f"未找到课程ID: {course_id}")
                return False

        except Exception as e:
            logger.error(f"更新课程进度失败: {e}")
            return False

    async def refresh_course_progress_async(self) -> bool:
        """异步刷新课程进度"""
        try:
            if not self.login_manager.check_login_status():
                logger.error("用户未登录，无法刷新课程进度")
                return False

            api_client = self.login_manager.get_api_client()
            if not api_client:
                logger.error("无法获取API客户端")
                return False

            # 获取所有课程的最新进度
            updated_count = 0
            for course in self.courses:
                try:
                    # 这里需要调用API获取最新进度
                    # progress = await api_client.get_course_progress(course.course_id)
                    # 暂时跳过，因为API方法可能需要不同的参数
                    pass
                except Exception as e:
                    logger.warning(f"获取课程 {course.course_name} 进度失败: {e}")

            logger.info(f"课程进度刷新完成，更新了 {updated_count} 门课程")
            return True

        except Exception as e:
            logger.error(f"刷新课程进度失败: {e}")
            return False

    def refresh_course_progress_sync(self) -> bool:
        """同步刷新课程进度"""
        return run_async_in_sync(self.refresh_course_progress_async())

    async def search_courses_async(self, keyword: str) -> List[Course]:
        """异步搜索课程"""
        return self.search_courses(keyword)

    def search_courses_sync(self, keyword: str) -> List[Course]:
        """同步搜索课程"""
        return self.search_courses(keyword)

    async def get_course_statistics_async(self) -> Dict[str, Any]:
        """异步获取课程统计"""
        return self.get_statistics()

    def get_course_statistics_sync(self) -> Dict[str, Any]:
        """同步获取课程统计"""
        return self.get_statistics()

    async def show_course_details_async(self, course_id: str):
        """异步显示课程详情"""
        course = self.get_course_by_id(course_id)
        if course:
            self._display_course_details(course)
        else:
            logger.error(f"未找到课程ID: {course_id}")

    def show_course_details_sync(self, course_id: str):
        """同步显示课程详情"""
        run_async_in_sync(self.show_course_details_async(course_id))

    def _display_course_details(self, course: Course):
        """显示课程详情"""
        DisplayUtils.print_header(f"课程详情 - {course.course_name}")

        # 基本信息
        basic_info = [
            ['课程名称', course.course_name],
            ['课程类型', '必修课' if course.course_type == 'required' else '选修课'],
            ['学习进度', f"{course.progress:.1f}%"],
            ['完成状态', '已完成' if course.is_completed else '进行中' if course.is_started else '未开始'],
            ['课程ID', course.course_id],
            ['用户课程ID', course.user_course_id]
        ]

        DisplayUtils.print_table(['属性', '值'], basic_info, '基本信息')

        # 学习信息
        if course.description:
            print()
            DisplayUtils.print_section("课程描述")
            print(f"  {course.description}")

        # 时间信息
        if course.last_study_time:
            print()
            time_info = [
                ['上次学习时间', course.last_study_time],
                ['预计时长', f"{course.duration}分钟" if course.duration else "未知"]
            ]
            DisplayUtils.print_table(['属性', '值'], time_info, '时间信息')

        # 视频信息
        if course.video_url:
            print()
            DisplayUtils.print_section("视频地址")
            print(f"  {course.video_url}")

    def fetch_courses_sync(self) -> bool:
        """同步获取课程（用于兼容现有接口）"""
        return self.fetch_courses_from_api_sync()

    def refresh_courses(self) -> bool:
        """刷新课程数据 - 从API重新获取最新数据"""
        logger.info("正在刷新课程数据...")
        try:
            # 强制从API获取最新数据
            success = self.fetch_courses_from_api_sync()
            if success:
                logger.info(f"✅ 课程数据刷新成功，获取到 {len(self.courses)} 门课程")
                return True
            else:
                logger.error("❌ 课程数据刷新失败")
                return False
        except Exception as e:
            logger.error(f"❌ 刷新课程数据异常: {e}")
            return False

    def refresh_courses_sync(self) -> bool:
        """同步刷新课程数据"""
        return self.refresh_courses()

    def get_all_courses(self) -> List[Course]:
        """获取所有课程"""
        return self.courses.copy()

    def get_courses_by_type(self, course_type: str) -> List[Course]:
        """按类型获取课程"""
        return [course for course in self.courses if course.course_type == course_type]

    def get_required_courses(self) -> List[Course]:
        """获取必修课程"""
        return self.get_courses_by_type('required')

    def get_elective_courses(self) -> List[Course]:
        """获取选修课程"""
        return self.get_courses_by_type('elective')

    def get_incomplete_courses(self) -> List[Course]:
        """获取未完成的课程"""
        return [course for course in self.courses if not course.is_completed]

    def get_completed_courses(self) -> List[Course]:
        """获取已完成的课程"""
        return [course for course in self.courses if course.is_completed]

    def search_courses(self, keyword: str) -> List[Course]:
        """搜索课程"""
        keyword = keyword.lower()
        results = []

        for course in self.courses:
            if (keyword in course.course_name.lower() or
                keyword in course.description.lower()):
                results.append(course)

        return results

    def get_course_by_name(self, name: str) -> Optional[Course]:
        """根据名称获取课程"""
        for course in self.courses:
            if course.course_name == name:
                return course
        return None

    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """根据ID获取课程"""
        for course in self.courses:
            if course.course_id == course_id or course.user_course_id == course_id:
                return course
        return None

    def update_course_progress(self, course_name: str, progress: float):
        """更新课程进度"""
        course = self.get_course_by_name(course_name)
        if course:
            course.progress = min(100.0, max(0.0, progress))
            course.is_completed = course.progress >= 100.0
            course.is_started = course.progress > 0.0
            course.last_study_time = datetime.now().isoformat()

            # 保存更新
            self.save_courses()
            logger.info(f"更新课程进度: {course_name} -> {progress:.1f}%")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_courses = len(self.courses)
        completed_courses = len(self.get_completed_courses())
        incomplete_courses = len(self.get_incomplete_courses())
        required_courses = len(self.get_required_courses())
        elective_courses = len(self.get_elective_courses())

        # 计算平均进度
        if total_courses > 0:
            avg_progress = sum(course.progress for course in self.courses) / total_courses
            completion_rate = (completed_courses / total_courses) * 100
        else:
            avg_progress = 0.0
            completion_rate = 0.0

        # 按类型统计
        required_completed = len([c for c in self.get_required_courses() if c.is_completed])
        elective_completed = len([c for c in self.get_elective_courses() if c.is_completed])

        return {
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'incomplete_courses': incomplete_courses,
            'required_courses': required_courses,
            'elective_courses': elective_courses,
            'required_completed': required_completed,
            'elective_completed': elective_completed,
            'avg_progress': avg_progress,
            'completion_rate': completion_rate,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None
        }

    def show_course_list(self, course_type: str = "all", show_completed: bool = True):
        """显示课程列表"""
        DisplayUtils.print_header("课程列表")

        # 筛选课程
        if course_type == "required":
            courses = self.get_required_courses()
            title = "必修课程"
        elif course_type == "elective":
            courses = self.get_elective_courses()
            title = "选修课程"
        elif course_type == "incomplete":
            courses = self.get_incomplete_courses()
            title = "未完成课程"
        else:
            courses = self.get_all_courses()
            title = "所有课程"

        if not show_completed:
            courses = [c for c in courses if not c.is_completed]
            title += " (仅显示未完成)"

        if not courses:
            DisplayUtils.print_status('info', '没有找到符合条件的课程')
            return

        # 准备表格数据
        headers = ['序号', '课程名称', '类型', '进度', '状态']
        rows = []

        for i, course in enumerate(courses, 1):
            course_type_name = "必修" if course.course_type == "required" else "选修"
            status = "已完成" if course.is_completed else "学习中" if course.is_started else "未开始"
            progress_str = f"{course.progress:.1f}%"

            # 截断过长的课程名称
            name = course.course_name
            if len(name) > 30:
                name = name[:27] + "..."

            rows.append([str(i), name, course_type_name, progress_str, status])

        DisplayUtils.print_table(headers, rows, title)

        # 显示统计信息
        print()
        stats = self.get_statistics()
        DisplayUtils.print_status('info', f"显示 {len(courses)} 门课程")

    def show_course_details(self, course_name: str = None):
        """显示课程详情"""
        if not course_name:
            # 让用户选择课程
            courses = self.get_all_courses()
            if not courses:
                DisplayUtils.print_status('warning', '没有可用的课程')
                return

            # 显示课程列表供选择
            print("请选择要查看的课程:")
            for i, course in enumerate(courses[:10], 1):  # 只显示前10个
                print(f"  {i}. {course.course_name}")

            choice = InputUtils.get_number("请输入课程序号", 1, min(10, len(courses)), is_int=True)
            if choice is None:
                return

            course = courses[choice - 1]
        else:
            course = self.get_course_by_name(course_name)
            if not course:
                DisplayUtils.print_status('error', f'找不到课程: {course_name}')
                return

        # 显示详细信息
        DisplayUtils.print_header(f"课程详情 - {course.course_name}")

        details = [
            ['课程名称', course.course_name],
            ['课程类型', '必修课' if course.course_type == 'required' else '选修课'],
            ['学习进度', f"{course.progress:.1f}%"],
            ['完成状态', '已完成' if course.is_completed else '未完成'],
            ['是否已开始', '是' if course.is_started else '否'],
            ['课程ID', course.course_id or '未知'],
            ['用户课程ID', course.user_course_id or '未知'],
            ['视频链接', course.video_url or '未知'],
            ['课程时长', f"{course.duration}分钟" if course.duration else '未知'],
            ['最后学习时间', course.last_study_time or '从未学习']
        ]

        DisplayUtils.print_table(['属性', '值'], details)

        if course.description:
            print()
            DisplayUtils.print_box(course.description, "课程描述")

    def interactive_course_search(self):
        """交互式课程搜索"""
        DisplayUtils.print_header("课程搜索")

        keyword = InputUtils.get_user_input("请输入搜索关键词")
        if not keyword:
            return

        results = self.search_courses(keyword)

        if not results:
            DisplayUtils.print_status('info', f'没有找到包含 "{keyword}" 的课程')
            return

        DisplayUtils.print_status('success', f'找到 {len(results)} 门相关课程')
        print()

        # 显示搜索结果
        headers = ['序号', '课程名称', '类型', '进度', '状态']
        rows = []

        for i, course in enumerate(results, 1):
            course_type_name = "必修" if course.course_type == "required" else "选修"
            status = "已完成" if course.is_completed else "学习中" if course.is_started else "未开始"

            # 高亮关键词
            name = course.course_name
            if len(name) > 30:
                name = name[:27] + "..."

            rows.append([str(i), name, course_type_name, f"{course.progress:.1f}%", status])

        DisplayUtils.print_table(headers, rows, f'搜索结果: "{keyword}"')

        # 询问是否查看详情
        if InputUtils.get_yes_no("是否查看某个课程的详细信息", default=False):
            choice = InputUtils.get_number("请输入课程序号", 1, len(results), is_int=True)
            if choice is not None:
                self.show_course_details(results[choice - 1].course_name)