#!/usr/bin/env python3
"""
测试自动学习引擎功能
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

async def test_learning_engine():
    """测试学习引擎"""
    print("🧪 测试自动学习引擎功能")
    print("=" * 60)

    # 1. 初始化系统组件
    print("📋 1. 初始化系统组件...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)
    learning_engine = LearningEngine(config_manager, course_manager)

    await course_manager.initialize()

    # 2. 检查课程数据
    print("\n📋 2. 检查课程数据...")
    courses = course_manager.get_all_courses()
    print(f"   本地课程数量: {len(courses)}")

    if len(courses) == 0:
        print("   没有课程数据，获取最新数据...")
        success = course_manager.refresh_courses()
        if success:
            courses = course_manager.get_all_courses()
            print(f"   获取到 {len(courses)} 门课程")
        else:
            print("   ❌ 无法获取课程数据")
            return

    # 3. 测试学习队列
    print("\n📋 3. 测试学习队列...")
    learning_queue = learning_engine.get_learning_queue()
    print(f"   学习队列数量: {len(learning_queue)}")

    if learning_queue:
        print("   前5门待学习课程:")
        for i, course in enumerate(learning_queue[:5]):
            course_type = "必修" if course.course_type == 'required' else "选修"
            print(f"     {i+1}. {course.course_name} ({course_type}) - {course.progress:.1f}%")

    # 4. 测试学习建议
    print("\n📋 4. 测试学习建议...")
    recommendations = learning_engine.get_learning_recommendations()
    print(f"   总课程数: {recommendations['total_courses']}")
    print(f"   完成率: {recommendations['completion_rate']:.1f}%")
    print(f"   平均进度: {recommendations['average_progress']:.1f}%")
    print(f"   未完成必修课: {recommendations['required_incomplete']}")
    print(f"   未完成选修课: {recommendations['elective_incomplete']}")
    print(f"   下一步建议: {recommendations['next_action']}")

    estimated_time = recommendations['estimated_time']
    print(f"   预计学习时间: {estimated_time['total_hours']}小时{estimated_time['remaining_minutes']}分钟")

    # 5. 测试学习会话创建
    print("\n📋 5. 测试学习会话...")
    if learning_queue:
        test_course = learning_queue[0]
        print(f"   测试课程: {test_course.course_name}")

        # 创建学习会话
        success = learning_engine.start_learning_session(test_course)
        if success:
            print("   ✅ 学习会话创建成功")
            current_session = learning_engine.current_session
            print(f"   会话状态: {current_session.status}")
            print(f"   初始进度: {current_session.initial_progress:.1f}%")

            # 停止会话
            learning_engine.stop_learning_session("测试完成")
            print("   ✅ 学习会话已停止")
        else:
            print("   ❌ 学习会话创建失败")

    # 6. 测试学习统计
    print("\n📋 6. 测试学习统计...")
    stats = learning_engine.get_statistics_summary()
    print(f"   总学习会话: {stats['total_sessions']}")
    print(f"   今日学习会话: {stats['today_sessions']}")
    print(f"   总学习时间: {stats['total_learning_time']}")
    print(f"   完成课程数: {stats['total_courses_completed']}")
    print(f"   学习成功率: {stats['success_rate']:.1f}%")
    print(f"   引擎状态: {stats['current_status']}")

    # 7. 测试配置设置
    print("\n📋 7. 测试配置设置...")
    print("   学习配置参数:")
    print(f"   - 单课程最大时长: {config_manager.get('learning.max_duration_per_course', 1800)//60}分钟")
    print(f"   - 总学习时长: {config_manager.get('learning.max_total_time', 7200)//60}分钟")
    print(f"   - 课程间休息: {config_manager.get('learning.rest_between_courses', 5)}秒")
    print(f"   - 进度检查间隔: {config_manager.get('learning.progress_check_interval', 30)}秒")

    # 8. 模拟短时间学习测试
    print("\n📋 8. 模拟短时间学习测试...")
    if learning_queue and learning_queue[0].progress < 100:
        test_course = learning_queue[0]
        print(f"   开始模拟学习: {test_course.course_name}")
        print(f"   初始进度: {test_course.progress:.1f}%")

        try:
            # 设置短时间学习 (60秒)
            session = learning_engine.learn_course(test_course, 60)

            if session:
                print(f"   ✅ 学习完成")
                print(f"   最终进度: {session.final_progress:.1f}%")
                print(f"   进度增长: +{session.get_progress_gained():.1f}%")
                print(f"   学习时长: {session.get_duration_str()}")
                print(f"   学习状态: {session.status}")
                print(f"   日志数量: {len(session.logs)}")

                # 显示部分日志
                if session.logs:
                    print("   最新日志:")
                    for log in session.logs[-3:]:
                        print(f"     • {log}")
            else:
                print("   ❌ 学习失败")

        except Exception as e:
            print(f"   ❌ 学习过程异常: {e}")

    print("\n🎉 学习引擎测试完成!")

if __name__ == "__main__":
    asyncio.run(test_learning_engine())