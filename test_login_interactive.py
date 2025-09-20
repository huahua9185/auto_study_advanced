#!/usr/bin/env python3
"""
测试登录管理器的交互式功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager

def test_interactive_login():
    """测试交互式登录"""
    print("🧪 测试交互式登录功能")
    print("=" * 50)

    # 1. 初始化
    print("📋 1. 初始化配置和登录管理器...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)

    # 2. 测试交互式登录
    print("📋 2. 测试交互式登录...")
    print("注意: 这会真正执行登录流程，包括验证码识别")

    try:
        success = login_manager.interactive_login()
        print(f"   交互式登录结果: {'成功' if success else '失败'}")

        if success:
            # 显示登录状态
            login_manager.show_login_status()

            # 获取API客户端
            api_client = login_manager.get_api_client()
            print(f"   API客户端: {'可用' if api_client else '不可用'}")

    except KeyboardInterrupt:
        print("\n⚠️ 用户取消了登录")
    except Exception as e:
        print(f"❌ 登录过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    # 3. 清理
    print("📋 3. 清理资源...")
    login_manager.close_sync()
    print("✅ 测试完成")

if __name__ == "__main__":
    test_interactive_login()