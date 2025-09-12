#!/usr/bin/env python3
"""
完全模拟 run.py 执行环境的跳动测试脚本
专门测试与 run.py 相同的复杂执行流程，包括应用初始化、登录状态检查、复杂重试等
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import login_manager
from config.config import Config
import time
import json

class RunPySimulationTester:
    """完全模拟 run.py 执行环境的测试器"""
    
    def __init__(self):
        self.login_manager = login_manager
        self.step_count = 0
        self.jump_records = []
        
    def record_step_state(self, step_name):
        """记录每个步骤的状态，专门针对跳动检测"""
        self.step_count += 1
        
        if not self.login_manager.page:
            return {'step': self.step_count, 'name': step_name, 'jumped': False, 'error': 'No page'}
            
        try:
            # 记录详细的页面状态信息
            state = self.login_manager.page.evaluate('''
                () => {
                    const dialog = document.querySelector('.el-dialog');
                    return {
                        // 页面基础状态
                        scrollX: window.scrollX,
                        scrollY: window.scrollY,
                        url: window.location.href,
                        bodyHeight: document.body.scrollHeight,
                        windowHeight: window.innerHeight,
                        
                        // 对话框状态
                        dialogExists: dialog !== null,
                        dialogTop: dialog ? dialog.getBoundingClientRect().top : null,
                        dialogLeft: dialog ? dialog.getBoundingClientRect().left : null,
                        dialogHeight: dialog ? dialog.getBoundingClientRect().height : null,
                        dialogWidth: dialog ? dialog.getBoundingClientRect().width : null,
                        dialogVisible: dialog ? dialog.style.display !== 'none' : false,
                        
                        // 输入框状态
                        usernameInput: document.querySelector('input[placeholder*="用户名"]') ? {
                            exists: true,
                            top: document.querySelector('input[placeholder*="用户名"]').getBoundingClientRect().top,
                            value: document.querySelector('input[placeholder*="用户名"]').value,
                            focused: document.activeElement === document.querySelector('input[placeholder*="用户名"]')
                        } : { exists: false },
                        
                        passwordInput: document.querySelector('input[type="password"]') ? {
                            exists: true,
                            top: document.querySelector('input[type="password"]').getBoundingClientRect().top,
                            valueLength: document.querySelector('input[type="password"]').value.length,
                            focused: document.activeElement === document.querySelector('input[type="password"]')
                        } : { exists: false },
                        
                        captchaInput: document.querySelector('input[placeholder*="验证码"]') ? {
                            exists: true,
                            top: document.querySelector('input[placeholder*="验证码"]').getBoundingClientRect().top,
                            value: document.querySelector('input[placeholder*="验证码"]').value,
                            focused: document.activeElement === document.querySelector('input[placeholder*="验证码"]')
                        } : { exists: false },
                        
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
        """检查两个步骤之间是否有跳动"""
        if 'error' in before_record or 'error' in after_record:
            return False, "无法比较"
            
        before_state = before_record.get('state', {})
        after_state = after_record.get('state', {})
        
        if not before_state or not after_state:
            return False, "状态数据缺失"
        
        # 检查各种跳动
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
        
        # 输入框位置变化
        for input_type in ['usernameInput', 'passwordInput', 'captchaInput']:
            before_input = before_state.get(input_type, {})
            after_input = after_state.get(input_type, {})
            
            if (before_input.get('exists') and after_input.get('exists') and
                before_input.get('top') is not None and after_input.get('top') is not None):
                input_top_diff = abs(after_input['top'] - before_input['top'])
                details[f'{input_type}_top_change'] = input_top_diff
                
                if input_top_diff > threshold:
                    jumped = True
        
        return jumped, details
    
    def execute_step_with_jump_monitoring(self, step_name, step_function):
        """执行步骤并监测跳动"""
        print(f"\n{'='*80}")
        print(f"🎯 步骤 #{self.step_count + 1}: {step_name}")
        print(f"{'='*80}")
        
        # 记录执行前状态
        before_record = self.record_step_state(f"{step_name} (执行前)")
        if 'error' not in before_record and 'state' in before_record:
            state = before_record['state']
            print(f"📏 执行前状态:")
            print(f"   滚动位置: ({state.get('scrollY', 0)}, {state.get('scrollX', 0)})")
            if state.get('dialogExists'):
                print(f"   对话框位置: ({state.get('dialogTop', 0):.1f}, {state.get('dialogLeft', 0):.1f})")
                print(f"   对话框大小: {state.get('dialogWidth', 0):.1f} x {state.get('dialogHeight', 0):.1f}")
        
        print(f"\n⚡ 执行操作: {step_name}")
        print("👁️  请仔细观察是否有跳动...")
        
        # 执行操作
        success = False
        try:
            result = step_function()
            success = result if isinstance(result, bool) else True
            print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            success = False
        
        # 等待页面稳定
        time.sleep(0.5)
        
        # 记录执行后状态
        after_record = self.record_step_state(f"{step_name} (执行后)")
        if 'error' not in after_record and 'state' in after_record:
            state = after_record['state']
            print(f"\n📏 执行后状态:")
            print(f"   滚动位置: ({state.get('scrollY', 0)}, {state.get('scrollX', 0)})")
            if state.get('dialogExists'):
                print(f"   对话框位置: ({state.get('dialogTop', 0):.1f}, {state.get('dialogLeft', 0):.1f})")
                print(f"   对话框大小: {state.get('dialogWidth', 0):.1f} x {state.get('dialogHeight', 0):.1f}")
        
        # 检查跳动
        jumped, details = self.check_step_jump(before_record, after_record)
        
        # 更新记录
        before_record['jumped'] = jumped
        if jumped:
            before_record['details'] = details
        
        self.jump_records.append(before_record)
        
        if jumped:
            print(f"\n⚠️ 检测到跳动！")
            print("   跳动详情:")
            for key, value in details.items():
                if value > 0:
                    print(f"      {key}: {value:.1f}px")
        else:
            print(f"\n✅ 无跳动")
        
        return success, jumped
    
    def simulate_run_py_full_flow(self):
        """完全模拟 run.py 的执行流程"""
        print("🎯 run.py 完整执行流程模拟测试")
        print("=" * 100)
        print("本测试完全模拟 run.py 的复杂执行环境，包括应用初始化、登录状态检查等")
        print("-" * 100)
        
        total_jumps = 0
        
        try:
            # 步骤1: 模拟 AutoStudyApp 初始化
            success, jumped = self.execute_step_with_jump_monitoring(
                "初始化应用程序 (AutoStudyApp.__init__)",
                lambda: True  # 初始化不涉及页面操作
            )
            if jumped: total_jumps += 1
            
            # 步骤2: 模拟浏览器初始化
            success, jumped = self.execute_step_with_jump_monitoring(
                "初始化浏览器 (login_manager.init_browser)",
                lambda: self.login_manager.init_browser()
            )
            if jumped: total_jumps += 1
            if not success:
                print("❌ 浏览器初始化失败")
                return False
            
            # 步骤3: 模拟登录状态检查
            success, jumped = self.execute_step_with_jump_monitoring(
                "检查登录状态 (login_manager.check_login_status)",
                lambda: self.login_manager.check_login_status()
            )
            if jumped: total_jumps += 1
            
            # 步骤4: 模拟主登录逻辑（这里是关键）
            if not success:  # 如果未登录
                success, jumped = self.execute_step_with_jump_monitoring(
                    "执行登录 (login_manager.login) - 完整复杂流程",
                    lambda: self.login_manager.login()
                )
                if jumped: total_jumps += 1
            
            # 步骤5: 模拟后续检查（如果登录成功）
            if success:
                success, jumped = self.execute_step_with_jump_monitoring(
                    "再次验证登录状态",
                    lambda: self.login_manager.check_login_status()
                )
                if jumped: total_jumps += 1
            
            # 生成详细报告
            print("\n" + "=" * 100)
            print("📊 run.py 执行流程跳动检测报告")
            print("=" * 100)
            
            if total_jumps > 0:
                print(f"⚠️ 检测到 {total_jumps} 个步骤出现跳动!")
                print("\n跳动步骤详情:")
                for i, record in enumerate(self.jump_records, 1):
                    if record.get('jumped'):
                        print(f"   {i}. {record['name']}")
                        if 'details' in record:
                            for key, value in record['details'].items():
                                if value > 0:
                                    print(f"      - {key}: {value:.1f}px")
            else:
                print("✅ 整个 run.py 执行流程中未检测到跳动")
            
            # 保存详细结果
            self.save_simulation_results()
            
            return True
            
        except Exception as e:
            print(f"❌ 模拟测试异常: {e}")
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
    
    def save_simulation_results(self):
        """保存模拟测试结果"""
        try:
            results = {
                'total_steps': len(self.jump_records),
                'jump_records': self.jump_records,
                'summary': {
                    'total_jumps': sum(1 for record in self.jump_records if record.get('jumped')),
                    'jump_steps': [record['name'] for record in self.jump_records if record.get('jumped')]
                }
            }
            
            with open('run_py_simulation_jump_test.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 详细测试结果已保存到: run_py_simulation_jump_test.json")
            
        except Exception as e:
            print(f"❌ 保存测试结果失败: {e}")

if __name__ == "__main__":
    print("🔍 run.py 完整执行流程跳动模拟测试工具")
    print("=" * 100)
    print("本工具完全模拟 run.py 的复杂执行环境，包括:")
    print("- 应用程序初始化流程")
    print("- 浏览器初始化和登录状态检查")
    print("- 完整的登录重试机制")
    print("- 与实际 run.py 相同的执行顺序和环境")
    print("-" * 100)
    
    try:
        tester = RunPySimulationTester()
        tester.simulate_run_py_full_flow()
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")