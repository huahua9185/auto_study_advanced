"""
主控制台界面模块
整合所有功能模块，提供统一的用户交互界面
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ..utils.async_utils import run_async_in_sync
from ..utils.logger_utils import LoggerContext
from ..ui.display_utils import DisplayUtils
from ..ui.input_utils import InputUtils
from ..ui.menu_system import Menu, MenuItem, MenuBuilder

from .config_manager import ConfigManager
from .login_manager import LoginManager
from .course_manager import CourseManager, Course
from .learning_engine import LearningEngine, LearningSession
from .concurrent_learning_manager import ConcurrentLearningManager, ConcurrentLearningSession


class SCORMConsoleInterface:
    """SCORM控制台界面主类"""

    def __init__(self):
        # 初始化核心管理器
        self.config_manager = ConfigManager()
        self.login_manager = LoginManager(self.config_manager)
        self.course_manager = CourseManager(self.config_manager, self.login_manager)
        self.learning_engine = LearningEngine(self.config_manager, self.course_manager)

        # 初始化并发学习管理器
        self.concurrent_manager = ConcurrentLearningManager(self.config_manager, self.course_manager)

        # UI工具
        self.display = DisplayUtils()
        self.input = InputUtils()

        # 状态
        self.running = True
        self.quick_mode = False

        # 设置学习引擎回调
        self._setup_learning_callbacks()

        # 构建菜单系统
        self._build_menu_system()

    def _setup_learning_callbacks(self):
        """设置学习引擎回调函数"""
        def on_progress_update(course: Course, progress: float):
            self.display.print_status(f"📈 课程进度更新: {course.course_name} - {progress:.1f}%", "info")

        def on_course_complete(course: Course):
            self.display.print_status(f"🎉 课程完成: {course.course_name}", "success")

        def on_session_start(session: LearningSession):
            self.display.print_status(f"▶️ 开始学习: {session.course.course_name}", "info")

        def on_session_end(session: LearningSession):
            duration = session.get_duration_str()
            progress_gained = session.get_progress_gained()
            self.display.print_status(
                f"⏹️ 学习结束: {session.course.course_name} - 用时{duration}, 进度+{progress_gained:.1f}%",
                "info"
            )

        self.learning_engine.set_progress_callback(on_progress_update)
        self.learning_engine.set_course_complete_callback(on_course_complete)
        self.learning_engine.set_session_callbacks(on_session_start, on_session_end)

    def _build_menu_system(self):
        """构建菜单系统"""
        # 1. 登录管理菜单
        login_menu = Menu("🔐 登录管理", "用户认证和登录状态管理")
        login_menu.add_item("1", "测试登录", self._test_login, "检查当前登录状态")
        login_menu.add_item("2", "重新登录", self._force_login, "强制重新登录")
        login_menu.add_item("3", "查看登录状态", self._show_login_status, "显示详细登录信息")
        login_menu.add_item("4", "登录设置", self._login_settings, "配置登录参数")

        # 2. 课程管理菜单
        course_menu = Menu("📚 课程管理", "课程信息获取和管理")
        course_menu.add_item("1", "获取课程列表", self._fetch_courses, "从服务器获取最新课程")
        course_menu.add_item("2", "查看课程详情", self._view_course_details, "显示详细课程信息")
        course_menu.add_item("3", "课程进度统计", self._course_statistics, "查看学习进度统计")
        course_menu.add_item("4", "课程搜索", self._search_courses, "搜索和筛选课程")
        course_menu.add_item("5", "刷新课程数据", self._refresh_courses, "重新获取课程进度")

        # 3. 自动学习菜单
        learning_menu = Menu("🎓 自动学习", "智能化学习引擎")
        learning_menu.add_item("1", "开始自动学习", self._start_auto_learning, "启动自动学习程序")
        learning_menu.add_item("2", "学习进度查看", self._view_learning_progress, "查看实时学习进度")
        learning_menu.add_item("3", "学习参数设置", self._learning_settings, "配置学习参数")
        learning_menu.add_item("4", "学习历史记录", self._learning_history, "查看历史学习记录")
        learning_menu.add_item("5", "停止学习", self._stop_learning, "停止当前学习任务")

        # 4. 并发学习菜单
        concurrent_menu = Menu("🚀 并发学习", "多课程同时并发学习")
        concurrent_menu.add_item("1", "开始并发学习", self._start_concurrent_learning, "同时学习多门课程")
        concurrent_menu.add_item("2", "并发状态监控", self._monitor_concurrent_status, "查看并发学习状态")
        concurrent_menu.add_item("3", "并发配置设置", self._concurrent_settings, "配置并发学习参数")
        concurrent_menu.add_item("4", "客户端池管理", self._manage_client_pool_sync, "管理API客户端池")
        concurrent_menu.add_item("5", "停止所有并发", self._stop_concurrent_learning, "停止所有并发学习")

        # 5. 系统设置菜单
        system_menu = Menu("⚙️ 系统设置", "系统配置和维护")
        system_menu.add_item("1", "系统配置", self._system_config, "修改系统参数")
        system_menu.add_item("2", "系统诊断", self._system_diagnosis, "检查系统状态")
        system_menu.add_item("3", "关于系统", self._about_system, "显示系统信息")

        # 主菜单
        self.main_menu = Menu("🎓 智能自动学习控制台系统", "基于SCORM标准的全功能学习管理平台")
        self.main_menu.add_item("1", "登录管理", submenu=login_menu, description="用户认证和状态管理")
        self.main_menu.add_item("2", "课程管理", submenu=course_menu, description="课程信息和进度管理")
        self.main_menu.add_item("3", "自动学习", submenu=learning_menu, description="传统单课程学习")
        self.main_menu.add_item("4", "并发学习", submenu=concurrent_menu, description="多课程同时学习")
        self.main_menu.add_item("5", "系统设置", submenu=system_menu, description="系统配置和维护")
        self.main_menu.add_separator()
        self.main_menu.add_item("8", "一键开始学习", self._quick_start_learning, "自动登录并开始学习")
        self.main_menu.add_item("9", "超级学习模式", self._super_learning_mode, "高效并发学习")

    def run(self, quick_mode: bool = False):
        """运行控制台系统"""
        self.quick_mode = quick_mode

        # 显示欢迎信息
        self._show_welcome()

        # 快速模式
        if quick_mode:
            self._quick_mode_flow()
            return

        # 正常模式
        try:
            while self.running:
                self._show_main_menu()
        except KeyboardInterrupt:
            self._exit_system()
        except Exception as e:
            with LoggerContext() as logger:
                logger.error(f"系统运行错误: {e}")
            self.display.print_status(f"❌ 系统错误: {e}", "error")
            self.input.wait_for_key("按任意键退出...")

    def _show_welcome(self):
        """显示欢迎信息"""
        self.display.clear_screen()
        self.display.print_header("🎓 智能自动学习控制台系统")

        # 显示系统状态
        try:
            courses = self.course_manager.get_all_courses()
            course_count = len(courses)
            completed_count = len([c for c in courses if c.progress >= 100.0])

            status_info = [
                ["项目", "状态"],
                ["课程数据", f"{course_count} 门课程"],
                ["完成进度", f"{completed_count}/{course_count} 门课程"],
                ["登录状态", "需要检查" if not self.login_manager.is_logged_in_sync() else "已登录"],
                ["学习引擎", "就绪"],
                ["系统版本", "v1.0.0"]
            ]

            self.display.print_table(["项目", "状态"], status_info[1:], "系统状态")

        except Exception as e:
            self.display.print_status(f"⚠️ 系统状态检查失败: {e}", "warning")

        print()

    def _show_main_menu(self):
        """显示主菜单"""
        try:
            result = self.main_menu.show()
            if result == "exit":
                self.running = False
        except Exception as e:
            with LoggerContext() as logger:
                logger.error(f"主菜单错误: {e}")
            self.display.print_status(f"❌ 菜单错误: {e}", "error")

    def _quick_mode_flow(self):
        """快速模式流程"""
        self.display.print_header("🚀 快速模式")

        # 1. 检查登录
        if not self.login_manager.is_logged_in_sync():
            self.display.print_status("🔐 检测到未登录，正在登录...", "info")
            if not self.login_manager.ensure_logged_in():
                self.display.print_status("❌ 登录失败，退出快速模式", "error")
                return

        # 2. 更新课程数据
        self.display.print_status("📚 正在更新课程数据...", "info")
        self._fetch_courses()

        # 3. 开始学习
        self.display.print_status("🎓 开始自动学习...", "info")
        self._start_auto_learning()

    # ==================== 登录管理功能 ====================

    def _test_login(self):
        """测试登录"""
        self.display.print_header("🔐 测试登录")

        try:
            is_logged_in = self.login_manager.is_logged_in_sync()

            if is_logged_in:
                self.display.print_status("✅ 当前已登录", "success")
            else:
                self.display.print_status("❌ 当前未登录，开始登录流程...", "warning")
                success = self.login_manager.ensure_logged_in()
                if success:
                    self.display.print_status("✅ 登录成功", "success")
                else:
                    self.display.print_status("❌ 登录失败", "error")

        except Exception as e:
            self.display.print_status(f"❌ 登录测试失败: {e}", "error")

        self.input.wait_for_key()

    def _force_login(self):
        """强制重新登录"""
        self.display.print_header("🔄 重新登录")

        username = self.input.get_user_input("请输入用户名", default="640302198607120020")
        password = self.input.get_user_input("请输入密码", default="My2062660")

        try:
            success = run_async_in_sync(
                self.login_manager.login(username, password, save_credentials=True)
            )

            if success:
                self.display.print_status("✅ 登录成功", "success")
            else:
                self.display.print_status("❌ 登录失败", "error")

        except Exception as e:
            self.display.print_status(f"❌ 登录过程出错: {e}", "error")

        self.input.wait_for_key()

    def _show_login_status(self):
        """显示登录状态"""
        self.display.print_header("📊 登录状态")

        try:
            status = run_async_in_sync(self.login_manager.get_login_status())

            status_data = [
                ["状态项", "值"],
                ["登录状态", "已登录" if status.get('is_logged_in') else "未登录"],
                ["用户名", status.get('username', '未知')],
                ["登录时间", status.get('login_time', '未知')],
                ["会话有效", "是" if status.get('session_valid') else "否"],
                ["API状态", status.get('api_status', '未知')]
            ]

            self.display.print_table(["状态项", "值"], status_data[1:], "登录详情")

        except Exception as e:
            self.display.print_status(f"❌ 获取登录状态失败: {e}", "error")

        self.input.wait_for_key()

    def _login_settings(self):
        """登录设置"""
        self.display.print_header("⚙️ 登录设置")

        current_timeout = self.config_manager.get('login.session_timeout', 3600)
        auto_login = self.config_manager.get('login.auto_login', True)

        self.display.print_status(f"当前会话超时: {current_timeout}秒", "info")
        self.display.print_status(f"自动登录: {'启用' if auto_login else '禁用'}", "info")

        if self.input.get_yes_no("是否修改设置?"):
            new_timeout = self.input.get_number("新的会话超时(秒)", 1, 86400, current_timeout)
            new_auto_login = self.input.get_yes_no("是否启用自动登录?", auto_login)

            self.config_manager.set('login.session_timeout', new_timeout)
            self.config_manager.set('login.auto_login', new_auto_login)
            self.config_manager.save()

            self.display.print_status("✅ 设置已保存", "success")

        self.input.wait_for_key()

    def _auto_login(self) -> bool:
        """自动登录"""
        try:
            return self.login_manager.auto_login()
        except Exception as e:
            with LoggerContext() as logger:
                logger.error(f"自动登录失败: {e}")
            return False

    # ==================== 课程管理功能 ====================

    def _ensure_logged_in(self) -> bool:
        """确保用户已登录，如果未登录则自动使用默认凭据登录"""
        if not self.login_manager.is_logged_in_sync():
            self.display.print_status("🔑 检测到未登录状态，正在自动登录...", "info")

            # 尝试使用默认凭据自动登录
            if self.login_manager.auto_login():
                self.display.print_status("✅ 自动登录成功", "success")
                return True
            else:
                self.display.print_status("❌ 自动登录失败，请手动登录", "error")
                # 如果自动登录失败，可以尝试交互式登录
                return self.login_manager.interactive_login()
        return True

    def _ensure_courses_available(self) -> bool:
        """确保课程数据可用"""
        courses = run_async_in_sync(self.course_manager.get_courses())
        if not courses:
            self.display.print_status("❌ 没有课程数据，请先获取课程信息", "error")
            return False
        return True

    def _fetch_courses(self):
        """获取课程列表"""
        self.display.print_header("📚 获取课程列表")

        try:
            self.display.print_status("正在从服务器获取课程数据...", "info")

            success = self.course_manager.fetch_courses_sync()
            if success:
                courses = self.course_manager.get_all_courses()
            else:
                courses = []

            if courses:
                self.display.print_status(f"✅ 成功获取 {len(courses)} 门课程", "success")

                # 显示课程统计
                required_count = len([c for c in courses if c.course_type == 'required'])
                elective_count = len([c for c in courses if c.course_type == 'elective'])
                completed_count = len([c for c in courses if c.progress >= 100.0])

                stats_data = [
                    ["类型", "数量"],
                    ["必修课程", str(required_count)],
                    ["选修课程", str(elective_count)],
                    ["已完成", str(completed_count)],
                    ["总计", str(len(courses))]
                ]

                self.display.print_table(["类型", "数量"], stats_data[1:], "课程统计")
            else:
                self.display.print_status("⚠️ 未获取到课程数据", "warning")

        except Exception as e:
            self.display.print_status(f"❌ 获取课程失败: {e}", "error")

        self.input.wait_for_key()

    def _view_course_details(self):
        """查看课程详情"""
        self.display.print_header("📖 课程详情")

        try:
            courses = self.course_manager.get_all_courses()

            if not courses:
                self.display.print_status("⚠️ 暂无课程数据，请先获取课程列表", "warning")
                self.input.wait_for_key()
                return

            # 显示课程列表供选择
            course_data = [["序号", "课程名称", "类型", "进度"]]
            for i, course in enumerate(courses[:10]):  # 限制显示前10门课程
                course_data.append([
                    str(i + 1),
                    course.course_name[:30] + "..." if len(course.course_name) > 30 else course.course_name,
                    "必修" if course.course_type == 'required' else "选修",
                    f"{course.progress:.1f}%"
                ])

            self.display.print_table(["序号", "课程名称", "类型", "进度"], course_data[1:], "课程列表")

            if len(courses) > 10:
                self.display.print_status(f"注: 仅显示前10门课程，共有{len(courses)}门课程", "info")

            choice = self.input.get_number("请选择要查看的课程序号", 1, min(10, len(courses)))
            selected_course = courses[choice - 1]

            # 显示详细信息
            details_data = [
                ["属性", "值"],
                ["课程名称", selected_course.course_name],
                ["课程类型", "必修课" if selected_course.course_type == 'required' else "选修课"],
                ["学习进度", f"{selected_course.progress:.1f}%"],
                ["课程ID", str(selected_course.course_id)],
                ["用户课程ID", str(selected_course.user_course_id)],
                ["视频地址", selected_course.video_url[:50] + "..." if len(selected_course.video_url) > 50 else selected_course.video_url]
            ]

            self.display.print_table(["属性", "值"], details_data[1:], f"课程详情 - {selected_course.course_name}")

        except Exception as e:
            self.display.print_status(f"❌ 查看课程详情失败: {e}", "error")

        self.input.wait_for_key()

    def _course_statistics(self):
        """课程进度统计"""
        self.display.print_header("📊 课程进度统计")

        try:
            stats = self.course_manager.get_statistics()

            # 基本统计
            basic_stats = [
                ["统计项", "数量"],
                ["总课程数", str(stats['total_courses'])],
                ["必修课程", str(stats['required_courses'])],
                ["选修课程", str(stats['elective_courses'])],
                ["已完成课程", str(stats['completed_courses'])],
                ["未完成课程", str(stats['incomplete_courses'])]
            ]

            self.display.print_table(["统计项", "数量"], basic_stats[1:], "基本统计")

            # 计算进度分布
            courses = self.course_manager.get_all_courses()
            progress_distribution = {
                '0%': 0, '1-25%': 0, '26-50%': 0,
                '51-75%': 0, '76-99%': 0, '100%': 0
            }

            for course in courses:
                if course.progress == 0:
                    progress_distribution['0%'] += 1
                elif course.progress <= 25:
                    progress_distribution['1-25%'] += 1
                elif course.progress <= 50:
                    progress_distribution['26-50%'] += 1
                elif course.progress <= 75:
                    progress_distribution['51-75%'] += 1
                elif course.progress < 100:
                    progress_distribution['76-99%'] += 1
                else:
                    progress_distribution['100%'] += 1

            progress_stats = [
                ["进度范围", "课程数量"],
                ["0%", str(progress_distribution['0%'])],
                ["1-25%", str(progress_distribution['1-25%'])],
                ["26-50%", str(progress_distribution['26-50%'])],
                ["51-75%", str(progress_distribution['51-75%'])],
                ["76-99%", str(progress_distribution['76-99%'])],
                ["100%", str(progress_distribution['100%'])]
            ]

            self.display.print_table(["进度范围", "课程数量"], progress_stats[1:], "进度分布")

            # 显示完成率
            completion_rate = (stats['completed_courses'] / stats['total_courses'] * 100) if stats['total_courses'] > 0 else 0
            self.display.print_status(f"📈 总体完成率: {completion_rate:.1f}%", "info")

            # 显示平均进度
            avg_progress = stats.get('average_progress', 0)
            self.display.print_status(f"📊 平均进度: {avg_progress:.1f}%", "info")

        except Exception as e:
            self.display.print_status(f"❌ 获取统计数据失败: {e}", "error")

        self.input.wait_for_key()

    def _search_courses(self):
        """课程搜索"""
        self.display.print_header("🔍 课程搜索")

        try:
            keyword = self.input.get_user_input("请输入搜索关键词")
            course_type = None

            if self.input.get_yes_no("是否按课程类型筛选?"):
                print("1. 必修课")
                print("2. 选修课")
                type_choice = self.input.get_menu_choice(["必修课", "选修课"], "请选择课程类型")
                course_type = 'required' if type_choice == 1 else 'elective'

            results = self.course_manager.search_courses(keyword)

            # 按类型过滤（如果指定了类型）
            if course_type:
                results = [c for c in results if c.course_type == course_type]

            if results:
                search_data = [["序号", "课程名称", "类型", "进度"]]
                for i, course in enumerate(results):
                    search_data.append([
                        str(i + 1),
                        course.course_name[:40] + "..." if len(course.course_name) > 40 else course.course_name,
                        "必修" if course.course_type == 'required' else "选修",
                        f"{course.progress:.1f}%"
                    ])

                self.display.print_table(["序号", "课程名称", "类型", "进度"], search_data[1:], f"搜索结果 - '{keyword}'")
                self.display.print_status(f"✅ 找到 {len(results)} 门相关课程", "success")
            else:
                self.display.print_status(f"⚠️ 未找到包含 '{keyword}' 的课程", "warning")

        except Exception as e:
            self.display.print_status(f"❌ 搜索失败: {e}", "error")

        self.input.wait_for_key()

    def _refresh_courses(self):
        """刷新课程数据"""
        self.display.print_header("🔄 刷新课程数据")

        try:
            self.display.print_status("正在从API重新获取最新课程数据...", "info")

            # 使用新的刷新方法，从API获取最新数据
            success = self.course_manager.refresh_courses()

            if success:
                courses = self.course_manager.get_all_courses()
                self.display.print_status(f"✅ 成功刷新 {len(courses)} 门课程数据", "success")

                # 显示课程统计
                required_count = len([c for c in courses if c.course_type == 'required'])
                elective_count = len([c for c in courses if c.course_type == 'elective'])
                completed_count = len([c for c in courses if c.progress >= 100.0])

                stats_data = [
                    ["类型", "数量"],
                    ["必修课程", str(required_count)],
                    ["选修课程", str(elective_count)],
                    ["已完成", str(completed_count)],
                    ["总计", str(len(courses))]
                ]

                self.display.print_table(["类型", "数量"], stats_data[1:], "最新课程统计")
            else:
                self.display.print_status("❌ 刷新失败，请检查网络连接或登录状态", "error")

        except Exception as e:
            self.display.print_status(f"❌ 刷新失败: {e}", "error")

        self.input.wait_for_key()

    # ==================== 自动学习功能 ====================

    def _start_auto_learning(self):
        """开始自动学习"""
        self.display.print_header("🎓 开始自动学习")

        try:
            # 1. 确保已登录
            if not self._ensure_logged_in():
                self.input.wait_for_key()
                return

            # 2. 获取课程列表
            courses = self.course_manager.get_all_courses()
            if not courses:
                self.display.print_status("⚠️ 没有可用的课程，请先获取课程列表", "warning")
                self.input.wait_for_key()
                return

            # 3. 获取学习队列
            learning_queue = self.learning_engine.get_learning_queue()
            if not learning_queue:
                self.display.print_status("🎉 所有课程已完成！", "success")
                self.input.wait_for_key()
                return

            # 4. 显示学习计划
            self.display.print_status(f"📋 发现 {len(learning_queue)} 门待学习课程", "info")

            queue_data = [["序号", "课程名称", "类型", "当前进度", "预计时间"]]
            for i, course in enumerate(learning_queue[:10]):  # 只显示前10门
                course_type = "必修" if course.course_type == 'required' else "选修"
                estimated_time = int((100 - course.progress) * 0.5)  # 估算分钟数
                queue_data.append([
                    str(i + 1),
                    course.course_name[:30] + "..." if len(course.course_name) > 30 else course.course_name,
                    course_type,
                    f"{course.progress:.1f}%",
                    f"{estimated_time}分钟"
                ])

            self.display.print_table(["序号", "课程名称", "类型", "当前进度", "预计时间"], queue_data[1:], "学习计划")

            if len(learning_queue) > 10:
                self.display.print_status(f"注: 仅显示前10门课程，总共有{len(learning_queue)}门待学习课程", "info")

            # 5. 选择学习模式
            print("\n🎯 学习模式选择:")
            print("  1. 学习单个课程")
            print("  2. 批量学习多个课程")
            print("  3. 自动学习所有未完成课程")

            mode = self.input.get_number("请选择学习模式", 1, 3)

            if mode == 1:
                self._learn_single_course(learning_queue)
            elif mode == 2:
                self._learn_multiple_courses(learning_queue)
            elif mode == 3:
                self._learn_all_courses(learning_queue)

        except Exception as e:
            self.display.print_status(f"❌ 启动自动学习失败: {e}", "error")

        self.input.wait_for_key()

    def _learn_single_course(self, learning_queue: List[Course]):
        """学习单个课程"""
        if not learning_queue:
            self.display.print_status("没有可学习的课程", "warning")
            return

        print("\n📖 选择要学习的课程:")
        course_choice = self.input.get_number("请输入课程序号", 1, min(10, len(learning_queue)))
        selected_course = learning_queue[course_choice - 1]

        # 询问学习时间
        max_time = self.input.get_number("设置最大学习时间(分钟)", 1, 180, 30)

        self.display.print_status(f"▶️ 开始学习: {selected_course.course_name}", "info")

        try:
            # 启用安静模式以减少日志输出
            os.environ['LEARNING_QUIET_MODE'] = 'true'

            # 开始学习
            session = self.learning_engine.learn_course(selected_course, max_time * 60)

            # 显示学习结果
            self._show_learning_result(session)

        except Exception as e:
            self.display.print_status(f"❌ 学习过程出错: {e}", "error")
        finally:
            # 恢复正常日志模式
            os.environ.pop('LEARNING_QUIET_MODE', None)

    def _learn_multiple_courses(self, learning_queue: List[Course]):
        """批量学习多个课程"""
        if not learning_queue:
            self.display.print_status("没有可学习的课程", "warning")
            return

        # 选择学习数量
        max_count = min(5, len(learning_queue))
        course_count = self.input.get_number(f"选择学习课程数量", 1, max_count, max_count)

        # 选择总学习时间
        total_time = self.input.get_number("设置总学习时间(分钟)", 10, 480, 120)

        # 是否只学必修课
        required_only = self.input.get_yes_no("是否只学习必修课?", True)

        # 过滤课程
        filtered_courses = learning_queue[:course_count]
        if required_only:
            filtered_courses = [c for c in filtered_courses if c.course_type == 'required']

        if not filtered_courses:
            self.display.print_status("没有符合条件的课程", "warning")
            return

        self.display.print_status(f"▶️ 开始批量学习 {len(filtered_courses)} 门课程", "info")

        try:
            # 启用安静模式以减少日志输出
            os.environ['LEARNING_QUIET_MODE'] = 'true'

            # 开始批量学习
            sessions = self.learning_engine.learn_multiple_courses(
                courses=filtered_courses,
                max_total_time=total_time * 60
            )

            # 显示批量学习结果
            self._show_batch_learning_result(sessions)

        except Exception as e:
            self.display.print_status(f"❌ 批量学习过程出错: {e}", "error")
        finally:
            # 恢复正常日志模式
            os.environ.pop('LEARNING_QUIET_MODE', None)

    def _learn_all_courses(self, learning_queue: List[Course]):
        """自动学习所有未完成课程"""
        if not learning_queue:
            self.display.print_status("没有可学习的课程", "warning")
            return

        # 设置总学习时间
        total_time = self.input.get_number("设置总学习时间(分钟)", 30, 720, 240)

        # 是否优先必修课
        required_first = self.input.get_yes_no("是否优先学习必修课?", True)

        # 最大课程数量限制
        max_courses = self.input.get_number("设置最大学习课程数量", 1, len(learning_queue), min(10, len(learning_queue)))

        self.display.print_status(f"▶️ 开始自动学习，目标: {max_courses}门课程，时长: {total_time}分钟", "info")

        try:
            # 启用安静模式以减少日志输出
            os.environ['LEARNING_QUIET_MODE'] = 'true'

            # 获取实际的学习队列
            actual_queue = self.learning_engine.get_learning_queue(
                course_type='required' if required_first else None,
                max_courses=max_courses
            )

            if not actual_queue:
                self.display.print_status("❌ 没有找到符合条件的待学习课程", "warning")
                self.display.print_status(f"   过滤条件: 课程类型={'必修' if required_first else '所有'}, 最大数量={max_courses}", "info")
                return

            self.display.print_status(f"📚 找到 {len(actual_queue)} 门待学习课程", "info")

            # 开始自动学习
            sessions = self.learning_engine.learn_multiple_courses(
                courses=actual_queue,  # 直接传递课程列表
                max_total_time=total_time * 60
            )

            # 显示自动学习结果
            self._show_batch_learning_result(sessions, auto_mode=True)

        except Exception as e:
            self.display.print_status(f"❌ 自动学习过程出错: {e}", "error")
        finally:
            # 恢复正常日志模式
            os.environ.pop('LEARNING_QUIET_MODE', None)

    def _show_learning_result(self, session: LearningSession):
        """显示单个学习结果"""
        summary = self.learning_engine.get_session_summary(session)

        result_data = [
            ["属性", "值"],
            ["课程名称", summary['course_name']],
            ["课程类型", "必修课" if summary['course_type'] == 'required' else "选修课"],
            ["学习时长", summary['duration']],
            ["初始进度", f"{summary['initial_progress']:.1f}%"],
            ["最终进度", f"{summary['final_progress']:.1f}%"],
            ["进度增长", f"+{summary['progress_gained']:.1f}%"],
            ["学习状态", summary['status']],
            ["日志条数", str(summary['log_count'])]
        ]

        status = summary['status']
        if status == 'completed':
            title = "✅ 学习完成"
            status_type = "success"
        elif status == 'failed':
            title = "❌ 学习失败"
            status_type = "error"
        else:
            title = "⚠️ 学习中断"
            status_type = "warning"

        self.display.print_table(["属性", "值"], result_data[1:], title)

        # 显示是否查看详细日志
        if self.input.get_yes_no("是否查看详细学习日志?", False):
            self._show_learning_logs(session)

    def _show_batch_learning_result(self, sessions: List[LearningSession], auto_mode: bool = False):
        """显示批量学习结果"""
        title = "🤖 自动学习结果" if auto_mode else "📊 批量学习结果"
        self.display.print_header(title)

        if not sessions:
            self.display.print_status("没有学习记录", "warning")
            return

        # 统计信息
        total_sessions = len(sessions)
        completed_sessions = len([s for s in sessions if s.status == 'completed'])
        failed_sessions = len([s for s in sessions if s.status == 'failed'])
        total_progress_gained = sum(s.get_progress_gained() for s in sessions)
        total_time = sum(s.duration.total_seconds() for s in sessions)

        # 统计表格
        stats_data = [
            ["统计项", "数值"],
            ["总学习课程", str(total_sessions)],
            ["成功完成", str(completed_sessions)],
            ["学习失败", str(failed_sessions)],
            ["成功率", f"{(completed_sessions/total_sessions*100):.1f}%" if total_sessions > 0 else "0%"],
            ["总进度增长", f"+{total_progress_gained:.1f}%"],
            ["总学习时间", f"{int(total_time//60)}分{int(total_time%60)}秒"]
        ]

        self.display.print_table(["统计项", "数值"], stats_data[1:], "学习统计")

        # 详细结果
        if sessions:
            print("\n📋 详细学习记录:")
            detail_data = [["序号", "课程名称", "状态", "进度变化", "用时"]]

            for i, session in enumerate(sessions):
                status_icon = "✅" if session.status == 'completed' else "❌" if session.status == 'failed' else "⚠️"
                progress_change = f"{session.initial_progress:.1f}% → {session.final_progress:.1f}%"
                detail_data.append([
                    str(i + 1),
                    session.course.course_name[:25] + "..." if len(session.course.course_name) > 25 else session.course.course_name,
                    f"{status_icon} {session.status}",
                    progress_change,
                    session.get_duration_str()
                ])

            self.display.print_table(["序号", "课程名称", "状态", "进度变化", "用时"], detail_data[1:], "学习详情")

    def _show_learning_logs(self, session: LearningSession):
        """显示学习日志"""
        self.display.print_header(f"📝 学习日志 - {session.course.course_name}")

        if not session.logs:
            self.display.print_status("没有学习日志", "info")
            return

        print("学习过程日志:")
        for i, log in enumerate(session.logs):
            print(f"  {i+1:2d}. {log}")

        print(f"\n总共 {len(session.logs)} 条日志记录")

    def _view_learning_progress(self):
        """查看学习进度"""
        self.display.print_header("📈 学习进度")

        try:
            # 获取当前学习状态
            if self.learning_engine.is_learning and self.learning_engine.current_session:
                session = self.learning_engine.current_session
                self.display.print_status("🟢 当前正在学习中", "success")

                # 显示当前学习信息
                current_data = [
                    ["属性", "值"],
                    ["课程名称", session.course.course_name],
                    ["课程类型", "必修课" if session.course.course_type == 'required' else "选修课"],
                    ["开始时间", session.start_time.strftime('%H:%M:%S')],
                    ["已学时长", session.get_duration_str()],
                    ["当前进度", f"{session.course.progress:.1f}%"],
                    ["初始进度", f"{session.initial_progress:.1f}%"],
                    ["进度增长", f"+{session.get_progress_gained():.1f}%"]
                ]

                self.display.print_table(["属性", "值"], current_data[1:], "当前学习状态")

                # 显示最新日志
                if session.logs:
                    print("\n📝 最新学习日志:")
                    for log in session.logs[-5:]:  # 显示最后5条日志
                        print(f"  • {log}")

            else:
                self.display.print_status("⚪ 当前没有进行中的学习任务", "info")

            # 显示学习统计
            stats = self.learning_engine.get_statistics_summary()
            stats_data = [
                ["统计项", "数值"],
                ["总学习会话", str(stats['total_sessions'])],
                ["今日学习会话", str(stats['today_sessions'])],
                ["总学习时间", stats['total_learning_time']],
                ["完成课程数", str(stats['total_courses_completed'])],
                ["总进度增长", f"+{stats['total_progress_gained']:.1f}%"],
                ["学习成功率", f"{stats['success_rate']:.1f}%"],
                ["引擎状态", stats['current_status']]
            ]

            self.display.print_table(["统计项", "数值"], stats_data[1:], "学习统计")

            # 获取学习建议
            recommendations = self.learning_engine.get_learning_recommendations()

            rec_data = [
                ["建议项", "内容"],
                ["课程完成率", f"{recommendations['completion_rate']:.1f}%"],
                ["平均进度", f"{recommendations['average_progress']:.1f}%"],
                ["待完成必修课", str(recommendations['required_incomplete'])],
                ["待完成选修课", str(recommendations['elective_incomplete'])],
                ["下一步建议", recommendations['next_action']]
            ]

            self.display.print_table(["建议项", "内容"], rec_data[1:], "学习建议")

        except Exception as e:
            self.display.print_status(f"❌ 获取学习进度失败: {e}", "error")

        self.input.wait_for_key()

    def _learning_settings(self):
        """学习参数设置"""
        self.display.print_header("⚙️ 学习参数设置")

        try:
            # 显示当前设置
            current_settings = [
                ["参数", "当前值", "说明"],
                ["单课程最大时长", f"{self.config_manager.get('learning.max_duration_per_course', 1800)//60}分钟", "单个课程的最大学习时间"],
                ["总学习时长", f"{self.config_manager.get('learning.max_total_time', 7200)//60}分钟", "批量学习的总时间限制"],
                ["课程间休息", f"{self.config_manager.get('learning.rest_between_courses', 5)}秒", "学习课程之间的休息时间"],
                ["进度检查间隔", f"{self.config_manager.get('learning.progress_check_interval', 30)}秒", "学习过程中检查进度的间隔"],
                ["预估单课程时间", f"{self.config_manager.get('learning.estimated_time_per_course', 30)}分钟", "用于时间估算的单课程预期时间"]
            ]

            self.display.print_table(["参数", "当前值", "说明"], current_settings[1:], "当前学习参数")

            if self.input.get_yes_no("是否修改学习参数?"):
                print("\n🔧 参数修改:")
                print("  1. 单课程最大时长")
                print("  2. 总学习时长")
                print("  3. 课程间休息时间")
                print("  4. 进度检查间隔")
                print("  5. 预估单课程时间")

                choice = self.input.get_number("请选择要修改的参数", 1, 5)

                if choice == 1:
                    current = self.config_manager.get('learning.max_duration_per_course', 1800) // 60
                    new_value = self.input.get_number("设置单课程最大时长(分钟)", 5, 180, current)
                    self.config_manager.set('learning.max_duration_per_course', new_value * 60)
                elif choice == 2:
                    current = self.config_manager.get('learning.max_total_time', 7200) // 60
                    new_value = self.input.get_number("设置总学习时长(分钟)", 30, 720, current)
                    self.config_manager.set('learning.max_total_time', new_value * 60)
                elif choice == 3:
                    current = self.config_manager.get('learning.rest_between_courses', 5)
                    new_value = self.input.get_number("设置课程间休息时间(秒)", 0, 60, current)
                    self.config_manager.set('learning.rest_between_courses', new_value)
                elif choice == 4:
                    current = self.config_manager.get('learning.progress_check_interval', 30)
                    new_value = self.input.get_number("设置进度检查间隔(秒)", 10, 120, current)
                    self.config_manager.set('learning.progress_check_interval', new_value)
                elif choice == 5:
                    current = self.config_manager.get('learning.estimated_time_per_course', 30)
                    new_value = self.input.get_number("设置预估单课程时间(分钟)", 10, 120, current)
                    self.config_manager.set('learning.estimated_time_per_course', new_value)

                self.config_manager.save()
                self.display.print_status("✅ 参数设置已保存", "success")

        except Exception as e:
            self.display.print_status(f"❌ 学习参数设置失败: {e}", "error")

        self.input.wait_for_key()

    def _learning_history(self):
        """学习历史记录"""
        self.display.print_header("📚 学习历史记录")

        try:
            stats = self.learning_engine.statistics
            sessions = stats.sessions

            if not sessions:
                self.display.print_status("暂无学习历史记录", "info")
                self.input.wait_for_key()
                return

            # 显示历史统计
            total_time = stats.get_learning_time_str()
            success_rate = stats.get_success_rate()

            history_stats = [
                ["统计项", "数值"],
                ["总学习会话", str(len(sessions))],
                ["总学习时间", total_time],
                ["完成课程数", str(stats.total_courses_completed)],
                ["总进度增长", f"+{stats.total_progress_gained:.1f}%"],
                ["学习成功率", f"{success_rate:.1f}%"]
            ]

            self.display.print_table(["统计项", "数值"], history_stats[1:], "历史统计")

            # 显示最近的学习记录
            recent_sessions = sessions[-10:] if len(sessions) > 10 else sessions
            if recent_sessions:
                history_data = [["时间", "课程名称", "状态", "进度变化", "用时"]]

                for session in reversed(recent_sessions):  # 最新的在前
                    start_time = session.start_time.strftime('%m/%d %H:%M')
                    status_icon = "✅" if session.status == 'completed' else "❌" if session.status == 'failed' else "⚠️"
                    progress_change = f"{session.initial_progress:.1f}% → {session.final_progress:.1f}%"

                    history_data.append([
                        start_time,
                        session.course.course_name[:20] + "..." if len(session.course.course_name) > 20 else session.course.course_name,
                        f"{status_icon} {session.status}",
                        progress_change,
                        session.get_duration_str()
                    ])

                title = f"最近{len(recent_sessions)}次学习记录"
                if len(sessions) > 10:
                    title += f" (共{len(sessions)}次)"

                self.display.print_table(["时间", "课程名称", "状态", "进度变化", "用时"], history_data[1:], title)

            # 询问是否查看详细记录
            if self.input.get_yes_no("是否查看某次学习的详细日志?", False):
                if len(recent_sessions) == 1:
                    selected_session = recent_sessions[0]
                else:
                    choice = self.input.get_number("请选择学习记录序号", 1, len(recent_sessions))
                    selected_session = list(reversed(recent_sessions))[choice - 1]

                self._show_learning_logs(selected_session)

        except Exception as e:
            self.display.print_status(f"❌ 获取学习历史失败: {e}", "error")

        self.input.wait_for_key()

    def _stop_learning(self):
        """停止学习"""
        self.display.print_header("⏹️ 停止学习")

        try:
            if not self.learning_engine.is_learning:
                self.display.print_status("当前没有正在进行的学习任务", "info")
                self.input.wait_for_key()
                return

            # 显示当前学习状态
            session = self.learning_engine.current_session
            if session:
                current_info = [
                    ["属性", "值"],
                    ["课程名称", session.course.course_name],
                    ["已学时长", session.get_duration_str()],
                    ["当前进度", f"{session.course.progress:.1f}%"],
                    ["进度增长", f"+{session.get_progress_gained():.1f}%"]
                ]

                self.display.print_table(["属性", "值"], current_info[1:], "当前学习状态")

            # 确认停止
            if self.input.get_yes_no("确定要停止当前学习任务吗?"):
                reason = self.input.get_user_input("请输入停止原因 (可选)", default="用户手动停止")

                self.learning_engine.stop_learning_session(reason)
                self.display.print_status("✅ 学习任务已停止", "success")

                if session:
                    self.display.print_status(f"本次学习用时: {session.get_duration_str()}", "info")
                    self.display.print_status(f"进度增长: +{session.get_progress_gained():.1f}%", "info")
            else:
                self.display.print_status("已取消停止操作", "info")

        except Exception as e:
            self.display.print_status(f"❌ 停止学习失败: {e}", "error")

        self.input.wait_for_key()

    def _system_config(self):
        """系统配置"""
        self.display.print_header("⚙️ 系统配置")
        self.display.print_status("⚠️ 系统配置功能开发中...", "warning")
        self.input.wait_for_key()

    def _system_diagnosis(self):
        """系统诊断"""
        self.display.print_header("🔍 系统诊断")
        self.display.print_status("⚠️ 系统诊断功能开发中...", "warning")
        self.input.wait_for_key()

    def _about_system(self):
        """关于系统"""
        self.display.print_header("ℹ️ 关于系统")

        about_data = [
            ["项目", "信息"],
            ["系统名称", "智能自动学习控制台系统"],
            ["版本", "v1.0.0"],
            ["开发目的", "基于SCORM的自动化学习管理"],
            ["主要功能", "登录管理、课程管理、自动学习"],
            ["技术栈", "Python + Playwright + SQLite"],
            ["架构设计", "模块化、异步支持、配置驱动"],
            ["开发时间", "2025年"],
            ["许可证", "MIT License"]
        ]

        self.display.print_table(["项目", "信息"], about_data[1:], "系统信息")

        print("\n🎯 主要特性:")
        features = [
            "✅ 完整的SCORM学习支持",
            "✅ 智能学习进度管理",
            "✅ 友好的控制台界面",
            "✅ 灵活的配置系统",
            "✅ 详细的学习统计",
            "✅ 异步操作支持"
        ]

        for feature in features:
            print(f"  {feature}")

        self.input.wait_for_key()

    def _quick_start_learning(self):
        """一键开始学习"""
        self.display.print_header("🚀 一键开始学习")

        try:
            # 1. 自动登录检查
            self.display.print_status("🔐 检查登录状态...", "info")

            if not self.login_manager.is_logged_in_sync():
                self.display.print_status("📝 自动登录中...", "info")
                success = self.login_manager.ensure_logged_in()
                if not success:
                    self.display.print_status("❌ 自动登录失败，请手动登录", "error")
                    self.input.wait_for_key()
                    return
                self.display.print_status("✅ 登录成功", "success")

            # 2. 获取课程数据
            self.display.print_status("📚 获取最新课程数据...", "info")
            courses = self.course_manager.get_all_courses()

            if not courses:
                self.display.print_status("📋 课程列表为空，从服务器刷新...", "info")
                refresh_success = self.course_manager.refresh_courses()
                if refresh_success:
                    courses = self.course_manager.get_all_courses()
                    self.display.print_status(f"✅ 获取到 {len(courses)} 门课程", "success")
                else:
                    self.display.print_status("❌ 无法获取课程数据", "error")
                    self.input.wait_for_key()
                    return

            # 3. 分析学习情况
            learning_queue = self.learning_engine.get_learning_queue()
            if not learning_queue:
                self.display.print_status("🎉 恭喜！所有课程已完成", "success")
                self.input.wait_for_key()
                return

            # 4. 智能学习计划
            required_courses = [c for c in learning_queue if c.course_type == 'required']
            elective_courses = [c for c in learning_queue if c.course_type == 'elective']

            self.display.print_status(f"📊 学习分析：待完成 {len(learning_queue)} 门课程 (必修: {len(required_courses)}, 选修: {len(elective_courses)})", "info")

            # 显示学习计划
            plan_data = [["项目", "数量", "建议"]]
            if required_courses:
                plan_data.append(["必修课程", str(len(required_courses)), "优先完成"])
            if elective_courses:
                plan_data.append(["选修课程", str(len(elective_courses)), "可选学习"])

            total_estimated_time = sum((100 - c.progress) * 0.5 for c in learning_queue[:10])
            plan_data.append(["预计时间", f"{int(total_estimated_time)}分钟", "前10门课程"])

            self.display.print_table(["项目", "数量", "建议"], plan_data[1:], "智能学习计划")

            # 5. 确认开始学习
            if not self.input.get_yes_no("是否开始自动学习?", True):
                self.display.print_status("已取消自动学习", "info")
                self.input.wait_for_key()
                return

            # 6. 设置学习参数
            print("\n⚙️ 快速设置:")
            learning_time = self.input.get_number("设置学习时长(分钟)", 10, 480, 60)
            max_courses = self.input.get_number("设置最大学习课程数", 1, min(20, len(learning_queue)), min(5, len(learning_queue)))
            required_only = self.input.get_yes_no("是否只学习必修课?", True) if required_courses else False

            # 7. 开始自动学习
            self.display.print_status(f"🚀 开始自动学习: {max_courses}门课程, {learning_time}分钟", "success")
            print("\n" + "="*60)
            print("🎓 自动学习进行中... (按 Ctrl+C 可以中断)")
            print("="*60)

            try:
                # 启用安静模式以减少日志输出
                os.environ['LEARNING_QUIET_MODE'] = 'true'

                # 执行学习
                course_type = 'required' if required_only else None
                sessions = self.learning_engine.learn_multiple_courses(
                    course_type=course_type,
                    max_courses=max_courses,
                    max_total_time=learning_time * 60
                )

                # 显示结果
                print("\n" + "="*60)
                self.display.print_status("🎯 自动学习完成！", "success")
                self._show_batch_learning_result(sessions, auto_mode=True)

                # 提供后续操作选项
                print("\n🎯 后续操作:")
                print("  1. 继续学习更多课程")
                print("  2. 查看详细学习报告")
                print("  3. 返回主菜单")

                choice = self.input.get_number("请选择", 1, 3, 3)

                if choice == 1:
                    self.display.print_status("继续学习...", "info")
                    remaining_queue = self.learning_engine.get_learning_queue()
                    if remaining_queue:
                        self._start_auto_learning()
                    else:
                        self.display.print_status("🎉 所有课程已完成！", "success")
                elif choice == 2:
                    self._view_learning_progress()
                # choice == 3 直接返回

            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断学习")
                if self.learning_engine.is_learning:
                    self.learning_engine.stop_learning_session("用户中断")
                self.display.print_status("学习已停止", "warning")

        except Exception as e:
            self.display.print_status(f"❌ 一键学习失败: {e}", "error")
        finally:
            # 恢复正常日志模式
            os.environ.pop('LEARNING_QUIET_MODE', None)

        self.input.wait_for_key()

    def _exit_system(self):
        """退出系统"""
        self.display.print_header("👋 退出系统")

        if self.learning_engine.is_learning:
            if self.input.get_yes_no("检测到学习任务正在进行，是否强制退出?"):
                self.learning_engine.stop_learning_session("系统退出")
            else:
                return

        self.display.print_status("感谢使用智能自动学习控制台系统!", "info")
        self.running = False

        # 保存配置
        try:
            self.config_manager.save()
        except Exception as e:
            with LoggerContext() as logger:
                logger.warning(f"保存配置失败: {e}")

        sys.exit(0)

    # ==================== 并发学习功能 ====================

    def _start_concurrent_learning(self):
        """开始并发学习"""
        self.display.print_header("🚀 多课程并发学习")

        try:
            # 检查登录状态
            if not self._ensure_logged_in():
                return

            # 确保有课程数据
            if not self._ensure_courses_available():
                return

            # 获取学习队列
            all_courses = run_async_in_sync(self.course_manager.get_courses())
            incomplete_courses = [c for c in all_courses if c.progress < 100.0]

            if not incomplete_courses:
                self.display.print_status("🎉 所有课程已完成！", "success")
                self.input.wait_for_key()
                return

            self.display.print_status(f"发现 {len(incomplete_courses)} 门未完成课程", "info")

            # 配置并发学习参数
            print("\n📋 并发学习配置:")
            max_concurrent = self.input.get_number(
                f"最大并发课程数 (1-{min(5, len(incomplete_courses))})",
                1, min(5, len(incomplete_courses)),
                min(3, len(incomplete_courses))
            )

            max_total_time = InputUtils.get_number(
                "最大总学习时间(分钟)",
                10, 480, 60
            ) * 60  # 转换为秒

            type_options = ["必修课", "选修课", "全部"]
            type_values = ["required", "elective", "all"]
            choice_index = InputUtils.get_menu_choice(
                type_options,
                "请选择课程类型 (1-必修课 2-选修课 3-全部)",
                allow_back=False
            )
            course_type = type_values[choice_index - 1]  # 转换为对应值

            # 筛选课程
            if course_type != "all":
                filtered_courses = [c for c in incomplete_courses if c.course_type == course_type]
                if not filtered_courses:
                    self.display.print_status(f"没有找到{course_type}类型的未完成课程", "warning")
                    self.input.wait_for_key()
                    return
                incomplete_courses = filtered_courses

            # 显示即将学习的课程
            print(f"\n📚 即将并发学习的课程 (前{min(max_concurrent * 2, len(incomplete_courses))}门):")
            for i, course in enumerate(incomplete_courses[:max_concurrent * 2], 1):
                print(f"  {i}. {course.course_name} - 进度: {course.progress:.1f}%")

            if not self.input.get_yes_no("\n确认开始并发学习?"):
                return

            # 设置并发回调
            def on_concurrent_progress(course, progress):
                self.display.print_status(f"📈 {course.course_name[:20]}... - {progress:.1f}%", "info")

            def on_concurrent_session(session):
                if session.status == "completed":
                    self.display.print_status(f"✅ 完成: {session.course.course_name}", "success")
                elif session.status == "failed":
                    self.display.print_status(f"❌ 失败: {session.course.course_name}", "error")

            self.concurrent_manager.set_progress_callback(on_concurrent_progress)
            self.concurrent_manager.set_session_callback(on_concurrent_session)

            # 开始并发学习
            self.display.print_status("🚀 启动并发学习引擎...", "info")

            sessions = run_async_in_sync(
                self.concurrent_manager.learn_courses_concurrently(
                    courses=incomplete_courses,
                    max_concurrent=max_concurrent,
                    max_total_time=max_total_time
                )
            )

            # 显示结果
            self._show_concurrent_results(sessions)

        except Exception as e:
            self.display.print_status(f"❌ 并发学习失败: {e}", "error")

        self.input.wait_for_key()

    def _monitor_concurrent_status(self):
        """监控并发学习状态"""
        self.display.print_header("📊 并发学习状态监控")

        if not self.concurrent_manager.is_running:
            self.display.print_status("当前没有活动的并发学习任务", "info")
            self.input.wait_for_key()
            return

        try:
            start_monitor_time = time.time()
            while self.concurrent_manager.is_running:
                self.display.clear_screen()
                self.display.print_header("📊 实时并发学习监控")

                # 统计信息
                active_count = self.concurrent_manager.get_active_sessions_count()
                completed_count = len(self.concurrent_manager.completed_sessions)
                failed_count = len(self.concurrent_manager.failed_sessions)
                total_sessions = active_count + completed_count + failed_count

                print(f"📈 总体统计:")
                print(f"  总会话数: {total_sessions}")
                print(f"  活动中: {active_count} | 已完成: {completed_count} | 已失败: {failed_count}")
                print(f"  成功率: {(completed_count / max(1, completed_count + failed_count)) * 100:.1f}%")
                print(f"  监控时长: {time.time() - start_monitor_time:.0f}秒")

                # 客户端池状态
                pool_size = len(self.concurrent_manager.client_pool)
                available_clients = len(self.concurrent_manager.available_clients)
                print(f"\n🏊‍♂️ 客户端池状态:")
                print(f"  池大小: {pool_size} | 可用: {available_clients} | 使用中: {pool_size - available_clients}")

                # 活动会话详情
                if self.concurrent_manager.active_sessions:
                    print(f"\n🎯 活动会话详情:")
                    for session_id, session in self.concurrent_manager.active_sessions.items():
                        elapsed = (datetime.now() - session.start_time).total_seconds()
                        progress_gained = session.current_progress - session.initial_progress
                        progress_rate = progress_gained / max(1, elapsed / 60)  # 每分钟进度

                        print(f"  📚 {session.course.course_name[:35]}...")
                        print(f"     进度: {session.initial_progress:.1f}% → {session.current_progress:.1f}% (+{progress_gained:.1f}%)")
                        print(f"     时长: {elapsed:.0f}s | 速率: {progress_rate:.1f}%/min")
                        print(f"     状态: {session.status} | 客户端: {session.assigned_client_id or '共享'}")

                        # 显示最新日志
                        if session.logs:
                            latest_log = session.logs[-1]
                            print(f"     最新: {latest_log[:50]}...")
                        print()

                # 最近完成的会话
                if self.concurrent_manager.completed_sessions:
                    recent_completed = self.concurrent_manager.completed_sessions[-3:]  # 显示最近3个
                    print(f"✅ 最近完成 ({len(recent_completed)}/{completed_count}):")
                    for session in recent_completed:
                        progress_gained = session.current_progress - session.initial_progress
                        print(f"  📚 {session.course.course_name[:35]}... (+{progress_gained:.1f}%)")

                print(f"\n💡 按 Ctrl+C 退出监控 | 自动刷新间隔: 3秒")
                time.sleep(3)

        except KeyboardInterrupt:
            self.display.print_status("退出监控", "info")

        self.input.wait_for_key()

    def _concurrent_settings(self):
        """并发学习配置"""
        self.display.print_header("⚙️ 并发学习配置")

        config = self.concurrent_manager.config

        print("当前配置:")
        print(f"  最大并发数: {config.max_concurrent_courses}")
        print(f"  进度更新间隔: {config.progress_update_interval}秒")
        print(f"  自动负载均衡: {'启用' if config.auto_balance_load else '禁用'}")
        print(f"  资源限制: {config.resource_limit_per_course:.1%}")

        # 显示客户端池状态
        print(f"\n📊 客户端池状态:")
        print(f"  池大小: {len(self.concurrent_manager.client_pool)}")
        print(f"  可用客户端: {len(self.concurrent_manager.available_clients)}")
        print(f"  已分配客户端: {len(self.concurrent_manager.client_pool) - len(self.concurrent_manager.available_clients)}")

        if self.input.get_yes_no("\n是否修改配置?"):
            config.max_concurrent_courses = self.input.get_number(
                "最大并发课程数", 1, 10, config.max_concurrent_courses
            )
            config.progress_update_interval = self.input.get_number(
                "进度更新间隔(秒)", 1, 30, config.progress_update_interval
            )
            config.auto_balance_load = self.input.get_yes_no(
                f"启用自动负载均衡? (当前: {'启用' if config.auto_balance_load else '禁用'})"
            )

            self.concurrent_manager.save_config()
            self.display.print_status("配置已保存", "success")

        self.input.wait_for_key()

    def _manage_client_pool_sync(self):
        """客户端池管理（同步版本）"""
        self.display.print_header("🏊‍♂️ 客户端池管理")

        # 显示客户端池状态
        print(f"📊 客户端池状态:")
        print(f"  池大小: {len(self.concurrent_manager.client_pool)}")
        print(f"  可用客户端: {len(self.concurrent_manager.available_clients)}")
        print(f"  已分配客户端: {len(self.concurrent_manager.client_pool) - len(self.concurrent_manager.available_clients)}")

        options = [
            "初始化客户端池",
            "清理客户端池",
            "测试客户端池",
            "返回"
        ]

        choice = InputUtils.get_menu_choice(options, "请选择操作")

        if choice == 1:  # 初始化客户端池
            if self.concurrent_manager.client_pool:
                if not self.input.get_yes_no("客户端池已存在，是否重新初始化?"):
                    return
                run_async_in_sync(self.concurrent_manager.cleanup_client_pool())

            pool_size = self.input.get_number("客户端池大小", 1, 10, 3)
            try:
                run_async_in_sync(self.concurrent_manager.initialize_client_pool(pool_size))
                self.display.print_status(f"✅ 客户端池初始化成功 ({pool_size}个客户端)", "success")
            except Exception as e:
                self.display.print_status(f"❌ 客户端池初始化失败: {e}", "error")

        elif choice == 2:  # 清理客户端池
            if self.concurrent_manager.client_pool:
                run_async_in_sync(self.concurrent_manager.cleanup_client_pool())
                self.display.print_status("✅ 客户端池已清理", "success")
            else:
                self.display.print_status("客户端池为空", "info")

        elif choice == 3:  # 测试客户端池
            if not self.concurrent_manager.client_pool:
                self.display.print_status("客户端池未初始化", "warning")
                self.input.wait_for_key()
                return

            print("🧪 测试客户端分配和回收...")
            client = self.concurrent_manager.get_available_client()
            if client:
                print(f"✅ 成功获取客户端: {client.client_id}")
                self.concurrent_manager.return_client(client.client_id)
                print(f"✅ 成功归还客户端: {client.client_id}")
                self.display.print_status("客户端池测试通过", "success")
            else:
                self.display.print_status("❌ 无法获取客户端", "error")

        self.input.wait_for_key()

    def _stop_concurrent_learning(self):
        """停止并发学习"""
        self.display.print_header("⏹️ 停止并发学习")

        if not self.concurrent_manager.is_running:
            self.display.print_status("当前没有运行的并发学习任务", "info")
            self.input.wait_for_key()
            return

        active_count = self.concurrent_manager.get_active_sessions_count()
        self.display.print_status(f"发现 {active_count} 个活动会话", "info")

        if self.input.get_yes_no("确认停止所有并发学习?"):
            self.concurrent_manager.stop_all_sessions()
            self.display.print_status("已发送停止信号，等待会话结束...", "info")

            # 等待所有会话结束
            import time
            timeout = 30
            start_time = time.time()

            while self.concurrent_manager.get_active_sessions_count() > 0:
                if time.time() - start_time > timeout:
                    self.display.print_status("等待超时，强制结束", "warning")
                    break
                time.sleep(1)

            self.display.print_status("并发学习已停止", "success")

        self.input.wait_for_key()

    def _show_concurrent_results(self, sessions: List[ConcurrentLearningSession]):
        """显示并发学习结果"""
        print("\n" + "="*60)
        print("📊 并发学习结果统计")
        print("="*60)

        if not sessions:
            print("❌ 没有完成的学习会话")
            return

        completed_sessions = [s for s in sessions if s.status == "completed"]
        failed_sessions = [s for s in sessions if s.status == "failed"]

        print(f"✅ 完成课程: {len(completed_sessions)}门")
        print(f"❌ 失败课程: {len(failed_sessions)}门")

        if completed_sessions:
            print(f"\n🎯 完成的课程:")
            for session in completed_sessions:
                duration = (session.last_update_time - session.start_time).total_seconds()
                progress_gained = session.current_progress - session.initial_progress
                print(f"  ✅ {session.course.course_name}")
                print(f"     进度: {session.initial_progress:.1f}% → {session.current_progress:.1f}% (+{progress_gained:.1f}%)")
                print(f"     时长: {duration:.0f}秒")

        if failed_sessions:
            print(f"\n❌ 失败的课程:")
            for session in failed_sessions:
                print(f"  ❌ {session.course.course_name}")
                if session.logs:
                    print(f"     最后日志: {session.logs[-1]}")

    def _super_learning_mode(self):
        """超级学习模式：高效并发学习"""
        self.display.print_header("🚀 超级学习模式")

        try:
            if not self._ensure_logged_in():
                return

            if not self._ensure_courses_available():
                return

            # 获取学习队列
            all_courses = run_async_in_sync(self.course_manager.get_courses())
            incomplete_courses = [c for c in all_courses if c.progress < 100.0]

            if not incomplete_courses:
                self.display.print_status("🎉 所有课程已完成！", "success")
                self.input.wait_for_key()
                return

            print("🚀 超级学习模式将使用高效的并发学习策略")
            print(f"发现 {len(incomplete_courses)} 门未完成课程")

            # 配置超级学习
            print("\n⚙️ 超级学习配置:")
            max_concurrent = InputUtils.get_number(
                f"并发课程数 (1-{min(5, len(incomplete_courses))})",
                1, min(5, len(incomplete_courses)),
                min(3, len(incomplete_courses))
            )

            max_total_time = InputUtils.get_number(
                "最大学习时间(分钟)",
                15, 240, 45
            ) * 60

            print(f"\n📋 超级学习配置:")
            print(f"  并发课程: {max_concurrent}门")
            print(f"  时间限制: {max_total_time//60}分钟")
            print(f"  并发效率: {max_concurrent}x")

            if not InputUtils.get_yes_no("\n🚀 启动超级学习模式?"):
                return

            # 设置回调
            def super_progress_callback(course, progress):
                self.display.print_status(f"🚀 {course.course_name[:15]}... - {progress:.1f}%", "info")

            self.concurrent_manager.set_progress_callback(super_progress_callback)

            # 启动超级学习
            self.display.print_status("🚀⚡ 启动超级学习引擎...", "info")

            sessions = run_async_in_sync(
                self.concurrent_manager.learn_courses_concurrently(
                    courses=incomplete_courses,
                    max_concurrent=max_concurrent,
                    max_total_time=max_total_time
                )
            )

            # 显示超级学习结果
            self._show_super_learning_results(sessions, max_concurrent)

        except Exception as e:
            self.display.print_status(f"❌ 超级学习失败: {e}", "error")

        self.input.wait_for_key()

    def _show_super_learning_results(self, sessions: List[ConcurrentLearningSession],
                                   concurrent: int):
        """显示超级学习结果"""
        print("\n" + "="*60)
        print("🚀⚡ 超级学习模式结果")
        print("="*60)

        completed_count = len([s for s in sessions if s.status == "completed"])
        failed_count = len([s for s in sessions if s.status == "failed"])

        total_progress_gained = sum(s.current_progress - s.initial_progress for s in sessions)
        concurrent_efficiency = concurrent

        print(f"✅ 完成课程: {completed_count}门")
        print(f"❌ 失败课程: {failed_count}门")
        print(f"📈 总进度提升: {total_progress_gained:.1f}%")
        print(f"🚀 并发效率: {concurrent_efficiency}x")

        if sessions:
            avg_session_time = sum((s.last_update_time - s.start_time).total_seconds() for s in sessions) / len(sessions)
            print(f"⏱️ 平均单课程时间: {avg_session_time:.0f}秒")

        print(f"\n🎯 详细结果:")
        for session in sessions:
            status_icon = "✅" if session.status == "completed" else "❌"
            duration = (session.last_update_time - session.start_time).total_seconds()
            progress_gained = session.current_progress - session.initial_progress

            print(f"  {status_icon} {session.course.course_name}")
            print(f"     进度: +{progress_gained:.1f}%, 时长: {duration:.0f}s")

    def _select_course_for_learning(self) -> Optional[Course]:
        """选择要学习的课程"""
        all_courses = run_async_in_sync(self.course_manager.get_courses())
        incomplete_courses = [c for c in all_courses if c.progress < 100.0]

        if not incomplete_courses:
            self.display.print_status("没有未完成的课程", "warning")
            return None

        print(f"\n📚 选择要学习的课程:")
        for i, course in enumerate(incomplete_courses[:10], 1):  # 限制显示前10门
            print(f"  {i}. {course.course_name}")
            print(f"     类型: {course.course_type}, 进度: {course.progress:.1f}%")

        if len(incomplete_courses) > 10:
            print(f"  ... 还有 {len(incomplete_courses) - 10} 门课程")

        choice = self.input.get_number(
            "请选择课程编号",
            1, min(10, len(incomplete_courses)),
            1
        )

        return incomplete_courses[choice - 1]