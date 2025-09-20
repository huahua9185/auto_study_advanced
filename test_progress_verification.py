#!/usr/bin/env python3
"""
验证学习后课程进度是否真的更新了
"""

import asyncio
import json
import time
from final_working_api_client import FinalWorkingAPIClient

async def check_course_progress():
    """检查课程进度变化"""
    print("🔍 验证课程进度更新")
    print("=" * 50)

    async with FinalWorkingAPIClient() as client:
        # 登录
        success = await client.login("640302198607120020", "My2062660")
        if not success:
            print("❌ 登录失败")
            return
        print("✅ 登录成功")

        course_id = 10599
        user_course_id = 1988341

        # 获取当前manifest信息
        print(f"\n📋 获取课程清单详细信息...")
        url = f"{client.base_url}/device/study_new!getManifest.do"
        params = {'id': course_id, '_': int(time.time() * 1000)}

        async with client.session.get(url, params=params) as response:
            if response.status == 200:
                manifest = json.loads(await response.text())

                print(f"课程标题: {manifest.get('title', 'N/A')}")
                print(f"当前播放位置: {manifest.get('lesson_location', '0')}秒")
                print(f"总时长: {manifest.get('total_time', 'N/A')}")
                print(f"进度测量: {manifest.get('progress_measure', 'N/A')}")
                print(f"完成状态: {manifest.get('completion_status', 'N/A')}")
                print(f"成功状态: {manifest.get('success_status', 'N/A')}")
                print(f"上次学习SCO: {manifest.get('last_study_sco', 'N/A')}")

                # 计算理论进度
                lesson_location = int(manifest.get('lesson_location', '0'))
                total_time = manifest.get('total_time', '')

                if total_time and ':' in total_time:
                    # 解析时:分:秒格式
                    time_parts = total_time.split(':')
                    if len(time_parts) == 3:
                        total_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
                        theoretical_progress = (lesson_location / total_seconds) * 100
                        print(f"理论进度: {theoretical_progress:.2f}% ({lesson_location}/{total_seconds}秒)")

                print(f"\n📄 完整manifest数据:")
                for key, value in manifest.items():
                    print(f"  {key}: {value}")

        # 同时检查课程API返回的进度
        print(f"\n📊 检查API返回的课程进度...")
        courses_data = await client.get_required_courses()

        if 'courses' in courses_data:
            for course in courses_data['courses']:
                if course.get('user_course_id') == user_course_id:
                    api_progress = course.get('progress', 0)
                    api_status = course.get('status', 0)

                    print(f"API返回进度: {api_progress * 100:.1f}%")
                    print(f"API返回状态: {api_status}")
                    print(f"课程名称: {course.get('course_name', 'N/A')}")
                    break
        else:
            print("❌ 无法获取课程API数据")

if __name__ == "__main__":
    asyncio.run(check_course_progress())