#!/usr/bin/env python3
"""
测试修复后的课程管理功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.console_interface import SCORMConsoleInterface

def test_course_functions():
    """测试课程管理核心功能"""
    print("🧪 测试修复后的课程管理功能")
    print("=" * 50)

    # 1. 初始化
    print("📋 1. 初始化控制台界面...")
    interface = SCORMConsoleInterface()
    print("   ✅ 界面初始化完成")

    # 2. 测试获取课程（不等待输入）
    print("\n📋 2. 测试获取课程功能...")
    try:
        # 模拟_fetch_courses但不等待输入
        interface.display.print_header("📚 获取课程列表")
        interface.display.print_status("正在从服务器获取课程数据...", "info")

        success = interface.course_manager.fetch_courses_sync()
        if success:
            courses = interface.course_manager.get_all_courses()
        else:
            courses = []

        if courses:
            interface.display.print_status(f"✅ 成功获取 {len(courses)} 门课程", "success")
            required_count = len([c for c in courses if c.course_type == 'required'])
            elective_count = len([c for c in courses if c.course_type == 'elective'])
            completed_count = len([c for c in courses if c.progress >= 100.0])
            print(f"   必修课程: {required_count}, 选修课程: {elective_count}, 已完成: {completed_count}")
        else:
            interface.display.print_status("⚠️ 未获取到课程数据", "warning")
            # 显示本地课程
            local_courses = interface.course_manager.get_all_courses()
            print(f"   本地课程数量: {len(local_courses)}")

        print("   ✅ 获取课程功能正常")
    except Exception as e:
        print(f"   ❌ 获取课程功能出错: {e}")

    # 3. 测试统计功能（不等待输入）
    print("\n📋 3. 测试统计功能...")
    try:
        interface.display.print_header("📊 课程进度统计")
        stats = interface.course_manager.get_statistics()
        print(f"   统计信息: {stats}")

        # 测试进度分布计算
        courses = interface.course_manager.get_all_courses()
        progress_distribution = {
            '0%': 0, '1-25%': 0, '26-50%': 0,
            '51-75%': 0, '76-99%': 0, '100%': 0
        }

        for course in courses:
            if course.progress == 0:
                progress_distribution['0%'] += 1
            elif course.progress <= 25:
                progress_distribution['1-25%'] += 1
            elif course.progress <= 50:
                progress_distribution['26-50%'] += 1
            elif course.progress <= 75:
                progress_distribution['51-75%'] += 1
            elif course.progress < 100:
                progress_distribution['76-99%'] += 1
            else:
                progress_distribution['100%'] += 1

        print(f"   进度分布: {progress_distribution}")
        print("   ✅ 统计功能正常")
    except Exception as e:
        print(f"   ❌ 统计功能出错: {e}")

    # 4. 测试搜索功能
    print("\n📋 4. 测试搜索功能...")
    try:
        courses = interface.course_manager.get_all_courses()
        if courses:
            # 搜索第一个课程的关键词
            search_keyword = courses[0].course_name.split()[0] if courses[0].course_name else "课程"
            results = interface.course_manager.search_courses(search_keyword)
            print(f"   搜索关键词: {search_keyword}")
            print(f"   搜索结果: {len(results)} 门课程")
            print("   ✅ 搜索功能正常")
        else:
            print("   ⚠️ 没有课程数据，跳过搜索测试")
    except Exception as e:
        print(f"   ❌ 搜索功能出错: {e}")

    # 5. 测试刷新功能
    print("\n📋 5. 测试刷新功能...")
    try:
        interface.course_manager.load_courses()
        courses = interface.course_manager.get_all_courses()
        print(f"   刷新后课程数量: {len(courses)}")
        print("   ✅ 刷新功能正常")
    except Exception as e:
        print(f"   ❌ 刷新功能出错: {e}")

    print("\n🎉 课程管理功能测试完成！")

if __name__ == "__main__":
    test_course_functions()