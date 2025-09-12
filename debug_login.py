#!/usr/bin/env python3
"""
登录页面调试工具
用于分析目标网站的登录页面结构，帮助改进自动登录实现
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from config.config import Config
import time

def analyze_login_page():
    """分析登录页面结构"""
    print("=== 登录页面结构分析工具 ===")
    print(f"目标网站: {Config.BASE_URL}")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.firefox.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            # 访问主页
            print("正在访问主页...")
            page.goto(Config.BASE_URL)
            page.wait_for_load_state('networkidle')
            
            # 截图保存
            page.screenshot(path="data/debug_homepage.png")
            print("主页截图已保存: data/debug_homepage.png")
            
            # 查找登录入口
            print("\n=== 查找登录入口 ===")
            login_entry_selectors = [
                'text=登录',
                'a[href*="login"]',
                '[class*="login"]',
                'button:has-text("登录")',
                '[title*="登录"]',
                '[id*="login"]'
            ]
            
            login_found = False
            for selector in login_entry_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        for i, element in enumerate(elements):
                            if element.is_visible():
                                print(f"找到登录入口 {i+1}: {selector}")
                                print(f"  文本: {element.inner_text().strip()}")
                                print(f"  href: {element.get_attribute('href') or 'N/A'}")
                                
                                # 点击第一个可见的登录按钮
                                if not login_found:
                                    element.click()
                                    login_found = True
                                    break
                except Exception as e:
                    continue
            
            if not login_found:
                print("未找到明显的登录入口，可能已在登录页面")
            
            # 等待页面跳转
            time.sleep(3)
            page.wait_for_load_state('networkidle')
            
            # 截图保存登录页面
            page.screenshot(path="data/debug_login_page.png")
            print("登录页面截图已保存: data/debug_login_page.png")
            
            print(f"\n当前页面URL: {page.url}")
            
            # 分析表单元素
            print("\n=== 分析表单元素 ===")
            
            # 查找所有input元素
            inputs = page.locator('input').all()
            print(f"找到 {len(inputs)} 个input元素:")
            
            for i, input_elem in enumerate(inputs):
                try:
                    if input_elem.is_visible():
                        input_type = input_elem.get_attribute('type') or 'text'
                        name = input_elem.get_attribute('name') or 'N/A'
                        id_attr = input_elem.get_attribute('id') or 'N/A'
                        placeholder = input_elem.get_attribute('placeholder') or 'N/A'
                        class_attr = input_elem.get_attribute('class') or 'N/A'
                        
                        print(f"  Input {i+1}:")
                        print(f"    type: {input_type}")
                        print(f"    name: {name}")
                        print(f"    id: {id_attr}")
                        print(f"    placeholder: {placeholder}")
                        print(f"    class: {class_attr}")
                        print()
                except Exception as e:
                    continue
            
            # 查找图片元素（可能的验证码）
            print("=== 分析图片元素 ===")
            images = page.locator('img').all()
            print(f"找到 {len(images)} 个img元素:")
            
            for i, img in enumerate(images):
                try:
                    if img.is_visible():
                        src = img.get_attribute('src') or 'N/A'
                        alt = img.get_attribute('alt') or 'N/A'
                        class_attr = img.get_attribute('class') or 'N/A'
                        id_attr = img.get_attribute('id') or 'N/A'
                        
                        # 获取图片尺寸
                        bbox = img.bounding_box()
                        size_info = f"{bbox['width']}x{bbox['height']}" if bbox else 'N/A'
                        
                        print(f"  Image {i+1}:")
                        print(f"    src: {src}")
                        print(f"    alt: {alt}")
                        print(f"    class: {class_attr}")
                        print(f"    id: {id_attr}")
                        print(f"    size: {size_info}")
                        
                        # 判断是否可能是验证码
                        if bbox and 50 < bbox['width'] < 300 and 20 < bbox['height'] < 100:
                            print(f"    -> 可能是验证码图片!")
                        print()
                except Exception as e:
                    continue
            
            # 查找按钮元素
            print("=== 分析按钮元素 ===")
            buttons = page.locator('button').all()
            print(f"找到 {len(buttons)} 个button元素:")
            
            for i, button in enumerate(buttons):
                try:
                    if button.is_visible():
                        text = button.inner_text().strip()
                        type_attr = button.get_attribute('type') or 'button'
                        class_attr = button.get_attribute('class') or 'N/A'
                        id_attr = button.get_attribute('id') or 'N/A'
                        
                        print(f"  Button {i+1}:")
                        print(f"    text: {text}")
                        print(f"    type: {type_attr}")
                        print(f"    class: {class_attr}")
                        print(f"    id: {id_attr}")
                        print()
                except Exception as e:
                    continue
            
            # 查找表单元素
            print("=== 分析表单元素 ===")
            forms = page.locator('form').all()
            print(f"找到 {len(forms)} 个form元素:")
            
            for i, form in enumerate(forms):
                try:
                    action = form.get_attribute('action') or 'N/A'
                    method = form.get_attribute('method') or 'GET'
                    class_attr = form.get_attribute('class') or 'N/A'
                    id_attr = form.get_attribute('id') or 'N/A'
                    
                    print(f"  Form {i+1}:")
                    print(f"    action: {action}")
                    print(f"    method: {method}")
                    print(f"    class: {class_attr}")
                    print(f"    id: {id_attr}")
                    print()
                except Exception as e:
                    continue
            
            print("\n=== 分析完成 ===")
            print("请查看截图文件了解页面结构:")
            print("- data/debug_homepage.png")
            print("- data/debug_login_page.png")
            
            print("\n按回车键关闭浏览器...")
            input()
            
        except Exception as e:
            print(f"分析过程中发生错误: {str(e)}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    analyze_login_page()