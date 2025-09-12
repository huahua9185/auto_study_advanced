#!/usr/bin/env python3
"""
集成式操作跟踪测试脚本
使用装饰器跟踪实际登录过程中的所有操作
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from operation_decorator import create_enhanced_login_manager, logger
from config.config import Config
import time

def test_login_with_full_tracking():
    """使用完整操作跟踪进行登录测试"""
    print("🎯 开始完整登录操作跟踪测试")
    print("=" * 60)
    print("💡 所有页面操作都会被分配编号，帮助您定位跳动原因")
    print("-" * 60)
    
    # 创建增强版LoginManager
    TrackedLoginManager = create_enhanced_login_manager()
    login = TrackedLoginManager()
    
    try:
        # 1. 初始化浏览器
        print("\n🚀 步骤1: 初始化浏览器")
        if not login.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        print("✅ 浏览器初始化完成")
        
        # 2. 执行登录流程
        print("\n🔐 步骤2: 开始登录流程")
        print("⚠️  请仔细观察哪个操作编号后出现了页面跳动")
        
        # 每个操作后都暂停，让用户观察
        def pause_for_observation(step_name):
            print(f"\n⏸️  {step_name} 完成")
            print("   👁️  请观察页面状态，是否有跳动？")
            print("   📝 如有跳动，请记录最后一个操作编号")
            time.sleep(2)  # 给用户观察时间
        
        # 开始登录流程
        success = login.login()
        
        if success:
            print("\n✅ 登录成功！")
        else:
            print("\n❌ 登录失败")
        
        pause_for_observation("整个登录流程")
        
        # 3. 保存详细的操作日志
        print("\n📊 步骤3: 保存操作分析报告")
        logger.save_log("detailed_login_operations.json")
        
        # 4. 显示操作摘要
        print(f"\n📈 操作摘要:")
        print(f"   总操作数: {logger.operation_counter}")
        print(f"   成功操作: {len([op for op in logger.operations_log if op['result'] == 'success'])}")
        print(f"   失败操作: {len([op for op in logger.operations_log if op['result'] == 'error'])}")
        
        # 5. 显示关键操作点
        print(f"\n🔍 关键操作点分析:")
        key_operations = [
            ('navigate', '页面导航'),
            ('click', '点击操作'),
            ('fill', '表单填写'),
            ('wait', '等待操作'),
            ('evaluate', 'JavaScript执行')
        ]
        
        for op_type, op_desc in key_operations:
            matching_ops = [op for op in logger.operations_log if op['type'] == op_type]
            if matching_ops:
                print(f"   {op_desc}: 编号 {[op['number'] for op in matching_ops]}")
        
        print(f"\n💡 使用指南:")
        print(f"   1. 如果看到页面跳动，记录跳动发生在哪个操作编号之后")
        print(f"   2. 查看 detailed_login_operations.json 找到对应操作的详细信息")
        print(f"   3. 该操作就是导致页面跳动的根源")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")
        import traceback
        traceback.print_exc()
        
        # 异常情况下也要保存日志
        logger.save_log("error_login_operations.json")
        return False
    
    finally:
        try:
            input("\n🔚 按回车键关闭浏览器并结束测试...")
            login.close_browser()  # 这里也会自动保存日志
        except:
            pass

def test_specific_operations():
    """测试特定的可能导致跳动的操作"""
    print("\n🎯 特定操作测试")
    print("=" * 40)
    
    TrackedLoginManager = create_enhanced_login_manager()
    login = TrackedLoginManager()
    
    try:
        # 初始化
        if not login.init_browser():
            return False
        
        # 导航
        if not login._navigate_to_login():
            return False
        
        print("\n⏳ 等待5秒，观察页面初始状态...")
        time.sleep(5)
        
        # 寻找并点击登录按钮
        print("\n🖱️  即将寻找登录按钮，请观察是否有跳动...")
        # 直接使用页面操作而不是调用不存在的方法
        try:
            login.page.click('button:has-text("登录")', timeout=3000)
            print("   ✅ 登录按钮点击成功")
        except Exception as e:
            print(f"   ❌ 登录按钮点击失败: {e}")
        
        print("\n⏳ 点击后等待3秒，观察页面变化...")
        time.sleep(3)
        
        # 等待模态框
        print("\n⏳ 等待登录模态框，观察是否有跳动...")
        try:
            login.page.wait_for_selector('.el-dialog', timeout=5000)
            print("   ✅ 登录模态框出现")
        except Exception as e:
            print(f"   ❌ 登录模态框等待失败: {e}")
        
        print("\n⏳ 模态框出现后等待3秒，观察页面状态...")
        time.sleep(3)
        
        # 应用稳定性修复
        print("\n🔧 应用稳定性修复，观察是否有跳动...")
        login._apply_modal_stability_fixes()
        
        print("\n⏳ 稳定性修复后等待3秒...")
        time.sleep(3)
        
        # 填写表单
        print("\n✏️  填写用户名，观察是否有跳动...")
        login._fill_username()  # 不需要参数
        
        print("\n⏳ 用户名填写后等待2秒...")
        time.sleep(2)
        
        print("\n✏️  填写密码，观察是否有跳动...")
        login._fill_password()  # 不需要参数
        
        print("\n⏳ 密码填写后等待2秒...")
        time.sleep(2)
        
        print("\n🚀 提交登录，观察是否有跳动...")
        login._submit_login_form()  # 修正方法名
        
        print("\n⏳ 登录提交后等待5秒...")
        time.sleep(5)
        
        logger.save_log("specific_operations_test.json")
        
        return True
        
    except Exception as e:
        print(f"❌ 特定操作测试异常: {e}")
        logger.save_log("specific_operations_error.json")
        return False
    
    finally:
        try:
            input("\n按回车键关闭...")
            login.close_browser()
        except:
            pass

if __name__ == "__main__":
    print("🎯 页面操作跟踪测试工具")
    print("=" * 60)
    print("选择测试模式:")
    print("1. 完整登录流程跟踪 (推荐)")
    print("2. 特定操作分步测试")
    print("3. 退出")
    
    try:
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == "1":
            test_login_with_full_tracking()
        elif choice == "2":
            test_specific_operations()
        elif choice == "3":
            print("退出")
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")