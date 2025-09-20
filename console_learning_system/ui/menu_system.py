#!/usr/bin/env python3
"""
菜单系统模块
提供分层菜单和导航功能
"""

from typing import Dict, List, Callable, Any, Optional
from .display_utils import DisplayUtils
from .input_utils import InputUtils


class MenuItem:
    """菜单项类"""

    def __init__(self, key: str, title: str, action: Callable = None,
                 description: str = "", submenu: 'Menu' = None):
        self.key = key
        self.title = title
        self.action = action
        self.description = description
        self.submenu = submenu

    def execute(self) -> Any:
        """执行菜单项"""
        if self.action:
            return self.action()
        elif self.submenu:
            return self.submenu.show()
        return None


class Menu:
    """菜单类"""

    def __init__(self, title: str, description: str = ""):
        self.title = title
        self.description = description
        self.items: List[MenuItem] = []
        self.parent: Optional['Menu'] = None

    def add_item(self, key: str, title: str, action: Callable = None,
                description: str = "", submenu: 'Menu' = None) -> 'MenuItem':
        """添加菜单项"""
        item = MenuItem(key, title, action, description, submenu)
        self.items.append(item)

        # 如果是子菜单，设置父菜单
        if submenu:
            submenu.parent = self

        return item

    def add_separator(self):
        """添加分隔符"""
        self.items.append(MenuItem("", "", None, ""))

    def find_item(self, key: str) -> Optional[MenuItem]:
        """查找菜单项"""
        for item in self.items:
            if item.key == key:
                return item
        return None

    def show(self) -> Any:
        """显示菜单并处理用户选择"""
        while True:
            self._display_menu()
            choice = self._get_user_choice()

            if choice is None:  # 用户取消
                return None

            if choice == "0" or choice == "back":  # 返回上级菜单
                return "back"

            if choice == "exit":  # 退出
                return "exit"

            # 查找对应的菜单项
            item = self.find_item(choice)
            if item:
                if item.action or item.submenu:
                    try:
                        result = item.execute()
                        if result == "exit":
                            return "exit"
                        elif result == "back":
                            continue
                    except Exception as e:
                        DisplayUtils.print_status('error', f'执行操作时出错: {str(e)}')
                        InputUtils.wait_for_key()
                else:
                    DisplayUtils.print_status('warning', '该功能暂未实现')
                    InputUtils.wait_for_key()
            else:
                DisplayUtils.print_status('error', '无效的选择')
                InputUtils.wait_for_key()

    def _display_menu(self):
        """显示菜单"""
        DisplayUtils.clear_screen()
        DisplayUtils.print_header(self.title)

        if self.description:
            print(DisplayUtils.colored_text(self.description, 'BRIGHT_BLACK'))
            print()

        # 显示菜单项
        for item in self.items:
            if item.key == "":  # 分隔符
                DisplayUtils.print_separator(50, "─", 'BRIGHT_BLACK')
            else:
                DisplayUtils.print_menu_item(item.key, item.title, item.description)

        print()

        # 显示导航选项
        nav_items = []
        if self.parent:
            nav_items.append("0. 返回上级菜单")
        nav_items.append("exit. 退出系统")

        if nav_items:
            DisplayUtils.print_section("导航选项")
            for nav_item in nav_items:
                print(f"  {DisplayUtils.colored_text(nav_item, 'BRIGHT_BLACK')}")

        print()

    def _get_user_choice(self) -> Optional[str]:
        """获取用户选择"""
        try:
            choice = input(DisplayUtils.colored_text("请选择: ", 'BRIGHT_CYAN')).strip().lower()
            return choice if choice else None
        except KeyboardInterrupt:
            print("\n")
            return "exit"
        except EOFError:
            print("\n")
            return "exit"


class MenuSystem:
    """菜单系统类"""

    def __init__(self):
        self.root_menu: Optional[Menu] = None
        self.current_menu: Optional[Menu] = None

    def create_root_menu(self, title: str, description: str = "") -> Menu:
        """创建根菜单"""
        self.root_menu = Menu(title, description)
        self.current_menu = self.root_menu
        return self.root_menu

    def run(self) -> None:
        """运行菜单系统"""
        if not self.root_menu:
            raise ValueError("未设置根菜单")

        try:
            result = self.root_menu.show()
            if result == "exit":
                self._show_goodbye()
        except KeyboardInterrupt:
            print("\n")
            self._show_goodbye()
        except Exception as e:
            DisplayUtils.print_status('error', f'系统错误: {str(e)}')

    def _show_goodbye(self):
        """显示退出信息"""
        print()
        DisplayUtils.print_status('info', '感谢使用智能自动学习控制台系统！')
        print()


class MenuBuilder:
    """菜单构建器"""

    def __init__(self):
        self.menu_system = MenuSystem()

    def create_menu(self, title: str, items: List[MenuItem]) -> Menu:
        """创建菜单"""
        menu = Menu(title)
        for item in items:
            if hasattr(item, 'submenu') and item.submenu:
                menu.add_item(item.key, item.title, submenu=item.submenu)
            else:
                menu.add_item(item.key, item.title, item.action)
        return menu

    def build_learning_system_menu(self, interface) -> MenuSystem:
        """构建学习系统菜单"""

        # 创建根菜单
        root = self.menu_system.create_root_menu(
            "🎓 智能自动学习控制台系统",
            "基于SCORM标准的全功能学习管理平台"
        )

        # 1. 登录管理菜单
        login_menu = Menu("🔐 登录管理", "用户认证和登录状态管理")
        login_menu.add_item("1", "测试登录", interface.test_login, "检查当前登录状态")
        login_menu.add_item("2", "重新登录", interface.relogin, "强制重新登录")
        login_menu.add_item("3", "查看登录状态", interface.show_login_status, "显示详细登录信息")
        login_menu.add_item("4", "登录设置", interface.login_settings, "配置登录参数")

        # 2. 课程管理菜单
        course_menu = Menu("📚 课程管理", "课程信息获取和管理")
        course_menu.add_item("1", "获取课程列表", interface.fetch_courses, "从服务器获取最新课程")
        course_menu.add_item("2", "查看课程详情", interface.show_course_details, "显示详细课程信息")
        course_menu.add_item("3", "课程进度统计", interface.show_course_statistics, "查看学习进度统计")
        course_menu.add_item("4", "课程搜索", interface.search_courses, "搜索和筛选课程")
        course_menu.add_item("5", "刷新课程数据", interface.refresh_course_data, "重新获取课程进度")

        # 3. 自动学习菜单
        learning_menu = Menu("🎓 自动学习", "智能化学习引擎")
        learning_menu.add_item("1", "开始自动学习", interface.start_auto_learning, "启动自动学习程序")
        learning_menu.add_item("2", "学习进度查看", interface.show_learning_progress, "查看实时学习进度")
        learning_menu.add_item("3", "学习参数设置", interface.learning_settings, "配置学习参数")
        learning_menu.add_item("4", "学习历史记录", interface.show_learning_history, "查看历史学习记录")
        learning_menu.add_item("5", "停止学习", interface.stop_learning, "停止当前学习任务")

        # 4. 系统设置菜单
        system_menu = Menu("⚙️ 系统设置", "系统配置和维护")
        system_menu.add_item("1", "系统配置", interface.system_config, "修改系统参数")
        system_menu.add_item("2", "日志管理", interface.log_management, "查看和管理日志")
        system_menu.add_item("3", "数据管理", interface.data_management, "数据备份和清理")
        system_menu.add_item("4", "系统诊断", interface.system_diagnosis, "检查系统状态")
        system_menu.add_item("5", "关于系统", interface.about_system, "显示系统信息")

        # 添加到根菜单
        root.add_item("1", "登录管理", submenu=login_menu, description="用户认证和状态管理")
        root.add_item("2", "课程管理", submenu=course_menu, description="课程信息和进度管理")
        root.add_item("3", "自动学习", submenu=learning_menu, description="智能化学习引擎")
        root.add_item("4", "系统设置", submenu=system_menu, description="系统配置和维护")

        return self.menu_system

    def build_quick_menu(self, interface) -> MenuSystem:
        """构建快速操作菜单"""
        root = self.menu_system.create_root_menu(
            "🚀 快速操作菜单",
            "常用功能快速访问"
        )

        root.add_item("1", "一键开始学习", interface.quick_start_learning, "自动登录并开始学习")
        root.add_item("2", "查看学习进度", interface.show_learning_progress, "快速查看当前进度")
        root.add_item("3", "获取课程列表", interface.fetch_courses, "更新课程信息")
        root.add_item("4", "系统状态检查", interface.system_diagnosis, "检查系统运行状态")
        root.add_separator()
        root.add_item("5", "完整功能菜单", interface.show_full_menu, "进入完整功能界面")

        return self.menu_system