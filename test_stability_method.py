#!/usr/bin/env python3
"""
测试稳定性方法是否能正常执行
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager
from config.config import Config
import time

def test_stability_method():
    """测试稳定性方法执行情况"""
    print("🧪 测试登录稳定性方法执行情况")
    print("=" * 50)
    
    login = LoginManager()
    
    try:
        # 1. 初始化浏览器
        print("1. 初始化浏览器...")
        if not login.initialize_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        # 2. 导航到登录页面
        print("2. 导航到登录页面...")
        if not login._navigate_to_login():
            print("❌ 导航失败")
            return False
        
        # 3. 等待登录框出现
        print("3. 等待登录框出现...")
        try:
            login.page.wait_for_selector('.el-dialog', timeout=5000)
            print("   ✅ 登录框已出现")
        except Exception as e:
            print(f"   ❌ 登录框未出现: {e}")
            return False
        
        # 4. 直接测试稳定性方法
        print("4. 直接调用稳定性方法...")
        try:
            result = login._wait_for_login_modal_stability(timeout_seconds=3)
            if result:
                print("   ✅ 稳定性方法执行成功")
            else:
                print("   ⚠️ 稳定性方法返回False")
        except Exception as e:
            print(f"   ❌ 稳定性方法执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 5. 测试单独的CSS修复方法
        print("5. 测试CSS修复方法...")
        try:
            css_result = login._apply_modal_stability_fixes()
            if css_result:
                print("   ✅ CSS修复方法执行成功")
            else:
                print("   ⚠️ CSS修复方法返回False")
        except Exception as e:
            print(f"   ❌ CSS修复方法执行异常: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(2)
        print("6. 测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            login.close_browser()
        except:
            pass

if __name__ == "__main__":
    test_stability_method()