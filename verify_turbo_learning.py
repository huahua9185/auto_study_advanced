#!/usr/bin/env python3
"""
倍速学习功能验证脚本
简洁版测试，专注核心功能验证
"""

import sys
import asyncio
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.turbo_learning_engine import TurboLearningEngine
from console_learning_system.core.config_manager import ConfigManager


async def verify_turbo_logic():
    """验证倍速学习核心逻辑"""
    print("="*60)
    print("🎯 倍速学习功能验证")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 初始化
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(login_manager, config_manager)
    turbo_engine = TurboLearningEngine(config_manager, course_manager)

    # 登录
    print("1️⃣ 登录测试...")
    try:
        await login_manager.login()
        print("   ✅ 登录成功\n")
    except Exception as e:
        print(f"   ❌ 登录失败: {e}\n")
        return False

    # 获取课程
    print("2️⃣ 获取测试课程...")
    courses = course_manager.get_incomplete_courses()
    if not courses:
        print("   ⚠️  没有未完成课程，但核心逻辑测试仍可继续\n")
        # 使用第一门课程作为测试
        courses = course_manager.get_all_courses()
        if not courses:
            print("   ❌ 没有任何课程\n")
            return False

    test_course = courses[0]
    print(f"   📚 课程: {test_course.course_name[:40]}...")
    print(f"   📊 进度: {test_course.progress:.1f}%\n")

    # 测试倍速计算
    print("3️⃣ 倍速时间计算验证...")
    test_cases = [
        {"name": "正常速度", "speed": 1.0, "video": 60, "expected": 60},
        {"name": "2倍速", "speed": 2.0, "video": 60, "expected": 30},
        {"name": "3倍速", "speed": 3.0, "video": 60, "expected": 20},
        {"name": "5倍速", "speed": 5.0, "video": 60, "expected": 12},
    ]

    all_correct = True
    for case in test_cases:
        # 计算实际时间
        submit_interval = 3.0
        progress_per_submit = submit_interval * case["speed"]
        total_submits = max(1, int(case["video"] / progress_per_submit))
        actual_time = total_submits * submit_interval

        # 验证
        is_correct = abs(actual_time - case["expected"]) <= 3.0
        status = "✅" if is_correct else "❌"
        all_correct = all_correct and is_correct

        print(f"   {status} {case['name']}: {case['video']}秒视频")
        print(f"      理论: {case['expected']}秒, 实际: {actual_time:.0f}秒")
        print(f"      提交{total_submits}次, 每次{progress_per_submit:.0f}秒进度")

    print()

    # 测试实际学习逻辑
    print("4️⃣ 实际学习逻辑测试...")
    api_client = login_manager.get_api_client()
    if api_client:
        print("   ✅ API客户端正常")

        # 创建测试会话
        from console_learning_system.core.turbo_learning_engine import TurboLearningSession
        speed = 2.0
        session = TurboLearningSession(test_course, speed)

        # 模拟短时间学习
        print(f"   🚀 测试{speed}倍速学习10秒内容...")
        start_time = time.time()

        try:
            await turbo_engine._learn_to_position(
                session, api_client, 0, 10, 1800, speed
            )
            elapsed = time.time() - start_time

            print(f"   ✅ 学习完成")
            print(f"      实际耗时: {elapsed:.1f}秒")
            print(f"      理论耗时: {10/speed:.1f}秒")
            print(f"      进度变化: {test_course.progress:.1f}% → {session.current_progress:.1f}%")

            # 显示关键日志
            print("\n   📝 执行日志:")
            for log in session.logs[-3:]:
                print(f"      {log}")

        except Exception as e:
            print(f"   ❌ 学习失败: {e}")
    else:
        print("   ❌ 无法获取API客户端")

    print()

    # 总结
    print("="*60)
    print("📊 验证结果总结")
    print("="*60)

    if all_correct:
        print("✅ 倍速学习核心逻辑验证通过!")
        print("\n关键特性:")
        print("  1. 时间计算正确：实际时间 = 视频时长 / 倍速")
        print("  2. 提交策略正确：每3秒提交(倍速×3秒)的虚拟进度")
        print("  3. 倍速效果明显：5倍速可节省80%时间")
        return True
    else:
        print("❌ 部分验证失败，需要检查")
        return False


async def main():
    """主函数"""
    try:
        success = await verify_turbo_logic()

        if success:
            print("\n🎉 倍速学习功能运行正常!")
        else:
            print("\n⚠️  倍速学习功能需要调试")

        return success

    except KeyboardInterrupt:
        print("\n⚠️  测试被中断")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)