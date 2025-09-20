#!/usr/bin/env python3
"""
完整的登录管理器功能测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager

async def test_login_manager_complete():
    """完整测试登录管理器功能"""
    print("🧪 完整登录管理器功能测试")
    print("=" * 60)

    # 1. 初始化
    print("📋 1. 初始化组件...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    print("   ✅ 组件初始化完成")

    # 2. 测试初始状态
    print("\n📋 2. 测试初始状态...")
    is_logged_in = await login_manager.is_logged_in()
    print(f"   初始登录状态: {is_logged_in}")

    login_info = login_manager.get_login_info()
    print(f"   初始登录信息: {login_info}")

    # 3. 测试API客户端初始化
    print("\n📋 3. 测试API客户端初始化...")
    init_success = await login_manager.initialize_client()
    print(f"   API客户端初始化: {'成功' if init_success else '失败'}")

    if not init_success:
        print("❌ API客户端初始化失败，无法继续测试")
        return

    # 4. 测试登录功能
    print("\n📋 4. 测试登录功能...")
    login_success = await login_manager.login()  # 使用默认凭据
    print(f"   登录结果: {'成功' if login_success else '失败'}")

    if login_success:
        # 5. 测试登录后状态
        print("\n📋 5. 测试登录后状态...")
        is_logged_in = await login_manager.is_logged_in()
        print(f"   登录状态: {is_logged_in}")

        login_info = login_manager.get_login_info()
        print(f"   登录信息: {login_info}")

        login_status = await login_manager.get_login_status()
        print(f"   详细状态: {login_status}")

        # 6. 测试API客户端获取
        api_client = login_manager.get_api_client()
        print(f"   API客户端状态: {'可用' if api_client else '不可用'}")

        # 7. 测试会话刷新
        print("\n📋 7. 测试会话刷新...")
        refresh_success = await login_manager.refresh_session()
        print(f"   会话刷新: {'成功' if refresh_success else '失败'}")

        # 8. 测试登录状态检查
        print("\n📋 8. 测试登录状态检查...")
        status_check = login_manager.check_login_status()
        print(f"   状态检查: {status_check}")

        # 9. 测试自动登录功能
        print("\n📋 9. 测试自动登录功能...")
        await login_manager.logout()  # 先登出
        auto_login_success = login_manager.auto_login()
        print(f"   自动登录: {'成功' if auto_login_success else '失败'}")

        # 10. 测试确保登录功能
        print("\n📋 10. 测试确保登录功能...")
        await login_manager.logout()  # 再次登出
        ensure_success = login_manager.ensure_logged_in()
        print(f"   确保登录: {'成功' if ensure_success else '失败'}")

    # 11. 测试登出功能
    print("\n📋 11. 测试登出功能...")
    logout_success = await login_manager.logout()
    print(f"   登出结果: {'成功' if logout_success else '失败'}")

    # 验证登出后状态
    is_logged_in = await login_manager.is_logged_in()
    print(f"   登出后状态: {'已登出' if not is_logged_in else '仍在登录'}")

    # 12. 清理资源
    print("\n📋 12. 清理资源...")
    await login_manager.close()
    print("   ✅ 资源清理完成")

    print("\n🎉 登录管理器功能测试完成！")

def test_sync_methods():
    """测试同步方法"""
    print("\n🧪 测试同步方法")
    print("=" * 40)

    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)

    # 测试同步初始化
    print("📋 测试同步API客户端初始化...")
    init_success = login_manager.initialize_client_sync()
    print(f"   同步初始化: {'成功' if init_success else '失败'}")

    if init_success:
        # 测试同步登录
        print("📋 测试同步登录...")
        login_success = login_manager.login_sync()
        print(f"   同步登录: {'成功' if login_success else '失败'}")

        # 测试同步状态检查
        print("📋 测试同步状态检查...")
        is_logged_in = login_manager.is_logged_in_sync()
        print(f"   同步状态检查: {is_logged_in}")

        # 测试同步登出
        print("📋 测试同步登出...")
        logout_success = login_manager.logout_sync()
        print(f"   同步登出: {'成功' if logout_success else '失败'}")

    # 清理
    login_manager.close_sync()
    print("✅ 同步方法测试完成")

if __name__ == "__main__":
    print("开始完整的登录管理器测试...")

    # 测试异步方法
    asyncio.run(test_login_manager_complete())

    # 测试同步方法
    test_sync_methods()

    print("\n🎊 所有测试完成！")