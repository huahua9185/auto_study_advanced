#!/usr/bin/env python3
"""
智能学习管理器 - 集成API学习引擎与现有系统
提供完整的自动化学习解决方案
"""

from playwright.sync_api import sync_playwright, Page
import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.login import LoginManager
from src.enhanced_course_parser import EnhancedCourseParser
from src.api_based_video_learner import APIBasedVideoLearner, StudyProgress
from src.database import db

@dataclass
class CourseStudyResult:
    """课程学习结果"""
    course_name: str
    user_course_id: str
    course_id: str
    success: bool
    duration_minutes: int
    completion_rate: float
    error_message: Optional[str] = None

class SmartLearningManager:
    """智能学习管理器"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.page: Optional[Page] = None
        self.browser = None
        self.login_manager: Optional[LoginManager] = None
        self.course_parser: Optional[EnhancedCourseParser] = None
        self.video_learner: Optional[APIBasedVideoLearner] = None

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger('SmartLearningManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def initialize(self) -> bool:
        """初始化系统"""
        try:
            self.logger.info("🚀 初始化智能学习管理器...")

            # 启动浏览器
            playwright = sync_playwright().start()
            self.browser = playwright.firefox.launch(headless=False)
            self.page = self.browser.new_page()

            # 初始化登录管理器
            self.login_manager = LoginManager()
            self.login_manager.browser = self.browser
            self.login_manager.page = self.page

            # 执行登录
            if not self.login_manager.login():
                self.logger.error("❌ 系统登录失败")
                return False

            self.logger.info("✅ 系统登录成功")

            # 初始化课程解析器
            self.course_parser = EnhancedCourseParser(self.page)

            # 获取cookies用于API调用
            cookies = self.page.context.cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

            # 初始化API视频学习器
            self.video_learner = APIBasedVideoLearner(cookie_dict)

            self.logger.info("✅ 智能学习管理器初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 初始化失败: {e}")
            return False

    def get_all_courses(self) -> Dict[str, List[Dict]]:
        """获取所有课程信息"""
        if not self.course_parser:
            self.logger.error("课程解析器未初始化")
            return {'required': [], 'elective': []}

        self.logger.info("📚 开始获取课程信息...")
        courses = self.course_parser.parse_all_courses()

        required_count = len(courses['required'])
        elective_count = len(courses['elective'])
        total_count = required_count + elective_count

        self.logger.info(f"📊 课程信息获取完成: 必修课 {required_count} 门, 选修课 {elective_count} 门, 总计 {total_count} 门")

        return courses

    def filter_incomplete_courses(self, courses: Dict[str, List[Dict]],
                                progress_threshold: float = 100.0) -> List[Dict]:
        """过滤未完成的课程"""
        incomplete_courses = []

        for course_type in ['required', 'elective']:
            for course in courses[course_type]:
                progress = course.get('progress', 0)
                if progress < progress_threshold:
                    course['course_type'] = course_type
                    incomplete_courses.append(course)

        self.logger.info(f"🎯 发现 {len(incomplete_courses)} 门未完成课程 (进度 < {progress_threshold}%)")

        return incomplete_courses

    def study_single_course(self, course: Dict, speed_multiplier: float = 2.0) -> CourseStudyResult:
        """学习单门课程"""
        course_name = course.get('course_name', 'Unknown Course')
        user_course_id = course.get('user_course_id', '')
        course_id = course.get('course_id', '') or course.get('id', '')

        self.logger.info(f"🎬 开始学习课程: {course_name}")

        try:
            if not self.video_learner:
                raise Exception("视频学习器未初始化")

            # 开始学习
            success = self.video_learner.start_course_study(
                user_course_id=user_course_id,
                course_id=course_id,
                speed_multiplier=speed_multiplier,
                async_mode=False
            )

            # 获取学习结果
            progress = self.video_learner.get_current_progress()
            duration_minutes = progress.total_duration // 60 if progress else 0
            completion_rate = progress.completion_rate if progress else 0.0

            result = CourseStudyResult(
                course_name=course_name,
                user_course_id=user_course_id,
                course_id=course_id,
                success=success,
                duration_minutes=duration_minutes,
                completion_rate=completion_rate
            )

            if success:
                self.logger.info(f"✅ 课程学习完成: {course_name} ({completion_rate:.1%})")
            else:
                self.logger.error(f"❌ 课程学习失败: {course_name}")

            return result

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ 课程学习异常: {course_name} - {error_msg}")

            return CourseStudyResult(
                course_name=course_name,
                user_course_id=user_course_id,
                course_id=course_id,
                success=False,
                duration_minutes=0,
                completion_rate=0.0,
                error_message=error_msg
            )

    def batch_auto_study(self,
                        progress_threshold: float = 100.0,
                        speed_multiplier: float = 2.0,
                        max_courses: Optional[int] = None,
                        course_types: List[str] = ['elective', 'required']) -> List[CourseStudyResult]:
        """批量自动学习"""
        try:
            self.logger.info("🎯 开始批量自动学习...")

            # 获取所有课程
            all_courses = self.get_all_courses()

            # 过滤未完成课程
            incomplete_courses = self.filter_incomplete_courses(all_courses, progress_threshold)

            # 按课程类型过滤
            if course_types:
                incomplete_courses = [
                    course for course in incomplete_courses
                    if course.get('course_type', '') in course_types
                ]

            # 限制课程数量
            if max_courses:
                incomplete_courses = incomplete_courses[:max_courses]

            if not incomplete_courses:
                self.logger.info("🎉 恭喜！所有课程都已完成")
                return []

            self.logger.info(f"📋 准备学习 {len(incomplete_courses)} 门课程")

            # 显示学习计划
            self.show_study_plan(incomplete_courses, speed_multiplier)

            # 开始批量学习
            results = []
            successful_count = 0
            total_study_time = 0

            for i, course in enumerate(incomplete_courses, 1):
                self.logger.info(f"\n{'='*80}")
                self.logger.info(f"📚 学习进度: {i}/{len(incomplete_courses)}")

                result = self.study_single_course(course, speed_multiplier)
                results.append(result)

                if result.success:
                    successful_count += 1
                    total_study_time += result.duration_minutes

                # 课程间休息
                if i < len(incomplete_courses):
                    rest_seconds = 15
                    self.logger.info(f"😴 课程间休息 {rest_seconds} 秒...")
                    time.sleep(rest_seconds)

            # 显示学习总结
            self.show_study_summary(results, successful_count, total_study_time)

            return results

        except Exception as e:
            self.logger.error(f"批量学习异常: {e}")
            return []

    def show_study_plan(self, courses: List[Dict], speed_multiplier: float):
        """显示学习计划"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info("📋 学习计划")
        self.logger.info(f"{'='*80}")

        total_duration = 0
        for i, course in enumerate(courses, 1):
            course_name = course.get('course_name', 'Unknown')
            progress = course.get('progress', 0)
            course_type = course.get('course_type', 'unknown')

            # 估算时长（暂定平均35分钟）
            estimated_minutes = 35
            total_duration += estimated_minutes

            type_emoji = "📘" if course_type == 'required' else "📕"
            self.logger.info(f"{i:2d}. {type_emoji} {course_name[:60]}... (进度: {progress}%)")

        estimated_time_minutes = int(total_duration / speed_multiplier)
        hours = estimated_time_minutes // 60
        minutes = estimated_time_minutes % 60

        self.logger.info(f"{'='*80}")
        self.logger.info(f"📊 预计学习时间: {hours}小时{minutes}分钟 (倍速: {speed_multiplier}x)")
        self.logger.info(f"{'='*80}")

    def show_study_summary(self, results: List[CourseStudyResult],
                          successful_count: int, total_study_time: int):
        """显示学习总结"""
        total_courses = len(results)
        failed_count = total_courses - successful_count
        hours = total_study_time // 60
        minutes = total_study_time % 60

        self.logger.info(f"\n{'='*80}")
        self.logger.info("🎯 学习总结")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"📊 课程总数: {total_courses}")
        self.logger.info(f"✅ 成功完成: {successful_count}")
        self.logger.info(f"❌ 学习失败: {failed_count}")
        self.logger.info(f"⏰ 总学习时间: {hours}小时{minutes}分钟")
        self.logger.info(f"📈 成功率: {successful_count/total_courses*100:.1f}%")

        if failed_count > 0:
            self.logger.info("\n❌ 失败课程:")
            for result in results:
                if not result.success:
                    self.logger.info(f"   • {result.course_name}")
                    if result.error_message:
                        self.logger.info(f"     错误: {result.error_message}")

        self.logger.info(f"{'='*80}")

    def interactive_study_mode(self):
        """交互式学习模式"""
        try:
            self.logger.info("🎮 进入交互式学习模式")

            while True:
                print("\n" + "="*80)
                print("🎓 智能学习管理器 - 交互模式")
                print("="*80)
                print("1. 查看所有课程")
                print("2. 学习未完成课程")
                print("3. 学习单门课程")
                print("4. 设置学习参数")
                print("5. 退出")
                print("="*80)

                choice = input("请选择操作 (1-5): ").strip()

                if choice == '1':
                    courses = self.get_all_courses()
                    self.show_course_list(courses)

                elif choice == '2':
                    self.interactive_batch_study()

                elif choice == '3':
                    self.interactive_single_study()

                elif choice == '4':
                    self.configure_study_settings()

                elif choice == '5':
                    self.logger.info("👋 退出交互模式")
                    break

                else:
                    print("❌ 无效选择，请重新输入")

        except KeyboardInterrupt:
            self.logger.info("👋 用户中断，退出交互模式")
        except Exception as e:
            self.logger.error(f"交互模式异常: {e}")

    def show_course_list(self, courses: Dict[str, List[Dict]]):
        """显示课程列表"""
        print(f"\n📚 课程列表")
        print("-" * 80)

        for course_type, course_list in courses.items():
            type_name = "必修课" if course_type == 'required' else "选修课"
            type_emoji = "📘" if course_type == 'required' else "📕"

            print(f"\n{type_emoji} {type_name} ({len(course_list)} 门)")
            print("-" * 60)

            for i, course in enumerate(course_list[:10], 1):  # 只显示前10门
                name = course.get('course_name', 'Unknown')[:50]
                progress = course.get('progress', 0)
                status = "✅" if progress >= 100 else "🔄"
                print(f"{i:2d}. {status} {name}... ({progress}%)")

            if len(course_list) > 10:
                print(f"    ... 还有 {len(course_list) - 10} 门课程")

    def interactive_batch_study(self):
        """交互式批量学习"""
        try:
            print("\n🎯 批量学习设置")
            print("-" * 40)

            # 学习倍速
            speed_str = input("学习倍速 (默认2.0): ").strip()
            speed_multiplier = float(speed_str) if speed_str else 2.0

            # 最大课程数
            max_str = input("最大学习课程数 (默认无限制): ").strip()
            max_courses = int(max_str) if max_str and max_str.isdigit() else None

            # 课程类型
            print("课程类型选择:")
            print("1. 仅选修课")
            print("2. 仅必修课")
            print("3. 全部课程 (默认)")
            type_choice = input("请选择 (1-3): ").strip()

            course_types = ['elective', 'required']
            if type_choice == '1':
                course_types = ['elective']
            elif type_choice == '2':
                course_types = ['required']

            print(f"\n🚀 开始批量学习 (倍速: {speed_multiplier}x, 类型: {course_types})")

            results = self.batch_auto_study(
                speed_multiplier=speed_multiplier,
                max_courses=max_courses,
                course_types=course_types
            )

        except ValueError:
            print("❌ 输入格式错误")
        except Exception as e:
            self.logger.error(f"交互式批量学习异常: {e}")

    def interactive_single_study(self):
        """交互式单门课程学习"""
        try:
            courses = self.get_all_courses()
            incomplete = self.filter_incomplete_courses(courses)

            if not incomplete:
                print("🎉 所有课程都已完成！")
                return

            print(f"\n📋 未完成课程列表 ({len(incomplete)} 门)")
            print("-" * 80)

            for i, course in enumerate(incomplete, 1):
                name = course.get('course_name', 'Unknown')[:50]
                progress = course.get('progress', 0)
                course_type = "必修" if course.get('course_type') == 'required' else "选修"
                print(f"{i:2d}. [{course_type}] {name}... ({progress}%)")

            choice_str = input(f"\n选择要学习的课程 (1-{len(incomplete)}): ").strip()

            if not choice_str.isdigit():
                print("❌ 无效输入")
                return

            choice_idx = int(choice_str) - 1
            if choice_idx < 0 or choice_idx >= len(incomplete):
                print("❌ 课程编号超出范围")
                return

            selected_course = incomplete[choice_idx]
            speed_str = input("学习倍速 (默认2.0): ").strip()
            speed_multiplier = float(speed_str) if speed_str else 2.0

            print(f"\n🎬 开始学习: {selected_course.get('course_name', 'Unknown')}")
            result = self.study_single_course(selected_course, speed_multiplier)

            if result.success:
                print(f"✅ 学习成功完成!")
            else:
                print(f"❌ 学习失败: {result.error_message}")

        except ValueError:
            print("❌ 输入格式错误")
        except Exception as e:
            self.logger.error(f"交互式单门学习异常: {e}")

    def configure_study_settings(self):
        """配置学习设置"""
        print("\n⚙️  学习参数设置")
        print("-" * 40)
        print("功能开发中，敬请期待...")

    def cleanup(self):
        """清理资源"""
        try:
            if self.video_learner:
                self.video_learner.stop_study()

            if self.browser:
                self.browser.close()

            self.logger.info("🧹 系统资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理异常: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()