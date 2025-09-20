#!/usr/bin/env python3
"""
测试学习时长修复
验证学习能否持续更长时间并正确显示进度
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path().absolute()))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.learning_engine import LearningEngine

async def test_learning_duration():
    """测试学习时长修复"""
    print("🕐 测试学习时长修复")
    print("验证学习能否持续更长时间并正确计算进度")
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

    # 获取目标课程（选择一个未完成的课程）
    print("\n📚 查找未完成的课程...")
    courses = course_manager.get_all_courses()
    target_courses = [c for c in courses if c.progress < 100.0 and c.status != 'completed']

    if not target_courses:
        print("❌ 未找到需要学习的课程")
        return

    target_course = target_courses[0]  # 选择第一个未完成的课程
    print(f"✅ 选择课程: {target_course.course_name}")
    print(f"   课程ID: {target_course.course_id}")
    print(f"   用户课程ID: {target_course.user_course_id}")
    print(f"   初始进度: {target_course.progress}%")

    # 设置回调函数来监控修复效果
    progress_updates = []
    learning_events = []

    def on_progress_update(course, progress):
        update = f"📈 {progress:.1f}%"
        progress_updates.append(progress)
        print(f"   {update}")

    def on_session_start(session):
        event = f"▶️ 开始: {session.course.course_name}"
        learning_events.append(event)
        print(f"   {event}")

    def on_session_end(session):
        event = f"⏹️ 结束: {session.status} - {session.get_duration_str()}"
        learning_events.append(event)
        print(f"   {event}")

    # 设置回调
    learning_engine.set_progress_callback(on_progress_update)
    learning_engine.set_session_callbacks(on_session_start, on_session_end)

    # 执行较长时间的学习测试（3分钟）
    print(f"\n🎯 开始学习测试（3分钟）...")
    print(f"验证是否能持续学习并正确计算进度")

    try:
        session = learning_engine.learn_course(target_course, 180)  # 3分钟测试

        if session:
            print(f"\n📊 学习会话结果:")
            print(f"   状态: {session.status}")
            print(f"   最终进度: {session.final_progress:.1f}%")
            print(f"   进度增长: +{session.get_progress_gained():.1f}%")
            print(f"   学习时长: {session.get_duration_str()}")

            print(f"\n📝 修复验证结果:")
            print(f"   进度更新次数: {len(progress_updates)}")
            print(f"   学习事件数量: {len(learning_events)}")

            if progress_updates:
                progress_growth = max(progress_updates) - min(progress_updates) if len(progress_updates) > 1 else 0
                print(f"   进度变化范围: {min(progress_updates):.1f}% - {max(progress_updates):.1f}%")
                print(f"   最大进度增长: +{progress_growth:.1f}%")

                if progress_growth > 0:
                    print(f"\n✅ 进度计算修复成功！检测到进度增长")
                else:
                    print(f"\n⚠️ 进度没有变化，可能课程已完成或需要更长学习时间")
            else:
                print(f"\n❌ 没有接收到进度更新")

            # 分析学习日志
            print(f"\n📝 学习过程分析:")
            scenario_logs = [log for log in session.logs if '执行学习场景' in log]
            progress_logs = [log for log in session.logs if '📈' in log]
            submit_logs = [log for log in session.logs if 'SCORM进度提交成功' in log]

            print(f"   执行的学习场景: {len(scenario_logs)}")
            print(f"   进度检查次数: {len(progress_logs)}")
            print(f"   成功提交次数: {len(submit_logs)}")

            if len(scenario_logs) > 4:
                print(f"   ✅ 学习场景修复成功！执行了 {len(scenario_logs)} 个场景（超过原来的4个）")
            else:
                print(f"   ⚠️ 学习场景可能未完全修复，只执行了 {len(scenario_logs)} 个场景")

            # 显示关键学习事件
            print(f"\n📋 关键学习事件:")
            key_logs = [log for log in session.logs if any(keyword in log for keyword in
                       ['学习场景', '📈', '播放位置', '学习会话完成', '执行场景数'])]

            for i, log in enumerate(key_logs[-10:], 1):  # 显示最后10条关键日志
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
    asyncio.run(test_learning_duration())