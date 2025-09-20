#!/usr/bin/env python3
"""
测试带登录的自动学习功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.learning_engine import LearningEngine

async def test_learning_with_login():
    """测试带登录的学习功能"""
    print("🧪 测试带登录的自动学习功能")
    print("=" * 60)

    # 1. 初始化系统组件
    print("📋 1. 初始化系统组件...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)
    learning_engine = LearningEngine(config_manager, course_manager)

    await course_manager.initialize()

    # 2. 执行登录
    print("\n📋 2. 执行登录...")
    username = "640302198607120020"
    password = "My2062660"

    print(f"   登录用户: {username}")
    success = await login_manager.login(username, password, save_credentials=True)

    if success:
        print("   ✅ 登录成功")
    else:
        print("   ❌ 登录失败，无法测试学习功能")
        return

    # 3. 获取课程数据
    print("\n📋 3. 获取课程数据...")
    courses = course_manager.get_all_courses()
    print(f"   本地课程数量: {len(courses)}")

    if len(courses) == 0:
        print("   从服务器刷新课程数据...")
        success = course_manager.refresh_courses()
        if success:
            courses = course_manager.get_all_courses()
            print(f"   获取到 {len(courses)} 门课程")
        else:
            print("   ❌ 无法获取课程数据")
            return

    # 4. 获取学习队列
    print("\n📋 4. 获取学习队列...")
    learning_queue = learning_engine.get_learning_queue()
    print(f"   学习队列数量: {len(learning_queue)}")

    if not learning_queue:
        print("   🎉 所有课程已完成！")
        return

    # 显示前5门课程
    print("   前5门待学习课程:")
    for i, course in enumerate(learning_queue[:5]):
        course_type = "必修" if course.course_type == 'required' else "选修"
        print(f"     {i+1}. {course.course_name} ({course_type}) - {course.progress:.1f}%")

    # 5. 测试单个课程学习
    print("\n📋 5. 测试单个课程学习...")
    test_course = learning_queue[0]
    print(f"   测试课程: {test_course.course_name}")
    print(f"   初始进度: {test_course.progress:.1f}%")
    print(f"   课程ID: {test_course.course_id}")
    print(f"   用户课程ID: {test_course.user_course_id}")

    # 设置学习回调
    def on_progress_update(course, progress):
        print(f"     📈 进度更新: {course.course_name} - {progress:.1f}%")

    def on_session_start(session):
        print(f"     ▶️ 开始学习: {session.course.course_name}")

    def on_session_end(session):
        duration = session.get_duration_str()
        progress_gained = session.get_progress_gained()
        print(f"     ⏹️ 学习结束: {session.course.course_name} - 用时{duration}, 进度+{progress_gained:.1f}%")

    learning_engine.set_progress_callback(on_progress_update)
    learning_engine.set_session_callbacks(on_session_start, on_session_end)

    try:
        # 开始学习（2分钟测试）
        print("   开始学习（2分钟测试）...")
        session = learning_engine.learn_course(test_course, 120)  # 120秒

        # 显示学习结果
        if session:
            print(f"   ✅ 学习会话完成")
            print(f"   最终进度: {session.final_progress:.1f}%")
            print(f"   进度增长: +{session.get_progress_gained():.1f}%")
            print(f"   学习时长: {session.get_duration_str()}")
            print(f"   学习状态: {session.status}")
            print(f"   日志数量: {len(session.logs)}")

            # 显示学习日志
            if session.logs:
                print("   学习日志:")
                for i, log in enumerate(session.logs):
                    print(f"     {i+1:2d}. {log}")
        else:
            print("   ❌ 学习会话失败")

    except Exception as e:
        print(f"   ❌ 学习过程异常: {e}")

    # 6. 显示学习统计
    print("\n📋 6. 学习统计...")
    stats = learning_engine.get_statistics_summary()
    print(f"   总学习会话: {stats['total_sessions']}")
    print(f"   今日学习会话: {stats['today_sessions']}")
    print(f"   总学习时间: {stats['total_learning_time']}")
    print(f"   完成课程数: {stats['total_courses_completed']}")
    print(f"   总进度增长: +{stats['total_progress_gained']:.1f}%")
    print(f"   学习成功率: {stats['success_rate']:.1f}%")

    # 7. 清理资源
    print("\n📋 7. 清理资源...")
    await login_manager.logout()
    print("   ✅ 清理完成")

    print("\n🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_learning_with_login())