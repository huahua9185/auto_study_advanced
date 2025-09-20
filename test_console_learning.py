#!/usr/bin/env python3
"""
测试控制台接口的学习功能
模拟控制台接口调用learning_engine.learn_course()
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path().absolute()))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.learning_engine import LearningEngine

async def test_console_learning():
    """测试控制台接口的学习功能"""
    print("🧪 测试控制台接口的学习功能")
    print("=" * 60)

    # 初始化组件（模拟控制台接口的初始化）
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

    # 获取目标课程（模拟控制台接口选择课程）
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
    print(f"   course_id: {target_course.course_id} (类型: {type(target_course.course_id)})")
    print(f"   user_course_id: {target_course.user_course_id} (类型: {type(target_course.user_course_id)})")
    print(f"   初始进度: {target_course.progress}%")

    # 设置回调函数
    def on_progress_update(course, progress):
        print(f"   📈 进度更新: {progress:.1f}%")

    def on_session_start(session):
        print(f"   ▶️ 会话开始: {session.course.course_name}")

    def on_session_end(session):
        print(f"   ⏹️ 会话结束: 用时 {session.get_duration_str()}")

    learning_engine.set_progress_callback(on_progress_update)
    learning_engine.set_session_callbacks(on_session_start, on_session_end)

    # 调用控制台接口使用的学习方法（同步版本）
    print(f"\n🎯 调用learning_engine.learn_course()（控制台接口使用的方法）...")
    print(f"   这是同步版本，内部调用_learn_course_async")

    try:
        # 这就是控制台接口第608行调用的方法
        session = learning_engine.learn_course(target_course, 1)  # 1分钟测试

        if session:
            print(f"\n📊 学习会话结果:")
            print(f"   状态: {session.status}")
            print(f"   最终进度: {session.final_progress:.1f}%")
            print(f"   进度增长: +{session.get_progress_gained():.1f}%")
            print(f"   学习时长: {session.get_duration_str()}")

            # 显示关键日志
            print(f"\n📝 关键学习日志:")
            key_logs = [log for log in session.logs if any(keyword in log for keyword in
                       ['获取课程清单', 'SCORM播放器', 'SCORM进度提交', '失败', '异常', '成功'])]

            for i, log in enumerate(key_logs, 1):
                print(f"   {i:2d}. {log}")

            # 检查错误
            error_logs = [log for log in session.logs if '失败' in log or '异常' in log or '错误' in log]
            if error_logs:
                print(f"\n⚠️ 发现 {len(error_logs)} 条错误日志:")
                for log in error_logs:
                    print(f"   ❌ {log}")
            else:
                print(f"\n✅ 没有发现错误日志！")

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
    asyncio.run(test_console_learning())