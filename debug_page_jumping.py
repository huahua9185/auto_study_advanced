#!/usr/bin/env python3
"""
监测登录界面页面跳动问题的调试脚本
通过多个断点和监测器来定位跳动原因
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager
from config.config import Config

class PageJumpDetector:
    def __init__(self):
        self.page = None
        self.jump_events = []
        self.element_changes = []
        self.dom_mutations = []
        self.network_requests = []
        self.console_messages = []
        self.layout_changes = []
        
    def init_monitoring(self):
        """初始化所有监测器"""
        if not self.page:
            return False
            
        try:
            # 1. 监测控制台消息
            self.page.on("console", self._on_console_message)
            
            # 2. 监测网络请求
            self.page.on("request", self._on_request)
            self.page.on("response", self._on_response)
            
            # 3. 监测页面加载事件
            self.page.on("load", self._on_page_load)
            self.page.on("domcontentloaded", self._on_dom_loaded)
            
            # 4. 注入页面监测脚本
            self._inject_monitoring_script()
            
            print("✅ 所有监测器已初始化")
            return True
            
        except Exception as e:
            print(f"❌ 监测器初始化失败: {str(e)}")
            return False
    
    def _on_console_message(self, msg):
        """控制台消息监测"""
        timestamp = time.time()
        self.console_messages.append({
            'timestamp': timestamp,
            'type': msg.type,
            'text': msg.text,
            'location': getattr(msg, 'location', None)
        })
        print(f"🖥️ [CONSOLE {msg.type}] {msg.text}")
    
    def _on_request(self, request):
        """网络请求监测"""
        timestamp = time.time()
        self.network_requests.append({
            'timestamp': timestamp,
            'type': 'request',
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type
        })
        # 只记录重要的请求
        if any(keyword in request.url for keyword in ['captcha', 'login', 'verify', 'api', 'ajax']):
            print(f"🌐 [REQUEST] {request.method} {request.url}")
    
    def _on_response(self, response):
        """网络响应监测"""
        timestamp = time.time()
        # 只记录重要的响应
        if any(keyword in response.url for keyword in ['captcha', 'login', 'verify', 'api', 'ajax']):
            print(f"📨 [RESPONSE] {response.status} {response.url}")
    
    def _on_page_load(self):
        """页面加载完成监测"""
        timestamp = time.time()
        print(f"📄 [PAGE_LOAD] 页面加载完成: {timestamp}")
    
    def _on_dom_loaded(self):
        """DOM加载完成监测"""
        timestamp = time.time()
        print(f"🏗️ [DOM_LOADED] DOM加载完成: {timestamp}")
    
    def _inject_monitoring_script(self):
        """注入页面监测脚本"""
        monitoring_script = """
        window.pageJumpDetector = {
            mutations: [],
            layoutChanges: [],
            animationEvents: [],
            styleChanges: [],
            
            // DOM变化监测器
            startMutationObserver: function() {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        const event = {
                            timestamp: Date.now(),
                            type: mutation.type,
                            target: mutation.target.tagName || 'unknown',
                            targetClass: mutation.target.className || '',
                            targetId: mutation.target.id || '',
                            addedNodes: mutation.addedNodes.length,
                            removedNodes: mutation.removedNodes.length,
                            attributeName: mutation.attributeName,
                            oldValue: mutation.oldValue
                        };
                        
                        this.mutations.push(event);
                        console.log('🔄 [DOM_MUTATION]', event);
                        
                        // 特别关注可能引起跳动的变化
                        if (mutation.type === 'childList' && (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0)) {
                            console.log('⚡ [POTENTIAL_JUMP] 子元素增删:', event);
                        }
                        
                        if (mutation.type === 'attributes' && ['style', 'class', 'height', 'width'].includes(mutation.attributeName)) {
                            console.log('📏 [LAYOUT_CHANGE] 布局属性变化:', event);
                        }
                    });
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeOldValue: true,
                    characterData: true,
                    characterDataOldValue: true
                });
                
                console.log('👀 DOM变化监测器已启动');
            },
            
            // 动画监测器
            startAnimationObserver: function() {
                ['animationstart', 'animationend', 'transitionstart', 'transitionend'].forEach(eventType => {
                    document.addEventListener(eventType, (e) => {
                        const event = {
                            timestamp: Date.now(),
                            type: eventType,
                            target: e.target.tagName,
                            targetClass: e.target.className,
                            animationName: e.animationName,
                            propertyName: e.propertyName
                        };
                        
                        this.animationEvents.push(event);
                        console.log('✨ [ANIMATION]', event);
                    });
                });
                
                console.log('🎬 动画监测器已启动');
            },
            
            // 滚动监测器
            startScrollObserver: function() {
                window.addEventListener('scroll', () => {
                    console.log('📜 [SCROLL] 页面滚动:', window.scrollY);
                });
                
                document.addEventListener('scroll', (e) => {
                    if (e.target !== document) {
                        console.log('📜 [SCROLL] 元素滚动:', e.target.tagName, e.target.className);
                    }
                });
                
                console.log('📜 滚动监测器已启动');
            },
            
            // 窗口变化监测器
            startResizeObserver: function() {
                window.addEventListener('resize', () => {
                    console.log('📐 [RESIZE] 窗口尺寸变化:', window.innerWidth, window.innerHeight);
                });
                
                if (window.ResizeObserver) {
                    const resizeObserver = new ResizeObserver((entries) => {
                        entries.forEach((entry) => {
                            console.log('📐 [ELEMENT_RESIZE] 元素尺寸变化:', {
                                target: entry.target.tagName,
                                class: entry.target.className,
                                width: entry.contentRect.width,
                                height: entry.contentRect.height
                            });
                        });
                    });
                    
                    // 监测主要容器
                    const containers = document.querySelectorAll('body, .el-dialog, .login-form, [class*="container"], [class*="wrapper"]');
                    containers.forEach(el => {
                        if (el) resizeObserver.observe(el);
                    });
                }
                
                console.log('📐 尺寸变化监测器已启动');
            },
            
            // 启动所有监测器
            startAll: function() {
                this.startMutationObserver();
                this.startAnimationObserver();
                this.startScrollObserver();
                this.startResizeObserver();
                console.log('🚀 所有页面监测器已启动');
            },
            
            // 获取监测数据
            getData: function() {
                return {
                    mutations: this.mutations,
                    layoutChanges: this.layoutChanges,
                    animationEvents: this.animationEvents,
                    styleChanges: this.styleChanges
                };
            }
        };
        
        // 页面加载完成后启动监测
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                window.pageJumpDetector.startAll();
            });
        } else {
            window.pageJumpDetector.startAll();
        }
        """
        
        try:
            self.page.add_init_script(monitoring_script)
            print("✅ 页面监测脚本已注入")
        except Exception as e:
            print(f"❌ 脚本注入失败: {str(e)}")
    
    def start_monitoring(self):
        """开始监测"""
        print("\n🔍 开始监测页面跳动...")
        print("=" * 60)
        
        try:
            # 初始化浏览器
            if not login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            self.page = login_manager.page
            
            # 初始化监测器
            if not self.init_monitoring():
                return False
            
            # 访问主页面
            print("📍 断点1: 访问主页面")
            login_url = Config.BASE_URL.rstrip('#/')
            self.page.goto(login_url)
            time.sleep(3)
            
            # 等待页面稳定
            print("📍 断点2: 等待初始页面稳定")
            time.sleep(2)
            
            # 截图查看当前页面状态
            print("📍 断点3: 截图查看当前页面状态")
            self.page.screenshot(path="page_before_login.png")
            print("  截图已保存为 page_before_login.png")
            
            # 触发登录框出现
            print("📍 断点4: 触发登录框出现")
            if not self._trigger_login_modal():
                print("❌ 无法触发登录框，继续监测当前页面")
                # 即使没有登录框，也继续监测页面跳动
                print("📍 监测当前页面的跳动情况")
            else:
                # 登录框出现后再截图
                self.page.screenshot(path="page_with_login.png")
                print("  登录框出现后截图已保存为 page_with_login.png")
            
            # 等待登录框完全加载
            print("📍 断点5: 等待页面稳定 (3秒)")
            time.sleep(3)
            
            # 检查登录框元素
            print("📍 断点6: 检查页面元素")
            self._check_login_modal_elements()
            
            # 开始重点监测页面跳动
            print("📍 断点7: 监测页面跳动 (30秒)")
            print("监测页面是否有跳动...")
            
            for i in range(30):
                time.sleep(1)
                print(f"⏱️ 监测中... {i+1}/30秒", end='\r')
                
                # 每5秒检查一次页面状态
                if (i + 1) % 5 == 0:
                    print(f"\n📍 第{i+1}秒检查:")
                    self._check_page_current_stability()
            
            print("\n📍 断点8: 收集监测数据")
            self._collect_monitoring_data()
            
            print("📍 断点9: 生成分析报告")
            self._generate_report()
            
            return True
            
        except Exception as e:
            print(f"❌ 监测过程出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if login_manager:
                print("\n📍 断点10: 清理资源")
                login_manager.close_browser()
    
    def _check_page_elements(self):
        """检查页面元素"""
        try:
            # 检查登录相关元素
            elements_to_check = [
                ('用户名输入框', 'input[placeholder*="用户名"]'),
                ('密码输入框', 'input[placeholder*="密码"]'),
                ('验证码输入框', 'input[placeholder*="验证码"]'),
                ('验证码图片', 'img[src*="captcha"]'),
                ('登录按钮', 'button:has-text("登录")'),
                ('登录表单', '.login-form'),
                ('对话框', '.el-dialog'),
                ('遮罩层', '.el-dialog__wrapper')
            ]
            
            for name, selector in elements_to_check:
                try:
                    count = self.page.locator(selector).count()
                    if count > 0:
                        element = self.page.locator(selector).first
                        is_visible = element.is_visible()
                        box = element.bounding_box()
                        print(f"  {name}: 数量={count}, 可见={is_visible}, 位置={box}")
                    else:
                        print(f"  {name}: 未找到")
                except Exception as e:
                    print(f"  {name}: 检查失败 - {str(e)}")
                    
        except Exception as e:
            print(f"❌ 页面元素检查失败: {str(e)}")
    
    def _check_page_stability(self):
        """检查页面稳定性"""
        try:
            # 检查页面滚动位置
            scroll_position = self.page.evaluate("window.scrollY")
            
            # 检查窗口尺寸
            viewport_size = self.page.evaluate("({width: window.innerWidth, height: window.innerHeight})")
            
            # 检查是否有加载指示器
            loading_indicators = [
                '.el-loading-mask',
                '.loading',
                '[class*="spin"]',
                '[class*="load"]'
            ]
            
            loading_count = 0
            for indicator in loading_indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        loading_count += 1
                except:
                    pass
            
            print(f"    滚动位置: {scroll_position}, 窗口尺寸: {viewport_size}, 加载元素: {loading_count}")
            
        except Exception as e:
            print(f"    稳定性检查失败: {str(e)}")
    
    def _collect_monitoring_data(self):
        """收集监测数据"""
        try:
            # 从页面获取监测数据
            page_data = self.page.evaluate("window.pageJumpDetector ? window.pageJumpDetector.getData() : {}")
            
            # 合并所有数据
            all_data = {
                'console_messages': self.console_messages,
                'network_requests': self.network_requests,
                'page_data': page_data,
                'timestamp': time.time()
            }
            
            # 保存数据
            with open('page_jump_monitoring.json', 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            
            print("✅ 监测数据已保存到 page_jump_monitoring.json")
            
        except Exception as e:
            print(f"❌ 数据收集失败: {str(e)}")
    
    def _generate_report(self):
        """生成分析报告"""
        print("\n" + "=" * 60)
        print("📊 页面跳动分析报告")
        print("=" * 60)
        
        try:
            # 分析控制台消息
            print(f"🖥️ 控制台消息: {len(self.console_messages)} 条")
            error_messages = [msg for msg in self.console_messages if msg['type'] == 'error']
            warning_messages = [msg for msg in self.console_messages if msg['type'] == 'warning']
            
            if error_messages:
                print("  ❌ 错误消息:")
                for msg in error_messages[-5:]:  # 显示最后5条错误
                    print(f"    {msg['text']}")
            
            if warning_messages:
                print("  ⚠️ 警告消息:")
                for msg in warning_messages[-5:]:  # 显示最后5条警告
                    print(f"    {msg['text']}")
            
            # 分析网络请求
            print(f"\n🌐 网络请求: {len(self.network_requests)} 个")
            
            # 分析可能的跳动原因
            print("\n🔍 可能的跳动原因分析:")
            print("  1. 检查 page_jump_monitoring.json 中的 DOM 变化")
            print("  2. 检查是否有动画或过渡效果")
            print("  3. 检查网络请求是否导致页面更新")
            print("  4. 检查控制台是否有 JavaScript 错误")
            
            # 给出建议
            print("\n💡 调试建议:")
            print("  1. 查看浏览器开发者工具的 Network 面板")
            print("  2. 查看 Elements 面板，观察 DOM 变化")
            print("  3. 查看 Console 面板的错误和警告")
            print("  4. 使用 Performance 面板录制页面加载过程")
            
        except Exception as e:
            print(f"❌ 报告生成失败: {str(e)}")
    
    def _trigger_login_modal(self):
        """触发登录框出现"""
        try:
            # 方法1: 尝试访问需要登录的页面来触发登录框
            print("  尝试触发登录框...")
            
            # 访问学习中心或其他需要登录的页面
            protected_urls = [
                f"{Config.BASE_URL}#/my_study",
                f"{Config.BASE_URL}#/study_center", 
                f"{Config.BASE_URL}#/personal"
            ]
            
            for url in protected_urls:
                try:
                    print(f"  访问: {url}")
                    self.page.goto(url, wait_until='networkidle', timeout=10000)
                    time.sleep(2)
                    
                    # 检查是否出现登录框
                    login_modal_selectors = [
                        '.el-dialog',
                        '.el-dialog__wrapper',
                        '.login-form',
                        '[class*="login"]',
                        '[class*="modal"]'
                    ]
                    
                    for selector in login_modal_selectors:
                        if self.page.locator(selector).count() > 0:
                            element = self.page.locator(selector).first
                            if element.is_visible():
                                box = element.bounding_box()
                                print(f"  ✅ 检测到可见登录框: {selector}, 位置: {box}")
                                # 额外验证：检查是否真的是登录对话框
                                if selector == '.el-dialog':
                                    # 检查对话框内容
                                    has_login_content = (
                                        self.page.locator('.el-dialog input[placeholder*="用户名"]').count() > 0 or
                                        self.page.locator('.el-dialog input[placeholder*="密码"]').count() > 0 or
                                        self.page.locator('.el-dialog button:has-text("登录")').count() > 0
                                    )
                                    if has_login_content:
                                        print(f"  ✅ 确认为真实登录对话框")
                                        return True
                                    else:
                                        print(f"  ⚠️ 检测到对话框但不是登录框")
                                        continue
                                else:
                                    return True
                        else:
                            print(f"  ❌ 未找到元素: {selector}")
                                
                except Exception as e:
                    print(f"  访问 {url} 失败: {str(e)}")
                    continue
            
            # 方法2: 尝试点击登录相关按钮
            print("  尝试点击登录按钮...")
            login_buttons = [
                'text="登录"',
                'button:has-text("登录")',
                '.login-btn',
                '[class*="login"]'
            ]
            
            for selector in login_buttons:
                try:
                    if self.page.locator(selector).count() > 0:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            print(f"  点击登录按钮: {selector}")
                            element.click()
                            time.sleep(2)
                            
                            # 检查是否出现登录框
                            if self.page.locator('.el-dialog').count() > 0:
                                print("  ✅ 登录框已出现")
                                return True
                except Exception as e:
                    continue
            
            print("  ⚠️ 无法通过常规方法触发登录框")
            return False
            
        except Exception as e:
            print(f"  ❌ 触发登录框失败: {str(e)}")
            return False
    
    def _check_login_modal_elements(self):
        """检查登录框元素"""
        try:
            print("  检查登录框相关元素:")
            
            # 检查登录框相关元素
            modal_elements = [
                ('登录对话框', '.el-dialog'),
                ('对话框遮罩', '.el-dialog__wrapper'),
                ('对话框头部', '.el-dialog__header'),
                ('对话框主体', '.el-dialog__body'),
                ('登录表单', '.login-form'),
                ('用户名输入框', 'input[placeholder*="用户名"]'),
                ('密码输入框', 'input[placeholder*="密码"]'),
                ('验证码输入框', 'input[placeholder*="验证码"]'),
                ('验证码图片', 'img[src*="captcha"]'),
                ('登录按钮', 'button:has-text("登录")'),
                ('关闭按钮', '.el-dialog__close')
            ]
            
            for name, selector in modal_elements:
                try:
                    count = self.page.locator(selector).count()
                    if count > 0:
                        element = self.page.locator(selector).first
                        is_visible = element.is_visible()
                        box = element.bounding_box() if is_visible else None
                        print(f"    {name}: 数量={count}, 可见={is_visible}, 位置={box}")
                    else:
                        print(f"    {name}: 未找到")
                except Exception as e:
                    print(f"    {name}: 检查失败 - {str(e)}")
                    
        except Exception as e:
            print(f"  ❌ 登录框元素检查失败: {str(e)}")
    
    def _check_login_modal_stability(self):
        """检查登录框稳定性"""
        try:
            # 检查登录框是否还存在且可见
            dialog_count = self.page.locator('.el-dialog').count()
            if dialog_count > 0:
                dialog = self.page.locator('.el-dialog').first
                is_visible = dialog.is_visible()
                box = dialog.bounding_box()
                print(f"    登录框状态: 数量={dialog_count}, 可见={is_visible}, 位置={box}")
                
                # 检查登录框内部元素的稳定性
                form_elements = [
                    ('用户名框', 'input[placeholder*="用户名"]'),
                    ('密码框', 'input[placeholder*="密码"]'),  
                    ('验证码框', 'input[placeholder*="验证码"]'),
                    ('登录按钮', 'button:has-text("登录")')
                ]
                
                for name, selector in form_elements:
                    try:
                        if self.page.locator(selector).count() > 0:
                            element = self.page.locator(selector).first
                            element_box = element.bounding_box() if element.is_visible() else None
                            print(f"      {name}: 位置={element_box}")
                    except:
                        pass
            else:
                print(f"    ⚠️ 登录框消失了")
                
            # 检查页面滚动位置
            scroll_position = self.page.evaluate("window.scrollY")
            print(f"    页面滚动位置: {scroll_position}")
            
        except Exception as e:
            print(f"    登录框稳定性检查失败: {str(e)}")
    
    def _check_page_current_stability(self):
        """检查当前页面的稳定性"""
        try:
            # 检查当前URL
            current_url = self.page.url
            print(f"    当前URL: {current_url}")
            
            # 检查是否有任何对话框
            dialog_count = self.page.locator('.el-dialog').count()
            visible_dialogs = []
            if dialog_count > 0:
                for i in range(dialog_count):
                    dialog = self.page.locator('.el-dialog').nth(i)
                    if dialog.is_visible():
                        box = dialog.bounding_box()
                        visible_dialogs.append(f"对话框{i+1}: {box}")
                        
            if visible_dialogs:
                print(f"    可见对话框: {len(visible_dialogs)}个")
                for dialog_info in visible_dialogs:
                    print(f"      {dialog_info}")
            else:
                print(f"    可见对话框: 0个")
            
            # 检查页面滚动位置
            scroll_position = self.page.evaluate("window.scrollY")
            print(f"    页面滚动位置: {scroll_position}")
            
            # 检查页面是否有加载指示器
            loading_indicators = [
                '.el-loading-mask',
                '.loading', 
                '[class*="loading"]',
                '.spinner'
            ]
            
            loading_count = 0
            for indicator in loading_indicators:
                try:
                    count = self.page.locator(indicator).count()
                    if count > 0:
                        loading_count += count
                except:
                    pass
            
            print(f"    加载指示器: {loading_count}个")
            
        except Exception as e:
            print(f"    页面稳定性检查失败: {str(e)}")

def main():
    """主函数"""
    print("🔍 页面跳动监测脚本")
    print("此脚本将监测登录界面的各种变化，帮助定位跳动原因")
    print()
    
    detector = PageJumpDetector()
    detector.start_monitoring()

if __name__ == "__main__":
    main()