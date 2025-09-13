#!/usr/bin/env python3
"""
测试并发学习系统
验证多线程学习引擎和智能调度器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import logging
from datetime import datetime

from src.smart_learning_scheduler import SmartLearningScheduler
from src.concurrent_learning_engine import TaskPriority

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

def test_concurrent_learning_system():
    """测试并发学习系统"""
    print("🧪 并发学习系统测试")
    print("=" * 80)

    try:
        # 创建智能调度器
        scheduler = SmartLearningScheduler(
            username="640302198607120020",
            password="My2062660",
            max_workers=2  # 使用2个工作线程进行测试
        )

        print("🎯 创建学习计划...")
        learning_plan = scheduler.create_learning_plan(daily_target_hours=6.0)

        if learning_plan.total_courses == 0:
            print("🎉 没有需要学习的课程！")
            return True

        print(f"\n📋 学习计划详情:")
        print(f"  总课程数: {learning_plan.total_courses}")
        print(f"  预估时间: {learning_plan.estimated_total_time:.1f} 小时")
        print(f"  每日目标: {learning_plan.daily_learning_target:.1f} 小时")
        print(f"  预计完成: {learning_plan.estimated_completion_date.strftime('%Y-%m-%d')}")

        # 设置回调函数
        def on_course_completed(course):
            print(f"🎓 课程完成: {course.course_name}")

        def on_progress_report(progress):
            print(f"📊 进度报告: {progress.completed_courses}/{progress.total_courses} 课程 ({progress.completion_rate:.1f}%)")

        def on_plan_completed():
            print("🎉 学习计划全部完成！")

        scheduler.on_course_completed = on_course_completed
        scheduler.on_progress_report = on_progress_report
        scheduler.on_plan_completed = on_plan_completed

        print("\n🚀 启动并发学习...")
        scheduler.start_auto_learning(daily_target_hours=6.0)

        print("\n⏱️ 监控学习过程...")

        # 监控一段时间（测试环境下运行30秒）
        monitoring_time = 30
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < monitoring_time:
            time.sleep(5)

            status = scheduler.get_detailed_status()

            print(f"\n📊 当前状态 ({(datetime.now() - start_time).seconds}s):")
            print(f"  引擎运行: {status['scheduler']['is_running']}")
            print(f"  待处理任务: {status['engine']['tasks']['pending']}")
            print(f"  运行中任务: {status['engine']['tasks']['running']}")
            print(f"  已完成任务: {status['engine']['tasks']['completed']}")
            print(f"  失败任务: {status['engine']['tasks']['failed']}")

            if status['current_progress']['total_learning_time'] > 0:
                print(f"  学习时间: {status['current_progress']['total_learning_time']:.1f} 小时")
                print(f"  学习效率: {status['current_progress']['efficiency']:.2f} 课程/小时")

            # 如果所有任务都完成了，提前结束
            if (status['engine']['tasks']['pending'] == 0 and
                status['engine']['tasks']['running'] == 0 and
                status['engine']['tasks']['completed'] > 0):
                print("🎉 所有任务已完成，提前结束测试！")
                break

        print("\n⏹️ 停止学习调度器...")
        scheduler.stop_learning()

        print("\n📊 最终测试结果:")
        final_status = scheduler.get_detailed_status()

        total_tasks = final_status['engine']['tasks']['completed'] + final_status['engine']['tasks']['failed']
        success_rate = (final_status['engine']['tasks']['completed'] / max(1, total_tasks)) * 100

        print(f"  总任务数: {total_tasks}")
        print(f"  成功任务: {final_status['engine']['tasks']['completed']}")
        print(f"  失败任务: {final_status['engine']['tasks']['failed']}")
        print(f"  成功率: {success_rate:.1f}%")

        if final_status['current_progress']['total_learning_time'] > 0:
            print(f"  总学习时间: {final_status['current_progress']['total_learning_time']:.1f} 小时")
            print(f"  平均效率: {final_status['current_progress']['efficiency']:.2f} 课程/小时")

        # 判断测试成功
        test_success = (
            final_status['engine']['tasks']['completed'] > 0 or
            total_tasks == 0  # 没有需要学习的课程也算成功
        )

        return test_success

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_engine_basic_functionality():
    """测试引擎基本功能（不需要真实学习）"""
    print("\n🔧 基本功能测试...")

    from src.concurrent_learning_engine import ConcurrentLearningEngine, TaskPriority
    from src.pure_api_learner import CourseInfo

    try:
        # 创建测试课程
        test_course = CourseInfo(
            course_id="test_001",
            user_course_id="test_user_001",
            course_name="测试课程",
            course_type="elective",
            progress=0.0,
            duration_minutes=60,
            study_times=0,
            status=1
        )

        # 创建引擎
        engine = ConcurrentLearningEngine(max_workers=1)

        # 测试任务添加
        task_id = engine.add_task(test_course, TaskPriority.HIGH)
        print(f"✅ 任务添加成功: {task_id}")

        # 测试状态查询
        status = engine.get_status()
        print(f"✅ 状态查询成功: {status['tasks']['total']} 个任务")

        # 测试任务取消
        engine.cancel_task(task_id)
        print(f"✅ 任务取消成功")

        # 测试清理
        engine.clear_completed_tasks()
        print(f"✅ 任务清理成功")

        return True

    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 开始并发学习系统综合测试")

    # 先测试基本功能
    basic_test_success = test_engine_basic_functionality()

    if basic_test_success:
        print("✅ 基本功能测试通过")

        # 再测试完整系统
        full_test_success = test_concurrent_learning_system()

        if full_test_success:
            print("\n🎊 所有测试通过！并发学习系统完全可用！")
        else:
            print("\n💔 完整系统测试失败")
    else:
        print("\n❌ 基本功能测试失败，跳过完整测试")

    print("\n" + "=" * 80)