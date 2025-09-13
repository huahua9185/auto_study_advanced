#!/usr/bin/env python3
"""
API学习系统演示 - 自动化测试单门课程学习流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from src.smart_learning_manager import SmartLearningManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def demo_api_learning_system():
    """演示API学习系统"""
    print("🎬 API学习系统演示")
    print("="*80)

    try:
        # 创建智能学习管理器
        manager = SmartLearningManager()

        # 初始化系统
        print("🚀 正在初始化系统...")
        if not manager.initialize():
            print("❌ 系统初始化失败")
            return

        print("✅ 系统初始化成功")

        # 获取课程信息
        print("\n📚 获取课程信息...")
        courses = manager.get_all_courses()
        print(f"📊 发现课程: 必修课 {len(courses['required'])} 门, 选修课 {len(courses['elective'])} 门")

        # 过滤未完成课程
        incomplete_courses = manager.filter_incomplete_courses(courses, progress_threshold=100.0)

        if not incomplete_courses:
            print("🎉 恭喜！所有课程都已完成")
            return

        print(f"🎯 发现 {len(incomplete_courses)} 门未完成课程")

        # 选择第一门未完成的课程进行演示
        demo_course = incomplete_courses[0]
        course_name = demo_course.get('course_name', 'Unknown')
        current_progress = demo_course.get('progress', 0)

        print(f"\n🎬 演示课程: {course_name}")
        print(f"📊 当前进度: {current_progress}%")
        print(f"⚡ 使用倍速: 10x (演示模式)")

        # 开始学习
        print(f"\n{'='*80}")
        print("🚀 开始API学习演示...")
        print(f"{'='*80}")

        result = manager.study_single_course(demo_course, speed_multiplier=10.0)

        # 显示结果
        print(f"\n{'='*80}")
        if result.success:
            print("✅ 演示成功！课程学习完成")
            print(f"📚 课程名称: {result.course_name}")
            print(f"⏱️ 学习时长: {result.duration_minutes} 分钟")
            print(f"📈 完成率: {result.completion_rate:.1%}")
            print(f"🆔 课程ID: {result.course_id}")
            print(f"👤 用户课程ID: {result.user_course_id}")
        else:
            print("❌ 演示失败")
            print(f"❗ 错误信息: {result.error_message}")
        print(f"{'='*80}")

        print("\n🎯 API学习系统演示完成！")
        print("\n💡 系统特点:")
        print("   • 绕过前端UI，直接调用后端API")
        print("   • 实时进度跟踪和上报")
        print("   • 支持倍速学习")
        print("   • 完整的SCORM学习流程模拟")
        print("   • 智能错误处理和重试机制")

    except Exception as e:
        print(f"❌ 演示过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        try:
            manager.cleanup()
        except:
            pass

if __name__ == "__main__":
    demo_api_learning_system()