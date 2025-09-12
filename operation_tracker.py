#!/usr/bin/env python3
"""
页面操作编号跟踪脚本
为每个页面元素操作分配编号，帮助识别造成页面跳动的具体操作
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager
from config.config import Config
import time
import json
from datetime import datetime

class OperationTracker:
    """页面操作跟踪器，为每个操作分配编号"""
    
    def __init__(self):
        self.operation_counter = 0
        self.operations_log = []
        self.login_manager = LoginManager()
        
    def log_operation(self, operation_type, element_selector, description, extra_info=None):
        """记录操作"""
        self.operation_counter += 1
        operation = {
            'number': self.operation_counter,
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'element': element_selector,
            'description': description,
            'extra_info': extra_info or {}
        }
        self.operations_log.append(operation)
        
        print(f"\n🔢 操作编号 #{self.operation_counter}")
        print(f"   类型: {operation_type}")
        print(f"   元素: {element_selector}")
        print(f"   描述: {description}")
        if extra_info:
            print(f"   额外信息: {extra_info}")
        print("-" * 50)
        
        return self.operation_counter
    
    def tracked_click(self, selector, description="点击元素", timeout=30000):
        """带跟踪的点击操作"""
        op_num = self.log_operation("click", selector, description)
        
        try:
            element = self.login_manager.page.wait_for_selector(selector, timeout=timeout)
            if element:
                element.click()
                print(f"✅ 操作 #{op_num} 执行成功")
                return True
            else:
                print(f"❌ 操作 #{op_num} 失败: 元素未找到")
                return False
        except Exception as e:
            print(f"❌ 操作 #{op_num} 异常: {e}")
            return False
    
    def tracked_fill(self, selector, value, description="填写表单"):
        """带跟踪的表单填写操作"""
        op_num = self.log_operation("fill", selector, description, {"value": "***隐藏***" if "密码" in description else value})
        
        try:
            element = self.login_manager.page.wait_for_selector(selector, timeout=30000)
            if element:
                element.fill(value)
                print(f"✅ 操作 #{op_num} 执行成功")
                return True
            else:
                print(f"❌ 操作 #{op_num} 失败: 元素未找到")
                return False
        except Exception as e:
            print(f"❌ 操作 #{op_num} 异常: {e}")
            return False
    
    def tracked_navigate(self, url, description="导航到页面"):
        """带跟踪的页面导航操作"""
        op_num = self.log_operation("navigate", "page", description, {"url": url})
        
        try:
            self.login_manager.page.goto(url)
            print(f"✅ 操作 #{op_num} 执行成功")
            return True
        except Exception as e:
            print(f"❌ 操作 #{op_num} 异常: {e}")
            return False
    
    def tracked_wait_for_selector(self, selector, description="等待元素出现", timeout=30000):
        """带跟踪的元素等待操作"""
        op_num = self.log_operation("wait", selector, description, {"timeout": timeout})
        
        try:
            element = self.login_manager.page.wait_for_selector(selector, timeout=timeout)
            if element:
                print(f"✅ 操作 #{op_num} 执行成功")
                return element
            else:
                print(f"❌ 操作 #{op_num} 失败: 超时")
                return None
        except Exception as e:
            print(f"❌ 操作 #{op_num} 异常: {e}")
            return None
    
    def tracked_evaluate(self, script, description="执行JavaScript"):
        """带跟踪的JavaScript执行操作"""
        op_num = self.log_operation("evaluate", "javascript", description, {"script": script[:100] + "..." if len(script) > 100 else script})
        
        try:
            result = self.login_manager.page.evaluate(script)
            print(f"✅ 操作 #{op_num} 执行成功")
            return result
        except Exception as e:
            print(f"❌ 操作 #{op_num} 异常: {e}")
            return None
    
    def tracked_hover(self, selector, description="鼠标悬停"):
        """带跟踪的鼠标悬停操作"""
        op_num = self.log_operation("hover", selector, description)
        
        try:
            element = self.login_manager.page.wait_for_selector(selector, timeout=30000)
            if element:
                element.hover()
                print(f"✅ 操作 #{op_num} 执行成功")
                return True
            else:
                print(f"❌ 操作 #{op_num} 失败: 元素未找到")
                return False
        except Exception as e:
            print(f"❌ 操作 #{op_num} 异常: {e}")
            return False
    
    def save_operations_log(self, filename="operations_log.json"):
        """保存操作日志"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.operations_log, f, ensure_ascii=False, indent=2)
        print(f"\n📄 操作日志已保存到: {filename}")

def test_login_with_operation_tracking():
    """使用操作跟踪进行登录测试"""
    print("🎯 开始页面操作跟踪测试")
    print("=" * 60)
    
    tracker = OperationTracker()
    
    try:
        # 1. 初始化浏览器
        print("\n🚀 第1步: 初始化浏览器")
        if not tracker.login_manager.initialize_browser():
            print("❌ 浏览器初始化失败")
            return False
        print("✅ 浏览器初始化成功")
        
        # 2. 导航到登录页面
        print("\n📍 第2步: 导航到登录页面")
        login_url = Config.BASE_URL.rstrip('#/')
        if not tracker.tracked_navigate(login_url, "导航到主页面"):
            print("❌ 导航失败")
            return False
        
        # 等待页面加载
        time.sleep(2)
        
        # 3. 寻找并点击登录按钮
        print("\n🔍 第3步: 寻找登录按钮")
        login_selectors = [
            '.login-btn',
            'button:has-text("登录")',
            'button:has-text("登陆")',
            '[class*="login"]',
            '[id*="login"]',
            'a[href*="login"]',
            '.el-button:has-text("登录")'
        ]
        
        login_found = False
        for i, selector in enumerate(login_selectors):
            print(f"\n🔍 尝试登录选择器 {i+1}: {selector}")
            if tracker.tracked_click(selector, f"点击登录按钮 (选择器{i+1})"):
                login_found = True
                break
            time.sleep(1)
        
        if not login_found:
            print("❌ 未找到任何登录按钮")
            # 尝试截图保存当前页面状态
            tracker.login_manager.page.screenshot(path="login_button_not_found.png")
            print("📸 页面截图已保存: login_button_not_found.png")
            return False
        
        # 4. 等待登录模态框出现
        print("\n⏳ 第4步: 等待登录模态框出现")
        modal_selectors = [
            '.el-dialog',
            '.modal',
            '.login-modal',
            '[role="dialog"]'
        ]
        
        modal_found = False
        for selector in modal_selectors:
            modal = tracker.tracked_wait_for_selector(selector, f"等待模态框: {selector}", timeout=5000)
            if modal:
                modal_found = True
                break
        
        if not modal_found:
            print("❌ 登录模态框未出现")
            return False
        
        # 5. 应用稳定性修复
        print("\n🔧 第5步: 应用页面稳定性修复")
        stability_script = """
        // 禁用所有动画和过渡效果
        const style = document.createElement('style');
        style.textContent = `
            *, *::before, *::after {
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
            }
            .el-dialog__wrapper {
                animation: none !important;
            }
            .el-fade-in-linear-enter-active, .el-fade-in-linear-leave-active {
                transition: none !important;
            }
        `;
        document.head.appendChild(style);
        console.log('稳定性CSS已应用');
        """
        
        tracker.tracked_evaluate(stability_script, "应用页面稳定性CSS修复")
        
        # 6. 填写登录信息
        print("\n✏️ 第6步: 填写登录信息")
        
        # 等待用户名输入框
        username_selectors = [
            'input[type="text"]',
            'input[placeholder*="用户名"]',
            'input[placeholder*="账号"]',
            '.el-input__inner[type="text"]'
        ]
        
        username_filled = False
        for selector in username_selectors:
            username_input = tracker.tracked_wait_for_selector(selector, f"等待用户名输入框: {selector}", timeout=3000)
            if username_input:
                if tracker.tracked_fill(selector, Config.USERNAME, "填写用户名"):
                    username_filled = True
                    break
        
        if not username_filled:
            print("❌ 用户名填写失败")
        
        # 等待密码输入框
        password_selectors = [
            'input[type="password"]',
            'input[placeholder*="密码"]',
            '.el-input__inner[type="password"]'
        ]
        
        password_filled = False
        for selector in password_selectors:
            password_input = tracker.tracked_wait_for_selector(selector, f"等待密码输入框: {selector}", timeout=3000)
            if password_input:
                if tracker.tracked_fill(selector, Config.PASSWORD, "填写密码"):
                    password_filled = True
                    break
        
        if not password_filled:
            print("❌ 密码填写失败")
        
        # 7. 检查验证码
        print("\n🔐 第7步: 检查验证码")
        captcha_selectors = [
            '.captcha',
            '[class*="captcha"]',
            'input[placeholder*="验证码"]',
            '.verify-code'
        ]
        
        for selector in captcha_selectors:
            captcha = tracker.tracked_wait_for_selector(selector, f"检查验证码: {selector}", timeout=2000)
            if captcha:
                print("⚠️ 检测到验证码，需要手动处理")
                break
        
        # 8. 点击登录提交按钮
        print("\n🚀 第8步: 点击登录提交按钮")
        submit_selectors = [
            'button[type="submit"]',
            '.login-submit',
            '.el-button--primary',
            'button:has-text("登录")',
            'button:has-text("确定")'
        ]
        
        submit_clicked = False
        for selector in submit_selectors:
            if tracker.tracked_click(selector, f"点击登录提交按钮: {selector}"):
                submit_clicked = True
                break
            time.sleep(1)
        
        if not submit_clicked:
            print("❌ 登录提交按钮点击失败")
        
        # 9. 等待登录结果
        print("\n⏳ 第9步: 等待登录结果")
        time.sleep(3)
        
        # 10. 检查页面状态
        print("\n🔍 第10步: 检查页面状态")
        current_url = tracker.tracked_evaluate("window.location.href", "获取当前页面URL")
        page_title = tracker.tracked_evaluate("document.title", "获取页面标题")
        
        print(f"当前URL: {current_url}")
        print(f"页面标题: {page_title}")
        
        # 保存操作日志
        tracker.save_operations_log("login_operations_log.json")
        
        print(f"\n✅ 测试完成，共执行了 {tracker.operation_counter} 个操作")
        print("📋 您可以查看 login_operations_log.json 了解详细的操作序列")
        print("💡 如果出现页面跳动，请记录跳动发生在哪个操作编号之后")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存异常时的操作日志
        tracker.save_operations_log("error_operations_log.json")
        return False
    
    finally:
        try:
            # 等待用户观察
            input("\n按回车键关闭浏览器...")
            tracker.login_manager.close_browser()
        except:
            pass

if __name__ == "__main__":
    test_login_with_operation_tracking()