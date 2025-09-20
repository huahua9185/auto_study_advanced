#!/usr/bin/env python3
"""
快速验证学习修复效果
较短的测试时间但足以验证修复
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path().absolute()))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.learning_engine import LearningEngine

async def test_quick_learning_fix():
    """快速测试学习修复效果"""
    print("⚡ 快速验证学习修复效果")
    print("90秒测试 - 验证持续学习和进度计算")
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

    # 设置简化回调来监控修复
    scenario_count = 0
    progress_count = 0

    def on_progress_update(course, progress):
        nonlocal progress_count
        progress_count += 1
        print(f"   📈 进度: {progress:.1f}% (第{progress_count}次更新)")

    def on_session_start(session):
        print(f"   ▶️ 会话开始")

    def on_session_end(session):
        print(f"   ⏹️ 会话结束: {session.status} - {session.get_duration_str()}")

    # 设置回调
    learning_engine.set_progress_callback(on_progress_update)
    learning_engine.set_session_callbacks(on_session_start, on_session_end)

    # 90秒学习测试
    print(f"\n🎯 开始学习测试（90秒）...")

    try:
        session = learning_engine.learn_course(target_course, 90)

        if session:
            print(f"\n📊 学习结果:")
            print(f"   状态: {session.status}")
            print(f"   时长: {session.get_duration_str()}")
            print(f"   进度: {session.initial_progress:.1f}% → {session.final_progress:.1f}%")

            # 分析学习日志
            scenario_logs = [log for log in session.logs if '执行学习场景' in log]
            progress_logs = [log for log in session.logs if '📈' in log]
            submit_logs = [log for log in session.logs if 'SCORM进度提交成功' in log]

            print(f"\n📈 修复验证:")
            print(f"   学习场景数: {len(scenario_logs)} (修复前只有4个)")
            print(f"   进度检查数: {len(progress_logs)}")
            print(f"   提交成功数: {len(submit_logs)}")
            print(f"   回调触发数: {progress_count}")

            if len(scenario_logs) > 4:
                print(f"   ✅ 时间修复成功！执行了 {len(scenario_logs)} 个场景")
            else:
                print(f"   ⚠️ 可能需要更长时间才能看到效果")

            if progress_count > 0:
                print(f"   ✅ 进度回调修复成功！触发了 {progress_count} 次更新")
            else:
                print(f"   ❌ 进度回调可能还有问题")

            # 显示最后几条关键日志
            print(f"\n📝 最后5条关键日志:")
            key_logs = [log for log in session.logs if any(keyword in log for keyword in
                       ['学习场景', '📈', '播放位置', '学习会话完成', '执行场景数'])]

            for i, log in enumerate(key_logs[-5:], 1):
                print(f"   {i}. {log}")

        else:
            print("❌ 学习会话创建失败")

    except Exception as e:
        print(f"❌ 学习过程异常: {e}")

    # 清理
    await login_manager.logout()
    print("\n✅ 快速测试完成!")

if __name__ == "__main__":
    asyncio.run(test_quick_learning_fix())