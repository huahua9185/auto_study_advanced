#!/usr/bin/env python3
"""
验证页面跳动修复效果的脚本
专门测试操作#2(_apply_modal_stability_fixes)是否还会引起跳动
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from operation_decorator import create_enhanced_login_manager, logger
import time

def test_jump_fix():
    """专门测试跳动修复效果"""
    print("🔧 验证页面跳动修复效果")
    print("=" * 60)
    print("⚠️  请重点观察操作#2是否还会引起页面跳动")
    print("-" * 60)
    
    TrackedLoginManager = create_enhanced_login_manager()
    login = TrackedLoginManager()
    
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
        
        # 3. 重点测试：应用稳定性修复（这是之前引起跳动的操作）
        print("\n🎯 步骤3: 应用稳定性修复 - 重点观察是否跳动")
        print("   📍 这是之前引起跳动的操作#2")
        print("   👁️  请仔细观察页面是否还会跳动...")
        
        # 执行修复操作
        result = login._apply_modal_stability_fixes()
        
        if result:
            print("   ✅ 稳定性修复执行成功")
        else:
            print("   ❌ 稳定性修复执行失败")
        
        # 等待观察
        print("\n⏳ 修复后等待5秒，继续观察页面状态...")
        time.sleep(5)
        
        # 4. 再次应用修复（测试重复应用是否会跳动）
        print("\n🔄 步骤4: 再次应用修复（测试重复应用）")
        print("   📍 测试重复应用是否会引起跳动...")
        
        result2 = login._apply_modal_stability_fixes()
        
        if result2:
            print("   ✅ 第二次修复执行成功")
        else:
            print("   ❌ 第二次修复执行失败")
        
        print("\n⏳ 第二次修复后等待3秒...")
        time.sleep(3)
        
        # 5. 检查浏览器控制台消息
        print("\n📋 步骤5: 检查控制台消息")
        try:
            # 获取控制台消息
            console_script = """
            () => {
                const logs = window.console._logs || [];
                return logs.slice(-5); // 获取最近5条消息
            }
            """
            logs = login.page.evaluate(console_script)
            if logs:
                print("   📝 控制台消息:")
                for log in logs:
                    print(f"      - {log}")
            else:
                print("   📝 没有捕获到控制台消息")
        except Exception as e:
            print(f"   ⚠️ 无法获取控制台消息: {e}")
        
        # 6. 保存操作日志
        logger.save_log("jump_fix_verification.json")
        
        print(f"\n✅ 验证测试完成！")
        print(f"   📊 总操作数: {logger.operation_counter}")
        print(f"   📄 详细日志: jump_fix_verification.json")
        
        print(f"\n💡 结果评估:")
        print(f"   ✅ 如果操作#2后没有看到页面跳动 - 修复成功")
        print(f"   ❌ 如果操作#2后仍然看到页面跳动 - 需要进一步优化")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证测试异常: {e}")
        import traceback
        traceback.print_exc()
        
        logger.save_log("jump_fix_verification_error.json")
        return False
    
    finally:
        try:
            input("\n🔚 按回车键关闭浏览器并结束验证...")
            login.close_browser()
        except:
            pass

def test_multiple_applications():
    """测试连续多次应用修复是否会累积跳动"""
    print("\n🔄 额外测试: 连续多次应用修复")
    print("=" * 40)
    
    TrackedLoginManager = create_enhanced_login_manager()
    login = TrackedLoginManager()
    
    try:
        if not login.init_browser():
            return False
        
        if not login._navigate_to_login():
            return False
        
        print("\n📍 将连续执行5次稳定性修复，观察累积效果...")
        
        for i in range(1, 6):
            print(f"\n🔧 第 {i} 次应用修复...")
            result = login._apply_modal_stability_fixes()
            print(f"   {'✅ 成功' if result else '❌ 失败'}")
            time.sleep(2)  # 等待观察
        
        print("\n✅ 连续应用测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 连续应用测试异常: {e}")
        return False
    
    finally:
        try:
            login.close_browser()
        except:
            pass

if __name__ == "__main__":
    print("🔧 页面跳动修复验证工具")
    print("=" * 60)
    print("选择测试模式:")
    print("1. 基础修复验证 (推荐)")
    print("2. 连续应用测试")
    print("3. 两个都测试")
    print("4. 退出")
    
    try:
        choice = input("\n请选择 (1/2/3/4): ").strip()
        
        if choice == "1":
            test_jump_fix()
        elif choice == "2":
            test_multiple_applications()
        elif choice == "3":
            test_jump_fix()
            time.sleep(2)
            test_multiple_applications()
        elif choice == "4":
            print("退出验证")
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n用户中断验证")
    except Exception as e:
        print(f"验证过程异常: {e}")