#!/usr/bin/env python3
"""
调试验证码错误前后网页结构变化
"""

import time
from playwright.sync_api import sync_playwright
from config.config import Config
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('page_structure_debug.log')
    ]
)

def analyze_page_structure():
    """分析验证码错误前后的页面结构变化"""
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.firefox.launch(
            headless=False,  # 显示浏览器窗口以便观察
            args=[
                '--no-sandbox', 
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        
        try:
            # 访问登录页面
            logging.info("=== 访问登录页面 ===")
            page.goto(Config.BASE_URL)
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # 点击登录按钮
            page.click('text=登录')
            page.wait_for_load_state('networkidle', timeout=5000)
            
            # 分析初始页面结构
            logging.info("=== 分析初始登录页面结构 ===")
            analyze_form_elements(page, "初始状态")
            
            # 填写用户名和密码
            logging.info("=== 填写用户名和密码 ===")
            page.fill('input[placeholder="用户名"]', Config.USERNAME)
            time.sleep(1)
            page.fill('input[type="password"].el-input__inner', Config.PASSWORD)
            time.sleep(1)
            
            # 分析填写信息后的页面结构
            logging.info("=== 分析填写信息后的页面结构 ===")
            analyze_form_elements(page, "填写信息后")
            
            # 故意输入错误验证码
            logging.info("=== 输入错误验证码 ===")
            captcha_input = page.locator('input[placeholder="验证码"].el-input__inner')
            captcha_input.fill("0000")  # 故意输入错误验证码
            time.sleep(1)
            
            # 提交登录
            logging.info("=== 提交登录表单 ===")
            page.click('button.el-button.el-button--primary:has-text("登录")')
            time.sleep(3)  # 等待错误响应
            
            # 分析验证码错误后的页面结构
            logging.info("=== 分析验证码错误后的页面结构 ===")
            analyze_form_elements(page, "验证码错误后")
            analyze_error_messages(page)
            
            # 等待一段时间观察页面状态变化
            logging.info("=== 等待观察页面状态变化 ===")
            for i in range(10):
                time.sleep(1)
                logging.info(f"--- {i+1}秒后的页面状态 ---")
                analyze_form_elements(page, f"{i+1}秒后")
                
                # 检查是否有动态变化
                if check_dynamic_changes(page):
                    logging.warning(f"检测到页面在第{i+1}秒发生动态变化!")
            
            # 尝试重新输入
            logging.info("=== 尝试重新定位和填写表单 ===")
            retry_form_filling(page)
            
            # 保持页面打开，便于手动观察
            input("按Enter键关闭浏览器...")
            
        except Exception as e:
            logging.error(f"分析过程发生错误: {e}")
            input("发生错误，按Enter键关闭浏览器...")
        finally:
            browser.close()

def analyze_form_elements(page, stage):
    """分析表单元素"""
    logging.info(f"--- {stage} 表单元素分析 ---")
    
    # 用户名输入框
    username_selectors = [
        'input[placeholder="用户名"]',
        'input[name="username"]',
        'input[type="text"]'
    ]
    
    for selector in username_selectors:
        count = page.locator(selector).count()
        if count > 0:
            logging.info(f"用户名输入框 {selector}: {count}个")
            for i in range(count):
                elem = page.locator(selector).nth(i)
                visible = elem.is_visible()
                enabled = elem.is_enabled()
                logging.info(f"  第{i+1}个: visible={visible}, enabled={enabled}")
    
    # 密码输入框
    password_selectors = [
        'input[type="password"].el-input__inner',
        'input[type="password"]',
        'input[placeholder*="密码"]'
    ]
    
    for selector in password_selectors:
        count = page.locator(selector).count()
        if count > 0:
            logging.info(f"密码输入框 {selector}: {count}个")
            for i in range(count):
                elem = page.locator(selector).nth(i)
                visible = elem.is_visible()
                enabled = elem.is_enabled()
                logging.info(f"  第{i+1}个: visible={visible}, enabled={enabled}")
    
    # 验证码输入框
    captcha_selectors = [
        'input[placeholder="验证码"].el-input__inner',
        'input[placeholder="验证码"]',
        'input[placeholder*="验证码"]'
    ]
    
    for selector in captcha_selectors:
        count = page.locator(selector).count()
        if count > 0:
            logging.info(f"验证码输入框 {selector}: {count}个")
            for i in range(count):
                elem = page.locator(selector).nth(i)
                visible = elem.is_visible()
                enabled = elem.is_enabled()
                value = elem.input_value() if visible else "不可见"
                logging.info(f"  第{i+1}个: visible={visible}, enabled={enabled}, value='{value}'")
    
    # 登录按钮
    login_button_selectors = [
        'button.el-button.el-button--primary:has-text("登录")',
        'button:has-text("登录")',
        'text=登录'
    ]
    
    for selector in login_button_selectors:
        count = page.locator(selector).count()
        if count > 0:
            logging.info(f"登录按钮 {selector}: {count}个")
            for i in range(count):
                elem = page.locator(selector).nth(i)
                visible = elem.is_visible()
                enabled = elem.is_enabled()
                logging.info(f"  第{i+1}个: visible={visible}, enabled={enabled}")

def analyze_error_messages(page):
    """分析错误信息"""
    logging.info("--- 错误信息分析 ---")
    
    error_selectors = [
        'text=校验码错误',
        'text=验证码错误',
        '.el-message--error',
        '.el-notification--error',
        '.error-message',
        '[class*="error"]'
    ]
    
    for selector in error_selectors:
        count = page.locator(selector).count()
        if count > 0:
            logging.info(f"错误信息 {selector}: {count}个")
            for i in range(count):
                elem = page.locator(selector).nth(i)
                visible = elem.is_visible()
                text = elem.inner_text() if visible else "不可见"
                logging.info(f"  第{i+1}个: visible={visible}, text='{text}'")

def check_dynamic_changes(page):
    """检查页面是否有动态变化"""
    try:
        # 检查是否有新的元素或loading状态
        loading_indicators = [
            '.loading',
            '.el-loading',
            '[class*="loading"]',
            '.spinner'
        ]
        
        for selector in loading_indicators:
            if page.locator(selector).count() > 0:
                return True
        
        return False
    except:
        return False

def retry_form_filling(page):
    """尝试重新填写表单"""
    logging.info("--- 重新填写表单测试 ---")
    
    try:
        # 重新定位用户名输入框
        username_input = page.locator('input[placeholder="用户名"]').first
        if username_input.is_visible():
            username_input.clear()
            username_input.fill(Config.USERNAME)
            logging.info("✓ 用户名重新填写成功")
        else:
            logging.error("✗ 用户名输入框不可见")
        
        time.sleep(1)
        
        # 重新定位密码输入框
        password_input = page.locator('input[type="password"].el-input__inner').first
        if password_input.is_visible():
            password_input.clear()
            password_input.fill(Config.PASSWORD)
            logging.info("✓ 密码重新填写成功")
        else:
            logging.error("✗ 密码输入框不可见")
        
        time.sleep(1)
        
        # 重新定位验证码输入框
        captcha_input = page.locator('input[placeholder="验证码"].el-input__inner').first
        if captcha_input.is_visible():
            captcha_input.clear()
            captcha_input.fill("1234")
            logging.info("✓ 验证码重新填写成功")
        else:
            logging.error("✗ 验证码输入框不可见")
            
    except Exception as e:
        logging.error(f"重新填写表单失败: {e}")

if __name__ == "__main__":
    analyze_page_structure()