#!/usr/bin/env python3
"""
测试登录状态传递问题
对比直接使用FinalWorkingAPIClient vs 通过learning_engine传递的API客户端
"""

import asyncio
import json
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path().absolute()))

from final_working_api_client import FinalWorkingAPIClient
from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager

async def test_direct_api_client():
    """测试直接使用FinalWorkingAPIClient的情况"""
    print("🧪 测试1: 直接使用FinalWorkingAPIClient")
    print("=" * 50)

    async with FinalWorkingAPIClient() as client:
        # 登录
        success = await client.login("640302198607120020", "My2062660")
        if not success:
            print("❌ 登录失败")
            return None
        print("✅ 登录成功")

        # 检查session状态
        print(f"Session对象: {type(client.session)}")
        print(f"Session headers: {dict(client.session.headers)}")
        print(f"Session cookies: {len(client.session.cookie_jar)} cookies")

        # 测试API调用
        course_id = 10599
        url = f"{client.base_url}/device/study_new!getManifest.do"
        params = {'id': course_id, '_': int(time.time() * 1000)}

        async with client.session.get(url, params=params) as response:
            if response.status == 200:
                manifest = json.loads(await response.text())
                print(f"✅ 直接API调用成功: 播放位置 {manifest.get('lesson_location')}秒")
                return manifest
            else:
                print(f"❌ 直接API调用失败: HTTP {response.status}")
                return None

async def test_through_learning_engine():
    """测试通过learning_engine获取的API客户端"""
    print("\n🧪 测试2: 通过learning_engine获取API客户端")
    print("=" * 50)

    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)

    await course_manager.initialize()

    # 登录
    success = await login_manager.login("640302198607120020", "My2062660", save_credentials=True)
    if not success:
        print("❌ learning_engine登录失败")
        return None
    print("✅ learning_engine登录成功")

    # 获取API客户端
    api_client = login_manager.get_api_client()
    if not api_client:
        print("❌ 无法获取API客户端")
        return None

    print(f"API客户端对象: {type(api_client)}")
    print(f"Session对象: {type(api_client.session)}")
    print(f"Session headers: {dict(api_client.session.headers)}")
    print(f"Session cookies: {len(api_client.session.cookie_jar)} cookies")

    # 测试API调用
    course_id = 10599
    url = f"{api_client.base_url}/device/study_new!getManifest.do"
    params = {'id': course_id, '_': int(time.time() * 1000)}

    async with api_client.session.get(url, params=params) as response:
        if response.status == 200:
            manifest = json.loads(await response.text())
            print(f"✅ learning_engine API调用成功: 播放位置 {manifest.get('lesson_location')}秒")
            await login_manager.logout()
            return manifest
        else:
            print(f"❌ learning_engine API调用失败: HTTP {response.status}")
            await login_manager.logout()
            return None

async def test_session_sharing():
    """测试session共享问题"""
    print("\n🧪 测试3: 检查session是否被正确共享")
    print("=" * 50)

    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)

    # 初始化并登录
    await login_manager.initialize_client()
    success = await login_manager.login("640302198607120020", "My2062660")

    if not success:
        print("❌ 登录失败")
        return

    api_client = login_manager.get_api_client()

    # 检查对象身份
    print(f"login_manager.api_client id: {id(login_manager.api_client)}")
    print(f"get_api_client() 返回 id: {id(api_client)}")
    print(f"两者是同一对象: {login_manager.api_client is api_client}")

    # 检查session身份
    print(f"login_manager.api_client.session id: {id(login_manager.api_client.session)}")
    print(f"api_client.session id: {id(api_client.session)}")
    print(f"session是同一对象: {login_manager.api_client.session is api_client.session}")

    # 检查cookies
    original_cookies = list(login_manager.api_client.session.cookie_jar)
    returned_cookies = list(api_client.session.cookie_jar)

    print(f"原始session cookies数量: {len(original_cookies)}")
    print(f"返回session cookies数量: {len(returned_cookies)}")

    if original_cookies:
        print(f"Cookie示例: {original_cookies[0]}")

    await login_manager.logout()

async def test_cookies_persistence():
    """测试cookies持久性"""
    print("\n🧪 测试4: 检查cookies在不同操作间的持久性")
    print("=" * 50)

    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)

    await course_manager.initialize()

    # 登录
    success = await login_manager.login("640302198607120020", "My2062660")
    if not success:
        print("❌ 登录失败")
        return

    api_client = login_manager.get_api_client()

    # 记录登录后的cookies
    login_cookies = list(api_client.session.cookie_jar)
    print(f"登录后cookies数量: {len(login_cookies)}")

    # 执行一些课程相关操作
    courses = course_manager.get_all_courses()
    print(f"获取课程列表: {len(courses)}门课程")

    # 再次检查cookies
    after_courses_cookies = list(api_client.session.cookie_jar)
    print(f"获取课程后cookies数量: {len(after_courses_cookies)}")

    # 执行manifest调用
    course_id = 10599
    url = f"{api_client.base_url}/device/study_new!getManifest.do"
    params = {'id': course_id, '_': int(time.time() * 1000)}

    async with api_client.session.get(url, params=params) as response:
        print(f"Manifest调用状态: HTTP {response.status}")

    # 最终检查cookies
    final_cookies = list(api_client.session.cookie_jar)
    print(f"最终cookies数量: {len(final_cookies)}")

    await login_manager.logout()

async def main():
    print("🔍 测试登录状态传递问题")
    print("=" * 60)

    # 执行所有测试
    manifest1 = await test_direct_api_client()
    manifest2 = await test_through_learning_engine()

    await test_session_sharing()
    await test_cookies_persistence()

    # 比较结果
    print("\n📊 结果对比:")
    print("=" * 30)
    if manifest1 and manifest2:
        loc1 = manifest1.get('lesson_location', '0')
        loc2 = manifest2.get('lesson_location', '0')
        print(f"直接API播放位置: {loc1}秒")
        print(f"learning_engine播放位置: {loc2}秒")
        print(f"结果一致: {'✅' if loc1 == loc2 else '❌'}")
    else:
        print("❌ 有测试失败，无法比较结果")

if __name__ == "__main__":
    asyncio.run(main())