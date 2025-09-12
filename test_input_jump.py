#!/usr/bin/env python3
"""
测试登录表单输入时的跳动问题
专门监测输入用户名、密码、验证码时的页面跳动和输入阻碍
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import login_manager
from config.config import Config
import time

class InputJumpTester:
    """输入跳动测试器"""
    
    def __init__(self):
        self.login_manager = login_manager
        self.step_count = 0
        
    def record_page_state(self, label):
        """记录页面状态，重点关注输入相关的变化"""
        if not self.login_manager.page:
            return {'label': label, 'error': 'No page'}
            
        try:
            state = self.login_manager.page.evaluate('''
                () => {
                    const dialog = document.querySelector('.el-dialog');
                    const usernameInput = document.querySelector('input[placeholder*="用户名"]');
                    const passwordInput = document.querySelector('input[type="password"]');
                    const captchaInput = document.querySelector('input[placeholder*="验证码"]');
                    
                    return {
                        // 页面滚动
                        scrollX: window.scrollX,
                        scrollY: window.scrollY,
                        
                        // 对话框状态
                        dialogExists: dialog !== null,
                        dialogTop: dialog ? dialog.getBoundingClientRect().top : null,
                        dialogLeft: dialog ? dialog.getBoundingClientRect().left : null,
                        dialogHeight: dialog ? dialog.getBoundingClientRect().height : null,
                        dialogWidth: dialog ? dialog.getBoundingClientRect().width : null,
                        
                        // 输入框状态
                        usernameInputExists: usernameInput !== null,
                        usernameInputTop: usernameInput ? usernameInput.getBoundingClientRect().top : null,
                        usernameInputFocused: usernameInput ? (document.activeElement === usernameInput) : false,
                        usernameInputValue: usernameInput ? usernameInput.value : '',
                        
                        passwordInputExists: passwordInput !== null,
                        passwordInputTop: passwordInput ? passwordInput.getBoundingClientRect().top : null,
                        passwordInputFocused: passwordInput ? (document.activeElement === passwordInput) : false,
                        passwordInputValue: passwordInput ? passwordInput.value.length : 0,
                        
                        captchaInputExists: captchaInput !== null,
                        captchaInputTop: captchaInput ? captchaInput.getBoundingClientRect().top : null,
                        captchaInputFocused: captchaInput ? (document.activeElement === captchaInput) : false,
                        captchaInputValue: captchaInput ? captchaInput.value : '',
                        
                        // 页面尺寸
                        bodyHeight: document.body.scrollHeight,
                        
                        timestamp: Date.now()
                    };
                }
            ''')
            state['label'] = label
            return state
        except Exception as e:
            return {'label': label, 'error': str(e)}
    
    def check_input_jump(self, before, after, threshold=5):
        """检查输入操作是否导致跳动"""
        if not before or not after or 'error' in before or 'error' in after:
            return False, "无法比较"
        
        # 检查各种位置变化
        changes = {}
        jumped = False
        
        # 滚动变化
        scroll_x_diff = abs(after.get('scrollX', 0) - before.get('scrollX', 0))
        scroll_y_diff = abs(after.get('scrollY', 0) - before.get('scrollY', 0))
        changes['scroll_x_change'] = scroll_x_diff
        changes['scroll_y_change'] = scroll_y_diff
        
        # 对话框位置变化
        if before.get('dialogTop') is not None and after.get('dialogTop') is not None:
            dialog_top_diff = abs(after['dialogTop'] - before['dialogTop'])
            dialog_left_diff = abs(after['dialogLeft'] - before['dialogLeft'])
            changes['dialog_top_change'] = dialog_top_diff
            changes['dialog_left_change'] = dialog_left_diff
            
            if dialog_top_diff > threshold or dialog_left_diff > threshold:
                jumped = True
        
        # 输入框位置变化
        for field in ['username', 'password', 'captcha']:
            before_top = before.get(f'{field}InputTop')
            after_top = after.get(f'{field}InputTop')
            if before_top is not None and after_top is not None:
                input_top_diff = abs(after_top - before_top)
                changes[f'{field}_input_top_change'] = input_top_diff
                if input_top_diff > threshold:
                    jumped = True
        
        # 页面高度变化
        height_diff = abs(after.get('bodyHeight', 0) - before.get('bodyHeight', 0))
        changes['body_height_change'] = height_diff
        
        # 滚动变化检查
        if scroll_x_diff > threshold or scroll_y_diff > threshold:
            jumped = True
        
        return jumped, changes
    
    def test_input_step(self, step_name, input_action):
        """测试单个输入步骤"""
        self.step_count += 1
        print(f"\n{'='*60}")
        print(f"🔢 输入步骤 #{self.step_count}: {step_name}")
        print(f"{'='*60}")
        
        # 记录输入前状态
        before_state = self.record_page_state(f"输入前_{step_name}")
        if 'error' not in before_state:
            print(f"📏 输入前状态:")
            print(f"   滚动: ({before_state.get('scrollY', 0)}, {before_state.get('scrollX', 0)})")
            if before_state.get('dialogTop') is not None:
                print(f"   对话框位置: ({before_state.get('dialogTop', 0):.1f}, {before_state.get('dialogLeft', 0):.1f})")
            print(f"   用户名: '{before_state.get('usernameInputValue', '')}', 焦点: {before_state.get('usernameInputFocused', False)}")
            print(f"   密码长度: {before_state.get('passwordInputValue', 0)}, 焦点: {before_state.get('passwordInputFocused', False)}")
            print(f"   验证码: '{before_state.get('captchaInputValue', '')}', 焦点: {before_state.get('captchaInputFocused', False)}")
        
        print(f"\n⚡ 执行输入操作: {step_name}")
        print("👁️  请观察是否有跳动和输入阻碍...")
        
        # 执行输入操作
        try:
            result = input_action()
            print(f"   结果: {'✅ 成功' if result else '❌ 失败'}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            result = False
        
        # 短暂等待，让任何动画或重排完成
        time.sleep(0.8)
        
        # 记录输入后状态
        after_state = self.record_page_state(f"输入后_{step_name}")
        if 'error' not in after_state:
            print(f"\n📏 输入后状态:")
            print(f"   滚动: ({after_state.get('scrollY', 0)}, {after_state.get('scrollX', 0)})")
            if after_state.get('dialogTop') is not None:
                print(f"   对话框位置: ({after_state.get('dialogTop', 0):.1f}, {after_state.get('dialogLeft', 0):.1f})")
            print(f"   用户名: '{after_state.get('usernameInputValue', '')}', 焦点: {after_state.get('usernameInputFocused', False)}")
            print(f"   密码长度: {after_state.get('passwordInputValue', 0)}, 焦点: {after_state.get('passwordInputFocused', False)}")
            print(f"   验证码: '{after_state.get('captchaInputValue', '')}', 焦点: {after_state.get('captchaInputFocused', False)}")
        
        # 检查跳动
        jumped, details = self.check_input_jump(before_state, after_state)
        
        if jumped:
            print(f"\n⚠️ 检测到输入时跳动!")
            print("   详情:")
            for key, value in details.items():
                if value > 0:
                    print(f"      {key}: {value:.1f}px")
        else:
            print(f"\n✅ 输入操作无跳动")
        
        return result, jumped
    
    def test_complete_input_flow(self):
        """测试完整的输入流程"""
        print("🎯 登录表单输入跳动专项测试")
        print("=" * 80)
        print("专门检测输入用户名、密码、验证码时的页面跳动和输入阻碍")
        print("-" * 80)
        
        try:
            # 初始化浏览器
            print("\n步骤1: 初始化浏览器...")
            if not self.login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            # 导航并点击登录按钮
            print("\n步骤2: 导航到主页并弹出登录框...")
            self.login_manager.page.goto(Config.BASE_URL.rstrip('#/'))
            time.sleep(2)
            
            # 点击登录按钮弹出登录框
            login_clicked = False
            login_selectors = ['text=登录', 'button:has-text("登录")']
            for selector in login_selectors:
                try:
                    element = self.login_manager.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        login_clicked = True
                        print(f"   ✅ 登录框弹出成功")
                        break
                except:
                    continue
            
            if not login_clicked:
                print("❌ 无法弹出登录框")
                return False
            
            # 等待登录框稳定
            time.sleep(1.5)
            
            # 测试用户名输入
            username_success, username_jumped = self.test_input_step(
                "输入用户名",
                lambda: self._fill_username()
            )
            
            # 测试密码输入
            password_success, password_jumped = self.test_input_step(
                "输入密码", 
                lambda: self._fill_password()
            )
            
            # 测试验证码输入（如果存在）
            captcha_success, captcha_jumped = self.test_input_step(
                "输入验证码",
                lambda: self._fill_captcha_test()
            )
            
            # 总结报告
            print("\n" + "=" * 80)
            print("📊 输入跳动测试报告")
            print("=" * 80)
            
            total_jumps = sum([username_jumped, password_jumped, captcha_jumped])
            
            if total_jumps > 0:
                print(f"⚠️ 发现 {total_jumps} 个输入步骤出现跳动:")
                if username_jumped:
                    print("   - 用户名输入时出现跳动")
                if password_jumped:
                    print("   - 密码输入时出现跳动")
                if captcha_jumped:
                    print("   - 验证码输入时出现跳动")
            else:
                print("✅ 所有输入操作均无跳动")
            
            # 检查输入成功率
            print(f"\n输入成功率:")
            print(f"   用户名: {'✅' if username_success else '❌'}")
            print(f"   密码: {'✅' if password_success else '❌'}")
            print(f"   验证码: {'✅' if captcha_success else '❌'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            try:
                print("\n关闭浏览器...")
                time.sleep(1)
                self.login_manager.close_browser()
            except:
                pass
    
    def _fill_username(self):
        """填写用户名"""
        try:
            selectors = [
                'input[placeholder*="用户名"]',
                'input[name*="username"]',
                'input[name*="user"]'
            ]
            
            for selector in selectors:
                element = self.login_manager.page.locator(selector).first
                if element.count() > 0 and element.is_visible():
                    element.click()
                    time.sleep(0.1)  # 等待焦点
                    element.fill(Config.USERNAME)
                    print(f"      用户名填写成功，选择器: {selector}")
                    return True
                    
            print("      未找到用户名输入框")
            return False
            
        except Exception as e:
            print(f"      用户名填写异常: {e}")
            return False
    
    def _fill_password(self):
        """填写密码"""
        try:
            selectors = [
                'input[type="password"]',
                'input[placeholder*="密码"]'
            ]
            
            for selector in selectors:
                element = self.login_manager.page.locator(selector).first
                if element.count() > 0 and element.is_visible():
                    element.click()
                    time.sleep(0.1)  # 等待焦点
                    element.fill(Config.PASSWORD)
                    print(f"      密码填写成功，选择器: {selector}")
                    return True
                    
            print("      未找到密码输入框")
            return False
            
        except Exception as e:
            print(f"      密码填写异常: {e}")
            return False
    
    def _fill_captcha_test(self):
        """测试验证码输入"""
        try:
            captcha_input = self.login_manager.page.locator('input[placeholder*="验证码"]').first
            if captcha_input.count() > 0 and captcha_input.is_visible():
                # 模拟验证码输入
                captcha_input.click()
                time.sleep(0.1)
                captcha_input.fill("TEST")  # 使用测试验证码
                print("      验证码测试输入成功")
                return True
            else:
                print("      未找到验证码输入框")
                return False
                
        except Exception as e:
            print(f"      验证码输入异常: {e}")
            return False

if __name__ == "__main__":
    print("🔍 登录表单输入跳动专项测试工具")
    print("=" * 80)
    print("本工具专门检测输入用户名、密码、验证码时的页面跳动和输入阻碍")
    print("-" * 80)
    
    try:
        tester = InputJumpTester()
        tester.test_complete_input_flow()
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")