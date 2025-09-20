#!/usr/bin/env python3
"""
测试刷新课程数据功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager

async def test_refresh_functionality():
    """测试刷新功能"""
    print("🧪 测试刷新课程数据功能")
    print("=" * 60)

    # 1. 初始化系统组件
    print("📋 1. 初始化系统组件...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)

    # login_manager 和 course_manager 的初始化在构造函数中已完成
    await course_manager.initialize()

    # 2. 显示当前课程数量（数据库中的）
    print("\n📋 2. 显示当前课程数量（本地数据）...")
    current_courses = course_manager.get_all_courses()
    print(f"   本地课程数量: {len(current_courses)}")

    # 3. 执行刷新操作
    print("\n📋 3. 执行刷新操作（从API获取）...")
    success = course_manager.refresh_courses()

    if success:
        # 4. 显示刷新后的课程数量
        print("\n📋 4. 显示刷新后的课程数量...")
        refreshed_courses = course_manager.get_all_courses()
        print(f"   刷新后课程数量: {len(refreshed_courses)}")

        # 统计课程类型
        required_count = len([c for c in refreshed_courses if c.course_type == 'required'])
        elective_count = len([c for c in refreshed_courses if c.course_type == 'elective'])

        print(f"   必修课程: {required_count}")
        print(f"   选修课程: {elective_count}")

        # 5. 显示课程示例
        print("\n📋 5. 显示课程示例...")
        if refreshed_courses:
            for i, course in enumerate(refreshed_courses[:5]):  # 显示前5门课程
                print(f"   {i+1}. {course.course_name} ({course.course_type}) - {course.progress:.1f}%")

        print(f"\n✅ 刷新功能测试成功!")
        print(f"   刷新前: {len(current_courses)} 门课程")
        print(f"   刷新后: {len(refreshed_courses)} 门课程")

        # 验证是否真正从API获取了新数据
        if len(refreshed_courses) > len(current_courses):
            print("   ✅ 检测到新增课程，说明确实从API获取了最新数据")
        elif len(refreshed_courses) == len(current_courses) and len(refreshed_courses) > 0:
            print("   ✅ 课程数量一致，数据已是最新")
        else:
            print("   ⚠️ 需要进一步检查数据同步情况")

    else:
        print("❌ 刷新失败")

    print("\n🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_refresh_functionality())