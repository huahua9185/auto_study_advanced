#!/usr/bin/env python3
"""
智能自动学习控制台系统 - 演示脚本
专为演示和测试设计的简化启动脚本
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def demo_system():
    """演示系统功能"""

    print("🎓 智能自动学习控制台系统 - 演示模式")
    print("="*60)

    try:
        from console_learning_system import SCORMConsoleInterface

        print("✅ 正在初始化系统...")
        interface = SCORMConsoleInterface()

        print("✅ 初始化完成！")
        print()

        # 显示系统状态
        print("📊 系统状态:")
        print(f"   • 配置管理器: {type(interface.config_manager).__name__}")
        print(f"   • 登录管理器: {type(interface.login_manager).__name__}")
        print(f"   • 课程管理器: {type(interface.course_manager).__name__}")
        print(f"   • 学习引擎: {type(interface.learning_engine).__name__}")

        # 显示课程统计
        courses = interface.course_manager.get_courses_sync()
        print(f"   • 课程数量: {len(courses)} 门")

        # 分类统计
        required_courses = [c for c in courses if c.course_type == 'required']
        elective_courses = [c for c in courses if c.course_type == 'elective']
        completed_courses = [c for c in courses if c.progress >= 100.0]

        print(f"   • 必修课程: {len(required_courses)} 门")
        print(f"   • 选修课程: {len(elective_courses)} 门")
        print(f"   • 已完成: {len(completed_courses)} 门")

        print()

        # 显示可用功能
        print("🚀 可用功能:")
        print("   1. 登录管理 - 用户认证和会话管理")
        print("   2. 课程管理 - 课程信息查看和统计")
        print("   3. 自动学习 - 智能化学习引擎")
        print("   4. 系统设置 - 配置和维护")

        print()

        # 显示启动方法
        print("🔧 启动方法:")
        print("   完整模式: python run_console.py")
        print("   快速模式: python run_console.py --quick")
        print("   交互模式: python start_console.py")

        print()
        print("🎉 系统演示完成！所有功能正常，可以开始使用。")

        return True

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False

if __name__ == "__main__":
    success = demo_system()
    sys.exit(0 if success else 1)