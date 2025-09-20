#!/usr/bin/env python3
"""
基于SCORM标准的正确学习系统
根据真实前端逻辑分析得出的正确实现
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from final_working_api_client import FinalWorkingAPIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scorm_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SCORMBasedLearningSystem:
    """基于SCORM标准的学习系统"""

    def __init__(self):
        self.client = None
        self.course_manifest = None

        # SCORM学习状态
        self.lesson_location = 0  # 当前播放位置(秒)
        self.session_time = 0     # 本次会话的累积学习时长(秒)
        self.start_time = None    # 会话开始时间
        self.last_submit_time = None  # 上次提交时间
        self.total_duration = 0   # 累积的总时长(duration参数)

    async def start_learning(self):
        """开始学习"""
        logger.info("🚀 启动基于SCORM的学习系统...")

        async with FinalWorkingAPIClient() as client:
            self.client = client

            # 登录
            success = await client.login("640302198607120020", "My2062660")
            if not success:
                logger.error("❌ 登录失败")
                return

            # 加载课程信息和初始状态
            await self._load_course_state()

            # 开始SCORM学习会话
            await self._start_scorm_session()

    async def _load_course_state(self):
        """加载课程状态"""
        logger.info("📋 加载课程状态...")

        course_id = 10598
        user_course_id = 1988340

        # 获取课程清单
        url = f"{self.client.base_url}/device/study_new!getManifest.do"
        params = {'id': course_id, '_': int(time.time() * 1000)}

        async with self.client.session.get(url, params=params) as response:
            if response.status == 200:
                self.course_manifest = json.loads(await response.text())

                # 从清单中获取当前学习状态
                self.lesson_location = int(self.course_manifest.get('lesson_location', '0'))

                logger.info("✅ 课程状态加载成功")
                logger.info(f"📖 课程: {self.course_manifest['title']}")
                logger.info(f"🎯 当前位置: {self.lesson_location}秒")
                logger.info(f"📍 上次SCO: {self.course_manifest['last_study_sco']}")

                # 初始化SCORM播放器
                await self._init_scorm_player(user_course_id)
            else:
                logger.error(f"❌ 获取课程清单失败: {response.status}")

    async def _init_scorm_player(self, user_course_id):
        """初始化SCORM播放器"""
        logger.info("🎮 初始化SCORM播放器...")

        url = f"{self.client.base_url}/device/study_new!scorm_play.do"
        params = {'terminal': 1, 'id': user_course_id}

        async with self.client.session.get(url, params=params) as response:
            if response.status == 200:
                logger.info("✅ SCORM播放器初始化成功")
            else:
                logger.error(f"❌ SCORM播放器初始化失败: {response.status}")

    async def _start_scorm_session(self):
        """开始SCORM学习会话"""
        logger.info("📚 开始SCORM学习会话...")

        self.start_time = time.time()
        self.last_submit_time = self.start_time
        self.session_time = 0
        self.total_duration = 0

        user_course_id = 1988340

        # 模拟真实的视频学习行为
        learning_scenarios = [
            # 场景1: 从当前位置开始播放
            {
                'action': 'play',
                'from_position': self.lesson_location,
                'to_position': self.lesson_location + 60,
                'play_duration': 45,  # 实际观看45秒
                'description': '从断点续播60秒'
            },
            # 场景2: 继续播放
            {
                'action': 'play',
                'from_position': self.lesson_location + 60,
                'to_position': self.lesson_location + 120,
                'play_duration': 55,  # 实际观看55秒
                'description': '继续播放60秒'
            },
            # 场景3: 用户快退到开头
            {
                'action': 'seek',
                'from_position': self.lesson_location + 120,
                'to_position': 0,
                'play_duration': 0,  # 快退无观看时长
                'description': '快退到视频开头'
            },
            # 场景4: 从开头播放一段
            {
                'action': 'play',
                'from_position': 0,
                'to_position': 90,
                'play_duration': 80,  # 实际观看80秒
                'description': '从开头播放90秒'
            },
            # 场景5: 继续播放
            {
                'action': 'play',
                'from_position': 90,
                'to_position': 180,
                'play_duration': 85,  # 实际观看85秒
                'description': '继续播放到3分钟'
            }
        ]

        for i, scenario in enumerate(learning_scenarios, 1):
            await self._execute_learning_scenario(user_course_id, scenario, i, len(learning_scenarios))

            # 等待间隔（模拟真实学习节奏）
            if i < len(learning_scenarios):
                wait_time = 20 + (i * 3)  # 递增等待时间
                logger.info(f"   ⏸️ 学习间隔 {wait_time}秒...")
                await asyncio.sleep(wait_time)

        # 学习会话总结
        await self._session_summary()

    async def _execute_learning_scenario(self, user_course_id, scenario, current, total):
        """执行学习场景"""
        current_time = time.time()
        time_since_last = current_time - self.last_submit_time

        # 更新学习状态
        if scenario['action'] == 'play':
            self.session_time += scenario['play_duration']  # 累积实际观看时长

        self.lesson_location = scenario['to_position']  # 更新当前播放位置
        self.total_duration += int(time_since_last)     # 累积总时长间隔

        logger.info(f"\n📈 执行学习场景 {current}/{total}: {scenario['description']}")
        logger.info(f"   🎬 播放位置: {scenario['from_position']}s -> {scenario['to_position']}s")
        logger.info(f"   📚 观看时长: {scenario['play_duration']}s")
        logger.info(f"   ⏱️ 时间间隔: {int(time_since_last)}s")
        logger.info(f"   📊 累积学习: {self.session_time}s")
        logger.info(f"   🔄 累积时长: {self.total_duration}s")

        # 构造SCORM进度数据（基于分析得出的正确格式）
        current_time_str = datetime.now().strftime('%Y-%m-%d+%H:%M:%S')

        serialize_sco = {
            "res01": {
                "lesson_location": self.lesson_location,  # 当前播放位置
                "session_time": scenario['play_duration'], # 本次观看时长（不是累积！）
                "last_learn_time": current_time_str
            },
            "last_study_sco": "res01"
        }

        post_data = {
            'id': str(user_course_id),
            'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
            'duration': str(self.total_duration)  # 累积的总时长
        }

        # 提交学习进度
        url = f"{self.client.base_url}/device/study_new!seek.do"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={user_course_id}'
        }

        async with self.client.session.post(url, data=post_data, headers=headers) as response:
            if response.status == 200:
                result = await response.text()
                logger.info(f"   ✅ SCORM进度提交成功: {result}")
            else:
                logger.error(f"   ❌ SCORM进度提交失败: {response.status}")

        # 更新时间戳
        self.last_submit_time = current_time

    async def _session_summary(self):
        """学习会话总结"""
        total_session_time = time.time() - self.start_time

        logger.info("\n🎉 SCORM学习会话完成！")
        logger.info("📊 会话总结:")
        logger.info(f"   ⏱️ 会话总时长: {int(total_session_time)}秒")
        logger.info(f"   📚 有效学习时长: {self.session_time}秒")
        logger.info(f"   🎬 最终播放位置: {self.lesson_location}秒")
        logger.info(f"   📈 学习效率: {self.session_time/total_session_time*100:.1f}%")

        # 保存学习记录
        session_record = {
            'timestamp': datetime.now().isoformat(),
            'total_session_time': int(total_session_time),
            'effective_learning_time': self.session_time,
            'final_lesson_location': self.lesson_location,
            'course_title': self.course_manifest['title'],
            'learning_efficiency': self.session_time/total_session_time
        }

        with open('scorm_session_record.json', 'w', encoding='utf-8') as f:
            json.dump(session_record, f, indent=2, ensure_ascii=False)

        logger.info("💾 学习记录已保存到 scorm_session_record.json")

async def main():
    system = SCORMBasedLearningSystem()
    await system.start_learning()

if __name__ == "__main__":
    asyncio.run(main())