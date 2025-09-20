#!/usr/bin/env python3
"""
输入处理工具模块
提供用户输入的处理和验证功能
"""

import sys
import select
import termios
import tty
if sys.platform == 'win32':
    import msvcrt
else:
    msvcrt = None
from typing import List, Optional, Callable, Any
from .display_utils import DisplayUtils


class InputUtils:
    """输入处理工具类"""

    @staticmethod
    def get_user_input(prompt: str = "请输入", default: str = None, validator: Callable = None) -> str:
        """
        获取用户输入

        Args:
            prompt: 提示信息
            default: 默认值
            validator: 验证函数

        Returns:
            用户输入的字符串
        """
        while True:
            if default:
                full_prompt = f"{prompt} (默认: {default}): "
            else:
                full_prompt = f"{prompt}: "

            try:
                user_input = input(DisplayUtils.colored_text(full_prompt, 'BRIGHT_CYAN')).strip()

                # 如果用户没有输入且有默认值，使用默认值
                if not user_input and default is not None:
                    user_input = default

                # 验证输入
                if validator:
                    if validator(user_input):
                        return user_input
                    else:
                        DisplayUtils.print_status('error', '输入无效，请重新输入')
                        continue

                return user_input

            except KeyboardInterrupt:
                print("\n")
                DisplayUtils.print_status('info', '操作被取消')
                return ""
            except EOFError:
                print("\n")
                return ""

    @staticmethod
    def get_menu_choice(menu_items: List[str], prompt: str = "请选择", allow_back: bool = True) -> int:
        """
        获取菜单选择

        Args:
            menu_items: 菜单项列表
            prompt: 提示信息
            allow_back: 是否允许返回（0选项）

        Returns:
            选择的菜单项索引（1开始），0表示返回/退出
        """
        while True:
            try:
                if allow_back:
                    choice_range = f"0-{len(menu_items)}"
                else:
                    choice_range = f"1-{len(menu_items)}"

                choice_prompt = f"{prompt} ({choice_range})"
                choice = input(DisplayUtils.colored_text(f"{choice_prompt}: ", 'BRIGHT_CYAN')).strip()

                if not choice:
                    continue

                choice_num = int(choice)

                if allow_back and choice_num == 0:
                    return 0
                elif 1 <= choice_num <= len(menu_items):
                    return choice_num
                else:
                    DisplayUtils.print_status('error', f'请输入 {choice_range} 之间的数字')

            except ValueError:
                DisplayUtils.print_status('error', '请输入有效的数字')
            except KeyboardInterrupt:
                print("\n")
                DisplayUtils.print_status('info', '操作被取消')
                return 0
            except EOFError:
                print("\n")
                return 0

    @staticmethod
    def get_yes_no(prompt: str = "确认", default: bool = None) -> bool:
        """
        获取是/否选择

        Args:
            prompt: 提示信息
            default: 默认值

        Returns:
            True表示是，False表示否
        """
        if default is True:
            choices = "(Y/n)"
        elif default is False:
            choices = "(y/N)"
        else:
            choices = "(y/n)"

        while True:
            try:
                choice = input(DisplayUtils.colored_text(f"{prompt} {choices}: ", 'BRIGHT_CYAN')).strip().lower()

                if not choice and default is not None:
                    return default

                if choice in ['y', 'yes', '是', '1', 'true']:
                    return True
                elif choice in ['n', 'no', '否', '0', 'false']:
                    return False
                else:
                    DisplayUtils.print_status('error', '请输入 y(是) 或 n(否)')

            except KeyboardInterrupt:
                print("\n")
                DisplayUtils.print_status('info', '操作被取消')
                return False
            except EOFError:
                print("\n")
                return False

    @staticmethod
    def get_number(prompt: str = "请输入数字", min_val: float = None, max_val: float = None,
                   default: float = None, is_int: bool = True) -> Optional[float]:
        """
        获取数字输入

        Args:
            prompt: 提示信息
            min_val: 最小值
            max_val: 最大值
            default: 默认值
            is_int: 是否只接受整数

        Returns:
            输入的数字，如果取消则返回None
        """
        while True:
            try:
                range_info = ""
                if min_val is not None and max_val is not None:
                    range_info = f" ({min_val}-{max_val})"
                elif min_val is not None:
                    range_info = f" (≥{min_val})"
                elif max_val is not None:
                    range_info = f" (≤{max_val})"

                if default is not None:
                    full_prompt = f"{prompt}{range_info} (默认: {default}): "
                else:
                    full_prompt = f"{prompt}{range_info}: "

                user_input = input(DisplayUtils.colored_text(full_prompt, 'BRIGHT_CYAN')).strip()

                if not user_input and default is not None:
                    return default

                if not user_input:
                    continue

                if is_int:
                    value = int(user_input)
                else:
                    value = float(user_input)

                # 验证范围
                if min_val is not None and value < min_val:
                    DisplayUtils.print_status('error', f'值不能小于 {min_val}')
                    continue

                if max_val is not None and value > max_val:
                    DisplayUtils.print_status('error', f'值不能大于 {max_val}')
                    continue

                return value

            except ValueError:
                if is_int:
                    DisplayUtils.print_status('error', '请输入有效的整数')
                else:
                    DisplayUtils.print_status('error', '请输入有效的数字')
            except KeyboardInterrupt:
                print("\n")
                DisplayUtils.print_status('info', '操作被取消')
                return None
            except EOFError:
                print("\n")
                return None

    @staticmethod
    def wait_for_key(prompt: str = "按任意键继续...") -> str:
        """
        等待用户按键

        Args:
            prompt: 提示信息

        Returns:
            按下的键
        """
        print(DisplayUtils.colored_text(prompt, 'BRIGHT_BLACK'), end='', flush=True)

        try:
            if sys.platform == 'win32':
                # Windows
                import msvcrt
                key = msvcrt.getch().decode('utf-8')
            else:
                # Unix/Linux/MacOS
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    key = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            print()  # 换行
            return key

        except Exception:
            # 如果上述方法失败，使用标准输入
            input()
            return ""

    @staticmethod
    def show_loading_with_cancel(message: str = "处理中", check_interval: float = 0.1) -> bool:
        """
        显示加载动画并允许用户取消

        Args:
            message: 加载信息
            check_interval: 检查间隔（秒）

        Returns:
            True表示正常完成，False表示用户取消
        """
        import time
        import threading
        from queue import Queue, Empty

        loading_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        cancelled = False

        def check_input(queue):
            try:
                if sys.platform == 'win32':
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'\x03':  # Ctrl+C
                            queue.put('cancel')
                else:
                    if select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)
                        if key == '\x03':  # Ctrl+C
                            queue.put('cancel')
            except:
                pass

        queue = Queue()

        print(DisplayUtils.colored_text(f"按 Ctrl+C 取消操作", 'BRIGHT_BLACK'))

        i = 0
        while not cancelled:
            char = loading_chars[i % len(loading_chars)]
            print(f"\r{DisplayUtils.colored_text(char, 'BRIGHT_BLUE')} {message}...", end='', flush=True)

            # 检查用户输入
            input_thread = threading.Thread(target=check_input, args=(queue,))
            input_thread.daemon = True
            input_thread.start()

            time.sleep(check_interval)

            try:
                result = queue.get_nowait()
                if result == 'cancel':
                    cancelled = True
                    print(f"\r{DisplayUtils.colored_text('❌ 操作被取消', 'BRIGHT_RED')}")
                    return False
            except Empty:
                pass

            i += 1

        return True

    @staticmethod
    def create_validator(pattern: str = None, min_length: int = None, max_length: int = None,
                        custom_func: Callable = None) -> Callable:
        """
        创建输入验证器

        Args:
            pattern: 正则表达式模式
            min_length: 最小长度
            max_length: 最大长度
            custom_func: 自定义验证函数

        Returns:
            验证函数
        """
        import re

        def validator(value: str) -> bool:
            # 长度验证
            if min_length is not None and len(value) < min_length:
                DisplayUtils.print_status('error', f'输入长度不能少于 {min_length} 个字符')
                return False

            if max_length is not None and len(value) > max_length:
                DisplayUtils.print_status('error', f'输入长度不能超过 {max_length} 个字符')
                return False

            # 模式验证
            if pattern and not re.match(pattern, value):
                DisplayUtils.print_status('error', '输入格式不正确')
                return False

            # 自定义验证
            if custom_func and not custom_func(value):
                return False

            return True

        return validator