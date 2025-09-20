#!/usr/bin/env python3
"""
登录管理模块
负责用户认证、登录状态管理和凭据处理
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# 添加父目录到路径，以便导入final_working_api_client
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from final_working_api_client import FinalWorkingAPIClient
from .config_manager import ConfigManager
from ..utils.async_utils import run_async_in_sync
from ..utils.logger_utils import setup_colored_logger
from ..ui.display_utils import DisplayUtils
from ..ui.input_utils import InputUtils

logger = setup_colored_logger(__name__)


class LoginManager:
    """登录管理器"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.api_client: Optional[FinalWorkingAPIClient] = None
        self._is_logged_in = False
        self.login_time: Optional[datetime] = None
        self.user_info: Dict[str, Any] = {}
        self.session_timeout = timedelta(hours=2)  # 会话超时时间

    async def is_logged_in(self) -> bool:
        """检查是否已登录（异步方法）"""
        return self.check_login_status()

    def is_logged_in_sync(self) -> bool:
        """检查是否已登录（同步方法）"""
        return self.check_login_status()

    async def initialize_client(self) -> bool:
        """初始化API客户端"""
        try:
            if self.api_client:
                await self.api_client.close()

            self.api_client = FinalWorkingAPIClient()
            await self.api_client.initialize()
            logger.info("API客户端初始化成功")
            return True

        except Exception as e:
            logger.error(f"API客户端初始化失败: {e}")
            return False

    def initialize_client_sync(self) -> bool:
        """同步方式初始化API客户端"""
        return run_async_in_sync(self.initialize_client())

    async def login(self, username: str = None, password: str = None,
                   save_credentials: bool = False) -> bool:
        """
        执行登录

        Args:
            username: 用户名
            password: 密码
            save_credentials: 是否保存凭据

        Returns:
            登录是否成功
        """
        try:
            # 确保API客户端已初始化
            if not self.api_client:
                if not await self.initialize_client():
                    return False

            # 获取登录凭据
            if not username or not password:
                credentials = self._get_login_credentials()
                username = username or credentials.get('username')
                password = password or credentials.get('password')

            if not username or not password:
                logger.error("缺少登录凭据")
                return False

            # 执行登录
            logger.info(f"正在尝试登录用户: {username}")
            success = await self.api_client.login(username, password)

            if success:
                self._is_logged_in = True
                self.login_time = datetime.now()
                self.user_info = {
                    'username': username,
                    'login_time': self.login_time.isoformat(),
                    'session_timeout': (self.login_time + self.session_timeout).isoformat()
                }

                # 保存凭据（如果请求）
                if save_credentials:
                    self.config_manager.save_login_config(
                        username=username,
                        remember=True
                    )

                logger.info("登录成功")
                return True
            else:
                logger.error("登录失败")
                self._is_logged_in = False
                return False

        except Exception as e:
            logger.error(f"登录过程中发生错误: {e}")
            self._is_logged_in = False
            return False

    def login_sync(self, username: str = None, password: str = None,
                  save_credentials: bool = False) -> bool:
        """同步方式登录"""
        return run_async_in_sync(self.login(username, password, save_credentials))

    async def logout(self) -> bool:
        """登出"""
        try:
            if self.api_client:
                await self.api_client.close()

            self._is_logged_in = False
            self.login_time = None
            self.user_info = {}
            self.api_client = None

            logger.info("已登出")
            return True

        except Exception as e:
            logger.error(f"登出时发生错误: {e}")
            return False

    def logout_sync(self) -> bool:
        """同步方式登出"""
        return run_async_in_sync(self.logout())

    def check_login_status(self) -> bool:
        """检查登录状态"""
        if not self._is_logged_in or not self.login_time:
            return False

        # 检查会话是否超时
        if datetime.now() > (self.login_time + self.session_timeout):
            logger.warning("会话已超时")
            self._is_logged_in = False
            return False

        return True

    def get_login_info(self) -> Dict[str, Any]:
        """获取登录信息"""
        if not self._is_logged_in:
            return {'logged_in': False}

        return {
            'logged_in': True,
            'username': self.user_info.get('username', ''),
            'login_time': self.user_info.get('login_time', ''),
            'session_timeout': self.user_info.get('session_timeout', ''),
            'session_remaining': self._get_session_remaining()
        }

    def _get_session_remaining(self) -> str:
        """获取剩余会话时间"""
        if not self.login_time:
            return "0分钟"

        remaining = (self.login_time + self.session_timeout) - datetime.now()
        if remaining.total_seconds() <= 0:
            return "已过期"

        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)

        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"

    def _get_login_credentials(self) -> Dict[str, str]:
        """获取登录凭据"""
        config = self.config_manager.get_login_config()

        # 硬编码的默认凭据（从原代码中获取）
        default_credentials = {
            'username': '640302198607120020',
            'password': 'My2062660'
        }

        return {
            'username': config.get('username') or default_credentials['username'],
            'password': default_credentials['password']  # 密码不从配置文件读取，安全考虑
        }

    def interactive_login(self) -> bool:
        """交互式登录"""
        try:
            DisplayUtils.print_header("用户登录")

            # 获取保存的用户名
            saved_username = self.config_manager.get('login.username', '')

            # 输入用户名
            if saved_username:
                username = InputUtils.get_user_input(
                    "用户名",
                    default=saved_username
                )
            else:
                username = InputUtils.get_user_input("用户名")

            if not username:
                DisplayUtils.print_status('error', '用户名不能为空')
                return False

            # 输入密码（使用默认密码）
            use_default = InputUtils.get_yes_no(
                "使用默认密码",
                default=True
            )

            if use_default:
                password = 'My2062660'  # 默认密码
            else:
                password = InputUtils.get_user_input("密码")

            if not password:
                DisplayUtils.print_status('error', '密码不能为空')
                return False

            # 询问是否保存用户名
            save_credentials = InputUtils.get_yes_no(
                "记住用户名",
                default=True
            )

            # 显示登录进度
            DisplayUtils.print_status('info', '正在登录...')

            # 执行登录
            success = self.login_sync(username, password, save_credentials)

            if success:
                DisplayUtils.print_status('success', f'登录成功！欢迎 {username}')
                return True
            else:
                DisplayUtils.print_status('error', '登录失败，请检查用户名和密码')
                return False

        except KeyboardInterrupt:
            print("\n")
            DisplayUtils.print_status('info', '登录被取消')
            return False
        except Exception as e:
            DisplayUtils.print_status('error', f'登录过程中发生错误: {e}')
            return False

    def show_login_status(self):
        """显示登录状态"""
        DisplayUtils.print_header("登录状态")

        login_info = self.get_login_info()

        if login_info['logged_in']:
            DisplayUtils.print_status('success', '当前已登录')
            print()

            # 创建状态表格
            status_data = [
                ['用户名', login_info.get('username', '未知')],
                ['登录时间', login_info.get('login_time', '未知')],
                ['剩余时间', login_info.get('session_remaining', '未知')],
                ['客户端状态', '已连接' if self.api_client else '未连接']
            ]

            DisplayUtils.print_table(
                ['属性', '值'],
                status_data,
                '登录详情'
            )
        else:
            DisplayUtils.print_status('warning', '当前未登录')

    def auto_login(self) -> bool:
        """自动登录"""
        try:
            if self.check_login_status():
                logger.info("用户已登录，无需自动登录")
                return True

            config = self.config_manager.get_login_config()
            username = config.get('username')

            # 如果没有配置用户名，使用默认凭据
            if not username:
                credentials = self._get_login_credentials()
                username = credentials.get('username')

            if not username:
                logger.warning("没有可用的登录凭据")
                return False

            logger.info("尝试自动登录...")
            return self.login_sync(username, save_credentials=False)

        except Exception as e:
            logger.error(f"自动登录失败: {e}")
            return False

    def ensure_logged_in(self) -> bool:
        """确保用户已登录"""
        if self.check_login_status():
            return True

        # 尝试自动登录
        if self.auto_login():
            return True

        # 提示用户登录
        DisplayUtils.print_status('warning', '需要登录才能继续操作')
        return self.interactive_login()

    async def refresh_session(self) -> bool:
        """刷新会话"""
        try:
            if not self.api_client or not self._is_logged_in:
                return False

            # 可以在这里添加会话刷新逻辑
            # 目前只是更新登录时间
            self.login_time = datetime.now()
            self.user_info['login_time'] = self.login_time.isoformat()
            self.user_info['session_timeout'] = (self.login_time + self.session_timeout).isoformat()

            logger.info("会话已刷新")
            return True

        except Exception as e:
            logger.error(f"刷新会话失败: {e}")
            return False

    def get_api_client(self) -> Optional[FinalWorkingAPIClient]:
        """获取API客户端"""
        return self.api_client if self._is_logged_in else None

    async def close(self):
        """关闭登录管理器"""
        if self.api_client:
            await self.api_client.close()
            self.api_client = None

        self._is_logged_in = False
        self.login_time = None
        self.user_info = {}

    def close_sync(self):
        """同步方式关闭"""
        run_async_in_sync(self.close())

    async def get_login_status(self) -> Dict[str, Any]:
        """获取详细登录状态"""
        return {
            'is_logged_in': self._is_logged_in,
            'username': self.user_info.get('username', '未知'),
            'login_time': self.login_time.strftime('%Y-%m-%d %H:%M:%S') if self.login_time else '未知',
            'session_valid': self.check_login_status(),
            'api_status': '已连接' if self.api_client else '未连接'
        }