#!/usr/bin/env python3
"""
简单的稳定性方法测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager

def test_method_exists():
    """测试方法是否存在并且可以调用"""
    print("🔍 检查稳定性方法是否存在...")
    
    login = LoginManager()
    
    # 检查方法是否存在
    if hasattr(login, '_wait_for_login_modal_stability'):
        print("✅ _wait_for_login_modal_stability 方法存在")
    else:
        print("❌ _wait_for_login_modal_stability 方法不存在")
        return False
    
    if hasattr(login, '_apply_modal_stability_fixes'):
        print("✅ _apply_modal_stability_fixes 方法存在")
    else:
        print("❌ _apply_modal_stability_fixes 方法不存在")
        return False
    
    # 尝试在没有浏览器的情况下调用方法（应该会出错，但至少能看到调用路径）
    print("\n🧪 测试方法调用路径...")
    try:
        result = login._wait_for_login_modal_stability(timeout_seconds=1)
        print(f"⚠️ 意外成功：{result}")
    except Exception as e:
        print(f"❌ 预期异常（无浏览器）: {e}")
    
    try:
        result = login._apply_modal_stability_fixes()
        print(f"⚠️ 意外成功：{result}")
    except Exception as e:
        print(f"❌ 预期异常（无浏览器）: {e}")
    
    return True

def test_method_code():
    """查看方法的实际代码"""
    print("\n📝 检查方法代码...")
    
    login = LoginManager()
    
    # 获取方法对象
    stability_method = getattr(login, '_wait_for_login_modal_stability', None)
    if stability_method:
        print("✅ 获取到 _wait_for_login_modal_stability 方法对象")
        print(f"   方法类型: {type(stability_method)}")
        print(f"   方法文档: {stability_method.__doc__}")
    else:
        print("❌ 无法获取 _wait_for_login_modal_stability 方法")
    
    css_method = getattr(login, '_apply_modal_stability_fixes', None)
    if css_method:
        print("✅ 获取到 _apply_modal_stability_fixes 方法对象")
        print(f"   方法类型: {type(css_method)}")
        print(f"   方法文档: {css_method.__doc__}")
    else:
        print("❌ 无法获取 _apply_modal_stability_fixes 方法")
    
    return True

if __name__ == "__main__":
    print("🔧 登录稳定性方法检查工具")
    print("=" * 40)
    
    success1 = test_method_exists()
    success2 = test_method_code()
    
    if success1 and success2:
        print("\n✅ 方法检查完成")
    else:
        print("\n❌ 方法检查失败")