#!/usr/bin/env python3
"""
智能自动学习控制台系统 - 主启动脚本
支持完整功能模式和快速操作模式
"""

import sys
import argparse
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    parser = argparse.ArgumentParser(
        description="智能自动学习控制台系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_console.py              # 正常模式
  python run_console.py --quick      # 快速模式
  python run_console.py --help       # 显示帮助
        """
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='快速模式：自动登录并开始学习'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='无头模式运行浏览器（默认启用）'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='智能自动学习控制台系统 v1.0.0'
    )

    args = parser.parse_args()

    try:
        from console_learning_system import SCORMConsoleInterface

        print("🎓 智能自动学习控制台系统")
        print("=" * 50)

        if args.quick:
            print("🚀 启动快速模式...")
        else:
            print("🖥️  启动完整功能模式...")

        print()

        # 创建并运行系统
        interface = SCORMConsoleInterface()
        interface.run(quick_mode=args.quick)

    except KeyboardInterrupt:
        print("\n👋 用户中断，系统退出")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()