#!/usr/bin/env python3
"""
最终工作版API客户端 - 基于真实API监控结果
使用监控到的真实API调用格式
"""

import asyncio
import json
import logging
import urllib.parse
import base64
from datetime import datetime
import aiohttp
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
try:
    import ddddocr
except ImportError:
    print("Installing ddddocr...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'ddddocr'])
    import ddddocr

# PIL 兼容性修复
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
        print("已修复 Pillow 兼容性: Image.ANTIALIAS -> Image.LANCZOS")
except ImportError:
    pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_api_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalWorkingAPIClient:
    """最终工作版API客户端"""

    def __init__(self):
        self.base_url = "https://edu.nxgbjy.org.cn"
        self.session = None
        self.ocr = ddddocr.DdddOcr()
        self.token = "3ee5648315e911e7b2f200fff6167960"

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """初始化session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'X-Requested-With': 'XMLHttpRequest',
                'token': self.token,
                'Referer': 'https://edu.nxgbjy.org.cn/nxxzxy/index.html'
            }
        )
        logger.info("✅ Session初始化完成")

    async def close(self):
        """关闭session"""
        if self.session:
            await self.session.close()

    async def login(self, username: str, password: str):
        """登录"""
        logger.info("🔐 开始登录...")

        try:
            # 1. 先访问首页获取session
            await self._init_session()

            # 2. 获取验证码
            captcha_code = await self._get_captcha()
            if not captcha_code:
                return False

            # 3. 加密密码
            encrypted_password = self._encrypt_password(password)

            # 4. 执行登录 - 使用真实的参数名
            login_data = {
                'username': username,
                'password': encrypted_password,
                'verify_code': captcha_code,
                'terminal': '1'
            }

            url = f"{self.base_url}/device/login.do"

            # 设置正确的请求头
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/plain, */*',
                'Access-Control-Allow-Origin': '*/*',
                'Origin': 'https://edu.nxgbjy.org.cn',
                'Cache-Control': 'no-cache'
            }

            async with self.session.post(url, data=login_data, headers=headers) as response:
                if response.status == 200:
                    # 手动获取响应内容
                    content = await response.text()

                    try:
                        # 尝试解析JSON
                        result = json.loads(content)
                        logger.info(f"📊 登录响应: {str(result)[:200]}...")
                        # 检查是否包含用户信息（登录成功的标志）
                        if result.get('user_id') or result.get('user'):
                            logger.info("✅ 登录成功")
                            return True
                        elif result.get('success'):
                            logger.info("✅ 登录成功")
                            return True
                        else:
                            logger.error(f"❌ 登录失败: {result.get('errorMsg', 'Unknown error')}")
                            return False
                    except json.JSONDecodeError:
                        # 如果不是JSON，检查是否是成功重定向
                        if "成功" in content or "index" in content:
                            logger.info("✅ 登录成功（重定向）")
                            return True
                        else:
                            logger.error(f"❌ 登录响应异常: {content[:100]}...")
                            return False
                else:
                    logger.error(f"❌ 登录请求失败: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            return False

    async def _init_session(self):
        """初始化session - 访问首页获取cookies"""
        try:
            url = f"{self.base_url}/nxxzxy/index.html"
            async with self.session.get(url) as response:
                if response.status == 200:
                    logger.info("✅ Session初始化成功")
                else:
                    logger.warning(f"⚠️ Session初始化响应: {response.status}")
        except Exception as e:
            logger.error(f"❌ Session初始化异常: {e}")

    async def _get_captcha(self):
        """获取并识别验证码"""
        try:
            # 使用真实的验证码API端点
            url = f"{self.base_url}/device/login!get_auth_code.do"
            params = {'terminal': 1, 'code': 88}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    image_data = await response.read()
                    captcha_code = self.ocr.classification(image_data)
                    if captcha_code and len(captcha_code) == 4 and captcha_code.isdigit():
                        logger.info(f"✅ 验证码识别成功: {captcha_code}")
                        return captcha_code
                    else:
                        logger.error(f"❌ 验证码识别失败: {captcha_code}")
                        return None
                else:
                    logger.error(f"❌ 获取验证码失败: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ 获取验证码异常: {e}")
            return None

    def _encrypt_password(self, password: str) -> str:
        """使用DES加密密码"""
        try:
            key = "CCR!@#$%"
            key_bytes = key.encode('utf-8')

            # 确保密码长度是8的倍数
            password_bytes = password.encode('utf-8')
            padded_password = pad(password_bytes, DES.block_size)

            cipher = DES.new(key_bytes, DES.MODE_ECB)
            encrypted = cipher.encrypt(padded_password)

            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"❌ 密码加密失败: {e}")
            return password

    async def get_selected_courses(self):
        """获取选中的课程"""
        logger.info("📋 获取选中课程...")

        try:
            url = f"{self.base_url}/device/userCourse_new!getUserCourse.do"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    courses = data.get('rows', [])
                    selected_courses = [c for c in courses if c.get('is_select') == 1]
                    logger.info(f"✅ 获取到 {len(selected_courses)} 个选中课程")
                    return selected_courses
                else:
                    logger.error(f"❌ 获取课程失败: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"❌ 获取课程异常: {e}")
            return []

    async def submit_learning_progress(self, user_course_id, current_location, session_time, duration):
        """提交学习进度 - 使用真实API格式"""
        try:
            # 格式化时间（使用+替代空格，这是关键发现！）
            current_time = datetime.now().strftime('%Y-%m-%d+%H:%M:%S')

            # 构造serializeSco JSON（使用res01作为sco_id，这是另一个关键发现！）
            serialize_sco = {
                "res01": {
                    "lesson_location": current_location,
                    "session_time": session_time,
                    "last_learn_time": current_time
                },
                "last_study_sco": "res01"
            }

            # 构造POST数据（使用form-data格式，不是JSON！）
            post_data = {
                'id': str(user_course_id),
                'serializeSco': json.dumps(serialize_sco, separators=(',', ':')),
                'duration': str(duration)
            }

            # 设置正确的Content-Type
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f'https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={user_course_id}'
            }

            # 提交进度
            url = f"{self.base_url}/device/study_new!seek.do"

            async with self.session.post(url, data=post_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.text()
                    logger.info(f"✅ 进度提交成功: {current_location}秒 - {result[:50]}...")
                    return True
                else:
                    logger.error(f"❌ 进度提交失败: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ 提交进度异常: {e}")
            return False

async def test_final_api():
    """测试最终API客户端"""
    logger.info("🚀 测试最终API客户端...")

    async with FinalWorkingAPIClient() as client:
        # 登录
        success = await client.login("640302198607120020", "My2062660")
        if not success:
            logger.error("❌ 登录失败，退出测试")
            return

        # 直接使用监控到的课程信息
        user_course_id = 1988340  # 从监控结果中获取的真实课程ID
        course_name = "测试课程"

        logger.info(f"📖 测试课程: {course_name} (ID: {user_course_id})")

        # 提交几次学习进度
        for i in range(5):
            current_location = (i + 1) * 30
            session_time = (i + 1) * 30
            duration = 30

            logger.info(f"📈 提交进度 {i+1}/5...")
            success = await client.submit_learning_progress(
                user_course_id, current_location, session_time, duration
            )

            if success:
                logger.info(f"✅ 第{i+1}次提交成功")
            else:
                logger.error(f"❌ 第{i+1}次提交失败")

            if i < 4:
                await asyncio.sleep(5)  # 5秒间隔

        logger.info("🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_final_api())