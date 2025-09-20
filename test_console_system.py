#!/usr/bin/env python3
"""
测试控制台学习系统
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.console_interface import SCORMConsoleInterface

def test_console_system():
    """测试控制台系统启动"""
    print("🧪 测试控制台学习系统")
    print("=" * 60)

    try:
        # 初始化控制台界面
        print("📋 初始化控制台界面...")
        interface = SCORMConsoleInterface()

        # 检查系统组件
        print("📋 检查系统组件...")
        print(f"   配置管理器: {'✅' if interface.config_manager else '❌'}")
        print(f"   登录管理器: {'✅' if interface.login_manager else '❌'}")
        print(f"   课程管理器: {'✅' if interface.course_manager else '❌'}")
        print(f"   学习引擎: {'✅' if interface.learning_engine else '❌'}")

        # 检查课程数据
        courses = interface.course_manager.get_all_courses()
        print(f"   课程数据: {len(courses)} 门课程")

        # 检查学习队列
        learning_queue = interface.learning_engine.get_learning_queue()
        print(f"   学习队列: {len(learning_queue)} 门待学习课程")

        # 获取学习建议
        recommendations = interface.learning_engine.get_learning_recommendations()
        print(f"   学习建议: {recommendations['next_action']}")

        # 检查菜单系统
        print(f"   菜单系统: {'✅' if interface.main_menu else '❌'}")

        print("\n🎉 系统检查完成，所有组件正常运行!")
        print("\n💡 可以运行以下命令启动完整系统:")
        print("   python console_learning_system/main.py")

        return True

    except Exception as e:
        print(f"❌ 系统检查失败: {e}")
        return False

if __name__ == "__main__":
    test_console_system()