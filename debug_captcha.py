#!/usr/bin/env python3
"""
验证码识别调试工具
专门用于调试验证码识别问题
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from config.config import Config
from src.captcha_solver import captcha_solver
import time

def debug_captcha():
    """调试验证码识别"""
    print("=== 验证码识别调试工具 ===")
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
            
            # 点击登录按钮
            print("点击登录按钮...")
            login_button_selectors = [
                'text=登录',
                'button:has-text("登录")',
                '[class*="login"]'
            ]
            
            for selector in login_button_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.click(selector)
                        page.wait_for_load_state('networkidle')
                        print(f"成功点击登录按钮: {selector}")
                        break
                except:
                    continue
            
            time.sleep(3)
            
            # 查找验证码输入框
            print("\n=== 查找验证码输入框 ===")
            captcha_input_selectors = [
                'input[placeholder="验证码"].el-input__inner',
                'input[placeholder="验证码"]',
                'input[name="captcha"]',
                'input[name="verifycode"]',
                'input[name="code"]',
                'input[placeholder*="验证码"]'
            ]
            
            captcha_input = None
            for selector in captcha_input_selectors:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            captcha_input = element
                            print(f"✓ 找到验证码输入框: {selector}")
                            break
                    if captcha_input:
                        break
                except:
                    continue
            
            if not captcha_input:
                print("✗ 未找到验证码输入框")
                return
            
            # 查找验证码图片
            print("\n=== 查找验证码图片 ===")
            captcha_image_selectors = [
                'img[src*="/device/login!get_auth_code.do"]',
                'img[src*="captcha"]',
                'img[src*="verifycode"]',
                'img[src*="code"]',
                'img[src*="verify"]'
            ]
            
            captcha_image_element = None
            captcha_selector = None
            
            for selector in captcha_image_selectors:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            bbox = element.bounding_box()
                            if bbox:
                                print(f"图片选择器: {selector}")
                                print(f"  尺寸: {bbox['width']}x{bbox['height']}")
                                print(f"  src: {element.get_attribute('src')}")
                                
                                if 50 < bbox['width'] < 300 and 20 < bbox['height'] < 100:
                                    captcha_image_element = element
                                    captcha_selector = selector
                                    print(f"✓ 确认为验证码图片!")
                                    break
                    if captcha_image_element:
                        break
                except Exception as e:
                    print(f"检查选择器失败 {selector}: {e}")
                    continue
            
            if not captcha_image_element:
                print("✗ 未找到验证码图片")
                return
            
            # 截图验证码
            print("\n=== 截图验证码 ===")
            captcha_screenshot = captcha_image_element.screenshot()
            with open("data/debug_captcha_image.png", "wb") as f:
                f.write(captcha_screenshot)
            print("验证码图片已保存: data/debug_captcha_image.png")
            
            # 尝试识别验证码
            print("\n=== 识别验证码 ===")
            try:
                # 直接使用captcha_solver识别
                captcha_text = captcha_solver.solve_captcha_from_element(page, captcha_selector)
                print(f"识别结果: '{captcha_text}'")
                print(f"识别长度: {len(captcha_text)}")
                print(f"识别字符: {list(captcha_text)}")
                
                # 验证结果有效性
                if captcha_solver._is_valid_captcha(captcha_text):
                    print("✓ 验证码格式有效")
                    
                    # 尝试输入验证码
                    print("\n=== 输入验证码 ===")
                    captcha_input.click()
                    time.sleep(0.5)
                    captcha_input.clear()
                    time.sleep(0.2)
                    
                    for char in captcha_text:
                        captcha_input.type(char)
                        time.sleep(0.1)
                    
                    print(f"✓ 验证码已输入: {captcha_text}")
                    
                    # 获取输入框的值来确认
                    input_value = captcha_input.input_value()
                    print(f"输入框当前值: '{input_value}'")
                    
                else:
                    print("✗ 验证码格式无效")
                    
            except Exception as e:
                print(f"✗ 验证码识别失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # 等待用户查看结果
            print("\n按回车键继续...")
            input()
            
        except Exception as e:
            print(f"调试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            browser.close()

if __name__ == "__main__":
    debug_captcha()