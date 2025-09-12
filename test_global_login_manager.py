#!/usr/bin/env python3
"""
使用全局login_manager实例的跳动测试
模拟run.py中的确切调用方式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import login_manager
import time

class GlobalLoginManagerTester:
    """使用全局login_manager实例的测试器"""
    
    def __init__(self):
        self.login_manager = login_manager
        self.step_count = 0
        self.jump_records = []
        
    def record_viewport_state(self, label):
        """记录视口状态"""
        if not self.login_manager.page:
            return {'label': label, 'step': self.step_count, 'error': 'No page'}
            
        try:
            state = self.login_manager.page.evaluate('''
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
        except Exception as e:
            return {'label': label, 'step': self.step_count, 'error': str(e)}
    
    def check_jump(self, before, after, threshold=5):
        """检查是否发生跳动"""
        if not before or not after or 'error' in before or 'error' in after:
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
        if 'error' not in before_state:
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
        if 'error' not in after_state:
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
    
    def test_global_manager_login(self):
        """测试全局login_manager的登录流程"""
        print("🎯 全局LoginManager实例跳动测试")
        print("=" * 80)
        print("使用与run.py相同的全局login_manager实例")
        print("-" * 80)
        
        try:
            # 步骤1: 初始化浏览器（与run.py中相同）
            if not self.execute_step("初始化浏览器", 
                lambda: self.login_manager.init_browser()):
                print("❌ 浏览器初始化失败，测试中止")
                return False
            
            # 步骤2: 检查登录状态（与run.py中相同）
            if not self.execute_step("检查登录状态", 
                lambda: self.login_manager.check_login_status()):
                
                print("当前未登录，开始登录流程...")
                
                # 步骤3: 执行登录（与run.py中相同的调用）
                if not self.execute_step("执行完整登录流程", 
                    lambda: self.login_manager.login(),
                    observe_time=5):
                    print("❌ 登录失败")
                    return False
                    
                print("✅ 登录成功！")
            else:
                print("✅ 检测到已登录状态")
            
            # 生成报告
            print("\n" + "=" * 80)
            print("📊 测试报告")
            print("=" * 80)
            
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
            
            return True
            
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            try:
                print("\n自动关闭浏览器...")
                time.sleep(2)
                self.login_manager.close_browser()
            except:
                pass

if __name__ == "__main__":
    print("🔍 全局LoginManager实例跳动测试工具")
    print("=" * 80)
    print("本工具使用与run.py完全相同的全局login_manager实例")
    print("-" * 80)
    
    try:
        print("自动开始测试...")
        tester = GlobalLoginManagerTester()
        tester.test_global_manager_login()
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")