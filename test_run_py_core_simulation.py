#!/usr/bin/env python3
"""
核心模拟 run.py 跳动测试脚本
专门测试 run.py 中导致跳动的核心流程，跳过验证码识别环节
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import login_manager
from config.config import Config
import time
import json

class RunPyCoreSimulationTester:
    """run.py 核心跳动测试器"""
    
    def __init__(self):
        self.login_manager = login_manager
        self.step_count = 0
        self.jump_records = []
        
    def record_step_state(self, step_name):
        """记录步骤状态，专注于跳动检测"""
        self.step_count += 1
        
        if not self.login_manager.page:
            return {'step': self.step_count, 'name': step_name, 'jumped': False, 'error': 'No page'}
            
        try:
            # 精简但全面的页面状态记录
            state = self.login_manager.page.evaluate('''
                () => {
                    const dialog = document.querySelector('.el-dialog');
                    return {
                        scrollX: window.scrollX,
                        scrollY: window.scrollY,
                        url: window.location.href,
                        dialogExists: dialog !== null,
                        dialogTop: dialog ? dialog.getBoundingClientRect().top : null,
                        dialogLeft: dialog ? dialog.getBoundingClientRect().left : null,
                        timestamp: Date.now()
                    };
                }
            ''')
            
            return {
                'step': self.step_count,
                'name': step_name,
                'state': state,
                'jumped': False
            }
            
        except Exception as e:
            return {
                'step': self.step_count,
                'name': step_name,
                'jumped': False,
                'error': str(e)
            }
    
    def check_step_jump(self, before_record, after_record, threshold=5):
        """检查跳动"""
        if 'error' in before_record or 'error' in after_record:
            return False, "无法比较"
            
        before_state = before_record.get('state', {})
        after_state = after_record.get('state', {})
        
        if not before_state or not after_state:
            return False, "状态数据缺失"
        
        details = {}
        jumped = False
        
        # 滚动变化
        scroll_x_diff = abs(after_state.get('scrollX', 0) - before_state.get('scrollX', 0))
        scroll_y_diff = abs(after_state.get('scrollY', 0) - before_state.get('scrollY', 0))
        details['scrollX_change'] = scroll_x_diff
        details['scrollY_change'] = scroll_y_diff
        
        if scroll_x_diff > threshold or scroll_y_diff > threshold:
            jumped = True
        
        # 对话框位置变化
        if (before_state.get('dialogTop') is not None and 
            after_state.get('dialogTop') is not None):
            dialog_top_diff = abs(after_state['dialogTop'] - before_state['dialogTop'])
            dialog_left_diff = abs(after_state['dialogLeft'] - before_state['dialogLeft'])
            details['dialogTop_change'] = dialog_top_diff
            details['dialogLeft_change'] = dialog_left_diff
            
            if dialog_top_diff > threshold or dialog_left_diff > threshold:
                jumped = True
        
        return jumped, details
    
    def execute_step_with_monitoring(self, step_name, step_function):
        """执行步骤并监测跳动"""
        print(f"\n{'='*80}")
        print(f"🎯 步骤 #{self.step_count + 1}: {step_name}")
        print(f"{'='*80}")
        
        # 记录前状态
        before_record = self.record_step_state(f"{step_name} (前)")
        if 'error' not in before_record and 'state' in before_record:
            state = before_record['state']
            print(f"📏 执行前: 滚动({state.get('scrollY', 0)}, {state.get('scrollX', 0)})")
            if state.get('dialogExists'):
                print(f"   对话框位置: ({state.get('dialogTop', 0):.1f}, {state.get('dialogLeft', 0):.1f})")
        
        print(f"\n⚡ 执行: {step_name}")
        print("👁️  观察跳动...")
        
        # 执行操作
        success = False
        try:
            result = step_function()
            success = result if isinstance(result, bool) else True
            print(f"   结果: {'✅' if success else '❌'}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            success = False
        
        # 等待稳定
        time.sleep(0.3)
        
        # 记录后状态
        after_record = self.record_step_state(f"{step_name} (后)")
        if 'error' not in after_record and 'state' in after_record:
            state = after_record['state']
            print(f"📏 执行后: 滚动({state.get('scrollY', 0)}, {state.get('scrollX', 0)})")
            if state.get('dialogExists'):
                print(f"   对话框位置: ({state.get('dialogTop', 0):.1f}, {state.get('dialogLeft', 0):.1f})")
        
        # 检查跳动
        jumped, details = self.check_step_jump(before_record, after_record)
        
        # 更新记录
        before_record['jumped'] = jumped
        if jumped:
            before_record['details'] = details
        
        self.jump_records.append(before_record)
        
        if jumped:
            print(f"\n⚠️ 检测到跳动！")
            for key, value in details.items():
                if value > 0:
                    print(f"   {key}: {value:.1f}px")
        else:
            print(f"\n✅ 无跳动")
        
        return success, jumped
    
    def simulate_core_flow(self):
        """模拟核心执行流程，完整测试到登录成功或失败"""
        print("🎯 run.py 核心流程跳动测试")
        print("=" * 80)
        print("专门测试 run.py 中最可能导致跳动的核心操作")
        print("完整测试到登录提交和结果处理")
        print("-" * 80)
        
        total_jumps = 0
        
        try:
            # 步骤1: 浏览器初始化
            success, jumped = self.execute_step_with_monitoring(
                "初始化浏览器",
                lambda: self.login_manager.init_browser()
            )
            if jumped: total_jumps += 1
            if not success:
                print("❌ 浏览器初始化失败")
                return False
            
            # 步骤2: 导航到主页
            success, jumped = self.execute_step_with_monitoring(
                "导航到主页",
                lambda: self.navigate_to_homepage()
            )
            if jumped: total_jumps += 1
            
            # 步骤3: 等待DOM加载
            success, jumped = self.execute_step_with_monitoring(
                "等待DOM加载", 
                lambda: self.wait_for_dom_ready()
            )
            if jumped: total_jumps += 1
            
            # 步骤4: 点击登录按钮（关键步骤）
            success, jumped = self.execute_step_with_monitoring(
                "点击登录按钮 (可能跳动源)",
                lambda: self.click_login_button()
            )
            if jumped: total_jumps += 1
            
            # 步骤5: 等待登录框出现
            success, jumped = self.execute_step_with_monitoring(
                "等待登录框出现",
                lambda: self.wait_for_login_modal()
            )
            if jumped: total_jumps += 1
            
            # 步骤6: 应用稳定性修复（关键步骤）
            success, jumped = self.execute_step_with_monitoring(
                "应用稳定性修复 (可能跳动源)",
                lambda: self.login_manager._apply_modal_stability_fixes()
            )
            if jumped: total_jumps += 1
            
            # 步骤7: 等待模态框稳定（关键步骤）
            success, jumped = self.execute_step_with_monitoring(
                "等待模态框稳定 (可能跳动源)",
                lambda: self.login_manager._wait_for_login_modal_stability()
            )
            if jumped: total_jumps += 1
            
            # 步骤8: 填写用户名
            success, jumped = self.execute_step_with_monitoring(
                "填写用户名 (可能跳动源)",
                lambda: self.fill_username()
            )
            if jumped: total_jumps += 1
            
            # 步骤9: 填写密码
            success, jumped = self.execute_step_with_monitoring(
                "填写密码 (可能跳动源)",
                lambda: self.fill_password()
            )
            if jumped: total_jumps += 1
            
            # 步骤10: 处理验证码（如果存在）
            success, jumped = self.execute_step_with_monitoring(
                "处理验证码 (尝试识别并输入)",
                lambda: self.handle_captcha_if_exists()
            )
            if jumped: total_jumps += 1
            
            # 步骤11: 点击提交按钮
            success, jumped = self.execute_step_with_monitoring(
                "点击提交按钮 (可能跳动源)",
                lambda: self.click_submit_button()
            )
            if jumped: total_jumps += 1
            
            # 步骤12: 等待登录结果并检查跳转
            success, jumped = self.execute_step_with_monitoring(
                "等待登录结果并检查跳转",
                lambda: self.wait_for_login_result()
            )
            if jumped: total_jumps += 1
            
            # 步骤13: 进一步检查登录状态
            success, jumped = self.execute_step_with_monitoring(
                "检查最终登录状态",
                lambda: self.check_final_login_status()
            )
            if jumped: total_jumps += 1
            
            # 生成报告
            print(f"\n{'='*80}")
            print("📊 run.py 核心流程跳动检测报告")
            print(f"{'='*80}")
            
            if total_jumps > 0:
                print(f"⚠️ 检测到 {total_jumps} 个步骤出现跳动!")
                print("\n跳动步骤:")
                for record in self.jump_records:
                    if record.get('jumped'):
                        print(f"   - {record['name']}")
                        if 'details' in record:
                            for key, value in record['details'].items():
                                if value > 0:
                                    print(f"     {key}: {value:.1f}px")
            else:
                print("✅ 未检测到跳动")
            
            # 保存结果
            self.save_results()
            return True
            
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            try:
                print("\n关闭浏览器...")
                time.sleep(0.5)
                self.login_manager.close_browser()
            except:
                pass
    
    def navigate_to_homepage(self):
        """导航到主页"""
        try:
            self.login_manager.page.goto(Config.BASE_URL.rstrip('#/'))
            return True
        except Exception as e:
            print(f"导航异常: {e}")
            return False
    
    def wait_for_dom_ready(self):
        """等待DOM准备就绪"""
        try:
            time.sleep(2)  # 基本等待
            return True
        except Exception as e:
            print(f"等待DOM异常: {e}")
            return False
    
    def click_login_button(self):
        """点击登录按钮"""
        try:
            login_selectors = ['text=登录', 'button:has-text("登录")']
            for selector in login_selectors:
                try:
                    element = self.login_manager.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        return True
                except:
                    continue
            return False
        except Exception as e:
            print(f"点击登录按钮异常: {e}")
            return False
    
    def wait_for_login_modal(self):
        """等待登录框出现"""
        try:
            time.sleep(1.5)  # 等待登录框出现
            return True
        except Exception as e:
            print(f"等待登录框异常: {e}")
            return False
    
    def fill_username(self):
        """填写用户名"""
        try:
            selectors = ['input[placeholder*="用户名"]']
            for selector in selectors:
                element = self.login_manager.page.locator(selector).first
                if element.count() > 0 and element.is_visible():
                    element.click()
                    element.fill(Config.USERNAME)
                    return True
            return False
        except Exception as e:
            print(f"填写用户名异常: {e}")
            return False
    
    def fill_password(self):
        """填写密码"""
        try:
            selectors = ['input[type="password"]']
            for selector in selectors:
                element = self.login_manager.page.locator(selector).first
                if element.count() > 0 and element.is_visible():
                    element.click()
                    element.fill(Config.PASSWORD)
                    return True
            return False
        except Exception as e:
            print(f"填写密码异常: {e}")
            return False
    
    def handle_captcha_if_exists(self):
        """处理验证码（如果存在）"""
        try:
            captcha_input = self.login_manager.page.locator('input[placeholder*="验证码"]').first
            if captcha_input.count() > 0 and captcha_input.is_visible():
                # 模拟验证码输入（使用测试验证码）
                captcha_input.click()
                captcha_input.fill("1234")  # 使用测试验证码避免识别延迟
                print("      验证码测试输入: 1234")
                return True
            else:
                print("      未找到验证码输入框")
                return True  # 没有验证码也算成功
        except Exception as e:
            print(f"处理验证码异常: {e}")
            return False
    
    def click_submit_button(self):
        """点击提交按钮"""
        try:
            # 常用的提交按钮选择器
            submit_selectors = [
                'button:has-text("登录")',
                'input[type="submit"]',
                'button[type="submit"]',
                '.el-button--primary:has-text("登录")',
                '[class*="submit"]:has-text("登录")',
                '.login-btn'
            ]
            
            for selector in submit_selectors:
                try:
                    element = self.login_manager.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        print(f"      提交按钮点击成功，选择器: {selector}")
                        return True
                except:
                    continue
            
            # 备用方案：按回车键
            print("      未找到提交按钮，使用回车键提交")
            self.login_manager.page.keyboard.press('Enter')
            return True
                    
        except Exception as e:
            print(f"点击提交按钮异常: {e}")
            return False
    
    def wait_for_login_result(self):
        """等待登录结果并检查跳转"""
        try:
            # 等待页面响应
            time.sleep(3)
            
            # 检查是否有错误消息
            current_url = self.login_manager.page.url
            
            # 检查常见的登录结果指示器
            try:
                # 检查是否有错误提示
                error_selectors = [
                    '.el-message--error',
                    '.error-message',
                    '[class*="error"]',
                    '.el-form-item__error',
                    '.el-message.el-message--error'
                ]
                
                has_error = False
                error_msg = ""
                for selector in error_selectors:
                    try:
                        elements = self.login_manager.page.locator(selector)
                        if elements.count() > 0:
                            for i in range(elements.count()):
                                element = elements.nth(i)
                                if element.is_visible():
                                    error_text = element.text_content()
                                    if error_text and error_text.strip():
                                        print(f"      检测到错误信息: {error_text}")
                                        error_msg = error_text
                                        has_error = True
                                        break
                    except:
                        continue
                    if has_error:
                        break
                
                # 检查是否有成功跳转
                success_indicators = [
                    "#/home",
                    "#/dashboard", 
                    "#/main",
                    "#/user"
                ]
                
                has_success = False
                for indicator in success_indicators:
                    if indicator in current_url:
                        print(f"      检测到成功跳转: {current_url}")
                        has_success = True
                        break
                
                if not has_error and not has_success:
                    print(f"      当前URL: {current_url}")
                    print("      未检测到明显错误或成功跳转，状态未知")
                    
                    # 检查是否登录框还在
                    modal_exists = self.login_manager.page.locator('.el-dialog').count() > 0
                    if modal_exists:
                        print("      登录框仍然存在，可能登录未成功")
                    else:
                        print("      登录框已消失")
                        
            except Exception as e:
                print(f"      检查登录结果时异常: {e}")
            
            return True  # 总是返回成功，因为我们主要关注跳动
            
        except Exception as e:
            print(f"等待登录结果异常: {e}")
            return False
    
    def check_final_login_status(self):
        """检查最终登录状态"""
        try:
            print("      执行最终登录状态检查...")
            
            # 使用与LoginManager相同的检查逻辑
            current_url = self.login_manager.page.url
            print(f"      最终URL: {current_url}")
            
            # 检查cookies
            cookies = self.login_manager.page.context.cookies()
            login_cookies = [c for c in cookies if any(keyword in c.get('name', '').lower() 
                                                     for keyword in ['session', 'token', 'login', 'auth'])]
            print(f"      登录相关cookies数量: {len(login_cookies)}")
            
            # 检查是否能找到用户信息
            user_selectors = [
                '[class*="user"]',
                '[class*="profile"]',
                '.user-name',
                '.username'
            ]
            
            has_user_info = False
            for selector in user_selectors:
                try:
                    if self.login_manager.page.locator(selector).count() > 0:
                        element = self.login_manager.page.locator(selector).first
                        if element.is_visible():
                            user_text = element.text_content()
                            if user_text and user_text.strip():
                                print(f"      找到用户信息: {user_text[:20]}...")
                                has_user_info = True
                                break
                except:
                    continue
            
            if not has_user_info:
                print("      未找到明显的用户信息")
            
            # 最终判断
            if '#/' in current_url and current_url != Config.BASE_URL and len(login_cookies) > 0:
                print("      ✅ 初步判断：登录可能成功")
            else:
                print("      ❌ 初步判断：登录可能未成功")
                
            return True
            
        except Exception as e:
            print(f"检查最终登录状态异常: {e}")
            return False
    
    def save_results(self):
        """保存测试结果"""
        try:
            results = {
                'total_steps': len(self.jump_records),
                'jump_records': self.jump_records,
                'summary': {
                    'total_jumps': sum(1 for record in self.jump_records if record.get('jumped')),
                    'jump_steps': [record['name'] for record in self.jump_records if record.get('jumped')]
                }
            }
            
            with open('run_py_core_simulation_test.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 详细结果已保存到: run_py_core_simulation_test.json")
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

if __name__ == "__main__":
    print("🔍 run.py 核心流程跳动测试工具")
    print("=" * 80)
    print("专门测试 run.py 中最可能导致跳动的核心操作")
    print("跳过验证码识别，专注于跳动检测")
    print("-" * 80)
    
    try:
        tester = RunPyCoreSimulationTester()
        tester.simulate_core_flow()
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")