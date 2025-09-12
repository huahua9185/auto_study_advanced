#!/usr/bin/env python3
"""
测试修复后的稳定性方法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager

def test_fixed_methods():
    """测试修复后的方法能否正确处理页面为空的情况"""
    print("🔧 测试修复后的稳定性方法")
    print("=" * 40)
    
    login = LoginManager()
    
    # 测试页面为空时的情况
    print("1. 测试页面为空时的处理...")
    print(f"   当前页面状态: {login.page}")
    
    # 测试稳定性方法
    try:
        result = login._wait_for_login_modal_stability(timeout_seconds=1)
        print(f"   稳定性方法返回: {result}")
        print("   ✅ 方法正确处理了页面为空的情况")
    except Exception as e:
        print(f"   ❌ 方法仍有异常: {e}")
        return False
    
    # 测试CSS修复方法
    try:
        result = login._apply_modal_stability_fixes()
        print(f"   CSS修复方法返回: {result}")
        print("   ✅ CSS方法正确处理了页面为空的情况")
    except Exception as e:
        print(f"   ❌ CSS方法仍有异常: {e}")
        return False
    
    print("\n2. 现在可以运行main.py了，应该能看到正确的日志输出")
    print("   预期日志:")
    print("   - '等待登录模态框稳定（深度优化版）...'")
    print("   - '页面对象为空，无法执行稳定性修复'")
    
    return True

if __name__ == "__main__":
    test_fixed_methods()