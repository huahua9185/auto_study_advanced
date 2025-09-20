#!/usr/bin/env python3
"""
复刻learning_engine.py的学习逻辑以便验证
直接使用FinalWorkingAPIClient模拟learning_engine的SCORM学习流程
"""

import asyncio
import json
import time
from datetime import datetime
from final_working_api_client import FinalWorkingAPIClient

class LearningEngineReplica:
    """复刻learning_engine.py的学习逻辑"""

    def __init__(self):
        self.client = None
        self.logs = []

    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(f"   {log_entry}")

    async def test_learning_engine_logic(self):
        """测试learning_engine的学习逻辑"""
        print("🔬 复刻learning_engine.py的学习逻辑")
        print("=" * 60)

        async with FinalWorkingAPIClient() as client:
            self.client = client

            # 登录
            success = await client.login("640302198607120020", "My2062660")
            if not success:
                print("❌ 登录失败")
                return
            print("✅ 登录成功")

            # 模拟learning_engine的课程对象
            class MockCourse:
                def __init__(self):
                    self.course_id = 10599
                    self.user_course_id = 1988341
                    self.course_name = "中国特色社会主义理论体系文献导读（上）"
                    self.progress = 11.6

            course = MockCourse()

            print(f"\n🎯 目标课程:")
            print(f"   课程名称: {course.course_name}")
            print(f"   course_id: {course.course_id}")
            print(f"   user_course_id: {course.user_course_id}")
            print(f"   当前进度: {course.progress}%")

            # 按照learning_engine的步骤执行
            print(f"\n📋 步骤1: 加载课程清单...")
            manifest = await self._load_course_manifest(client, course)
            if not manifest:
                print("❌ 无法获取课程清单")
                return

            print(f"\n🎮 步骤2: 初始化SCORM播放器...")
            await self._init_scorm_player(client, course)

            print(f"\n📚 步骤3: 执行SCORM学习会话...")
            success = await self._execute_scorm_learning_session(client, course, manifest, 60)

            print(f"\n📊 学习结果:")
            print(f"   成功: {'✅' if success else '❌'}")
            print(f"   日志条数: {len(self.logs)}")

            print(f"\n📝 详细日志:")
            for i, log in enumerate(self.logs, 1):
                print(f"   {i:2d}. {log}")

            # 检查错误
            error_logs = [log for log in self.logs if '失败' in log or '异常' in log or '错误' in log]
            if error_logs:
                print(f"\n⚠️ 发现 {len(error_logs)} 条错误日志:")
                for log in error_logs:
                    print(f"   ❌ {log}")
            else:
                print(f"\n✅ 没有发现错误日志！")

    async def _load_course_manifest(self, api_client, course) -> dict:
        """加载课程清单和状态（复刻learning_engine逻辑）"""
        try:
            self.add_log("获取课程清单和当前学习状态...")

            url = f"{api_client.base_url}/device/study_new!getManifest.do"
            params = {'id': course.course_id, '_': int(time.time() * 1000)}

            # 复刻learning_engine: 使用原始session保持登录状态
            async with api_client.session.get(url, params=params) as response:
                if response.status == 200:
                    manifest = json.loads(await response.text())

                    lesson_location = int(manifest.get('lesson_location', '0'))
                    self.add_log(f"课程: {manifest.get('title', course.course_name)}")
                    self.add_log(f"当前播放位置: {lesson_location}秒")
                    self.add_log(f"上次学习SCO: {manifest.get('last_study_sco', 'res01')}")

                    return manifest
                else:
                    self.add_log(f"获取课程清单失败: HTTP {response.status}")
                    return None
        except Exception as e:
            self.add_log(f"加载课程清单异常: {e}")
            return None

    async def _init_scorm_player(self, api_client, course):
        """初始化SCORM播放器（复刻learning_engine逻辑）"""
        try:
            self.add_log("初始化SCORM播放器...")

            url = f"{api_client.base_url}/device/study_new!scorm_play.do"
            params = {'terminal': 1, 'id': course.user_course_id}

            # 复刻learning_engine: 使用原始session保持登录状态
            async with api_client.session.get(url, params=params) as response:
                if response.status == 200:
                    self.add_log("SCORM播放器初始化成功")
                else:
                    self.add_log(f"SCORM播放器初始化失败: HTTP {response.status}")
        except Exception as e:
            self.add_log(f"初始化SCORM播放器异常: {e}")

    async def _execute_scorm_learning_session(self, api_client, course, manifest: dict, max_time: int) -> bool:
        """执行SCORM学习会话（复刻learning_engine逻辑）"""
        start_time = time.time()
        lesson_location = int(manifest.get('lesson_location', '0'))
        session_time = 0
        total_duration = 0
        last_submit_time = start_time

        self.add_log(f"开始SCORM学习会话，从位置 {lesson_location}秒 开始")

        # 复刻learning_engine的学习场景
        learning_scenarios = [
            {
                'action': 'play',
                'duration': 45,  # 观看45秒
                'advance': 60,   # 播放位置前进60秒
                'description': '正常播放学习'
            },
            {
                'action': 'play',
                'duration': 55,  # 观看55秒
                'advance': 60,   # 播放位置前进60秒
                'description': '继续学习'
            },
            {
                'action': 'play',
                'duration': 40,  # 观看40秒
                'advance': 45,   # 播放位置前进45秒
                'description': '深入学习'
            }
        ]

        for i, scenario in enumerate(learning_scenarios):
            if (time.time() - start_time) >= max_time:
                break

            current_time = time.time()
            time_since_last = current_time - last_submit_time

            # 更新SCORM状态
            session_time += scenario['duration']  # 累积观看时长
            lesson_location += scenario['advance'] # 更新播放位置
            total_duration += int(time_since_last) # 累积总时长

            self.add_log(f"执行学习场景 {i+1}: {scenario['description']}")
            self.add_log(f"  观看时长: {scenario['duration']}秒, 播放位置: {lesson_location}秒")

            # 构造SCORM进度数据（复刻learning_engine格式）
            current_time_str = datetime.now().strftime('%Y-%m-%d+%H:%M:%S')

            serialize_sco = {
                "res01": {
                    "lesson_location": lesson_location,
                    "session_time": scenario['duration'],  # 本次观看时长
                    "last_learn_time": current_time_str
                },
                "last_study_sco": "res01"
            }

            post_data = {
                'id': str(course.user_course_id),
                'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
                'duration': str(total_duration)
            }

            # 提交SCORM进度（复刻learning_engine逻辑）
            try:
                url = f"{api_client.base_url}/device/study_new!seek.do"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={course.user_course_id}'
                }

                # 复刻learning_engine: 使用原始session保持登录状态，临时添加额外headers
                original_headers = dict(api_client.session.headers)
                api_client.session.headers.update(headers)

                try:
                    async with api_client.session.post(url, data=post_data) as response:
                        if response.status == 200:
                            result = await response.text()
                            # 复刻修复后的logic: HTTP 200就表示成功
                            self.add_log(f"  SCORM进度提交成功: {result}")
                        else:
                            self.add_log(f"  SCORM进度提交失败: HTTP {response.status}")
                finally:
                    # 恢复原始headers
                    api_client.session.headers.clear()
                    api_client.session.headers.update(original_headers)

            except Exception as e:
                self.add_log(f"  提交进度异常: {e}")

            last_submit_time = current_time

            # 学习间隔（复刻learning_engine模式）
            if i < len(learning_scenarios) - 1:
                wait_time = 15 + (i * 5)  # 递增等待时间
                self.add_log(f"  学习间隔 {wait_time}秒...")
                await asyncio.sleep(wait_time)

        # 学习会话总结
        total_session_time = time.time() - start_time
        self.add_log(f"SCORM学习会话完成")
        self.add_log(f"  会话总时长: {int(total_session_time)}秒")
        self.add_log(f"  有效学习时长: {session_time}秒")
        self.add_log(f"  最终播放位置: {lesson_location}秒")
        self.add_log(f"  学习效率: {session_time/total_session_time*100:.1f}%")

        return True

async def main():
    replica = LearningEngineReplica()
    await replica.test_learning_engine_logic()

if __name__ == "__main__":
    asyncio.run(main())