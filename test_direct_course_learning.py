#!/usr/bin/env python3
"""
完全复刻learning_engine.py的课程学习逻辑
直接指定user_course_id=1988341，绕过课程管理模块
用于验证是否是课程管理模块传递了错误的course_id
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path().absolute()))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager

class DirectCourseLearner:
    """直接课程学习器，绕过课程管理模块"""

    def __init__(self):
        self.logs = []
        self.config = ConfigManager()
        self.login_manager = LoginManager(self.config)

    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(f"   {log_entry}")

    async def test_direct_learning(self):
        """测试直接学习指定课程"""
        print("🎯 直接课程学习测试")
        print("绕过课程管理模块，直接指定课程参数")
        print("=" * 60)

        # 初始化登录管理器
        await self.login_manager.initialize_client()

        # 登录
        success = await self.login_manager.login("640302198607120020", "My2062660")
        if not success:
            print("❌ 登录失败")
            return
        print("✅ 登录成功")

        # 直接指定课程参数（绕过课程管理模块）
        direct_course_params = {
            'course_id': 10599,              # 正确的course_id
            'user_course_id': 1988341,       # 目标user_course_id
            'course_name': '中国特色社会主义理论体系文献导读（上）'
        }

        print(f"\n🎯 直接指定课程参数:")
        for key, value in direct_course_params.items():
            print(f"   {key}: {value}")

        # 获取API客户端
        api_client = self.login_manager.get_api_client()
        if not api_client:
            print("❌ 无法获取API客户端")
            return

        print(f"\n📋 步骤1: 直接加载课程清单...")
        manifest = await self._load_course_manifest_direct(api_client, direct_course_params)
        if not manifest:
            print("❌ 无法获取课程清单")
            return

        print(f"\n🎮 步骤2: 直接初始化SCORM播放器...")
        await self._init_scorm_player_direct(api_client, direct_course_params)

        print(f"\n📚 步骤3: 直接执行SCORM学习会话...")
        success = await self._execute_scorm_learning_session_direct(
            api_client, direct_course_params, manifest, 60
        )

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

        # 验证播放位置更新
        print(f"\n🔍 验证播放位置更新...")
        await self._verify_position_update(api_client, direct_course_params)

        await self.login_manager.logout()

    async def _load_course_manifest_direct(self, api_client, course_params) -> dict:
        """直接加载课程清单（复刻learning_engine逻辑）"""
        try:
            self.add_log("获取课程清单和当前学习状态...")

            url = f"{api_client.base_url}/device/study_new!getManifest.do"
            params = {'id': course_params['course_id'], '_': int(time.time() * 1000)}

            async with api_client.session.get(url, params=params) as response:
                if response.status == 200:
                    manifest = json.loads(await response.text())

                    lesson_location = int(manifest.get('lesson_location', '0'))
                    self.add_log(f"课程: {manifest.get('title', course_params['course_name'])}")
                    self.add_log(f"当前播放位置: {lesson_location}秒")
                    self.add_log(f"上次学习SCO: {manifest.get('last_study_sco', 'res01')}")

                    return manifest
                else:
                    self.add_log(f"获取课程清单失败: HTTP {response.status}")
                    return None
        except Exception as e:
            self.add_log(f"加载课程清单异常: {e}")
            return None

    async def _init_scorm_player_direct(self, api_client, course_params):
        """直接初始化SCORM播放器（复刻learning_engine逻辑）"""
        try:
            self.add_log("初始化SCORM播放器...")

            url = f"{api_client.base_url}/device/study_new!scorm_play.do"
            params = {'terminal': 1, 'id': course_params['user_course_id']}

            async with api_client.session.get(url, params=params) as response:
                if response.status == 200:
                    self.add_log("SCORM播放器初始化成功")
                else:
                    self.add_log(f"SCORM播放器初始化失败: HTTP {response.status}")
        except Exception as e:
            self.add_log(f"初始化SCORM播放器异常: {e}")

    async def _execute_scorm_learning_session_direct(self, api_client, course_params, manifest: dict, max_time: int) -> bool:
        """直接执行SCORM学习会话（完全复刻learning_engine逻辑）"""
        start_time = time.time()
        lesson_location = int(manifest.get('lesson_location', '0'))
        session_time = 0
        total_duration = 0
        last_submit_time = start_time

        self.add_log(f"开始SCORM学习会话，从位置 {lesson_location}秒 开始")

        # 完全复刻learning_engine的学习场景
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
            },
            {
                'action': 'play',
                'duration': 50,  # 观看50秒
                'advance': 55,   # 播放位置前进55秒
                'description': '持续学习'
            }
        ]

        for i, scenario in enumerate(learning_scenarios):
            if (time.time() - start_time) >= max_time:
                break

            current_time = time.time()
            time_since_last = current_time - last_submit_time

            # 更新SCORM状态（完全复刻learning_engine）
            session_time += scenario['duration']  # 累积观看时长
            lesson_location += scenario['advance'] # 更新播放位置
            total_duration += int(time_since_last) # 累积总时长

            self.add_log(f"执行学习场景 {i+1}: {scenario['description']}")
            self.add_log(f"  观看时长: {scenario['duration']}秒, 播放位置: {lesson_location}秒")

            # 构造SCORM进度数据（完全复刻learning_engine格式）
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
                'id': str(course_params['user_course_id']),
                'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
                'duration': str(total_duration)
            }

            # 提交SCORM进度（完全复刻learning_engine逻辑）
            try:
                url = f"{api_client.base_url}/device/study_new!seek.do"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={course_params["user_course_id"]}'
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

    async def _verify_position_update(self, api_client, course_params):
        """验证播放位置是否真的更新了"""
        try:
            # 等待一下让服务器处理
            await asyncio.sleep(3)

            url = f"{api_client.base_url}/device/study_new!getManifest.do"
            params = {'id': course_params['course_id'], '_': int(time.time() * 1000)}

            async with api_client.session.get(url, params=params) as response:
                if response.status == 200:
                    manifest = json.loads(await response.text())
                    new_position = int(manifest.get('lesson_location', '0'))
                    print(f"   当前播放位置: {new_position}秒")

                    # 比较之前记录的位置
                    if hasattr(self, '_initial_position'):
                        growth = new_position - self._initial_position
                        print(f"   播放位置增长: +{growth}秒")
                    else:
                        print(f"   无法比较位置变化（未记录初始位置）")
                else:
                    print(f"   ❌ 验证失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 验证异常: {e}")

async def compare_with_course_manager():
    """对比课程管理器获取的课程信息"""
    print("\n🔍 对比课程管理器获取的课程信息")
    print("=" * 50)

    try:
        from console_learning_system.core.course_manager import CourseManager

        config = ConfigManager()
        login_manager = LoginManager(config)
        course_manager = CourseManager(config, login_manager)

        await course_manager.initialize()
        await login_manager.login("640302198607120020", "My2062660")

        # 从课程管理器获取课程信息
        courses = course_manager.get_all_courses()
        target_course = None
        for course in courses:
            if str(course.user_course_id) == '1988341':
                target_course = course
                break

        if target_course:
            print(f"课程管理器返回的课程信息:")
            print(f"   course_id: {target_course.course_id}")
            print(f"   user_course_id: {target_course.user_course_id}")
            print(f"   course_name: {target_course.course_name}")
            print(f"   progress: {target_course.progress}%")
            print(f"   status: {target_course.status}")

            # 对比预期值
            expected = {'course_id': 10599, 'user_course_id': 1988341}
            actual = {'course_id': target_course.course_id, 'user_course_id': target_course.user_course_id}

            print(f"\n对比结果:")
            print(f"   预期: {expected}")
            print(f"   实际: {actual}")
            print(f"   一致: {'✅' if expected == actual else '❌'}")

            if expected != actual:
                print(f"\n❌ 发现课程管理器问题！")
                print(f"   课程管理器返回了错误的course_id或user_course_id")
        else:
            print("❌ 课程管理器中未找到user_course_id=1988341的课程")

        await login_manager.logout()

    except Exception as e:
        print(f"❌ 对比过程异常: {e}")

async def main():
    print("🧪 测试课程管理模块是否传递了错误的课程参数")
    print("直接指定user_course_id=1988341，绕过课程管理模块")
    print()

    # 执行直接学习测试
    learner = DirectCourseLearner()
    await learner.test_direct_learning()

    # 对比课程管理器的结果
    await compare_with_course_manager()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("如果直接学习成功，但课程管理器信息不一致，")
    print("则说明问题出在课程管理模块！")

if __name__ == "__main__":
    asyncio.run(main())