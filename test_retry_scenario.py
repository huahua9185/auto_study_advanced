#!/usr/bin/env python3
"""
测试登录重试场景的跳动问题
专门模拟验证码失败后的重试流程，包括页面重新加载
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import login_manager
from config.config import Config
import time

class RetryScenarioTester:
    """重试场景跳动测试器"""
    
    def __init__(self):
        self.login_manager = login_manager
        
    def record_page_state(self, label):
        """记录页面状态"""
        if not self.login_manager.page:
            return {'label': label, 'error': 'No page'}
            
        try:
            state = self.login_manager.page.evaluate('''
                () => {
                    return {
                        scrollX: window.scrollX,
                        scrollY: window.scrollY,
                        url: window.location.href,
                        timestamp: Date.now()
                    };
                }
            ''')
            state['label'] = label
            return state
        except Exception as e:
            return {'label': label, 'error': str(e)}
    
    def check_page_jump(self, before, after, threshold=5):
        """检查页面跳动"""
        if not before or not after or 'error' in before or 'error' in after:
            return False, "无法比较"
        
        scroll_x_diff = abs(after.get('scrollX', 0) - before.get('scrollX', 0))
        scroll_y_diff = abs(after.get('scrollY', 0) - before.get('scrollY', 0))
        
        jumped = (scroll_x_diff > threshold or scroll_y_diff > threshold)
        
        details = {
            'scroll_x_change': scroll_x_diff,
            'scroll_y_change': scroll_y_diff,
            'url_changed': before.get('url') != after.get('url')
        }
        
        return jumped, details
    
    def test_page_reload_jump(self):
        """测试页面重新加载时的跳动"""
        print("🎯 登录重试场景跳动测试")
        print("=" * 80)
        print("专门测试验证码失败后页面重新加载导致的跳动")
        print("-" * 80)
        
        try:
            # 初始化浏览器
            print("\n步骤1: 初始化浏览器...")
            if not self.login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            # 初始导航
            print("\n步骤2: 初始导航...")
            self.login_manager.page.goto(Config.BASE_URL.rstrip('#/'))
            time.sleep(2)
            
            # 点击登录按钮，弹出登录框
            print("\n步骤3: 弹出登录框...")
            login_selectors = ['text=登录', 'button:has-text("登录")']
            for selector in login_selectors:
                try:
                    element = self.login_manager.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        print(f"   ✅ 登录框弹出成功")
                        break
                except:
                    continue
            
            time.sleep(2)  # 等待登录框稳定
            
            # 记录重新加载前状态
            print("\n步骤4: 记录页面重新加载前的状态...")
            before_state = self.record_page_state("页面重新加载前")
            if 'error' not in before_state:
                print(f"   📏 重新加载前: scroll=({before_state.get('scrollY', 0)}, {before_state.get('scrollX', 0)})")
                print(f"   🌐 URL: {before_state.get('url')}")
            
            print("\n步骤5: 模拟验证码失败后的页面重新加载...")
            print("👁️  请仔细观察页面重新加载时是否有跳动...")
            
            # 执行与 run.py 中相同的重新加载逻辑
            print("   执行: self.page.goto(Config.BASE_URL)")
            self.login_manager.page.goto(Config.BASE_URL)
            
            print("   执行: _smart_wait_for_page_load")
            self.login_manager._smart_wait_for_page_load('networkidle', 10000)
            
            print("   执行: time.sleep(3) - Vue.js 渲染等待")
            time.sleep(3)
            
            # 记录重新加载后状态
            print("\n步骤6: 记录页面重新加载后的状态...")
            after_state = self.record_page_state("页面重新加载后")
            if 'error' not in after_state:
                print(f"   📏 重新加载后: scroll=({after_state.get('scrollY', 0)}, {after_state.get('scrollX', 0)})")
                print(f"   🌐 URL: {after_state.get('url')}")
            
            # 检查跳动
            jumped, details = self.check_page_jump(before_state, after_state)
            
            print("\n" + "=" * 60)
            print("📊 页面重新加载跳动检测结果")
            print("=" * 60)
            
            if jumped:
                print("⚠️ 检测到页面重新加载时的跳动！")
                print("   跳动详情:")
                if details['scroll_x_change'] > 0:
                    print(f"      - 水平滚动变化: {details['scroll_x_change']:.1f}px")
                if details['scroll_y_change'] > 0:
                    print(f"      - 垂直滚动变化: {details['scroll_y_change']:.1f}px")
                if details['url_changed']:
                    print(f"      - URL发生了变化")
                
                print("\n💡 这很可能就是 run.py 中跳动问题的根源！")
                print("   当验证码识别失败重试时，页面重新加载导致跳动。")
            else:
                print("✅ 页面重新加载过程中未检测到明显跳动")
                if details['url_changed']:
                    print("   URL已正常变化，但没有导致页面跳动")
            
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

if __name__ == "__main__":
    print("🔍 登录重试场景跳动测试工具")
    print("=" * 80)
    print("本工具专门测试验证码失败后页面重新加载是否导致跳动")
    print("-" * 80)
    
    try:
        tester = RetryScenarioTester()
        tester.test_page_reload_jump()
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")