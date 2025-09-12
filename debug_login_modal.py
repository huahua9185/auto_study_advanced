#!/usr/bin/env python3
"""
专门分析登录框相关抖动问题的脚本
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

class LoginModalAnalyzer:
    def __init__(self):
        self.analysis_results = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'login_modal_elements': [],
            'modal_behavior': {},
            'shake_triggers': [],
            'element_changes': [],
            'recommendations': []
        }
    
    def analyze_login_modal(self):
        """分析登录模态框的抖动问题"""
        print("=" * 60)
        print("登录模态框抖动分析")
        print("=" * 60)
        
        try:
            # 1. 初始化浏览器
            print("1. 初始化浏览器...")
            if not login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            page = login_manager.page
            
            # 2. 访问主页面
            print("2. 访问主页面...")
            page.goto("https://edu.nxgbjy.org.cn/nxxzxy/index.html")
            page.wait_for_load_state('networkidle', timeout=10000)
            time.sleep(2)
            
            # 3. 点击登录按钮，打开登录框
            print("3. 打开登录框...")
            login_selectors = ['text=登录', 'a[href*="login"]', '[class*="login"]']
            
            login_opened = False
            for selector in login_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        element = page.locator(selector).first
                        if element.is_visible():
                            element.click()
                            login_opened = True
                            print(f"   ✅ 点击登录按钮: {selector}")
                            time.sleep(2)
                            break
                except:
                    continue
            
            if not login_opened:
                print("❌ 无法打开登录框")
                return False
            
            # 4. 分析登录框结构
            print("4. 分析登录框结构...")
            self.analyze_modal_structure(page)
            
            # 5. 监控登录框行为
            print("5. 监控登录框动态行为...")
            self.monitor_modal_behavior(page)
            
            # 6. 检查验证码相关元素
            print("6. 分析验证码相关抖动...")
            self.analyze_captcha_behavior(page)
            
            # 7. 等待并观察页面抖动
            print("7. 观察页面抖动现象...")
            shake_detected = self.detect_page_shake(page)
            
            if shake_detected:
                print("   ⚠️  检测到页面抖动")
            else:
                print("   ✅ 未检测到明显抖动")
            
            # 8. 手动关闭登录框测试
            print("8. 测试关闭登录框后的效果...")
            self.test_modal_close_effect(page)
            
            # 9. 生成分析结果
            self.generate_recommendations()
            
            # 10. 保存结果
            self.save_analysis_results()
            
            return True
            
        except Exception as e:
            print(f"❌ 分析过程中出现错误: {str(e)}")
            return False
            
        finally:
            if login_manager:
                login_manager.close_browser()
    
    def analyze_modal_structure(self, page):
        """分析登录模态框的结构"""
        print("   分析登录框结构...")
        
        # 可能的登录框选择器
        modal_selectors = [
            '.modal', '.dialog', '.popup', '.overlay',
            '[class*="modal"]', '[class*="dialog"]', '[class*="popup"]',
            '.el-dialog', '.ant-modal', '.layui-layer',
            '.login-modal', '.login-dialog', '.login-popup',
            '[id*="modal"]', '[id*="dialog"]', '[id*="login"]'
        ]
        
        modal_elements = []
        
        for selector in modal_selectors:
            try:
                elements = page.locator(selector).all()
                for element in elements:
                    if element.is_visible():
                        bbox = element.bounding_box()
                        if bbox and bbox['width'] > 200 and bbox['height'] > 100:  # 合理的模态框大小
                            modal_info = {
                                'selector': selector,
                                'tag': element.evaluate('el => el.tagName'),
                                'classes': element.get_attribute('class'),
                                'id': element.get_attribute('id'),
                                'bbox': bbox,
                                'z_index': element.evaluate('el => window.getComputedStyle(el).zIndex'),
                                'position': element.evaluate('el => window.getComputedStyle(el).position')
                            }
                            modal_elements.append(modal_info)
                            print(f"     找到模态框: {selector} (大小: {bbox['width']}x{bbox['height']})")
            except:
                continue
        
        self.analysis_results['login_modal_elements'] = modal_elements
    
    def monitor_modal_behavior(self, page):
        """监控模态框的动态行为"""
        print("   监控模态框动态行为...")
        
        behavior_info = {
            'transitions': [],
            'animations': [],
            'height_changes': [],
            'content_updates': []
        }
        
        try:
            # 记录初始状态
            initial_height = page.evaluate('document.body.scrollHeight')
            initial_viewport = page.evaluate('document.documentElement.clientHeight')
            
            # 监控一段时间内的变化
            for i in range(10):  # 监控10秒
                time.sleep(1)
                
                # 检查高度变化
                current_height = page.evaluate('document.body.scrollHeight')
                current_viewport = page.evaluate('document.documentElement.clientHeight')
                
                if abs(current_height - initial_height) > 5:
                    behavior_info['height_changes'].append({
                        'time': i,
                        'initial': initial_height,
                        'current': current_height,
                        'diff': current_height - initial_height
                    })
                
                # 检查是否有CSS动画
                animated_elements = page.evaluate('''
                    () => {
                        const elements = document.querySelectorAll('*');
                        const animated = [];
                        elements.forEach(el => {
                            const style = window.getComputedStyle(el);
                            if (style.animationName !== 'none' || style.transitionDuration !== '0s') {
                                animated.push({
                                    tag: el.tagName,
                                    classes: el.className,
                                    animation: style.animationName,
                                    transition: style.transitionDuration
                                });
                            }
                        });
                        return animated.slice(0, 5); // 只返回前5个
                    }
                ''')
                
                if animated_elements:
                    behavior_info['animations'].extend(animated_elements)
                
                print(f"     监控进度: {i+1}/10 - 高度: {current_height}")
        
        except Exception as e:
            print(f"     监控异常: {str(e)}")
        
        self.analysis_results['modal_behavior'] = behavior_info
    
    def analyze_captcha_behavior(self, page):
        """分析验证码相关的抖动行为"""
        print("   分析验证码相关行为...")
        
        captcha_info = {
            'captcha_images': [],
            'refresh_buttons': [],
            'refresh_triggered': False,
            'layout_impact': []
        }
        
        # 查找验证码图片
        captcha_selectors = [
            'img[src*="captcha"]', 'img[src*="code"]', 'img[src*="auth"]',
            '.captcha-img', '.code-img', '.verify-img',
            '[class*="captcha"]', '[class*="code"]', '[alt*="验证码"]'
        ]
        
        for selector in captcha_selectors:
            try:
                elements = page.locator(selector).all()
                for element in elements:
                    if element.is_visible():
                        bbox = element.bounding_box()
                        captcha_info['captcha_images'].append({
                            'selector': selector,
                            'bbox': bbox,
                            'src': element.get_attribute('src')
                        })
                        print(f"     找到验证码: {selector}")
                        
                        # 测试验证码刷新是否引起抖动
                        try:
                            initial_y = bbox['y'] if bbox else 0
                            element.click()  # 尝试点击刷新验证码
                            time.sleep(0.5)
                            
                            new_bbox = element.bounding_box()
                            if new_bbox and abs(new_bbox['y'] - initial_y) > 2:
                                captcha_info['layout_impact'].append({
                                    'trigger': 'captcha_refresh',
                                    'y_shift': new_bbox['y'] - initial_y
                                })
                                captcha_info['refresh_triggered'] = True
                                print(f"     ⚠️  验证码刷新导致位置偏移: {new_bbox['y'] - initial_y}px")
                        except:
                            pass
            except:
                continue
        
        self.analysis_results['captcha_behavior'] = captcha_info
    
    def detect_page_shake(self, page):
        """检测页面抖动"""
        print("   检测页面抖动...")
        
        shake_detected = False
        shake_events = []
        
        try:
            # 监控关键元素的位置变化
            key_selectors = [
                '.modal', '.dialog', '.login-form', 
                'input[type="password"]', 'input[placeholder*="用户名"]',
                'button:has-text("登录")'
            ]
            
            element_positions = {}
            
            # 记录初始位置
            for selector in key_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        element = page.locator(selector).first
                        if element.is_visible():
                            bbox = element.bounding_box()
                            if bbox:
                                element_positions[selector] = bbox['y']
                except:
                    continue
            
            # 监控5秒内的位置变化
            for i in range(50):  # 每100ms检查一次，共5秒
                time.sleep(0.1)
                
                for selector, initial_y in element_positions.items():
                    try:
                        if page.locator(selector).count() > 0:
                            element = page.locator(selector).first
                            if element.is_visible():
                                bbox = element.bounding_box()
                                if bbox and abs(bbox['y'] - initial_y) > 2:
                                    shake_events.append({
                                        'time': i * 0.1,
                                        'selector': selector,
                                        'y_shift': bbox['y'] - initial_y
                                    })
                                    shake_detected = True
                                    element_positions[selector] = bbox['y']  # 更新位置
                    except:
                        continue
        
        except Exception as e:
            print(f"     抖动检测异常: {str(e)}")
        
        self.analysis_results['shake_events'] = shake_events
        return shake_detected
    
    def test_modal_close_effect(self, page):
        """测试关闭模态框后的效果"""
        print("   测试关闭登录框...")
        
        close_selectors = [
            '.close', '.el-dialog__close', '.modal-close',
            '[class*="close"]', 'button:has-text("取消")',
            'button:has-text("关闭")', '.layui-layer-close'
        ]
        
        modal_closed = False
        for selector in close_selectors:
            try:
                if page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if element.is_visible():
                        print(f"     点击关闭按钮: {selector}")
                        element.click()
                        time.sleep(2)
                        modal_closed = True
                        break
            except:
                continue
        
        if not modal_closed:
            # 尝试按ESC键关闭
            try:
                page.keyboard.press('Escape')
                time.sleep(2)
                modal_closed = True
                print("     使用ESC键关闭")
            except:
                print("     无法关闭登录框")
        
        if modal_closed:
            # 检查关闭后是否还有抖动
            print("     检查关闭后的页面状态...")
            post_close_shake = self.detect_page_shake(page)
            
            self.analysis_results['post_close_analysis'] = {
                'modal_closed': True,
                'shake_after_close': post_close_shake
            }
            
            if not post_close_shake:
                print("     ✅ 关闭登录框后抖动消失")
                self.analysis_results['shake_triggers'].append("登录框本身是抖动的主要原因")
            else:
                print("     ⚠️  关闭后仍有抖动")
    
    def generate_recommendations(self):
        """生成优化建议"""
        recommendations = []
        
        # 基于分析结果生成建议
        if self.analysis_results.get('shake_events'):
            recommendations.append({
                'type': 'modal_stability',
                'issue': '登录框存在位置抖动',
                'suggestion': '在操作登录框前等待其完全稳定，避免在动画期间进行操作',
                'priority': 'high'
            })
        
        if self.analysis_results.get('captcha_behavior', {}).get('refresh_triggered'):
            recommendations.append({
                'type': 'captcha_impact',
                'issue': '验证码刷新影响页面布局',
                'suggestion': '在验证码刷新后添加短暂等待，确保布局稳定',
                'priority': 'medium'
            })
        
        modal_elements = self.analysis_results.get('login_modal_elements', [])
        if modal_elements:
            recommendations.append({
                'type': 'modal_detection',
                'issue': f'检测到{len(modal_elements)}个可能的模态框元素',
                'suggestion': '使用具体的模态框选择器而不是通用选择器，提高稳定性',
                'priority': 'medium'
            })
        
        self.analysis_results['recommendations'] = recommendations
        
        print(f"\n生成了 {len(recommendations)} 条建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['issue']}")
            print(f"      建议: {rec['suggestion']}")
    
    def save_analysis_results(self):
        """保存分析结果"""
        try:
            with open('login_modal_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            print(f"\n分析结果已保存到: login_modal_analysis.json")
        except Exception as e:
            print(f"❌ 保存分析结果失败: {str(e)}")

def main():
    """主函数"""
    analyzer = LoginModalAnalyzer()
    
    try:
        success = analyzer.analyze_login_modal()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 登录模态框分析完成!")
            print("详细分析结果请查看: login_modal_analysis.json")
            print("=" * 60)
            return 0
        else:
            print("\n❌ 登录模态框分析失败!")
            return 1
            
    except Exception as e:
        print(f"\n💥 分析过程中出现异常: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)