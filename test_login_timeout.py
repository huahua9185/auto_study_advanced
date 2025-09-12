#!/usr/bin/env python
"""
测试登录页面加载超时问题
"""

import logging
import sys
import time

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加src目录到系统路径
sys.path.insert(0, 'src')

from login import LoginManager
from config.config import Config

def test_login():
    """测试登录流程，特别关注页面加载超时"""
    login_manager = LoginManager()
    
    try:
        print("=" * 60)
        print("开始测试登录页面加载")
        print("=" * 60)
        
        # 初始化浏览器
        login_manager.init_browser()
        print("✅ 浏览器初始化成功")
        
        # 测试页面加载
        print("\n测试页面加载（带超时设置）...")
        start_time = time.time()
        
        # 访问登录页面
        login_manager.page.goto(Config.BASE_URL)
        
        # 测试不同的等待策略
        print("\n1. 测试 networkidle 等待（5秒超时）...")
        try:
            login_manager.page.wait_for_load_state('networkidle', timeout=5000)
            print(f"   ✅ networkidle 完成，耗时: {time.time() - start_time:.2f}秒")
        except Exception as e:
            print(f"   ⚠️  networkidle 超时，耗时: {time.time() - start_time:.2f}秒")
        
        print("\n2. 测试 domcontentloaded 等待...")
        start_time = time.time()
        try:
            login_manager.page.wait_for_load_state('domcontentloaded', timeout=5000)
            print(f"   ✅ domcontentloaded 完成，耗时: {time.time() - start_time:.2f}秒")
        except Exception as e:
            print(f"   ⚠️  domcontentloaded 超时，耗时: {time.time() - start_time:.2f}秒")
        
        print("\n3. 测试 load 等待...")
        start_time = time.time()
        try:
            login_manager.page.wait_for_load_state('load', timeout=5000)
            print(f"   ✅ load 完成，耗时: {time.time() - start_time:.2f}秒")
        except Exception as e:
            print(f"   ⚠️  load 超时，耗时: {time.time() - start_time:.2f}秒")
        
        # 检查关键元素是否存在
        print("\n检查登录页面关键元素...")
        
        # 检查登录按钮
        login_button_exists = login_manager.page.locator('text=登录').count() > 0
        print(f"   登录按钮: {'✅ 存在' if login_button_exists else '❌ 不存在'}")
        
        # 检查用户名输入框
        username_input_exists = login_manager.page.locator('input[placeholder*="用户名"]').count() > 0
        print(f"   用户名输入框: {'✅ 存在' if username_input_exists else '❌ 不存在'}")
        
        # 检查密码输入框
        password_input_exists = login_manager.page.locator('input[type="password"]').count() > 0
        print(f"   密码输入框: {'✅ 存在' if password_input_exists else '❌ 不存在'}")
        
        # 测试完整登录流程
        print("\n" + "=" * 60)
        print("测试完整登录流程")
        print("=" * 60)
        
        success = login_manager.login()
        
        if success:
            print("✅ 登录成功！")
        else:
            print("❌ 登录失败")
        
        print("\n保持浏览器打开10秒以便观察...")
        time.sleep(10)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        if hasattr(login_manager, 'browser') and login_manager.browser:
            login_manager.close_browser()
            print("\n浏览器已关闭")

if __name__ == "__main__":
    test_login()