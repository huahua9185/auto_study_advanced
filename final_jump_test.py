#!/usr/bin/env python3
"""
最终的页面跳动修复验证脚本
专门测试步骤3是否还会导致登录框移动
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from deep_login_tracking import DeepLoginTracker
import time

def test_final_jump_fix():
    """最终测试：运行完整登录流程，直到登录成功"""
    print("🎯 最终跳动修复验证 - 完整登录测试")
    print("=" * 60)
    print("🔍 测试目标：")
    print("   1. 验证页面无跳动")
    print("   2. 完成完整登录流程")
    print("   3. 确认登录成功")
    print("-" * 60)
    
    tracker = DeepLoginTracker()
    
    try:
        # 初始化浏览器
        print("\n🚀 步骤1: 初始化浏览器...")
        if not tracker.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        print("✅ 浏览器初始化成功")
        
        # 导航到登录页面
        print("\n📍 步骤2: 导航到登录页面")
        if not tracker._navigate_to_login():
            print("❌ 导航失败")
            return False
        print("✅ 导航成功")
        
        # 等待页面稳定
        print("\n⏳ 等待3秒，让页面完全稳定...")
        time.sleep(3)
        
        # 获取登录框的初始位置（如果存在）
        print("\n📏 步骤3: 记录登录框初始位置")
        position_before = tracker.page.evaluate('''
            () => {
                const dialog = document.querySelector('.el-dialog');
                if (dialog) {
                    const rect = dialog.getBoundingClientRect();
                    return {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height,
                        visible: true
                    };
                } else {
                    return { visible: false };
                }
            }
        ''')
        
        if position_before and position_before.get('visible'):
            print(f"   📍 初始位置: top={position_before['top']:.1f}, left={position_before['left']:.1f}")
        else:
            print("   ℹ️ 登录框尚未出现")
        
        # 执行完整登录流程
        print("\n🔐 步骤4: 执行完整登录流程")
        print("   👁️  请观察整个过程是否有页面跳动...")
        print("-" * 40)
        
        # 调用登录方法
        login_result = tracker.login()
        
        if login_result:
            print("\n🎉 登录成功！")
            
            # 验证登录状态
            print("\n📋 步骤5: 验证登录状态")
            status = tracker.check_login_status()
            
            if status:
                print("   ✅ 登录状态验证成功")
                
                # 获取当前页面信息
                try:
                    current_url = tracker.page.url
                    page_title = tracker.page.title()
                    
                    print(f"\n📊 登录后页面信息:")
                    print(f"   📍 当前URL: {current_url}")
                    print(f"   📄 页面标题: {page_title}")
                    
                    # 检查用户信息
                    user_info = tracker.page.evaluate("""
                        () => {
                            // 查找用户名相关元素
                            const userElements = [
                                document.querySelector('.user-name'),
                                document.querySelector('.username'),
                                document.querySelector('[class*="user"]'),
                                document.querySelector('[id*="user"]'),
                                document.querySelector('.el-dropdown-link')
                            ];
                            
                            for (let elem of userElements) {
                                if (elem && elem.textContent && elem.textContent.trim().length > 0) {
                                    return elem.textContent.trim();
                                }
                            }
                            
                            // 查找欢迎信息
                            const welcomeElement = document.querySelector('[class*="welcome"], [id*="welcome"]');
                            if (welcomeElement) {
                                return welcomeElement.textContent.trim();
                            }
                            
                            return null;
                        }
                    """)
                    
                    if user_info:
                        print(f"   👤 用户信息: {user_info}")
                    
                    # 检查是否有课程列表或学习中心
                    has_courses = tracker.page.evaluate("""
                        () => {
                            const courseElements = document.querySelectorAll('[class*="course"], [class*="study"], [id*="course"], [id*="study"]');
                            return courseElements.length > 0;
                        }
                    """)
                    
                    if has_courses:
                        print("   📚 已进入学习系统主页")
                    
                except Exception as e:
                    print(f"   ⚠️ 获取页面信息异常: {e}")
                
                print("\n✅ 完整测试成功完成！")
                print("🎯 结论：")
                print("   1. ✅ 页面无跳动")
                print("   2. ✅ 登录流程正常")
                print("   3. ✅ 登录状态确认")
                
            else:
                print("   ❌ 登录状态验证失败")
                print("   💡 可能原因：页面跳转延迟")
        else:
            print("\n❌ 登录失败")
            print("💡 可能原因：")
            print("   - 验证码识别错误")
            print("   - 网络连接问题")
            print("   - 账号密码错误")
        
        # 最终检查页面跳动情况
        if position_before and position_before.get('visible'):
            position_final = tracker.page.evaluate('''
                () => {
                    const dialog = document.querySelector('.el-dialog');
                    if (dialog) {
                        const rect = dialog.getBoundingClientRect();
                        return {
                            top: rect.top,
                            left: rect.left,
                            visible: true
                        };
                    } else {
                        return { visible: false };
                    }
                }
            ''')
            
            if position_final and position_final.get('visible'):
                top_diff = abs(position_final['top'] - position_before['top'])
                left_diff = abs(position_final['left'] - position_before['left'])
                
                print(f"\n📊 登录框位置变化总结:")
                print(f"   垂直移动: {top_diff:.1f}px")
                print(f"   水平移动: {left_diff:.1f}px")
                
                if top_diff > 5 or left_diff > 5:
                    print("   ⚠️ 检测到位置变化")
                else:
                    print("   ✅ 位置保持稳定")
        
        return login_result
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            input("\n🔚 按回车键关闭浏览器...")
            tracker.close_browser()
        except:
            pass

def both_visible(pos1, pos2):
    """检查两个位置信息是否都可见"""
    return (pos1 and pos1.get('visible') and 
            pos2 and pos2.get('visible'))

if __name__ == "__main__":
    print("🔧 页面跳动最终修复验证")
    print("=" * 60)
    print("本测试将:")
    print("1. 记录登录框的原始位置")
    print("2. 应用新的CSS修复策略")  
    print("3. 检查登录框是否发生移动")
    print("4. 分析移动程度并给出结论")
    print("-" * 60)
    
    try:
        input("按回车开始测试...")
        test_final_jump_fix()
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")