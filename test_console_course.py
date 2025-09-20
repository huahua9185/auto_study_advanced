#!/usr/bin/env python3
"""
测试控制台界面的课程管理功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.console_interface import SCORMConsoleInterface

def test_console_course():
    """测试控制台课程功能"""
    print("🧪 测试控制台界面课程功能")
    print("=" * 50)

    # 1. 初始化控制台界面
    print("📋 1. 初始化控制台界面...")
    interface = SCORMConsoleInterface()
    print("   ✅ 界面初始化完成")

    # 2. 测试获取课程列表功能
    print("\n📋 2. 测试获取课程列表功能...")
    try:
        interface._fetch_courses()
        print("   ✅ 获取课程列表功能执行完成")
    except Exception as e:
        print(f"   ❌ 获取课程列表功能出错: {e}")
        import traceback
        traceback.print_exc()

    # 3. 测试课程统计功能
    print("\n📋 3. 测试课程统计功能...")
    try:
        interface._course_statistics()
        print("   ✅ 课程统计功能执行完成")
    except Exception as e:
        print(f"   ❌ 课程统计功能出错: {e}")
        import traceback
        traceback.print_exc()

    # 4. 测试刷新课程数据功能
    print("\n📋 4. 测试刷新课程数据功能...")
    try:
        interface._refresh_courses()
        print("   ✅ 刷新课程数据功能执行完成")
    except Exception as e:
        print(f"   ❌ 刷新课程数据功能出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 控制台课程功能测试完成！")

if __name__ == "__main__":
    test_console_course()