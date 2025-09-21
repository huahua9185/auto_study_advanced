#!/usr/bin/env python3
"""
配置管理模块
负责系统配置的加载、保存和管理
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..utils.logger_utils import setup_colored_logger

# 检查是否在学习模式（安静模式）
quiet_mode = os.environ.get('LEARNING_QUIET_MODE', 'false').lower() == 'true'
logger = setup_colored_logger(__name__, console_output=not quiet_mode)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = "console_learning_system/data"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.json"
        self.user_config_file = self.config_dir / "user_config.json"

        self._config = {}
        self._user_config = {}
        self._load_configs()

    def _load_configs(self):
        """加载配置文件"""
        # 加载系统配置
        self._config = self._load_config_file(self.config_file, self._get_default_config())

        # 加载用户配置
        self._user_config = self._load_config_file(self.user_config_file, self._get_default_user_config())

    def _load_config_file(self, file_path: Path, default_config: Dict) -> Dict:
        """加载配置文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置（处理新增的配置项）
                merged_config = {**default_config, **config}
                return merged_config
            else:
                # 创建默认配置文件
                self._save_config_file(file_path, default_config)
                return default_config
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")
            return default_config

    def _save_config_file(self, file_path: Path, config: Dict):
        """保存配置文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置文件失败 {file_path}: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认系统配置"""
        return {
            "system": {
                "name": "智能自动学习控制台系统",
                "version": "1.0.0",
                "debug_mode": False,
                "auto_save_interval": 60,  # 自动保存间隔（秒）
                "max_log_files": 10,
                "log_level": "INFO"
            },
            "api": {
                "base_url": "https://edu.nxgbjy.org.cn",
                "timeout": 30,
                "retry_times": 3,
                "retry_delay": 2
            },
            "learning": {
                "default_session_duration": 300,  # 默认学习时长（秒）
                "progress_save_interval": 30,     # 进度保存间隔（秒）
                "auto_next_course": True,         # 自动学习下一课程
                "learning_speed": "normal",       # 学习速度: slow, normal, fast
                "max_daily_learning_hours": 8     # 每日最大学习小时数
            },
            "ui": {
                "theme": "default",
                "show_progress_bar": True,
                "show_timestamps": True,
                "auto_refresh_interval": 5,
                "confirm_dangerous_operations": True
            }
        }

    def _get_default_user_config(self) -> Dict[str, Any]:
        """获取默认用户配置"""
        return {
            "login": {
                "username": "",
                "remember_login": False,
                "auto_login": False,
                "login_timeout": 30
            },
            "preferences": {
                "show_welcome_message": True,
                "auto_check_updates": True,
                "save_learning_history": True,
                "notification_enabled": True
            },
            "courses": {
                "auto_fetch_on_startup": False,
                "default_course_filter": "all",  # all, required, elective
                "sort_by": "progress",           # name, progress, type
                "sort_order": "asc"              # asc, desc
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')

        # 先从用户配置中查找
        value = self._get_nested_value(self._user_config, keys)
        if value is not None:
            return value

        # 再从系统配置中查找
        value = self._get_nested_value(self._config, keys)
        if value is not None:
            return value

        return default

    def set(self, key: str, value: Any, save_to_user: bool = True):
        """设置配置值"""
        keys = key.split('.')
        config = self._user_config if save_to_user else self._config

        # 设置嵌套值
        self._set_nested_value(config, keys, value)

        # 保存配置
        if save_to_user:
            self.save_user_config()
        else:
            self.save_system_config()

    def _get_nested_value(self, config: Dict, keys: list) -> Any:
        """获取嵌套配置值"""
        try:
            current = config
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None

    def _set_nested_value(self, config: Dict, keys: list, value: Any):
        """设置嵌套配置值"""
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def save_system_config(self):
        """保存系统配置"""
        self._save_config_file(self.config_file, self._config)

    def save_user_config(self):
        """保存用户配置"""
        self._save_config_file(self.user_config_file, self._user_config)

    def reload_configs(self):
        """重新加载配置"""
        self._load_configs()

    def get_login_config(self) -> Dict[str, Any]:
        """获取登录配置"""
        return {
            'username': self.get('login.username', ''),
            'remember_login': self.get('login.remember_login', False),
            'auto_login': self.get('login.auto_login', False),
            'timeout': self.get('login.login_timeout', 30)
        }

    def save_login_config(self, username: str = None, remember: bool = None, auto_login: bool = None):
        """保存登录配置"""
        if username is not None:
            self.set('login.username', username)
        if remember is not None:
            self.set('login.remember_login', remember)
        if auto_login is not None:
            self.set('login.auto_login', auto_login)

    def get_learning_config(self) -> Dict[str, Any]:
        """获取学习配置"""
        return {
            'session_duration': self.get('learning.default_session_duration', 300),
            'progress_save_interval': self.get('learning.progress_save_interval', 30),
            'auto_next_course': self.get('learning.auto_next_course', True),
            'learning_speed': self.get('learning.learning_speed', 'normal'),
            'max_daily_hours': self.get('learning.max_daily_learning_hours', 8)
        }

    def save_learning_config(self, **kwargs):
        """保存学习配置"""
        for key, value in kwargs.items():
            if key in ['session_duration', 'progress_save_interval', 'auto_next_course',
                      'learning_speed', 'max_daily_hours']:
                config_key = f'learning.{key}' if key != 'max_daily_hours' else 'learning.max_daily_learning_hours'
                self.set(config_key, value)

    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return {
            'theme': self.get('ui.theme', 'default'),
            'show_progress_bar': self.get('ui.show_progress_bar', True),
            'show_timestamps': self.get('ui.show_timestamps', True),
            'auto_refresh_interval': self.get('ui.auto_refresh_interval', 5),
            'confirm_dangerous_operations': self.get('ui.confirm_dangerous_operations', True)
        }

    def export_config(self, file_path: str = None) -> str:
        """导出配置"""
        if file_path is None:
            file_path = self.config_dir / f"config_backup_{int(time.time())}.json"

        export_data = {
            'system_config': self._config,
            'user_config': self._user_config,
            'export_time': time.time(),
            'version': self.get('system.version', '1.0.0')
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已导出到: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            raise

    def import_config(self, file_path: str):
        """导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if 'system_config' in import_data:
                self._config = import_data['system_config']
                self.save_system_config()

            if 'user_config' in import_data:
                self._user_config = import_data['user_config']
                self.save_user_config()

            logger.info(f"配置已从 {file_path} 导入")
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise

    def reset_to_defaults(self, reset_user: bool = False):
        """重置为默认配置"""
        self._config = self._get_default_config()
        self.save_system_config()

        if reset_user:
            self._user_config = self._get_default_user_config()
            self.save_user_config()

        logger.info("配置已重置为默认值")

    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []

        # 检查必要的配置项
        required_keys = [
            'system.name',
            'system.version',
            'api.base_url',
            'learning.default_session_duration'
        ]

        for key in required_keys:
            if self.get(key) is None:
                errors.append(f"缺少必要配置项: {key}")

        # 检查数值范围
        if self.get('learning.default_session_duration', 0) <= 0:
            errors.append("学习时长必须大于0")

        if self.get('api.timeout', 0) <= 0:
            errors.append("API超时时间必须大于0")

        return errors