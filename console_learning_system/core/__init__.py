"""
核心模块 - 包含系统的主要逻辑组件
"""

from .console_interface import SCORMConsoleInterface
from .login_manager import LoginManager
from .course_manager import CourseManager
from .learning_engine import LearningEngine
from .config_manager import ConfigManager

__all__ = [
    'SCORMConsoleInterface',
    'LoginManager',
    'CourseManager',
    'LearningEngine',
    'ConfigManager'
]