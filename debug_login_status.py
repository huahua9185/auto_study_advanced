#!/usr/bin/env python3
"""
登录状态检测调试工具
用于分析登录前后的页面变化，找出最可靠的登录成功标志
"""

import sys
from pathlib import Path
import time
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from config.config import Config
from src.captcha_solver import captcha_solver

def analyze_login_status():
    """分析登录状态变化"""
    print("=== 登录状态检测分析工具 ===")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        try:
            # 1. 分析登录前的页面状态
            print("\n【阶段1：登录前页面分析】")
            page.goto(Config.BASE_URL)
            page.wait_for_load_state('networkidle')
            
            before_login = {
                'url': page.url,
                'title': page.title(),
                'cookies': len(page.context.cookies()),
                'localStorage_items': page.evaluate('() => Object.keys(localStorage).length'),
                'sessionStorage_items': page.evaluate('() => Object.keys(sessionStorage).length'),
            }
            
            print(f"登录前URL: {before_login['url']}")
            print(f"页面标题: {before_login['title']}")
            print(f"Cookie数量: {before_login['cookies']}")
            print(f"LocalStorage项数: {before_login['localStorage_items']}")
            print(f"SessionStorage项数: {before_login['sessionStorage_items']}")
            
            # 获取页面上的关键元素
            print("\n登录前页面元素:")
            elements_before = []
            test_selectors = [
                'text=登录',
                'text=退出',
                'text=学习中心',
                'text=个人中心',
                'text=我的学习',
                '[class*="login"]',
                '[class*="user"]',
                '[class*="logout"]',
            ]
            
            for selector in test_selectors:
                count = page.locator(selector).count()
                if count > 0:
                    elements_before.append(f"  ✓ {selector}: {count}个")
                    
            for elem in elements_before:
                print(elem)
            
            # 2. 执行登录
            print("\n【阶段2：执行登录】")
            print("点击登录按钮...")
            page.click('text=登录')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # 填写登录表单
            print("填写用户名...")
            username_input = page.locator('input[placeholder="用户名"]').first
            username_input.click()
            username_input.fill(Config.USERNAME)
            
            print("填写密码...")
            password_input = page.locator('input[type="password"]').first
            password_input.click()
            password_input.fill(Config.PASSWORD)
            
            # 处理验证码
            print("识别验证码...")
            captcha_text = captcha_solver.solve_captcha_from_element(
                page, 
                'img[src*="/device/login!get_auth_code.do"]'
            )
            print(f"验证码: {captcha_text}")
            
            captcha_input = page.locator('input[placeholder="验证码"]').first
            captcha_input.click()
            captcha_input.fill(captcha_text)
            
            # 截图登录前状态
            page.screenshot(path="data/debug_before_submit.png")
            
            # 提交登录
            print("提交登录表单...")
            submit_button = page.locator('button.el-button.el-button--primary:has-text("登录")').first
            submit_button.click()
            
            # 3. 监控登录后的变化
            print("\n【阶段3：监控页面变化】")
            
            # 等待页面变化
            for i in range(10):  # 最多等待10秒
                time.sleep(1)
                current_url = page.url
                print(f"第{i+1}秒 - URL: {current_url}")
                
                # 检查URL变化
                if current_url != before_login['url']:
                    print(f"  ✓ URL已变化!")
                    break
                    
                # 检查是否有错误提示
                error_messages = [
                    'text=用户名或密码错误',
                    'text=验证码错误',
                    'text=登录失败',
                    '.el-message--error',
                    '.el-notification__content'
                ]
                
                for error_sel in error_messages:
                    if page.locator(error_sel).count() > 0:
                        error_text = page.locator(error_sel).first.inner_text()
                        print(f"  ✗ 发现错误提示: {error_text}")
                        
            # 4. 分析登录后的页面状态
            print("\n【阶段4：登录后页面分析】")
            page.wait_for_load_state('networkidle')
            
            after_login = {
                'url': page.url,
                'title': page.title(),
                'cookies': len(page.context.cookies()),
                'localStorage_items': page.evaluate('() => Object.keys(localStorage).length'),
                'sessionStorage_items': page.evaluate('() => Object.keys(sessionStorage).length'),
            }
            
            print(f"登录后URL: {after_login['url']}")
            print(f"页面标题: {after_login['title']}")
            print(f"Cookie数量: {after_login['cookies']}")
            print(f"LocalStorage项数: {after_login['localStorage_items']}")
            print(f"SessionStorage项数: {after_login['sessionStorage_items']}")
            
            # 获取localStorage和sessionStorage内容
            print("\nLocalStorage内容:")
            local_storage = page.evaluate('() => Object.entries(localStorage)')
            for key, value in local_storage[:5]:  # 只显示前5个
                print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
                
            print("\nSessionStorage内容:")
            session_storage = page.evaluate('() => Object.entries(sessionStorage)')
            for key, value in session_storage[:5]:  # 只显示前5个
                print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
            
            # 检查登录后的页面元素
            print("\n登录后页面元素:")
            elements_after = []
            
            for selector in test_selectors:
                count = page.locator(selector).count()
                if count > 0:
                    elements_after.append(f"  ✓ {selector}: {count}个")
                    
            for elem in elements_after:
                print(elem)
                
            # 截图登录后状态
            page.screenshot(path="data/debug_after_login.png")
            
            # 5. 提出判定建议
            print("\n【阶段5：登录成功判定建议】")
            print("基于以上分析，建议使用以下条件判定登录成功：")
            
            # URL变化
            if after_login['url'] != before_login['url']:
                print(f"1. URL变化: {before_login['url']} -> {after_login['url']}")
                
            # Cookie变化
            if after_login['cookies'] > before_login['cookies']:
                print(f"2. Cookie增加: {before_login['cookies']} -> {after_login['cookies']}")
                
            # Storage变化
            if after_login['localStorage_items'] > before_login['localStorage_items']:
                print(f"3. LocalStorage增加: {before_login['localStorage_items']} -> {after_login['localStorage_items']}")
                
            # 元素变化
            print("4. 页面元素变化:")
            for elem in elements_after:
                if elem not in elements_before:
                    print(f"   新增元素: {elem}")
                    
            # 检查特定的登录成功标志
            print("\n5. 特定登录成功标志:")
            
            # 检查token
            token_keys = ['token', 'access_token', 'auth', 'jwt']
            for key in token_keys:
                # 检查localStorage
                local_value = page.evaluate(f'() => localStorage.getItem("{key}")')
                if local_value:
                    print(f"   ✓ LocalStorage中发现{key}: {local_value[:20]}...")
                    
                # 检查sessionStorage
                session_value = page.evaluate(f'() => sessionStorage.getItem("{key}")')
                if session_value:
                    print(f"   ✓ SessionStorage中发现{key}: {session_value[:20]}...")
                    
            # 检查用户信息
            user_keys = ['user', 'userInfo', 'username', 'userId']
            for key in user_keys:
                local_value = page.evaluate(f'() => localStorage.getItem("{key}")')
                if local_value:
                    print(f"   ✓ 用户信息{key}: {local_value[:30]}...")
                    
            print("\n分析完成！请查看 data/debug_*.png 截图文件")
            
        except Exception as e:
            print(f"分析过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            print("\n按回车键关闭浏览器...")
            input()
            browser.close()

if __name__ == "__main__":
    analyze_login_status()