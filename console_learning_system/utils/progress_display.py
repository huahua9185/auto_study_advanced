"""
进度条显示工具
提供类似 Ant Design 风格的进度条显示功能
"""

from typing import Optional, Tuple
import math

# 尝试导入colorama，如果不存在则使用空的替代
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    # 如果没有colorama，使用空字符串替代颜色代码
    class _DummyColors:
        GREEN = RED = CYAN = YELLOW = MAGENTA = BLUE = WHITE = ""

    class _DummyStyle:
        RESET_ALL = ""

    Fore = _DummyColors()
    Style = _DummyStyle()
    HAS_COLORAMA = False


class ProgressBar:
    """进度条显示类"""

    # Unicode字符用于绘制进度条
    BLOCKS = {
        'full': '█',
        'three_quarters': '▓',
        'half': '▒',
        'quarter': '░',
        'empty': '░'
    }

    # 进度条颜色配置
    COLORS = {
        'success': Fore.GREEN,
        'info': Fore.CYAN,
        'warning': Fore.YELLOW,
        'danger': Fore.RED,
        'normal': Fore.WHITE
    }

    @staticmethod
    def create_bar(progress: float, width: int = 30,
                   show_percentage: bool = True,
                   color: str = 'auto') -> str:
        """
        创建进度条字符串

        Args:
            progress: 进度百分比 (0-100)
            width: 进度条宽度（字符数）
            show_percentage: 是否显示百分比
            color: 颜色模式 ('auto', 'success', 'info', 'warning', 'danger', 'normal')

        Returns:
            格式化的进度条字符串
        """
        # 确保进度在有效范围内
        progress = max(0, min(100, progress))

        # 自动选择颜色
        if color == 'auto':
            if progress >= 100:
                color = 'success'
            elif progress >= 80:
                color = 'info'
            elif progress >= 60:
                color = 'normal'
            elif progress >= 30:
                color = 'warning'
            else:
                color = 'danger'

        # 计算填充长度
        filled_length = int(width * progress / 100)

        # 创建进度条
        bar = ProgressBar.BLOCKS['full'] * filled_length
        bar += ProgressBar.BLOCKS['empty'] * (width - filled_length)

        # 应用颜色
        color_code = ProgressBar.COLORS.get(color, Fore.WHITE)
        colored_bar = f"{color_code}{bar}{Style.RESET_ALL}"

        # 添加百分比显示
        if show_percentage:
            percentage_str = f" {progress:5.1f}%"
            return f"[{colored_bar}]{percentage_str}"
        else:
            return f"[{colored_bar}]"

    @staticmethod
    def create_circular_progress(progress: float, radius: int = 3) -> str:
        """
        创建圆形进度指示器（ASCII art风格）

        Args:
            progress: 进度百分比 (0-100)
            radius: 半径大小

        Returns:
            圆形进度指示器字符串
        """
        progress = max(0, min(100, progress))

        # 使用简化的圆形表示
        if progress >= 100:
            indicator = "⬤"  # 实心圆
            color = Fore.GREEN
        elif progress >= 75:
            indicator = "◕"  # 3/4圆
            color = Fore.CYAN
        elif progress >= 50:
            indicator = "◐"  # 半圆
            color = Fore.YELLOW
        elif progress >= 25:
            indicator = "◔"  # 1/4圆
            color = Fore.MAGENTA
        else:
            indicator = "○"  # 空心圆
            color = Fore.RED

        return f"{color}{indicator} {progress:.1f}%{Style.RESET_ALL}"

    @staticmethod
    def create_step_progress(current: int, total: int) -> str:
        """
        创建步骤进度显示

        Args:
            current: 当前步骤
            total: 总步骤数

        Returns:
            步骤进度字符串
        """
        result = ""
        for i in range(1, total + 1):
            if i < current:
                result += f"{Fore.GREEN}●{Style.RESET_ALL}"
            elif i == current:
                result += f"{Fore.CYAN}◉{Style.RESET_ALL}"
            else:
                result += f"{Fore.WHITE}○{Style.RESET_ALL}"

            if i < total:
                result += "─"

        return result

    @staticmethod
    def create_speed_indicator(speed: float, unit: str = "%/min") -> str:
        """
        创建速度指示器

        Args:
            speed: 速度值
            unit: 单位

        Returns:
            速度指示器字符串
        """
        if speed > 10:
            arrow = "⚡"
            color = Fore.GREEN
        elif speed > 5:
            arrow = "▶"
            color = Fore.CYAN
        elif speed > 1:
            arrow = "→"
            color = Fore.YELLOW
        else:
            arrow = "⇢"
            color = Fore.RED

        return f"{color}{arrow} {speed:.1f}{unit}{Style.RESET_ALL}"

    @staticmethod
    def create_status_badge(status: str, with_icon: bool = True) -> str:
        """
        创建状态徽章

        Args:
            status: 状态文本
            with_icon: 是否包含图标

        Returns:
            状态徽章字符串
        """
        status_configs = {
            'learning': ('🎯', Fore.GREEN, '学习中'),
            'paused': ('⏸️', Fore.YELLOW, '已暂停'),
            'completed': ('✅', Fore.GREEN, '已完成'),
            'failed': ('❌', Fore.RED, '失败'),
            'waiting': ('⏳', Fore.CYAN, '等待中'),
            'preparing': ('🔄', Fore.MAGENTA, '准备中'),
            'submitting': ('📤', Fore.BLUE, '提交中')
        }

        config = status_configs.get(status, ('●', Fore.WHITE, status))
        icon, color, text = config

        if with_icon:
            return f"{icon} {color}{text}{Style.RESET_ALL}"
        else:
            return f"{color}[{text}]{Style.RESET_ALL}"

    @staticmethod
    def create_time_display(seconds: float) -> str:
        """
        创建友好的时间显示

        Args:
            seconds: 秒数

        Returns:
            格式化的时间字符串
        """
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"


class ConcurrentProgressDisplay:
    """并发学习进度显示器"""

    @staticmethod
    def create_session_card(session) -> str:
        """
        创建会话卡片显示

        Args:
            session: ConcurrentLearningSession对象

        Returns:
            格式化的会话卡片字符串
        """
        lines = []

        # 标题行
        course_name = session.course.course_name[:40]
        if len(session.course.course_name) > 40:
            course_name += "..."

        status_badge = ProgressBar.create_status_badge(session.status)
        lines.append(f"\n┌─ {status_badge} {course_name}")

        # 进度条
        progress = session.current_progress
        progress_bar = ProgressBar.create_bar(progress, width=40, color='auto')
        progress_delta = session.current_progress - session.initial_progress
        delta_str = f"{Fore.GREEN}+{progress_delta:.1f}%{Style.RESET_ALL}" if progress_delta > 0 else ""
        lines.append(f"│  进度: {progress_bar} {delta_str}")

        # 速度指示器
        speed = session.get_progress_rate()
        speed_indicator = ProgressBar.create_speed_indicator(speed)
        elapsed = (session.get_elapsed_time())
        time_str = ProgressBar.create_time_display(elapsed)
        lines.append(f"│  速率: {speed_indicator}  运行: {time_str}")

        # 统计信息
        if session.api_submissions > 0:
            success_rate = (session.api_success_count / session.api_submissions) * 100
            success_color = Fore.GREEN if success_rate >= 90 else Fore.YELLOW
            lines.append(f"│  提交: {session.api_submissions}次  成功率: {success_color}{success_rate:.0f}%{Style.RESET_ALL}")

        lines.append("└" + "─" * 60)

        return "\n".join(lines)

    @staticmethod
    def create_summary_dashboard(active_sessions, completed_sessions, failed_sessions,
                                total_time: float, max_concurrent: int) -> str:
        """
        创建汇总仪表板

        Args:
            active_sessions: 活动会话字典
            completed_sessions: 已完成会话列表
            failed_sessions: 失败会话列表
            total_time: 总耗时（秒）
            max_concurrent: 最大并发数

        Returns:
            格式化的仪表板字符串
        """
        lines = []

        # 标题
        lines.append("\n" + "=" * 70)
        lines.append(f"{Fore.CYAN}📊 并发学习仪表板{Style.RESET_ALL}".center(78))
        lines.append("=" * 70)

        # 状态概览
        active = len(active_sessions)
        completed = len(completed_sessions)
        failed = len(failed_sessions)
        total = active + completed + failed

        # 进度概览条
        if total > 0:
            completion_rate = (completed / total) * 100
            progress_bar = ProgressBar.create_bar(completion_rate, width=50)
            lines.append(f"\n总体进度: {progress_bar}")

        # 状态统计
        lines.append("\n📈 状态统计:")
        lines.append(f"  {Fore.GREEN}● 活动中: {active}/{max_concurrent}{Style.RESET_ALL}    "
                    f"{Fore.BLUE}✓ 已完成: {completed}{Style.RESET_ALL}    "
                    f"{Fore.RED}✗ 失败: {failed}{Style.RESET_ALL}")

        # 时间统计
        time_display = ProgressBar.create_time_display(total_time)
        lines.append(f"\n⏱️  运行时间: {time_display}")

        # 效率统计
        if completed_sessions:
            total_progress = sum(s.current_progress - s.initial_progress for s in completed_sessions)
            avg_rate = total_progress / (total_time / 60) if total_time > 0 else 0
            efficiency = ProgressBar.create_speed_indicator(avg_rate)
            lines.append(f"⚡ 学习效率: {efficiency}")

        lines.append("=" * 70)

        return "\n".join(lines)