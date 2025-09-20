#!/usr/bin/env python3
"""
测试登录管理器功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager

async def test_login_manager():
    """测试登录管理器"""
    print("🧪 测试登录管理器功能")
    print("=" * 50)

    # 1. 初始化
    print("📋 1. 初始化配置和登录管理器...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)

    # 2. 检查初始状态
    print("📋 2. 检查初始登录状态...")
    is_logged_in = await login_manager.is_logged_in()
    print(f"   初始登录状态: {is_logged_in}")

    # 3. 初始化API客户端
    print("📋 3. 初始化API客户端...")
    init_success = await login_manager.initialize_client()
    print(f"   API客户端初始化: {'成功' if init_success else '失败'}")

    if not init_success:
        print("❌ API客户端初始化失败，无法继续测试")
        return

    # 4. 尝试登录
    print("📋 4. 尝试登录...")
    username = "640302198607120020"
    password = "My2062660"

    try:
        login_success = await login_manager.login(username, password)
        print(f"   登录结果: {'成功' if login_success else '失败'}")

        if login_success:
            # 5. 检查登录后状态
            print("📋 5. 检查登录后状态...")
            is_logged_in = await login_manager.is_logged_in()
            print(f"   登录状态: {is_logged_in}")

            login_info = login_manager.get_login_info()
            print(f"   登录信息: {login_info}")

            # 6. 获取API客户端
            api_client = login_manager.get_api_client()
            print(f"   API客户端状态: {'可用' if api_client else '不可用'}")

    except Exception as e:
        print(f"❌ 登录过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    # 7. 清理
    print("📋 7. 清理资源...")
    await login_manager.close()
    print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_login_manager())