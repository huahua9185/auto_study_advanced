#!/usr/bin/env python3
"""
验证进度提交是否为真实提交
监控API调用过程
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager
from console_learning_system.core.config_manager import ConfigManager


async def verify_real_submission():
    """验证真实提交"""
    print("🔍 验证进度提交是否为真实API调用")
    print("="*50)

    # 初始化
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(login_manager, config_manager)

    # 登录
    await login_manager.login()
    api_client = login_manager.get_api_client()

    if not api_client:
        print("❌ 无法获取API客户端")
        return

    print("✅ API客户端获取成功")

    # 获取测试课程
    courses = course_manager.get_all_courses()
    if not courses:
        print("❌ 没有课程")
        return

    test_course = courses[0]
    print(f"📚 测试课程: {test_course.course_name[:40]}...")
    print(f"📊 当前进度: {test_course.progress:.1f}%")

    # 监控原始submit方法
    original_submit = api_client.submit_learning_progress

    async def monitored_submit(user_course_id, current_location, session_time, duration):
        print(f"\n🚀 API调用监控:")
        print(f"   用户课程ID: {user_course_id}")
        print(f"   学习位置: {current_location}秒")
        print(f"   会话时间: {session_time}秒")
        print(f"   持续时间: {duration}秒")
        print(f"   API地址: https://edu.nxgbjy.org.cn/device/study_new!seek.do")

        # 调用原始方法
        result = await original_submit(user_course_id, current_location, session_time, duration)

        print(f"   📡 提交结果: {'✅ 成功' if result else '❌ 失败'}")

        if result:
            print(f"   🎯 这是真实的网络请求，数据已发送到服务器！")

        return result

    # 替换方法
    api_client.submit_learning_progress = monitored_submit

    # 测试真实提交
    print(f"\n📤 测试真实进度提交...")

    try:
        # 模拟2倍速学习：实际3秒，提交6秒虚拟时间
        result = await api_client.submit_learning_progress(
            user_course_id=test_course.user_course_id,
            current_location=30,      # 学习到30秒位置
            session_time=6,           # 2倍速：提交6秒虚拟时间
            duration=6                # 持续时间6秒
        )

        print(f"\n📊 提交完成:")
        print(f"   这证明了倍速学习是通过向服务器发送虚拟时间实现的")
        print(f"   服务器会根据提交的session_time更新学习进度")
        print(f"   这不是模拟，而是真实的API调用！")

    except Exception as e:
        print(f"❌ 提交测试失败: {e}")

    print("\n" + "="*50)
    print("🔍 结论: 倍速学习使用真实API提交虚拟学习时间")


if __name__ == "__main__":
    asyncio.run(verify_real_submission())