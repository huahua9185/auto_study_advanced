#!/usr/bin/env python3
"""
测试批量学习修复效果
验证批量学习是否也应用了单课程学习的修复
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path().absolute()))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.learning_engine import LearningEngine

async def test_batch_learning_fix():
    """测试批量学习修复效果"""
    print("📚 测试批量学习修复效果")
    print("验证批量学习是否应用了单课程学习的修复")
    print("=" * 60)

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

    # 获取多个需要学习的课程
    print("\n📚 查找需要学习的课程...")
    courses = course_manager.get_all_courses()

    # 选择几个进度不是100%的课程
    target_courses = []
    for course in courses:
        if course.progress < 100.0 and course.status != 'completed':
            target_courses.append(course)
        if len(target_courses) >= 2:  # 只选2门课程进行测试
            break

    if len(target_courses) < 2:
        print("❌ 找不到足够的未完成课程进行批量学习测试")
        return

    print(f"✅ 选择了 {len(target_courses)} 门课程进行批量学习测试:")
    for i, course in enumerate(target_courses, 1):
        print(f"   {i}. {course.course_name} - 当前进度: {course.progress}%")

    # 设置回调函数来监控批量学习
    progress_updates = []
    session_events = []

    def on_progress_update(course, progress):
        update = f"📈 {course.course_name}: {progress:.1f}%"
        progress_updates.append(update)
        print(f"   {update}")

    def on_session_start(session):
        event = f"▶️ 开始: {session.course.course_name}"
        session_events.append(event)
        print(f"   {event}")

    def on_session_end(session):
        event = f"⏹️ 结束: {session.course.course_name} - {session.status} - {session.get_duration_str()}"
        session_events.append(event)
        print(f"   {event}")

    # 设置回调
    learning_engine.set_progress_callback(on_progress_update)
    learning_engine.set_session_callbacks(on_session_start, on_session_end)

    # 执行批量学习测试（每门课程60秒，总共2分钟）
    print(f"\n🎯 开始批量学习测试...")
    print(f"每门课程学习60秒，总时长约2分钟")

    try:
        # 使用学习引擎的批量学习方法
        sessions = learning_engine.learn_multiple_courses(
            courses=target_courses,
            max_total_time=120  # 2分钟总时长
        )

        print(f"\n📊 批量学习结果:")
        print(f"   完成课程数: {len(sessions)}")
        print(f"   总进度更新次数: {len(progress_updates)}")
        print(f"   总会话事件次数: {len(session_events)}")

        # 分析每个学习会话
        for i, session in enumerate(sessions, 1):
            print(f"\n   课程 {i}: {session.course.course_name}")
            print(f"      状态: {session.status}")
            print(f"      时长: {session.get_duration_str()}")
            print(f"      进度: {session.initial_progress:.1f}% → {session.final_progress:.1f}%")

            # 分析学习日志
            scenario_logs = [log for log in session.logs if '执行学习场景' in log]
            submit_logs = [log for log in session.logs if 'SCORM进度提交成功' in log]

            print(f"      学习场景数: {len(scenario_logs)}")
            print(f"      提交成功数: {len(submit_logs)}")

            if len(scenario_logs) > 4:
                print(f"      ✅ 修复生效：执行了 {len(scenario_logs)} 个场景（超过原来的4个）")
            else:
                print(f"      ⚠️ 可能需要检查：只执行了 {len(scenario_logs)} 个场景")

        # 检查批量学习特有的功能
        print(f"\n📋 批量学习验证:")
        completed_sessions = [s for s in sessions if s.status == 'completed']
        failed_sessions = [s for s in sessions if s.status == 'failed']

        print(f"   成功完成: {len(completed_sessions)}/{len(sessions)} 门课程")
        print(f"   失败课程: {len(failed_sessions)} 门")

        if len(completed_sessions) == len(sessions):
            print(f"   ✅ 批量学习修复成功！所有课程都正常完成")
        elif len(completed_sessions) > 0:
            print(f"   ✅ 批量学习基本正常，部分课程完成")
        else:
            print(f"   ❌ 批量学习可能存在问题，没有课程成功完成")

        # 显示进度更新统计
        if progress_updates:
            print(f"\n📈 进度更新详情:")
            for update in progress_updates:
                print(f"      {update}")
        else:
            print(f"\n❌ 没有接收到任何进度更新")

    except Exception as e:
        print(f"❌ 批量学习过程异常: {e}")
        import traceback
        traceback.print_exc()

    # 清理
    await login_manager.logout()
    print("\n✅ 批量学习测试完成!")

if __name__ == "__main__":
    asyncio.run(test_batch_learning_fix())