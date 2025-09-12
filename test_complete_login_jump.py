#!/usr/bin/env python3
"""
完整测试登录流程中的每个环节
精确定位跳动发生的具体步骤
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager
from config.config import Config
import time
import json

class CompleteLoginJumpTester(LoginManager):
    """完整登录流程跳动测试器"""
    
    def __init__(self):
        super().__init__()
        self.jump_records = []
        self.step_count = 0
        
    def record_viewport_state(self, label):
        """记录视口状态"""
        try:
            state = self.page.evaluate('''
                () => {
                    const dialog = document.querySelector('.el-dialog');
                    return {
                        scrollX: window.scrollX,
                        scrollY: window.scrollY,
                        dialogExists: dialog !== null,
                        dialogTop: dialog ? dialog.getBoundingClientRect().top : null,
                        dialogLeft: dialog ? dialog.getBoundingClientRect().left : null,
                        timestamp: Date.now()
                    };
                }
            ''')
            state['label'] = label
            state['step'] = self.step_count
            return state
        except:
            return {'label': label, 'step': self.step_count, 'error': 'Failed to get state'}
    
    def check_jump(self, before, after, threshold=5):
        """检查是否发生跳动"""
        if not before or not after:
            return False, "无法比较"
        
        # 检查滚动
        scroll_x_diff = abs(after.get('scrollX', 0) - before.get('scrollX', 0))
        scroll_y_diff = abs(after.get('scrollY', 0) - before.get('scrollY', 0))
        
        # 检查对话框位置
        dialog_top_diff = 0
        dialog_left_diff = 0
        
        if before.get('dialogExists') and after.get('dialogExists'):
            if before.get('dialogTop') is not None and after.get('dialogTop') is not None:
                dialog_top_diff = abs(after['dialogTop'] - before['dialogTop'])
                dialog_left_diff = abs(after['dialogLeft'] - before['dialogLeft'])
        
        jumped = (scroll_x_diff > threshold or 
                 scroll_y_diff > threshold or 
                 dialog_top_diff > threshold or 
                 dialog_left_diff > threshold)
        
        details = {
            'scrollX_change': scroll_x_diff,
            'scrollY_change': scroll_y_diff,
            'dialogTop_change': dialog_top_diff,
            'dialogLeft_change': dialog_left_diff
        }
        
        return jumped, details
    
    def execute_step(self, step_name, action_func, observe_time=1):
        """执行一个步骤并记录跳动"""
        self.step_count += 1
        print(f"\n{'='*60}")
        print(f"🔢 步骤 #{self.step_count}: {step_name}")
        print(f"{'='*60}")
        
        # 记录执行前状态
        before_state = self.record_viewport_state(f"before_{step_name}")
        print(f"📏 执行前: scroll=({before_state.get('scrollY', 0)}, {before_state.get('scrollX', 0)})")
        if before_state.get('dialogExists'):
            print(f"   对话框位置: ({before_state.get('dialogTop', 0):.1f}, {before_state.get('dialogLeft', 0):.1f})")
        
        print(f"\n⚡ 执行操作: {step_name}")
        print("👁️  请观察是否有跳动...")
        
        # 执行操作
        try:
            result = action_func() if action_func else True
            print(f"   结果: {'✅ 成功' if result else '❌ 失败'}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            result = False
        
        # 等待并观察
        time.sleep(observe_time)
        
        # 记录执行后状态
        after_state = self.record_viewport_state(f"after_{step_name}")
        print(f"\n📏 执行后: scroll=({after_state.get('scrollY', 0)}, {after_state.get('scrollX', 0)})")
        if after_state.get('dialogExists'):
            print(f"   对话框位置: ({after_state.get('dialogTop', 0):.1f}, {after_state.get('dialogLeft', 0):.1f})")
        
        # 检查跳动
        jumped, details = self.check_jump(before_state, after_state)
        
        if jumped:
            print(f"\n⚠️ 检测到跳动!")
            print(f"   详情: {details}")
            self.jump_records.append({
                'step': self.step_count,
                'name': step_name,
                'jumped': True,
                'details': details
            })
        else:
            print(f"\n✅ 无跳动")
            self.jump_records.append({
                'step': self.step_count,
                'name': step_name,
                'jumped': False
            })
        
        return result
    
    def _handle_captcha_test(self):
        """处理验证码的测试版本"""
        try:
            # 调用原始的验证码处理方法
            return self._fill_captcha()
        except Exception as e:
            print(f"   验证码处理异常: {e}")
            # 如果验证码处理失败，尝试手动输入
            print("   尝试等待用户手动输入验证码...")
            time.sleep(5)  # 给用户5秒时间输入验证码
            return True
    
    def _wait_for_login_result(self):
        """等待登录结果"""
        try:
            # 等待页面跳转或错误消息
            time.sleep(3)
            
            # 检查是否登录成功（页面跳转）
            current_url = self.page.url
            if "login" not in current_url.lower():
                print(f"   ✅ 页面已跳转: {current_url}")
                return True
            
            # 检查是否有错误消息
            error_messages = self.page.evaluate('''
                () => {
                    const errors = document.querySelectorAll('.el-message--error, .error-message, [class*="error"]');
                    return Array.from(errors).map(el => el.textContent.trim()).filter(text => text.length > 0);
                }
            ''')
            
            if error_messages:
                print(f"   ⚠️ 发现错误消息: {error_messages}")
                return False
            
            # 检查登录状态
            return self.check_login_status()
            
        except Exception as e:
            print(f"   登录结果检查异常: {e}")
            return False
    
    def test_complete_login_flow(self):
        """测试完整的登录流程"""
        print("🎯 完整登录流程跳动测试")
        print("=" * 80)
        print("将逐步执行登录的每个环节，监控跳动情况")
        print("-" * 80)
        
        try:
            # 步骤1: 初始化浏览器
            if not self.execute_step("初始化浏览器", lambda: self.init_browser()):
                print("❌ 浏览器初始化失败，测试中止")
                return False
            
            # 步骤2: 导航到主页
            if not self.execute_step("导航到主页", 
                lambda: self.page.goto(Config.BASE_URL) or True, 
                observe_time=3):
                print("❌ 导航失败")
                return False
            
            # 步骤3: 等待页面加载
            self.execute_step("等待DOM加载", 
                lambda: self.page.wait_for_load_state('domcontentloaded', timeout=5000) or True,
                observe_time=2)
            
            # 步骤4: 查找登录按钮
            login_button = None
            for selector in ['text=登录', 'button:has-text("登录")', 'a[href*="login"]']:
                try:
                    if self.page.locator(selector).count() > 0:
                        login_button = selector
                        break
                except:
                    continue
            
            if login_button:
                # 步骤5: 点击登录按钮
                self.execute_step(f"点击登录按钮 ({login_button})", 
                    lambda: self.page.click(login_button),
                    observe_time=2)
                
                # 步骤6: 等待登录框出现
                self.execute_step("等待登录框出现", 
                    lambda: self.page.wait_for_selector('.el-dialog', timeout=5000) or True,
                    observe_time=1)
                
                # 步骤7: 应用稳定性修复
                self.execute_step("应用稳定性修复 (_apply_modal_stability_fixes)", 
                    lambda: self._apply_modal_stability_fixes(),
                    observe_time=2)
                
                # 步骤8: 等待模态框稳定
                self.execute_step("等待模态框稳定 (_wait_for_login_modal_stability)", 
                    lambda: self._wait_for_login_modal_stability(),
                    observe_time=2)
                
                # 步骤9: 查找用户名输入框
                username_input = None
                for selector in ['input[placeholder*="用户名"]', 'input[name="username"]', '#username']:
                    try:
                        if self.page.locator(selector).count() > 0:
                            username_input = selector
                            break
                    except:
                        continue
                
                if username_input:
                    # 步骤10: 填写用户名
                    self.execute_step(f"填写用户名 ({username_input})", 
                        lambda: self.page.fill(username_input, Config.USERNAME),
                        observe_time=1)
                    
                    # 步骤11: 查找密码输入框
                    password_input = None
                    for selector in ['input[type="password"]', 'input[placeholder*="密码"]', '#password']:
                        try:
                            if self.page.locator(selector).count() > 0:
                                password_input = selector
                                break
                        except:
                            continue
                    
                    if password_input:
                        # 步骤12: 填写密码
                        self.execute_step(f"填写密码 ({password_input})", 
                            lambda: self.page.fill(password_input, Config.PASSWORD),
                            observe_time=1)
                        
                        # 步骤13: 检查验证码
                        captcha_input = None
                        for selector in ['input[placeholder*="验证码"]', 'input[name="captcha"]', '#captcha']:
                            try:
                                if self.page.locator(selector).count() > 0:
                                    captcha_input = selector
                                    break
                            except:
                                continue
                        
                        if captcha_input:
                            # 步骤14: 处理验证码（尝试实际识别）
                            self.execute_step("处理验证码 (尝试识别并输入)", 
                                lambda: self._handle_captcha_test(),
                                observe_time=2)
                        
                        # 步骤15: 查找提交按钮
                        submit_button = None
                        for selector in ['button:has-text("登录")', 'button[type="submit"]', '.el-button--primary']:
                            try:
                                if self.page.locator(selector).count() > 0:
                                    submit_button = selector
                                    break
                            except:
                                continue
                        
                        if submit_button:
                            # 步骤15: 实际提交登录
                            self.execute_step(f"点击提交按钮 ({submit_button})", 
                                lambda: self.page.click(submit_button),
                                observe_time=3)
                            
                            # 步骤16: 等待登录结果
                            self.execute_step("等待登录结果并检查跳转", 
                                lambda: self._wait_for_login_result(),
                                observe_time=2)
                        
            # 生成报告
            self.generate_report()
            
            return True
            
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            try:
                print("\n自动关闭浏览器...")
                time.sleep(2)  # 给用户2秒时间查看结果
                self.close_browser()
            except:
                pass
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("📊 测试报告")
        print("=" * 80)
        
        # 统计跳动
        jump_steps = [r for r in self.jump_records if r.get('jumped')]
        
        if jump_steps:
            print(f"\n⚠️ 发现 {len(jump_steps)} 个跳动步骤:")
            for step in jump_steps:
                print(f"   步骤#{step['step']}: {step['name']}")
                if 'details' in step:
                    details = step['details']
                    if details['scrollY_change'] > 0:
                        print(f"      - 垂直滚动: {details['scrollY_change']:.1f}px")
                    if details['scrollX_change'] > 0:
                        print(f"      - 水平滚动: {details['scrollX_change']:.1f}px")
                    if details['dialogTop_change'] > 0:
                        print(f"      - 对话框垂直移动: {details['dialogTop_change']:.1f}px")
                    if details['dialogLeft_change'] > 0:
                        print(f"      - 对话框水平移动: {details['dialogLeft_change']:.1f}px")
        else:
            print("\n✅ 没有检测到明显跳动")
        
        # 保存详细日志
        with open('complete_login_jump_test.json', 'w', encoding='utf-8') as f:
            json.dump({
                'total_steps': self.step_count,
                'jump_records': self.jump_records,
                'summary': {
                    'total_jumps': len(jump_steps),
                    'jump_steps': [s['name'] for s in jump_steps]
                }
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细日志已保存: complete_login_jump_test.json")

if __name__ == "__main__":
    print("🔍 完整登录流程跳动测试工具")
    print("=" * 80)
    print("本工具将测试登录流程的每个环节，精确定位跳动位置")
    print("-" * 80)
    
    try:
        print("自动开始测试...")
        tester = CompleteLoginJumpTester()
        tester.test_complete_login_flow()
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")