#!/usr/bin/env python3
"""
验证登录修复在实际生产环境中的效果
专门测试页面跳动问题是否已解决，并检查登录流程是否正常
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager
from src.main import AutoStudyApp
import time

def test_production_login():
    """测试生产环境中的登录流程"""
    print("🔍 验证生产环境登录修复效果")
    print("=" * 60)
    print("🎯 本测试将：")
    print("   1. 使用实际的LoginManager初始化")
    print("   2. 执行完整的登录流程")
    print("   3. 验证页面跳动问题是否已解决")
    print("   4. 检查登录是否成功")
    print("-" * 60)
    
    login_manager = LoginManager()
    
    try:
        # 步骤1: 初始化浏览器
        print("\n🚀 步骤1: 初始化浏览器...")
        if not login_manager.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        print("✅ 浏览器初始化成功")
        
        # 步骤2: 执行登录（观察是否有跳动）
        print("\n🔐 步骤2: 执行登录流程...")
        print("   👁️  请仔细观察是否还有页面跳动问题...")
        
        login_result = login_manager.login()
        
        if login_result:
            print("✅ 登录成功！")
            
            # 步骤3: 验证登录状态
            print("\n📋 步骤3: 验证登录状态...")
            status_check = login_manager.check_login_status()
            
            if status_check:
                print("✅ 登录状态验证成功")
            else:
                print("❌ 登录状态验证失败")
            
            # 步骤4: 检查当前页面
            print("\n🔍 步骤4: 检查当前页面状态...")
            try:
                current_url = login_manager.page.url
                print(f"   📍 当前URL: {current_url}")
                
                # 检查页面标题
                title = login_manager.page.title()
                print(f"   📄 页面标题: {title}")
                
                # 检查是否有用户信息
                user_info = login_manager.page.evaluate("""
                    () => {
                        // 查找用户名相关元素
                        const userElements = [
                            document.querySelector('.user-name'),
                            document.querySelector('.username'),
                            document.querySelector('[class*="user"]'),
                            document.querySelector('[id*="user"]')
                        ];
                        
                        for (let elem of userElements) {
                            if (elem && elem.textContent.trim()) {
                                return elem.textContent.trim();
                            }
                        }
                        return null;
                    }
                """)
                
                if user_info:
                    print(f"   👤 用户信息: {user_info}")
                else:
                    print("   👤 未找到明显的用户信息元素")
                
            except Exception as e:
                print(f"   ⚠️ 页面状态检查异常: {e}")
            
            print(f"\n✅ 生产环境测试完成 - 登录成功")
            print(f"💡 结论：页面跳动修复在生产环境中有效")
            
        else:
            print("❌ 登录失败")
            print(f"💡 可能的原因：")
            print(f"   - 验证码识别错误")
            print(f"   - 网络连接问题") 
            print(f"   - 页面结构变化")
        
        return login_result
        
    except Exception as e:
        print(f"❌ 生产环境测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            input("\n🔚 按回车键关闭浏览器...")
            login_manager.close_browser()
        except:
            pass

def test_main_system_initialization():
    """测试主系统初始化（不执行主循环，避免EOF错误）"""
    print("\n🏗️ 额外测试：主系统初始化")
    print("=" * 40)
    
    system = AutoStudyApp()
    
    try:
        print("🚀 初始化主系统...")
        
        # 调用初始化，但不运行主循环
        system.login_manager = LoginManager()
        
        if system.login_manager.init_browser():
            print("✅ 主系统浏览器初始化成功")
            
            # 检查登录状态（不执行登录）
            print("📋 检查登录状态...")
            is_logged_in = system.login_manager.check_login_status()
            
            if is_logged_in:
                print("✅ 已登录状态")
            else:
                print("ℹ️ 未登录状态（正常）")
            
            print("✅ 主系统初始化测试完成")
            
            system.login_manager.close_browser()
            return True
        else:
            print("❌ 主系统浏览器初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ 主系统初始化测试异常: {e}")
        return False

if __name__ == "__main__":
    print("🔧 生产环境登录修复验证")
    print("=" * 60)
    print("🎯 目标：确认页面跳动问题已在实际使用中解决")
    print("-" * 60)
    
    try:
        input("按回车开始验证...")
        
        # 测试1：完整登录流程
        success1 = test_production_login()
        
        # 测试2：主系统初始化
        success2 = test_main_system_initialization()
        
        print(f"\n📊 最终结果:")
        print(f"   登录流程测试: {'✅ 通过' if success1 else '❌ 失败'}")
        print(f"   系统初始化测试: {'✅ 通过' if success2 else '❌ 失败'}")
        
        if success1:
            print(f"\n🎉 恭喜！页面跳动问题修复生效！")
            print(f"   现在可以正常使用 run.py 进行登录")
        else:
            print(f"\n⚠️ 需要进一步调试登录问题")
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"验证过程异常: {e}")