#!/usr/bin/env python3
"""
监控页面跳动的详细脚本
精确定位跳动发生的时机和原因
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.login import LoginManager
import time
import json

class JumpMonitor(LoginManager):
    """页面跳动监控器"""
    
    def __init__(self):
        super().__init__()
        self.jump_events = []
        
    def monitor_viewport_changes(self):
        """监控视口变化"""
        return self.page.evaluate('''
            () => {
                // 获取当前视口滚动位置
                return {
                    scrollX: window.scrollX,
                    scrollY: window.scrollY,
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    documentHeight: document.documentElement.scrollHeight,
                    documentWidth: document.documentElement.scrollWidth
                };
            }
        ''')
    
    def monitor_dialog_position(self):
        """监控登录框位置"""
        return self.page.evaluate('''
            () => {
                const dialog = document.querySelector('.el-dialog');
                if (dialog) {
                    const rect = dialog.getBoundingClientRect();
                    const computed = window.getComputedStyle(dialog);
                    return {
                        exists: true,
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height,
                        position: computed.position,
                        transform: computed.transform,
                        transition: computed.transition,
                        animation: computed.animation
                    };
                }
                return { exists: false };
            }
        ''')
    
    def setup_jump_detector(self):
        """设置跳动检测器"""
        self.page.evaluate('''
            () => {
                window.jumpDetected = [];
                
                // 监听滚动事件
                window.addEventListener('scroll', (e) => {
                    window.jumpDetected.push({
                        type: 'scroll',
                        scrollX: window.scrollX,
                        scrollY: window.scrollY,
                        timestamp: Date.now()
                    });
                });
                
                // 使用MutationObserver监控DOM变化
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'attributes' && 
                            (mutation.attributeName === 'style' || 
                             mutation.attributeName === 'class')) {
                            window.jumpDetected.push({
                                type: 'dom_change',
                                target: mutation.target.tagName + '.' + mutation.target.className,
                                attribute: mutation.attributeName,
                                timestamp: Date.now()
                            });
                        }
                    });
                });
                
                // 开始观察
                observer.observe(document.body, {
                    attributes: true,
                    childList: true,
                    subtree: true,
                    attributeOldValue: true
                });
                
                console.log('跳动检测器已设置');
            }
        ''')
    
    def get_jump_events(self):
        """获取跳动事件"""
        return self.page.evaluate('() => window.jumpDetected || []')
    
    def test_navigation_jump(self):
        """测试导航阶段的跳动"""
        print("🔍 监控导航阶段的页面跳动")
        print("=" * 60)
        
        try:
            # 初始化浏览器
            print("\n🚀 初始化浏览器...")
            if not self.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            # 设置跳动检测器
            print("📊 设置跳动检测器...")
            self.setup_jump_detector()
            
            # 记录初始状态
            print("\n📏 记录初始视口状态...")
            initial_viewport = self.monitor_viewport_changes()
            print(f"   初始视口: {initial_viewport}")
            
            # 导航到登录页面
            print("\n🌐 开始导航到登录页面...")
            print("   👁️ 请观察页面跳动...")
            
            # 访问主页
            from config.config import Config
            self.page.goto(Config.BASE_URL)
            
            # 等待页面加载
            print("   ⏳ 等待页面加载...")
            time.sleep(2)
            
            # 检查视口变化
            after_load_viewport = self.monitor_viewport_changes()
            print(f"\n📏 页面加载后视口: {after_load_viewport}")
            
            if initial_viewport['scrollY'] != after_load_viewport['scrollY']:
                print(f"   ⚠️ 检测到垂直滚动: {after_load_viewport['scrollY']}px")
            
            # 查找登录按钮
            print("\n🔍 查找登录按钮...")
            login_button = None
            for selector in ['text=登录', 'button:has-text("登录")', '[class*="login"]']:
                try:
                    if self.page.locator(selector).count() > 0:
                        login_button = selector
                        print(f"   ✅ 找到登录按钮: {selector}")
                        break
                except:
                    continue
            
            if login_button:
                # 记录点击前状态
                before_click_viewport = self.monitor_viewport_changes()
                before_click_dialog = self.monitor_dialog_position()
                
                print(f"\n🖱️ 点击登录按钮...")
                print("   👁️ 请观察是否有跳动...")
                
                # 点击登录按钮
                self.page.click(login_button)
                
                # 等待模态框出现
                time.sleep(1)
                
                # 检查点击后状态
                after_click_viewport = self.monitor_viewport_changes()
                after_click_dialog = self.monitor_dialog_position()
                
                print(f"\n📏 点击后视口: {after_click_viewport}")
                
                if before_click_viewport['scrollY'] != after_click_viewport['scrollY']:
                    print(f"   ⚠️ 点击后垂直滚动: {after_click_viewport['scrollY']}px")
                    self.jump_events.append({
                        'stage': 'click_login_button',
                        'scroll_change': after_click_viewport['scrollY'] - before_click_viewport['scrollY']
                    })
                
                if after_click_dialog['exists']:
                    print(f"\n📦 登录框状态:")
                    print(f"   位置: top={after_click_dialog['top']:.1f}, left={after_click_dialog['left']:.1f}")
                    print(f"   定位方式: {after_click_dialog['position']}")
                    print(f"   变换: {after_click_dialog['transform']}")
                    print(f"   过渡动画: {after_click_dialog['transition']}")
                    
                    if 'transition' in after_click_dialog['transition'] or 'animation' in after_click_dialog['animation']:
                        print("   ⚠️ 检测到动画效果，可能导致视觉跳动")
                
                # 获取所有跳动事件
                js_events = self.get_jump_events()
                if js_events:
                    print(f"\n📋 检测到的DOM事件:")
                    for event in js_events[-10:]:  # 只显示最后10个事件
                        print(f"   - {event}")
            
            # 调用稳定性修复看是否有影响
            print("\n🔧 测试稳定性修复方法...")
            before_fix_viewport = self.monitor_viewport_changes()
            before_fix_dialog = self.monitor_dialog_position()
            
            # 调用修复方法（现在应该是跳过的）
            self._apply_modal_stability_fixes()
            
            time.sleep(1)
            
            after_fix_viewport = self.monitor_viewport_changes()
            after_fix_dialog = self.monitor_dialog_position()
            
            if before_fix_viewport != after_fix_viewport:
                print("   ⚠️ 修复方法导致了视口变化！")
                self.jump_events.append({
                    'stage': 'apply_fixes',
                    'viewport_change': True
                })
            else:
                print("   ✅ 修复方法未导致视口变化")
            
            if before_fix_dialog != after_fix_dialog and after_fix_dialog['exists']:
                print("   ⚠️ 修复方法导致了登录框变化！")
                self.jump_events.append({
                    'stage': 'apply_fixes',
                    'dialog_change': True
                })
            else:
                print("   ✅ 修复方法未导致登录框变化")
            
            # 总结
            print("\n" + "=" * 60)
            print("📊 跳动分析总结:")
            if self.jump_events:
                print("   检测到以下跳动事件:")
                for event in self.jump_events:
                    print(f"   - {event}")
            else:
                print("   ✅ 未检测到明显跳动")
            
            # 保存详细日志
            with open('jump_monitor_log.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'jump_events': self.jump_events,
                    'js_events': js_events if 'js_events' in locals() else []
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 详细日志已保存: jump_monitor_log.json")
            
            return True
            
        except Exception as e:
            print(f"❌ 监控异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            try:
                input("\n按回车键关闭浏览器...")
                self.close_browser()
            except:
                pass

if __name__ == "__main__":
    print("🔍 页面跳动精确监控工具")
    print("=" * 60)
    print("本工具将精确监控页面跳动的时机和原因")
    print("-" * 60)
    
    try:
        input("按回车开始监控...")
        monitor = JumpMonitor()
        monitor.test_navigation_jump()
    except KeyboardInterrupt:
        print("\n用户中断监控")
    except Exception as e:
        print(f"监控异常: {e}")