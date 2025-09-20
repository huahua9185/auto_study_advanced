#!/usr/bin/env python3
"""
快速批量学习测试
较短的测试来验证批量学习修复
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path().absolute()))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.learning_engine import LearningEngine

async def test_quick_batch_learning():
    """快速批量学习测试"""
    print("⚡ 快速批量学习测试")
    print("每门课程30秒，验证批量学习修复")
    print("=" * 50)

    # 初始化组件
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)
    learning_engine = LearningEngine(config_manager, course_manager)

    await course_manager.initialize()

    # 登录
    print("🔐 执行登录...")
    success = await login_manager.login("640302198607120020", "My2062660", save_credentials=True)
    if not success:
        print("❌ 登录失败")
        return
    print("✅ 登录成功")

    # 获取2门需要学习的课程
    print("\n📚 查找课程...")
    courses = course_manager.get_all_courses()
    target_courses = [c for c in courses if c.progress < 100.0 and c.status != 'completed'][:2]

    if len(target_courses) < 2:
        print("❌ 课程不足")
        return

    print(f"✅ 选择 {len(target_courses)} 门课程:")
    for i, course in enumerate(target_courses, 1):
        print(f"   {i}. {course.course_name[:30]}... ({course.progress:.1f}%)")

    # 设置简化回调
    total_progress_updates = 0
    total_session_events = 0

    def on_progress_update(course, progress):
        nonlocal total_progress_updates
        total_progress_updates += 1
        print(f"   📈 {course.course_name[:20]}...: {progress:.1f}%")

    def on_session_start(session):
        nonlocal total_session_events
        total_session_events += 1
        print(f"   ▶️ 开始: {session.course.course_name[:25]}...")

    def on_session_end(session):
        nonlocal total_session_events
        total_session_events += 1
        print(f"   ⏹️ 结束: {session.course.course_name[:20]}... - {session.status}")

    # 设置回调
    learning_engine.set_progress_callback(on_progress_update)
    learning_engine.set_session_callbacks(on_session_start, on_session_end)

    # 批量学习测试（每门课30秒，总共1分钟）
    print(f"\n🎯 开始批量学习（每门课30秒）...")

    try:
        sessions = learning_engine.learn_multiple_courses(
            courses=target_courses,
            max_total_time=60  # 1分钟总时长
        )

        print(f"\n📊 批量学习结果:")
        print(f"   完成课程数: {len(sessions)}")
        print(f"   进度更新次数: {total_progress_updates}")
        print(f"   会话事件次数: {total_session_events}")

        # 快速分析每个会话
        for i, session in enumerate(sessions, 1):
            scenario_logs = [log for log in session.logs if '执行学习场景' in log]
            submit_logs = [log for log in session.logs if 'SCORM进度提交成功' in log]

            print(f"\n   课程 {i}: {session.course.course_name[:25]}...")
            print(f"      状态: {session.status}")
            print(f"      时长: {session.get_duration_str()}")
            print(f"      学习场景: {len(scenario_logs)} (修复前只有4个)")
            print(f"      提交次数: {len(submit_logs)}")

            if len(scenario_logs) > 4:
                print(f"      ✅ 修复生效")
            else:
                print(f"      ⚠️ 需要检查")

        # 总体验证
        successful_courses = [s for s in sessions if s.status == 'completed']
        high_scenario_courses = [s for s in sessions
                               if len([log for log in s.logs if '执行学习场景' in log]) > 4]

        print(f"\n🎯 批量学习修复验证:")
        print(f"   成功完成课程: {len(successful_courses)}/{len(sessions)}")
        print(f"   应用修复课程: {len(high_scenario_courses)}/{len(sessions)}")

        if len(high_scenario_courses) == len(sessions):
            print(f"   ✅ 批量学习修复完全成功！")
        elif len(high_scenario_courses) > 0:
            print(f"   ✅ 批量学习修复部分成功")
        else:
            print(f"   ❌ 批量学习修复可能失败")

    except Exception as e:
        print(f"❌ 批量学习异常: {e}")

    # 清理
    await login_manager.logout()
    print("\n✅ 快速批量学习测试完成!")

if __name__ == "__main__":
    asyncio.run(test_quick_batch_learning())