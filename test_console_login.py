#!/usr/bin/env python3
"""
测试控制台界面的登录功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.console_interface import SCORMConsoleInterface

def test_console_login():
    """测试控制台登录功能"""
    print("🧪 测试控制台界面登录功能")
    print("=" * 50)

    # 1. 初始化控制台界面
    print("📋 1. 初始化控制台界面...")
    interface = SCORMConsoleInterface()
    print("   ✅ 界面初始化完成")

    # 2. 测试登录状态检查
    print("\n📋 2. 测试登录状态检查...")
    is_logged_in = interface.login_manager.is_logged_in_sync()
    print(f"   当前登录状态: {is_logged_in}")

    # 3. 测试自动登录功能
    print("\n📋 3. 测试自动登录功能...")
    try:
        auto_login_success = interface._auto_login()
        print(f"   自动登录结果: {'成功' if auto_login_success else '失败'}")
    except Exception as e:
        print(f"   自动登录出错: {e}")
        import traceback
        traceback.print_exc()

    # 4. 测试登录测试功能
    print("\n📋 4. 测试登录测试功能...")
    try:
        interface._test_login()
        print("   ✅ 登录测试功能执行完成")
    except Exception as e:
        print(f"   ❌ 登录测试功能出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 控制台登录功能测试完成！")

if __name__ == "__main__":
    test_console_login()