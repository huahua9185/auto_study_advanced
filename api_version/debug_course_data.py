#!/usr/bin/env python3
"""
调试课程数据脚本 - 获取真实的课程信息和SCORM状态
"""

import asyncio
import json
from final_working_api_client import FinalWorkingAPIClient

async def debug_course_data():
    """调试课程数据"""
    print("🔍 调试课程数据...")

    async with FinalWorkingAPIClient() as client:
        # 登录
        success = await client.login("640302198607120020", "My2062660")
        if not success:
            print("❌ 登录失败")
            return

        print("✅ 登录成功，开始调试...")

        # 1. 获取课程清单（使用监控到的参数）
        print("\n1. 获取课程清单...")
        course_id = 10598  # 从监控结果中获取
        url = f"{client.base_url}/device/study_new!getManifest.do"
        params = {'id': course_id, '_': 1758343559397}

        async with client.session.get(url, params=params) as response:
            if response.status == 200:
                manifest_data = json.loads(await response.text())
                print(f"✅ 课程清单获取成功:")
                print(json.dumps(manifest_data, indent=2, ensure_ascii=False)[:1000] + "...")

                # 保存完整数据
                with open('debug_manifest.json', 'w', encoding='utf-8') as f:
                    json.dump(manifest_data, f, indent=2, ensure_ascii=False)
                print("💾 完整清单已保存到 debug_manifest.json")
            else:
                print(f"❌ 获取课程清单失败: {response.status}")

        # 2. 初始化SCORM播放器（使用监控到的参数）
        print("\n2. 初始化SCORM播放器...")
        user_course_id = 1988340  # 从监控结果中获取
        url = f"{client.base_url}/device/study_new!scorm_play.do"
        params = {'terminal': 1, 'id': user_course_id}

        async with client.session.get(url, params=params) as response:
            if response.status == 200:
                scorm_html = await response.text()
                print(f"✅ SCORM播放器初始化成功 (HTML长度: {len(scorm_html)})")

                # 保存HTML以供分析
                with open('debug_scorm.html', 'w', encoding='utf-8') as f:
                    f.write(scorm_html)
                print("💾 SCORM HTML已保存到 debug_scorm.html")

                # 查找可能的初始状态
                if '"lesson_location"' in scorm_html:
                    print("🔍 发现lesson_location相关信息...")
                    # 提取相关的JavaScript变量
                    lines = scorm_html.split('\n')
                    for line in lines:
                        if 'lesson_location' in line.lower() or 'session_time' in line.lower():
                            print(f"   {line.strip()}")
            else:
                print(f"❌ 初始化SCORM播放器失败: {response.status}")

        # 3. 分析真实的学习进度提交逻辑
        print("\n3. 分析学习进度提交逻辑...")
        print("从监控结果分析:")
        print("- lesson_location: 51 -> 60 -> 0 (不是累积的！)")
        print("- session_time: 15 -> 0 -> 10 (本次学习时长)")
        print("- duration: 14 -> 17 -> 27 (实际时间间隔)")

        print("\n🤔 可能的问题:")
        print("1. lesson_location 需要从视频播放器获取当前位置")
        print("2. session_time 应该是有效学习时长，不是总时长")
        print("3. 我们的API调用缺少了SCORM播放器的状态同步")

        # 4. 尝试获取当前学习状态
        print("\n4. 查找学习状态API...")

        # 检查是否有获取当前状态的API
        potential_apis = [
            f"/device/study_new!getCurrentStatus.do?id={user_course_id}",
            f"/device/study_new!getProgress.do?id={user_course_id}",
            f"/device/study_new!getLessonData.do?id={user_course_id}",
        ]

        for api_path in potential_apis:
            url = f"{client.base_url}{api_path}"
            try:
                async with client.session.get(url) as response:
                    if response.status == 200:
                        data = await response.text()
                        print(f"✅ 发现API: {api_path}")
                        print(f"   响应: {data[:200]}...")
                    else:
                        print(f"❌ API不存在: {api_path} (状态: {response.status})")
            except Exception as e:
                print(f"❌ API调用异常: {api_path} - {e}")

if __name__ == "__main__":
    asyncio.run(debug_course_data())