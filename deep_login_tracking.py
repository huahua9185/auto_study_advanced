#!/usr/bin/env python3
"""
深度跟踪login()方法内部操作的脚本
定位登录流程中具体哪个操作导致页面跳动
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager
from config.config import Config
import time
import json
from datetime import datetime

class DeepLoginTracker(LoginManager):
    """深度跟踪login()方法的每个步骤"""
    
    def __init__(self):
        super().__init__()
        self.step_counter = 0
        self.login_steps = []
    
    def log_step(self, step_name, description, action_func=None):
        """记录登录流程中的每个步骤"""
        self.step_counter += 1
        step_info = {
            'step': self.step_counter,
            'name': step_name,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n🔢 登录步骤 #{self.step_counter}")
        print(f"   名称: {step_name}")
        print(f"   描述: {description}")
        print(f"   👁️  请观察是否有跳动...")
        
        try:
            if action_func:
                result = action_func()
                step_info['result'] = 'success' if result else 'failed'
                step_info['return_value'] = str(result)
            else:
                step_info['result'] = 'executed'
                
            print(f"   ✅ 步骤完成: {step_info.get('result', 'unknown')}")
            
        except Exception as e:
            step_info['result'] = 'error'
            step_info['error'] = str(e)
            print(f"   ❌ 步骤异常: {e}")
        
        self.login_steps.append(step_info)
        time.sleep(1)  # 给用户观察时间
        return step_info.get('result') == 'success'
    
    def login(self):
        """重写login方法，添加详细步骤跟踪"""
        print("🚀 开始深度跟踪登录流程")
        print("=" * 60)
        print("⚠️  请仔细观察每个步骤是否引起页面跳动")
        print("-" * 60)
        
        try:
            # 步骤1: 导航到登录页面
            if not self.log_step("navigate", "导航到登录页面", lambda: self._navigate_to_login()):
                return False
            
            # 步骤2: 查找登录按钮
            self.log_step("find_login_btn", "查找登录按钮")
            
            # 这里我们需要模拟原始login()方法的逻辑
            # 让我们逐步执行主要操作
            max_attempts = 3
            for attempt in range(max_attempts):
                print(f"\n📋 登录尝试 {attempt + 1}/{max_attempts}")
                
                # 步骤3: 应用稳定性修复
                self.log_step(f"stability_fix_{attempt+1}", 
                             f"第{attempt+1}次应用稳定性修复", 
                             lambda: self._apply_modal_stability_fixes())
                
                # 步骤4: 等待模态框稳定
                self.log_step(f"wait_stability_{attempt+1}", 
                             f"第{attempt+1}次等待模态框稳定", 
                             lambda: self._wait_for_login_modal_stability())
                
                # 步骤5: 填写登录表单
                self.log_step(f"fill_form_{attempt+1}", 
                             f"第{attempt+1}次填写登录表单", 
                             lambda: self._fill_login_form())
                
                # 步骤6: 提交表单
                self.log_step(f"submit_form_{attempt+1}", 
                             f"第{attempt+1}次提交登录表单", 
                             lambda: self._submit_login_form_and_wait())
                
                # 步骤7: 检查登录结果  
                self.log_step(f"check_result_{attempt+1}", 
                             f"第{attempt+1}次检查登录结果", 
                             lambda: self.check_login_status())
                
                # 检查是否成功
                if self.check_login_status():
                    print("✅ 登录成功！")
                    self.save_steps_log("successful_login_steps.json")
                    return True
                else:
                    print(f"❌ 第{attempt+1}次登录失败，准备重试...")
                    time.sleep(2)
            
            print("❌ 所有登录尝试都失败了")
            self.save_steps_log("failed_login_steps.json")
            return False
            
        except Exception as e:
            self.log_step("error", f"登录流程异常: {e}")
            self.save_steps_log("error_login_steps.json")
            return False
    
    def _fill_login_form(self):
        """重写填写表单方法，添加更细粒度跟踪"""
        try:
            # 分解成更小的步骤
            self.log_step("fill_username_detail", "填写用户名字段", 
                         lambda: self._fill_username())
            
            self.log_step("fill_password_detail", "填写密码字段", 
                         lambda: self._fill_password())
            
            # 检查是否需要填写验证码
            self.log_step("check_captcha", "检查验证码需求", 
                         lambda: self._fill_captcha())
            
            return True
            
        except Exception as e:
            print(f"填写表单异常: {e}")
            return False
    
    def save_steps_log(self, filename):
        """保存详细的步骤日志"""
        log_data = {
            'total_steps': self.step_counter,
            'timestamp': datetime.now().isoformat(),
            'steps': self.login_steps
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细步骤日志已保存: {filename}")
        print(f"📊 总步骤数: {self.step_counter}")
        
        # 显示步骤摘要
        print(f"\n📋 步骤摘要:")
        for step in self.login_steps:
            status = "✅" if step.get('result') == 'success' else "❌" 
            print(f"   {status} 步骤#{step['step']}: {step['name']} - {step.get('result', 'unknown')}")

def test_deep_login_tracking():
    """执行深度登录跟踪测试"""
    print("🔍 深度登录流程跟踪")
    print("=" * 60)
    print("💡 这将逐步执行登录过程，帮助精确定位跳动源")
    print("-" * 60)
    
    tracker = DeepLoginTracker()
    
    try:
        # 初始化浏览器
        print("\n🚀 初始化浏览器...")
        if not tracker.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        print("✅ 浏览器初始化成功")
        print("\n👁️  现在开始逐步跟踪登录流程，请观察每个步骤...")
        
        # 开始深度跟踪登录
        result = tracker.login()
        
        if result:
            print("\n🎉 深度跟踪完成 - 登录成功！")
        else:
            print("\n📋 深度跟踪完成 - 登录失败")
        
        print(f"\n💡 分析指南:")
        print(f"   1. 查看控制台输出，找到跳动发生的步骤编号")
        print(f"   2. 查看生成的JSON日志文件获取详细信息")
        print(f"   3. 重点关注跳动前后的操作类型")
        
        return result
        
    except Exception as e:
        print(f"❌ 深度跟踪异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            input("\n🔚 按回车键关闭浏览器...")
            tracker.close_browser()
        except:
            pass

if __name__ == "__main__":
    test_deep_login_tracking()