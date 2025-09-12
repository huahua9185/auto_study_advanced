#!/usr/bin/env python3
"""
登录稳定性分析脚本
分析登录过程中可能导致页面抖动和元素识别延迟的问题
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager

class LoginStabilityAnalyzer:
    def __init__(self):
        self.analysis_results = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'page_load_analysis': [],
            'element_stability': [],
            'dynamic_content': [],
            'layout_changes': [],
            'recommendations': []
        }
    
    def analyze_login_stability(self):
        """分析登录过程的稳定性问题"""
        print("登录稳定性分析")
        print("=" * 60)
        
        try:
            # 1. 初始化浏览器
            print("1. 初始化浏览器...")
            if not login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            page = login_manager.page
            
            # 2. 分析页面加载过程
            print("2. 分析登录页面加载过程...")
            self.analyze_page_loading(page)
            
            # 3. 分析页面元素稳定性
            print("3. 分析页面元素稳定性...")
            self.analyze_element_stability(page)
            
            # 4. 检测动态内容
            print("4. 检测动态内容和布局变化...")
            self.analyze_dynamic_content(page)
            
            # 5. 生成建议
            self.generate_recommendations()
            
            # 6. 保存分析结果
            self.save_analysis_results()
            
            return True
            
        except Exception as e:
            print(f"❌ 分析过程中出现错误: {str(e)}")
            return False
            
        finally:
            if login_manager:
                login_manager.close_browser()
    
    def analyze_page_loading(self, page):
        """分析页面加载过程"""
        loading_analysis = {
            'initial_load_time': 0,
            'dom_ready_time': 0,
            'network_requests': 0,
            'js_errors': [],
            'css_files': 0,
            'js_files': 0
        }
        
        try:
            # 监听网络请求
            requests = []
            def handle_request(request):
                requests.append({
                    'url': request.url,
                    'resource_type': request.resource_type,
                    'method': request.method
                })
            
            page.on("request", handle_request)
            
            # 监听JS错误
            js_errors = []
            def handle_error(error):
                js_errors.append({
                    'message': str(error),
                    'timestamp': time.time()
                })
            
            page.on("pageerror", handle_error)
            
            # 访问登录页面
            start_time = time.time()
            page.goto("https://edu.nxgbjy.org.cn/nxxzxy/index.html", wait_until='domcontentloaded')
            dom_ready_time = time.time() - start_time
            
            # 等待网络空闲
            page.wait_for_load_state('networkidle')
            total_load_time = time.time() - start_time
            
            loading_analysis['initial_load_time'] = total_load_time
            loading_analysis['dom_ready_time'] = dom_ready_time
            loading_analysis['network_requests'] = len(requests)
            loading_analysis['js_errors'] = js_errors
            
            # 分析资源类型
            css_files = [r for r in requests if r['resource_type'] == 'stylesheet']
            js_files = [r for r in requests if r['resource_type'] == 'script']
            loading_analysis['css_files'] = len(css_files)
            loading_analysis['js_files'] = len(js_files)
            
            self.analysis_results['page_load_analysis'] = loading_analysis
            
            print(f"   页面加载时间: {total_load_time:.2f}s")
            print(f"   DOM就绪时间: {dom_ready_time:.2f}s")
            print(f"   网络请求数: {len(requests)}")
            print(f"   JS错误数: {len(js_errors)}")
            
        except Exception as e:
            print(f"   ⚠️  页面加载分析失败: {str(e)}")
    
    def analyze_element_stability(self, page):
        """分析关键元素的稳定性"""
        print("   检查登录相关元素...")
        
        # 关键元素选择器
        key_elements = {
            'login_button': ['button:has-text("登录")', '.login-btn', '[type="submit"]'],
            'username_input': ['input[placeholder="用户名"]', 'input[name="username"]', '#username'],
            'password_input': ['input[type="password"]', 'input[name="password"]', '#password'],
            'captcha_input': ['input[placeholder="验证码"]', 'input[name="captcha"]', '#captcha'],
            'captcha_image': ['img[src*="auth_code"]', '.captcha-img', '[alt*="验证码"]']
        }
        
        stability_results = {}
        
        for element_name, selectors in key_elements.items():
            print(f"   检查 {element_name}...")
            element_info = {
                'found': False,
                'selector_used': None,
                'position_changes': [],
                'visibility_changes': [],
                'attempts': 0
            }
            
            # 尝试多个选择器
            for selector in selectors:
                try:
                    element_info['attempts'] += 1
                    
                    # 检查元素是否存在
                    if page.locator(selector).count() > 0:
                        element_info['found'] = True
                        element_info['selector_used'] = selector
                        
                        # 监控元素位置变化
                        initial_box = None
                        try:
                            element = page.locator(selector).first
                            if element.is_visible():
                                initial_box = element.bounding_box()
                                
                                # 等待一段时间，检查位置是否变化
                                time.sleep(1)
                                current_box = element.bounding_box()
                                
                                if initial_box and current_box:
                                    if (abs(initial_box['y'] - current_box['y']) > 5 or 
                                        abs(initial_box['x'] - current_box['x']) > 5):
                                        element_info['position_changes'].append({
                                            'initial': initial_box,
                                            'current': current_box,
                                            'y_diff': current_box['y'] - initial_box['y'],
                                            'x_diff': current_box['x'] - initial_box['x']
                                        })
                        except:
                            pass
                        
                        break
                        
                except Exception as e:
                    continue
            
            stability_results[element_name] = element_info
            
            if element_info['found']:
                print(f"     ✅ 找到 (选择器: {element_info['selector_used']})")
                if element_info['position_changes']:
                    print(f"     ⚠️  检测到位置变化: {len(element_info['position_changes'])}次")
            else:
                print(f"     ❌ 未找到 (尝试了 {element_info['attempts']} 个选择器)")
        
        self.analysis_results['element_stability'] = stability_results
    
    def analyze_dynamic_content(self, page):
        """分析动态内容和可能导致布局抖动的元素"""
        print("   分析动态内容...")
        
        dynamic_analysis = {
            'animated_elements': [],
            'loading_indicators': [],
            'dynamic_styles': [],
            'height_changes': []
        }
        
        try:
            # 检查可能的动态元素
            dynamic_selectors = [
                '.loading', '.spinner', '[class*="loading"]', '[class*="spinner"]',
                '.animation', '[class*="animate"]', '[class*="transition"]',
                '.message', '.alert', '.notification', '[class*="message"]',
                '.banner', '.announcement', '[class*="banner"]'
            ]
            
            for selector in dynamic_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        for element in elements:
                            if element.is_visible():
                                dynamic_analysis['animated_elements'].append({
                                    'selector': selector,
                                    'tag': element.evaluate('el => el.tagName'),
                                    'classes': element.get_attribute('class'),
                                    'text': element.text_content()[:50] if element.text_content() else ''
                                })
                except:
                    continue
            
            # 检查页面高度变化
            initial_height = page.evaluate('document.body.scrollHeight')
            time.sleep(2)
            current_height = page.evaluate('document.body.scrollHeight')
            
            if abs(current_height - initial_height) > 10:
                dynamic_analysis['height_changes'].append({
                    'initial': initial_height,
                    'current': current_height,
                    'difference': current_height - initial_height
                })
            
            # 检查是否有定时器或间隔器
            timers_info = page.evaluate('''
                () => {
                    const timers = [];
                    const originalSetTimeout = window.setTimeout;
                    const originalSetInterval = window.setInterval;
                    
                    window.setTimeout = function(...args) {
                        timers.push({type: 'timeout', delay: args[1]});
                        return originalSetTimeout.apply(this, args);
                    };
                    
                    window.setInterval = function(...args) {
                        timers.push({type: 'interval', delay: args[1]});
                        return originalSetInterval.apply(this, args);
                    };
                    
                    return timers;
                }
            ''')
            
            dynamic_analysis['timers'] = timers_info
            
        except Exception as e:
            print(f"     ⚠️  动态内容分析失败: {str(e)}")
        
        self.analysis_results['dynamic_content'] = dynamic_analysis
        
        if dynamic_analysis['animated_elements']:
            print(f"     发现 {len(dynamic_analysis['animated_elements'])} 个动态元素")
        if dynamic_analysis['height_changes']:
            print(f"     检测到页面高度变化: {dynamic_analysis['height_changes']}")
    
    def generate_recommendations(self):
        """根据分析结果生成优化建议"""
        recommendations = []
        
        # 分析页面加载
        load_analysis = self.analysis_results.get('page_load_analysis', {})
        if load_analysis.get('initial_load_time', 0) > 5:
            recommendations.append({
                'type': 'performance',
                'issue': '页面加载时间过长',
                'suggestion': '增加页面加载超时时间，添加更多等待条件',
                'priority': 'high'
            })
        
        if load_analysis.get('js_errors'):
            recommendations.append({
                'type': 'stability',
                'issue': '页面存在JavaScript错误',
                'suggestion': '添加JS错误处理，等待页面稳定后再进行操作',
                'priority': 'medium'
            })
        
        # 分析元素稳定性
        stability = self.analysis_results.get('element_stability', {})
        for element_name, info in stability.items():
            if not info.get('found'):
                recommendations.append({
                    'type': 'element',
                    'issue': f'{element_name}元素未找到',
                    'suggestion': f'为{element_name}添加更多备选选择器，增加重试机制',
                    'priority': 'high'
                })
            
            if info.get('position_changes'):
                recommendations.append({
                    'type': 'layout',
                    'issue': f'{element_name}元素位置不稳定',
                    'suggestion': '等待页面布局稳定后再进行操作，添加位置稳定性检查',
                    'priority': 'high'
                })
        
        # 分析动态内容
        dynamic = self.analysis_results.get('dynamic_content', {})
        if dynamic.get('animated_elements'):
            recommendations.append({
                'type': 'animation',
                'issue': '页面存在动画元素',
                'suggestion': '等待动画完成，或禁用CSS动画',
                'priority': 'medium'
            })
        
        if dynamic.get('height_changes'):
            recommendations.append({
                'type': 'layout',
                'issue': '页面高度动态变化',
                'suggestion': '等待页面高度稳定，添加布局稳定性检查',
                'priority': 'high'
            })
        
        self.analysis_results['recommendations'] = recommendations
        
        print(f"\n生成了 {len(recommendations)} 条优化建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['issue']}")
            print(f"      建议: {rec['suggestion']}")
    
    def save_analysis_results(self):
        """保存分析结果"""
        try:
            with open('login_stability_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            print(f"\n分析结果已保存到: login_stability_analysis.json")
        except Exception as e:
            print(f"❌ 保存分析结果失败: {str(e)}")

def main():
    """主函数"""
    analyzer = LoginStabilityAnalyzer()
    
    try:
        success = analyzer.analyze_login_stability()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 登录稳定性分析完成!")
            print("详细分析结果请查看: login_stability_analysis.json")
            print("=" * 60)
            return 0
        else:
            print("\n❌ 登录稳定性分析失败!")
            return 1
            
    except Exception as e:
        print(f"\n💥 分析过程中出现异常: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)