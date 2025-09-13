#!/usr/bin/env python3
"""
测试智能学习系统 - 验证完整的API学习流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from src.smart_learning_manager import SmartLearningManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

def test_single_course_study():
    """测试单门课程学习"""
    print("🧪 测试模式：单门课程学习")

    try:
        with SmartLearningManager() as manager:
            # 初始化系统
            if not manager.initialize():
                print("❌ 系统初始化失败")
                return

            # 获取课程列表
            courses = manager.get_all_courses()
            incomplete_courses = manager.filter_incomplete_courses(courses)

            if not incomplete_courses:
                print("🎉 所有课程都已完成！")
                return

            # 选择第一门未完成的课程进行测试
            test_course = incomplete_courses[0]
            print(f"\n🎯 测试课程: {test_course.get('course_name', 'Unknown')}")
            print(f"当前进度: {test_course.get('progress', 0)}%")

            # 开始学习（使用高倍速进行快速测试）
            result = manager.study_single_course(test_course, speed_multiplier=10.0)

            if result.success:
                print(f"✅ 测试成功！课程学习完成")
                print(f"学习时长: {result.duration_minutes} 分钟")
                print(f"完成率: {result.completion_rate:.1%}")
            else:
                print(f"❌ 测试失败: {result.error_message}")

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

def test_batch_study():
    """测试批量学习"""
    print("🧪 测试模式：批量学习 (限制3门课程)")

    try:
        with SmartLearningManager() as manager:
            # 初始化系统
            if not manager.initialize():
                print("❌ 系统初始化失败")
                return

            # 批量学习（限制课程数量和使用高倍速）
            results = manager.batch_auto_study(
                speed_multiplier=8.0,  # 高倍速测试
                max_courses=3,         # 限制3门课程
                course_types=['elective']  # 只学习选修课
            )

            if results:
                success_count = sum(1 for r in results if r.success)
                print(f"✅ 批量测试完成: {success_count}/{len(results)} 门课程成功")
            else:
                print("ℹ️ 没有需要学习的课程")

    except Exception as e:
        print(f"❌ 批量测试异常: {e}")
        import traceback
        traceback.print_exc()

def test_interactive_mode():
    """测试交互模式"""
    print("🧪 测试模式：交互式学习")

    try:
        with SmartLearningManager() as manager:
            # 初始化系统
            if not manager.initialize():
                print("❌ 系统初始化失败")
                return

            print("✅ 系统初始化成功，进入交互模式...")
            print("📝 提示：选择 '1' 查看课程列表，然后选择 '5' 退出")

            # 启动交互模式
            manager.interactive_study_mode()

    except Exception as e:
        print(f"❌ 交互模式测试异常: {e}")

def main():
    """主测试函数"""
    print("🚀 智能学习系统测试")
    print("="*80)
    print("测试选项:")
    print("1. 单门课程学习测试")
    print("2. 批量学习测试 (3门课程)")
    print("3. 交互模式测试")
    print("4. 完整系统演示")
    print("="*80)

    try:
        choice = input("请选择测试模式 (1-4): ").strip()

        if choice == '1':
            test_single_course_study()
        elif choice == '2':
            test_batch_study()
        elif choice == '3':
            test_interactive_mode()
        elif choice == '4':
            print("🎬 完整系统演示")
            test_interactive_mode()
        else:
            print("❌ 无效选择")

    except KeyboardInterrupt:
        print("\n👋 用户取消测试")
    except Exception as e:
        print(f"❌ 测试程序异常: {e}")

if __name__ == "__main__":
    main()