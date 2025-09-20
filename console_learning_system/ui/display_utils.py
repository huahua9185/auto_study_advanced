#!/usr/bin/env python3
"""
显示工具模块
提供控制台显示的美化和格式化功能
"""

import os
import sys
from typing import List, Dict, Any
from datetime import datetime


class DisplayUtils:
    """控制台显示工具类"""

    # ANSI 颜色代码
    COLORS = {
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BRIGHT_BLACK': '\033[90m',
        'BRIGHT_RED': '\033[91m',
        'BRIGHT_GREEN': '\033[92m',
        'BRIGHT_YELLOW': '\033[93m',
        'BRIGHT_BLUE': '\033[94m',
        'BRIGHT_MAGENTA': '\033[95m',
        'BRIGHT_CYAN': '\033[96m',
        'BRIGHT_WHITE': '\033[97m',
        'RESET': '\033[0m'
    }

    # 背景颜色
    BG_COLORS = {
        'BLACK': '\033[40m',
        'RED': '\033[41m',
        'GREEN': '\033[42m',
        'YELLOW': '\033[43m',
        'BLUE': '\033[44m',
        'MAGENTA': '\033[45m',
        'CYAN': '\033[46m',
        'WHITE': '\033[47m'
    }

    # 样式
    STYLES = {
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'ITALIC': '\033[3m',
        'UNDERLINE': '\033[4m',
        'BLINK': '\033[5m',
        'REVERSE': '\033[7m',
        'STRIKETHROUGH': '\033[9m'
    }

    @classmethod
    def clear_screen(cls):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')

    @classmethod
    def colored_text(cls, text: str, color: str = 'WHITE', bg_color: str = None, style: str = None) -> str:
        """
        返回带颜色的文本

        Args:
            text: 文本内容
            color: 前景色
            bg_color: 背景色
            style: 样式

        Returns:
            格式化后的文本
        """
        result = ""

        # 添加样式
        if style and style in cls.STYLES:
            result += cls.STYLES[style]

        # 添加背景色
        if bg_color and bg_color in cls.BG_COLORS:
            result += cls.BG_COLORS[bg_color]

        # 添加前景色
        if color in cls.COLORS:
            result += cls.COLORS[color]

        result += text + cls.COLORS['RESET']
        return result

    @classmethod
    def print_header(cls, title: str, width: int = 60, char: str = "="):
        """打印标题头"""
        print()
        print(cls.colored_text(char * width, 'CYAN'))
        title_line = f"{' ' * ((width - len(title)) // 2)}{title}"
        print(cls.colored_text(title_line, 'BRIGHT_CYAN', style='BOLD'))
        print(cls.colored_text(char * width, 'CYAN'))
        print()

    @classmethod
    def print_section(cls, title: str, width: int = 50, char: str = "-"):
        """打印章节标题"""
        print()
        print(cls.colored_text(f"{char * 5} {title} {char * (width - len(title) - 7)}", 'YELLOW'))

    @classmethod
    def print_menu_item(cls, number: str, text: str, description: str = ""):
        """打印菜单项"""
        number_colored = cls.colored_text(f"{number}.", 'BRIGHT_GREEN', style='BOLD')
        text_colored = cls.colored_text(text, 'WHITE')

        if description:
            desc_colored = cls.colored_text(f" - {description}", 'BRIGHT_BLACK')
            print(f"  {number_colored} {text_colored}{desc_colored}")
        else:
            print(f"  {number_colored} {text_colored}")

    @classmethod
    def print_status(cls, status: str, message: str):
        """打印状态信息"""
        if status.lower() == 'success':
            status_colored = cls.colored_text("✅ 成功", 'BRIGHT_GREEN', style='BOLD')
        elif status.lower() == 'error':
            status_colored = cls.colored_text("❌ 错误", 'BRIGHT_RED', style='BOLD')
        elif status.lower() == 'warning':
            status_colored = cls.colored_text("⚠️ 警告", 'BRIGHT_YELLOW', style='BOLD')
        elif status.lower() == 'info':
            status_colored = cls.colored_text("ℹ️ 信息", 'BRIGHT_BLUE', style='BOLD')
        else:
            status_colored = cls.colored_text(f"📝 {status}", 'WHITE', style='BOLD')

        print(f"{status_colored} {message}")

    @classmethod
    def print_progress_bar(cls, current: int, total: int, width: int = 50, prefix: str = "进度"):
        """打印进度条"""
        percent = (current / total) * 100 if total > 0 else 0
        filled_width = int(width * current / total) if total > 0 else 0

        bar = '█' * filled_width + '░' * (width - filled_width)

        prefix_colored = cls.colored_text(prefix, 'WHITE')
        bar_colored = cls.colored_text(bar, 'BRIGHT_GREEN')
        percent_colored = cls.colored_text(f"{percent:.1f}%", 'BRIGHT_CYAN')

        print(f"\r{prefix_colored}: [{bar_colored}] {percent_colored} ({current}/{total})", end='', flush=True)

    @classmethod
    def print_table(cls, headers: List[str], rows: List[List[str]], title: str = None):
        """打印表格"""
        if not headers or not rows:
            return

        # 计算列宽
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # 打印标题
        if title:
            print()
            total_width = sum(col_widths) + len(headers) * 3 + 1
            print(cls.colored_text(title.center(total_width), 'BRIGHT_CYAN', style='BOLD'))

        # 打印分隔线
        separator = "+" + "+".join(["-" * (width + 2) for width in col_widths]) + "+"
        print(cls.colored_text(separator, 'CYAN'))

        # 打印表头
        header_row = "|"
        for i, header in enumerate(headers):
            header_row += f" {cls.colored_text(header.ljust(col_widths[i]), 'BRIGHT_YELLOW', style='BOLD')} |"
        print(header_row)

        # 打印分隔线
        print(cls.colored_text(separator, 'CYAN'))

        # 打印数据行
        for row in rows:
            data_row = "|"
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    data_row += f" {str(cell).ljust(col_widths[i])} |"
            print(data_row)

        # 打印底部分隔线
        print(cls.colored_text(separator, 'CYAN'))

    @classmethod
    def print_box(cls, content: str, title: str = None, width: int = 60, padding: int = 2):
        """打印边框文本"""
        lines = content.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        box_width = max(width, max_line_length + padding * 2 + 2)

        # 顶部边框
        if title:
            title_len = len(title)
            title_padding = (box_width - title_len - 4) // 2
            top_line = "┌" + "─" * title_padding + f"[ {title} ]" + "─" * (box_width - title_padding - title_len - 4) + "┐"
        else:
            top_line = "┌" + "─" * (box_width - 2) + "┐"

        print(cls.colored_text(top_line, 'CYAN'))

        # 内容行
        for line in lines:
            content_line = "│" + " " * padding + line.ljust(box_width - padding * 2 - 2) + " " * padding + "│"
            print(cls.colored_text("│", 'CYAN') + content_line[1:-1] + cls.colored_text("│", 'CYAN'))

        # 底部边框
        bottom_line = "└" + "─" * (box_width - 2) + "┘"
        print(cls.colored_text(bottom_line, 'CYAN'))

    @classmethod
    def print_separator(cls, width: int = 60, char: str = "-", color: str = 'BRIGHT_BLACK'):
        """打印分隔线"""
        print(cls.colored_text(char * width, color))

    @classmethod
    def format_datetime(cls, dt: datetime = None) -> str:
        """格式化日期时间"""
        if dt is None:
            dt = datetime.now()
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def format_duration(cls, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"

    @classmethod
    def print_loading(cls, message: str = "处理中"):
        """打印加载信息"""
        loading_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        import time
        import threading

        def animate():
            i = 0
            while getattr(animate, 'running', True):
                char = loading_chars[i % len(loading_chars)]
                print(f"\r{cls.colored_text(char, 'BRIGHT_BLUE')} {message}...", end='', flush=True)
                time.sleep(0.1)
                i += 1

        thread = threading.Thread(target=animate)
        thread.daemon = True
        thread.start()
        return thread