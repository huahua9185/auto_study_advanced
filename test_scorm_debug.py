#!/usr/bin/env python3
"""
调试SCORM进度提交问题
"""

import asyncio
import json
import time
from datetime import datetime
from final_working_api_client import FinalWorkingAPIClient

async def test_scorm_submission():
    """测试SCORM进度提交的各种参数组合"""
    print("🔍 调试SCORM进度提交")
    print("=" * 60)

    async with FinalWorkingAPIClient() as client:
        # 登录
        success = await client.login("640302198607120020", "My2062660")
        if not success:
            print("登录失败")
            return

        # 测试课程
        test_cases = [
            {
                'name': '以新质生产力支撑高质量发展（下）',
                'course_id': 11061,
                'user_course_id': 1989044
            }
        ]

        for test_case in test_cases:
            print(f"\n测试课程: {test_case['name']}")
            print("-" * 40)

            course_id = test_case['course_id']
            user_course_id = test_case['user_course_id']

            # 1. 获取manifest确认课程状态
            print("\n1. 获取课程状态...")
            url = f"{client.base_url}/device/study_new!getManifest.do"
            params = {'id': course_id, '_': int(time.time() * 1000)}

            async with client.session.get(url, params=params) as response:
                if response.status == 200:
                    manifest = json.loads(await response.text())
                    print(f"   标题: {manifest.get('title', 'N/A')}")
                    print(f"   当前位置: {manifest.get('lesson_location', '0')}")
                    print(f"   总时长: {manifest.get('total_time', 'N/A')}")
                    print(f"   进度: {manifest.get('progress_measure', 'N/A')}")
                    current_location = int(manifest.get('lesson_location', '0'))
                else:
                    print(f"   获取失败: HTTP {response.status}")
                    continue

            # 2. 初始化SCORM播放器
            print("\n2. 初始化SCORM播放器...")
            url = f"{client.base_url}/device/study_new!scorm_play.do"
            params = {'terminal': 1, 'id': user_course_id}

            async with client.session.get(url, params=params) as response:
                print(f"   响应: HTTP {response.status}")
                if response.status == 200:
                    # 尝试获取响应内容
                    content = await response.text()
                    if content:
                        print(f"   内容: {content[:100]}...")

            # 3. 测试不同的提交参数组合
            print("\n3. 测试SCORM进度提交...")

            # 测试配置
            test_configs = [
                {
                    'desc': '测试1: 标准格式（整数lesson_location）',
                    'lesson_location': current_location + 60,
                    'session_time': 45,
                    'duration': 30
                },
                {
                    'desc': '测试2: 字符串lesson_location',
                    'lesson_location': str(current_location + 120),
                    'session_time': 55,
                    'duration': 60
                },
                {
                    'desc': '测试3: 字符串session_time',
                    'lesson_location': current_location + 180,
                    'session_time': "60",
                    'duration': "90"
                }
            ]

            for config in test_configs:
                print(f"\n   {config['desc']}")

                current_time_str = datetime.now().strftime('%Y-%m-%d+%H:%M:%S')

                serialize_sco = {
                    "res01": {
                        "lesson_location": config['lesson_location'],
                        "session_time": config['session_time'],
                        "last_learn_time": current_time_str
                    },
                    "last_study_sco": "res01"
                }

                post_data = {
                    'id': str(user_course_id),
                    'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
                    'duration': str(config['duration'])
                }

                print(f"     提交数据:")
                print(f"       id: {post_data['id']}")
                print(f"       lesson_location: {config['lesson_location']} (类型: {type(config['lesson_location'])})")
                print(f"       session_time: {config['session_time']} (类型: {type(config['session_time'])})")
                print(f"       duration: {config['duration']}")

                url = f"{client.base_url}/device/study_new!seek.do"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={user_course_id}'
                }

                async with client.session.post(url, data=post_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.text()
                        print(f"     响应: {result}")

                        # 检查是否真的成功
                        if result == "1":
                            print(f"     ✅ 提交成功")
                        elif result == "0":
                            print(f"     ❌ 提交失败（返回0）")
                        else:
                            print(f"     ⚠️ 未知响应: {result}")
                    else:
                        print(f"     ❌ HTTP错误: {response.status}")

                # 等待一下避免太频繁
                await asyncio.sleep(2)

            # 4. 重新获取manifest验证进度是否更新
            print("\n4. 验证进度更新...")
            await asyncio.sleep(3)  # 等待服务器处理

            params = {'id': course_id, '_': int(time.time() * 1000)}
            async with client.session.get(f"{client.base_url}/device/study_new!getManifest.do", params=params) as response:
                if response.status == 200:
                    manifest = json.loads(await response.text())
                    print(f"   新位置: {manifest.get('lesson_location', '0')}")
                    print(f"   新进度: {manifest.get('progress_measure', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_scorm_submission())