#!/usr/bin/env python3
"""
对比scorm_based_learning.py和learning_engine.py的进度提交
"""

import asyncio
import json
import time
from datetime import datetime
from final_working_api_client import FinalWorkingAPIClient

async def test_direct_scorm_submit():
    """直接测试SCORM进度提交（模拟scorm_based_learning.py）"""
    print("=" * 60)
    print("测试1: 直接SCORM提交（scorm_based_learning.py方式）")
    print("=" * 60)

    async with FinalWorkingAPIClient() as client:
        # 登录
        success = await client.login("640302198607120020", "My2062660")
        if not success:
            print("登录失败")
            return

        course_id = 10599
        user_course_id = 1988341

        # 1. 获取manifest
        print(f"\n1. 获取课程清单 (course_id={course_id})...")
        url = f"{client.base_url}/device/study_new!getManifest.do"
        params = {'id': course_id, '_': int(time.time() * 1000)}

        async with client.session.get(url, params=params) as response:
            if response.status == 200:
                manifest = json.loads(await response.text())
                print(f"   ✅ 获取成功: {manifest.get('title', 'N/A')}")
                lesson_location = int(manifest.get('lesson_location', '0'))
                print(f"   当前位置: {lesson_location}秒")
            else:
                print(f"   ❌ 获取失败: HTTP {response.status}")
                return

        # 2. 初始化播放器
        print(f"\n2. 初始化SCORM播放器 (user_course_id={user_course_id})...")
        url = f"{client.base_url}/device/study_new!scorm_play.do"
        params = {'terminal': 1, 'id': user_course_id}

        async with client.session.get(url, params=params) as response:
            print(f"   响应状态: HTTP {response.status}")

        # 3. 提交进度
        print(f"\n3. 提交SCORM进度...")
        current_time_str = datetime.now().strftime('%Y-%m-%d+%H:%M:%S')

        serialize_sco = {
            "res01": {
                "lesson_location": lesson_location + 60,
                "session_time": 45,
                "last_learn_time": current_time_str
            },
            "last_study_sco": "res01"
        }

        post_data = {
            'id': str(user_course_id),
            'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
            'duration': '30'
        }

        url = f"{client.base_url}/device/study_new!seek.do"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={user_course_id}'
        }

        print(f"   提交数据:")
        print(f"     id: {post_data['id']}")
        print(f"     serializeSco: {post_data['serializeSco'][:100]}...")
        print(f"     duration: {post_data['duration']}")

        async with client.session.post(url, data=post_data, headers=headers) as response:
            if response.status == 200:
                result = await response.text()
                print(f"   ✅ 提交成功: {result[:100]}...")
            else:
                print(f"   ❌ 提交失败: HTTP {response.status}")

async def test_learning_engine():
    """测试learning_engine.py的实现"""
    print("\n" + "=" * 60)
    print("测试2: Learning Engine方式")
    print("=" * 60)

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path().absolute()))

    from console_learning_system.core.config_manager import ConfigManager
    from console_learning_system.core.login_manager import LoginManager
    from console_learning_system.core.course_manager import CourseManager
    from console_learning_system.core.learning_engine import LearningEngine

    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)
    learning_engine = LearningEngine(config_manager, course_manager)

    await course_manager.initialize()

    # 登录
    print("\n1. 执行登录...")
    success = await login_manager.login("640302198607120020", "My2062660", save_credentials=True)
    if not success:
        print("   ❌ 登录失败")
        return
    print("   ✅ 登录成功")

    # 获取user_course_id=1988341的课程
    print("\n2. 查找目标课程...")
    courses = course_manager.get_all_courses()
    target_course = None
    for course in courses:
        if str(course.user_course_id) == '1988341':
            target_course = course
            break

    if not target_course:
        print("   ❌ 未找到目标课程")
        return

    print(f"   ✅ 找到课程: {target_course.course_name}")
    print(f"     course_id: {target_course.course_id}")
    print(f"     user_course_id: {target_course.user_course_id}")

    # 测试_load_course_manifest
    print("\n3. 测试获取manifest...")
    api_client = login_manager.get_api_client()

    # 创建一个临时的session来记录日志
    from console_learning_system.core.learning_engine import LearningSession
    learning_engine.current_session = LearningSession(target_course)

    manifest = await learning_engine._load_course_manifest(api_client, target_course)
    if manifest:
        print(f"   ✅ Manifest获取成功")
        for log in learning_engine.current_session.logs:
            print(f"     {log}")
    else:
        print(f"   ❌ Manifest获取失败")

    await login_manager.logout()

async def main():
    print("🔍 对比SCORM进度提交实现")
    print()

    # 测试直接SCORM提交
    await test_direct_scorm_submit()

    # 测试learning engine
    await test_learning_engine()

    print("\n" + "=" * 60)
    print("测试完成！")

if __name__ == "__main__":
    asyncio.run(main())