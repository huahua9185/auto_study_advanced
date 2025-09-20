#!/usr/bin/env python3
"""
智能自动学习控制台系统 - 简化启动脚本
最简单的启动方式，适合日常使用
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """简化启动流程"""
    try:
        from console_learning_system import SCORMConsoleInterface

        print("🎓 智能自动学习控制台系统")
        print("=" * 50)
        print("正在启动系统，请稍候...")
        print()

        # 创建并运行系统
        interface = SCORMConsoleInterface()
        interface.run()

    except KeyboardInterrupt:
        print("\n👋 用户中断，系统退出")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("\n💡 解决建议:")
        print("1. 确保在项目根目录下运行此脚本")
        print("2. 检查是否所有模块文件都存在")
        print("3. 运行 'python demo_console.py' 进行系统检查")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        print("\n💡 排查建议:")
        print("1. 运行 'python demo_console.py' 检查系统状态")
        print("2. 检查日志文件中的详细错误信息")
        print("3. 尝试重新安装依赖包")
        sys.exit(1)

if __name__ == "__main__":
    main()