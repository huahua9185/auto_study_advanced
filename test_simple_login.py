#!/usr/bin/env python3
"""
简单登录测试 - 验证修复页面抖动问题后的效果
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager

def simple_login_test():
    """简单的登录测试"""
    print("=" * 50)
    print("简单登录测试 - 验证页面抖动修复")
    print("=" * 50)
    
    try:
        # 初始化浏览器
        print("1. 初始化浏览器...")
        if not login_manager.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        print("2. 开始登录测试...")
        start_time = time.time()
        
        # 执行登录
        login_success = login_manager.login()
        
        login_time = time.time() - start_time
        
        if login_success:
            print(f"✅ 登录成功！耗时: {login_time:.2f}s")
            print("\n检查登录状态...")
            if login_manager.check_login_status():
                print("✅ 登录状态确认")
            else:
                print("⚠️  登录状态未确认")
            return True
        else:
            print(f"❌ 登录失败！耗时: {login_time:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        return False
        
    finally:
        if login_manager:
            login_manager.close_browser()
        print("\n测试完成")

if __name__ == "__main__":
    success = simple_login_test()
    exit_code = 0 if success else 1
    sys.exit(exit_code)