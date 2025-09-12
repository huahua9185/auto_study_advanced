#!/usr/bin/env python3
"""
测试登录框弹出后的网页跳动问题
专门监测登录框div弹出时是否导致整个网页的上下跳动
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import login_manager
from config.config import Config
import time

class ModalPopupJumpTester:
    """登录框弹出跳动测试器"""
    
    def __init__(self):
        self.login_manager = login_manager
        self.jump_records = []
        
    def record_page_state(self, label):
        """记录整个页面的状态，专注于检测网页本身的跳动"""
        if not self.login_manager.page:
            return {'label': label, 'error': 'No page'}
            
        try:
            state = self.login_manager.page.evaluate('''
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    const dialog = document.querySelector('.el-dialog');
                    
                    return {
                        // 页面滚动位置
                        scrollX: window.scrollX,
                        scrollY: window.scrollY,
                        
                        // 页面整体尺寸
                        bodyHeight: body.scrollHeight,
                        bodyWidth: body.scrollWidth,
                        clientHeight: html.clientHeight,
                        clientWidth: html.clientWidth,
                        
                        // 窗口视口
                        innerWidth: window.innerWidth,
                        innerHeight: window.innerHeight,
                        
                        // 对话框状态
                        dialogExists: dialog !== null,
                        dialogVisible: dialog ? (dialog.style.display !== 'none') : false,
                        
                        // 页面元素位置（检查主要内容是否发生位移）
                        bodyOffsetTop: body.offsetTop,
                        bodyOffsetLeft: body.offsetLeft,
                        
                        // 时间戳
                        timestamp: Date.now()
                    };
                }
            ''')
            state['label'] = label
            return state
        except Exception as e:
            return {'label': label, 'error': str(e)}
    
    def check_page_jump(self, before, after, threshold=3):
        """检查整个页面是否发生跳动"""
        if not before or not after or 'error' in before or 'error' in after:
            return False, "无法比较"
        
        # 检查各种可能导致页面跳动的因素
        scroll_x_diff = abs(after.get('scrollX', 0) - before.get('scrollX', 0))
        scroll_y_diff = abs(after.get('scrollY', 0) - before.get('scrollY', 0))
        body_height_diff = abs(after.get('bodyHeight', 0) - before.get('bodyHeight', 0))
        body_top_diff = abs(after.get('bodyOffsetTop', 0) - before.get('bodyOffsetTop', 0))
        
        jumped = (scroll_x_diff > threshold or 
                 scroll_y_diff > threshold or 
                 body_height_diff > 10 or 
                 body_top_diff > threshold)
        
        details = {
            'scroll_x_change': scroll_x_diff,
            'scroll_y_change': scroll_y_diff,
            'body_height_change': body_height_diff,
            'body_top_change': body_top_diff,
            'dialog_appeared': after.get('dialogExists') and not before.get('dialogExists')
        }
        
        return jumped, details
    
    def test_modal_popup_jump(self):
        """专门测试登录框弹出时的网页跳动"""
        print("🎯 登录框弹出跳动专项测试")
        print("=" * 80)
        print("专门检测登录框div弹出时是否导致整个网页上下跳动")
        print("-" * 80)
        
        try:
            # 初始化浏览器
            print("\n步骤1: 初始化浏览器...")
            if not self.login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            print("✅ 浏览器初始化成功")
            
            # 导航到主页
            print("\n步骤2: 导航到主页...")
            self.login_manager.page.goto(Config.BASE_URL.rstrip('#/'))
            time.sleep(2)  # 等待页面加载
            
            # 记录登录框弹出前的页面状态
            print("\n步骤3: 记录登录框弹出前的页面状态...")
            before_state = self.record_page_state("登录框弹出前")
            
            if 'error' not in before_state:
                print(f"   📏 弹出前状态:")
                print(f"      滚动位置: ({before_state.get('scrollY', 0)}, {before_state.get('scrollX', 0)})")
                print(f"      页面高度: {before_state.get('bodyHeight', 0)}")
                print(f"      body位置: {before_state.get('bodyOffsetTop', 0)}")
                print(f"      对话框存在: {before_state.get('dialogExists', False)}")
            
            print("\n步骤4: 点击登录按钮，触发登录框弹出...")
            print("👁️  请仔细观察是否有整个网页的上下跳动...")
            
            # 查找并点击登录按钮
            login_clicked = False
            login_selectors = [
                'text=登录',
                'button:has-text("登录")',
                'a[href*="login"]',
                '[class*="login"]'
            ]
            
            for selector in login_selectors:
                try:
                    element = self.login_manager.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        login_clicked = True
                        print(f"   ✅ 登录按钮点击成功: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not login_clicked:
                print("   ❌ 未能找到登录按钮")
                return False
            
            # 短暂等待，让登录框开始出现
            time.sleep(0.5)
            
            # 记录登录框弹出后的页面状态
            print("\n步骤5: 记录登录框弹出后的页面状态...")
            after_state = self.record_page_state("登录框弹出后")
            
            if 'error' not in after_state:
                print(f"   📏 弹出后状态:")
                print(f"      滚动位置: ({after_state.get('scrollY', 0)}, {after_state.get('scrollX', 0)})")
                print(f"      页面高度: {after_state.get('bodyHeight', 0)}")
                print(f"      body位置: {after_state.get('bodyOffsetTop', 0)}")
                print(f"      对话框存在: {after_state.get('dialogExists', False)}")
                print(f"      对话框可见: {after_state.get('dialogVisible', False)}")
            
            # 检查是否发生跳动
            jumped, details = self.check_page_jump(before_state, after_state)
            
            print("\n" + "=" * 60)
            print("📊 跳动检测结果")
            print("=" * 60)
            
            if jumped:
                print("⚠️ 检测到网页跳动！")
                print("   跳动详情:")
                if details['scroll_x_change'] > 0:
                    print(f"      - 水平滚动变化: {details['scroll_x_change']:.1f}px")
                if details['scroll_y_change'] > 0:
                    print(f"      - 垂直滚动变化: {details['scroll_y_change']:.1f}px")
                if details['body_height_change'] > 0:
                    print(f"      - 页面高度变化: {details['body_height_change']:.1f}px")
                if details['body_top_change'] > 0:
                    print(f"      - body位置变化: {details['body_top_change']:.1f}px")
                if details['dialog_appeared']:
                    print(f"      - 登录框已出现: 是")
            else:
                print("✅ 未检测到明显的网页跳动")
                if details['dialog_appeared']:
                    print("   登录框已正常弹出，没有导致页面跳动")
            
            # 等待一下，让用户观察
            print("\n继续观察3秒...")
            time.sleep(3)
            
            # 再次检查，看看是否有延迟的跳动
            final_state = self.record_page_state("最终状态")
            final_jumped, final_details = self.check_page_jump(after_state, final_state)
            
            if final_jumped:
                print("⚠️ 检测到延迟跳动！")
                print(f"   详情: {final_details}")
            else:
                print("✅ 页面保持稳定，无延迟跳动")
            
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
    print("🔍 登录框弹出跳动专项测试工具")
    print("=" * 80)
    print("本工具专门检测登录框div弹出时是否导致整个网页上下跳动")
    print("-" * 80)
    
    try:
        tester = ModalPopupJumpTester()
        tester.test_modal_popup_jump()
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")