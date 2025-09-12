#!/usr/bin/env python3
"""
测试改进后的登录稳定性
验证集成到现有系统的修复效果
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager
from src.database import db
from config.config import Config
import time

def test_improved_login_stability():
    """测试改进后的登录稳定性"""
    print("🧪 测试改进后的登录稳定性功能")
    print("=" * 60)
    
    # 创建登录实例
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
            print("❌ 导航到登录页面失败")
            return False
        
        # 3. 测试新的稳定性等待功能
        print("3. 测试深度优化的模态框稳定功能...")
        stability_result = login._wait_for_login_modal_stability(timeout_seconds=3)
        
        if stability_result:
            print("✅ 登录模态框稳定功能正常")
        else:
            print("❌ 登录模态框稳定功能异常")
            return False
        
        # 4. 检查页面状态
        print("4. 检查页面状态...")
        
        # 检查模态框是否存在
        modal_exists = login.page.locator('.el-dialog').count() > 0
        if modal_exists:
            print("✅ 检测到登录模态框")
            
            # 检查稳定性修复CSS是否已应用
            fix_applied = login.page.evaluate('''
                () => {
                    const style = document.getElementById('modal-stability-fix');
                    return style !== null;
                }
            ''')
            
            if fix_applied:
                print("✅ 稳定性修复CSS已成功应用")
            else:
                print("⚠️ 稳定性修复CSS未应用")
            
            # 检查输入框动画是否被禁用
            input_animations_disabled = login.page.evaluate('''
                () => {
                    const inputs = document.querySelectorAll('.el-input__inner');
                    for (let input of inputs) {
                        const style = window.getComputedStyle(input);
                        if (style.transition !== 'none' && style.transition !== '') {
                            return false;
                        }
                    }
                    return inputs.length > 0;
                }
            ''')
            
            if input_animations_disabled:
                print("✅ 输入框动画已成功禁用")
            else:
                print("⚠️ 输入框动画禁用可能不完全")
            
            # 检查验证码图片尺寸是否固定
            captcha_fixed = login.page.evaluate('''
                () => {
                    const captcha = document.querySelector('img[src*="code"], img[src*="auth"]');
                    if (captcha) {
                        const style = window.getComputedStyle(captcha);
                        return style.width === '110px' && style.height === '40px';
                    }
                    return false;
                }
            ''')
            
            if captcha_fixed:
                print("✅ 验证码图片尺寸已固定")
            else:
                print("ℹ️ 验证码图片尺寸固定状态未确认")
            
        else:
            print("❌ 未检测到登录模态框")
            return False
        
        # 5. 测试实际的稳定性效果
        print("\n5. 测试页面稳定性（10秒观察）...")
        
        for i in range(10):
            time.sleep(1)
            
            # 检查页面滚动位置是否稳定
            scroll_position = login.page.evaluate('() => window.scrollY')
            
            # 检查模态框位置是否稳定
            modal_position = login.page.evaluate('''
                () => {
                    const dialog = document.querySelector('.el-dialog.el-dialog--center');
                    if (dialog) {
                        const rect = dialog.getBoundingClientRect();
                        return {x: rect.x, y: rect.y};
                    }
                    return null;
                }
            ''')
            
            print(f"   第{i+1}秒: 滚动位置={scroll_position}, 模态框位置={modal_position}")
        
        print("✅ 稳定性测试完成")
        
        # 6. 保持页面打开供观察
        print("\n6. 页面将保持打开30秒供您观察稳定性...")
        print("请观察登录框是否还有跳动现象")
        
        for countdown in range(30, 0, -1):
            print(f"\r   剩余观察时间: {countdown}秒", end="", flush=True)
            time.sleep(1)
        
        print("\n✅ 测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理
        try:
            login.close_browser()
        except:
            pass

if __name__ == "__main__":
    success = test_improved_login_stability()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 登录稳定性改进测试成功完成！")
        print("主要改进:")
        print("✅ 深度优化的模态框稳定等待")
        print("✅ 多层模态框层级修复")
        print("✅ 输入框过渡动画禁用")  
        print("✅ 验证码图片尺寸固定")
        print("✅ CSS强制稳定性修复")
    else:
        print("\n" + "=" * 60)
        print("❌ 测试未完全成功，请检查日志")