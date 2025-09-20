#!/usr/bin/env python3
"""
测试课程管理器功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager

def test_course_manager():
    """测试课程管理器功能"""
    print("🧪 测试课程管理器功能")
    print("=" * 50)

    # 1. 初始化
    print("📋 1. 初始化组件...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)
    print("   ✅ 组件初始化完成")

    # 2. 测试获取课程
    print("\n📋 2. 测试从本地获取课程...")
    course_manager.load_courses()
    courses = course_manager.get_all_courses()
    print(f"   本地课程数量: {len(courses)}")

    if courses:
        print(f"   示例课程: {courses[0].course_name}")

    # 3. 测试课程统计
    print("\n📋 3. 测试课程统计...")
    stats = course_manager.get_statistics()
    print(f"   统计信息: {stats}")

    # 4. 测试课程搜索
    print("\n📋 4. 测试课程搜索...")
    if courses:
        first_course_name = courses[0].course_name
        search_keyword = first_course_name.split()[0] if first_course_name else "课程"
        results = course_manager.search_courses(search_keyword)
        print(f"   搜索关键词: {search_keyword}")
        print(f"   搜索结果数量: {len(results)}")

    # 5. 测试按类型获取课程
    print("\n📋 5. 测试按类型获取课程...")
    required_courses = course_manager.get_required_courses()
    elective_courses = course_manager.get_elective_courses()
    print(f"   必修课程: {len(required_courses)}")
    print(f"   选修课程: {len(elective_courses)}")

    # 6. 测试从API获取课程（需要登录）
    print("\n📋 6. 测试从API获取课程...")
    try:
        # 先登录
        login_success = login_manager.login_sync()
        if login_success:
            print("   登录成功，开始获取课程...")
            fetch_success = course_manager.fetch_courses_sync()
            if fetch_success:
                new_courses = course_manager.get_all_courses()
                print(f"   ✅ API获取成功，课程数量: {len(new_courses)}")
            else:
                print("   ❌ API获取失败")
        else:
            print("   ⚠️ 登录失败，跳过API测试")
    except Exception as e:
        print(f"   ❌ API测试出错: {e}")

    print("\n🎉 课程管理器功能测试完成！")

if __name__ == "__main__":
    test_course_manager()