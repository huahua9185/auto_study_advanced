#!/usr/bin/env python3
"""
验证控制台学习功能修复
测试修复后的进度回调和状态报告
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path().absolute()))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.learning_engine import LearningEngine

async def test_console_fix():
    """测试修复后的控制台学习功能"""
    print("🔧 测试控制台学习功能修复")
    print("验证进度回调和状态报告是否正常")
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

    # 获取目标课程
    print("\n📚 查找目标课程...")
    courses = course_manager.get_all_courses()
    target_course = None
    for course in courses:
        if str(course.user_course_id) == '1988341':
            target_course = course
            break

    if not target_course:
        print("❌ 未找到目标课程")
        return

    print(f"✅ 找到课程: {target_course.course_name}")
    print(f"   初始进度: {target_course.progress}%")

    # 设置回调函数来验证修复
    progress_updates = []
    session_events = []

    def on_progress_update(course, progress):
        update_msg = f"📈 进度更新: {progress:.1f}%"
        progress_updates.append(update_msg)
        print(f"   {update_msg}")

    def on_session_start(session):
        start_msg = f"▶️ 会话开始: {session.course.course_name}"
        session_events.append(start_msg)
        print(f"   {start_msg}")

    def on_session_end(session):
        end_msg = f"⏹️ 会话结束: {session.status} - 用时 {session.get_duration_str()}"
        session_events.append(end_msg)
        print(f"   {end_msg}")

    def on_course_complete(course):
        complete_msg = f"🎉 课程完成: {course.course_name}"
        session_events.append(complete_msg)
        print(f"   {complete_msg}")

    # 设置回调
    learning_engine.set_progress_callback(on_progress_update)
    learning_engine.set_session_callbacks(on_session_start, on_session_end)
    learning_engine.set_course_complete_callback(on_course_complete)

    # 执行学习（1分钟测试）
    print(f"\n🎯 开始学习测试（1分钟）...")
    print(f"验证是否有进度回调和正确的状态报告")

    try:
        session = learning_engine.learn_course(target_course, 60)  # 1分钟测试

        if session:
            print(f"\n📊 学习会话结果:")
            print(f"   状态: {session.status}")
            print(f"   最终进度: {session.final_progress:.1f}%")
            print(f"   进度增长: +{session.get_progress_gained():.1f}%")
            print(f"   学习时长: {session.get_duration_str()}")

            print(f"\n📝 验证修复结果:")
            print(f"   进度更新次数: {len(progress_updates)}")
            print(f"   会话事件数量: {len(session_events)}")

            if progress_updates:
                print(f"\n✅ 进度回调修复成功！接收到 {len(progress_updates)} 次进度更新:")
                for i, update in enumerate(progress_updates, 1):
                    print(f"      {i}. {update}")
            else:
                print(f"\n❌ 进度回调修复失败：没有接收到进度更新")

            if session_events:
                print(f"\n✅ 会话事件修复成功！接收到 {len(session_events)} 个事件:")
                for i, event in enumerate(session_events, 1):
                    print(f"      {i}. {event}")
            else:
                print(f"\n❌ 会话事件修复失败：没有接收到会话事件")

            # 验证状态
            if session.status == 'completed':
                print(f"\n✅ 状态报告修复成功：会话正常完成")
            elif session.status == 'failed':
                print(f"\n⚠️ 会话失败，但状态报告正常")
            elif session.status == 'interrupted':
                print(f"\n❌ 状态报告修复失败：仍显示为中断状态")
            else:
                print(f"\n❓ 未知状态: {session.status}")

            # 显示关键学习日志
            print(f"\n📝 关键学习日志:")
            key_logs = [log for log in session.logs if any(keyword in log for keyword in
                       ['获取课程清单', 'SCORM播放器', '进度更新', '失败', '异常', '成功', '📈'])]

            for i, log in enumerate(key_logs, 1):
                print(f"   {i:2d}. {log}")

        else:
            print("❌ 学习会话创建失败")

    except Exception as e:
        print(f"❌ 学习过程异常: {e}")
        import traceback
        traceback.print_exc()

    # 清理
    await login_manager.logout()
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_console_fix())