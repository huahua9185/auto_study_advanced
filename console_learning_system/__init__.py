"""
智能自动学习控制台系统
基于SCORM标准的全功能学习管理界面
"""

__version__ = "1.0.0"
__author__ = "Auto Study API Team"
__description__ = "基于SCORM标准的智能自动学习控制台系统"

# 主要模块导入
from .core.console_interface import SCORMConsoleInterface
from .core.config_manager import ConfigManager
from .core.login_manager import LoginManager
from .core.course_manager import CourseManager, Course
from .core.learning_engine import LearningEngine, LearningSession

# UI 模块
from .ui.display_utils import DisplayUtils
from .ui.input_utils import InputUtils
from .ui.menu_system import Menu, MenuItem, MenuBuilder

# 工具模块
from .utils.async_utils import run_async_in_sync
from .utils.logger_utils import LoggerContext

__all__ = [
    'SCORMConsoleInterface',
    'ConfigManager',
    'LoginManager',
    'CourseManager',
    'Course',
    'LearningEngine',
    'LearningSession',
    'DisplayUtils',
    'InputUtils',
    'Menu',
    'MenuItem',
    'MenuBuilder',
    'run_async_in_sync',
    'LoggerContext'
]

# 快速启动函数
def quick_start(headless: bool = True, quick_mode: bool = False):
    """
    快速启动控制台系统

    Args:
        headless: 是否使用无头模式运行浏览器
        quick_mode: 是否使用快速模式（自动登录并开始学习）
    """
    try:
        interface = SCORMConsoleInterface()
        interface.run(quick_mode=quick_mode)
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        return False
    return True