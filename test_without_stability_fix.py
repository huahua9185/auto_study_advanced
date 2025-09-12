#!/usr/bin/env python3
"""
测试完全不执行稳定性修复的情况
用于验证跳动是否真的来自_apply_modal_stability_fixes方法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from operation_decorator import create_enhanced_login_manager, logger
import time

def test_without_stability_fix():
    """测试完全跳过稳定性修复的登录流程"""
    print("🧪 测试：完全跳过稳定性修复")
    print("=" * 60)
    print("💡 这次将跳过所有稳定性修复操作，观察是否还有跳动")
    print("-" * 60)
    
    # 创建一个修改版的LoginManager，跳过稳定性修复
    TrackedLoginManager = create_enhanced_login_manager()
    
    class NoStabilityLoginManager(TrackedLoginManager):
        """跳过稳定性修复的LoginManager"""
        
        def _apply_modal_stability_fixes(self):
            """完全跳过稳定性修复"""
            print("   🚫 跳过稳定性修复操作")
            return True  # 返回True但实际不执行任何操作
        
        def _wait_for_login_modal_stability(self, timeout_seconds=3):
            """简化的等待，不应用修复"""
            print("   🚫 跳过模态框稳定性等待")
            time.sleep(1)  # 简单等待1秒
            return True
    
    login = NoStabilityLoginManager()
    
    try:
        # 1. 初始化浏览器
        print("\n🚀 步骤1: 初始化浏览器")
        if not login.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        print("✅ 浏览器初始化成功")
        
        # 2. 导航到页面
        print("\n📍 步骤2: 导航到登录页面")
        if not login._navigate_to_login():
            print("❌ 导航失败")
            return False
        print("✅ 导航成功")
        
        # 等待页面稳定
        print("\n⏳ 等待3秒，让页面完全加载...")
        time.sleep(3)
        
        # 3. 关键测试：调用原本会执行修复的方法
        print("\n🎯 步骤3: 调用稳定性修复方法（但实际跳过）")
        print("   📍 这次不会执行任何CSS修改")
        print("   👁️  请观察是否还有跳动...")
        
        # 这次应该不会有任何DOM/CSS操作
        result = login._apply_modal_stability_fixes()
        
        if result:
            print("   ✅ 方法调用成功（但跳过了实际修复）")
        else:
            print("   ❌ 方法调用失败")
        
        # 等待观察
        print("\n⏳ 等待5秒，继续观察...")
        time.sleep(5)
        
        # 4. 再次调用
        print("\n🔄 步骤4: 再次调用（确认一致性）")
        result2 = login._apply_modal_stability_fixes()
        print(f"   {'✅ 成功' if result2 else '❌ 失败'}（仍然跳过实际修复）")
        
        print("\n⏳ 再等待3秒...")
        time.sleep(3)
        
        # 5. 尝试真正的登录流程
        print("\n🔐 步骤5: 尝试登录流程（不含稳定性修复）")
        try:
            # 直接调用登录，但稳定性修复已被跳过
            login_result = login.login()
            print(f"   登录结果: {'成功' if login_result else '失败'}")
        except Exception as e:
            print(f"   登录过程异常: {e}")
        
        # 保存日志
        logger.save_log("no_stability_fix_test.json")
        
        print(f"\n✅ 测试完成！")
        print(f"   📊 总操作数: {logger.operation_counter}")
        print(f"   📄 详细日志: no_stability_fix_test.json")
        
        print(f"\n💡 结果分析:")
        print(f"   ✅ 如果这次没有看到跳动 - 确认问题来自稳定性修复方法")
        print(f"   ❌ 如果仍然有跳动 - 问题可能来自其他操作")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        
        logger.save_log("no_stability_fix_error.json")
        return False
    
    finally:
        try:
            input("\n🔚 按回车键关闭浏览器...")
            login.close_browser()
        except:
            pass

def test_minimal_operations():
    """最小化操作测试 - 只做必要操作"""
    print("\n🎯 最小化操作测试")
    print("=" * 40)
    
    TrackedLoginManager = create_enhanced_login_manager()
    login = TrackedLoginManager()
    
    try:
        print("🚀 初始化浏览器...")
        if not login.init_browser():
            return False
        
        print("📍 导航到页面...")
        if not login._navigate_to_login():
            return False
        
        print("⏳ 等待10秒，只观察页面，不做任何操作...")
        time.sleep(10)
        
        print("✅ 最小化测试完成")
        
        logger.save_log("minimal_operations_test.json")
        return True
        
    except Exception as e:
        print(f"❌ 最小化测试异常: {e}")
        return False
    
    finally:
        try:
            input("按回车关闭...")
            login.close_browser()
        except:
            pass

if __name__ == "__main__":
    print("🧪 页面跳动根因测试工具")
    print("=" * 60)
    print("选择测试模式:")
    print("1. 跳过稳定性修复测试 (推荐)")
    print("2. 最小化操作测试")
    print("3. 两个都测试")
    print("4. 退出")
    
    try:
        choice = input("\n请选择 (1/2/3/4): ").strip()
        
        if choice == "1":
            test_without_stability_fix()
        elif choice == "2":
            test_minimal_operations()
        elif choice == "3":
            test_without_stability_fix()
            time.sleep(2)
            test_minimal_operations()
        elif choice == "4":
            print("退出测试")
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试过程异常: {e}")