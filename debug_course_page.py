#!/usr/bin/env python3
"""
课程页面结构分析调试工具
用于分析必修课和选修课页面的HTML结构，找出正确的解析逻辑
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

def analyze_course_pages():
    """分析课程页面结构"""
    print("=== 课程页面结构分析工具 ===")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        try:
            # 先登录
            print("\n【阶段1：执行登录】")
            success = login_to_system(page)
            if not success:
                print("登录失败，无法继续分析")
                return
            
            # 分析必修课页面
            print("\n【阶段2：分析必修课页面】")
            analyze_required_courses(page)
            
            # 分析选修课页面
            print("\n【阶段3：分析选修课页面】")
            analyze_elective_courses(page)
            
        except Exception as e:
            print(f"分析过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            print("\n按回车键关闭浏览器...")
            input()
            browser.close()

def login_to_system(page):
    """登录到系统"""
    try:
        page.goto(Config.BASE_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        # 点击登录
        print("点击登录按钮...")
        page.click('text=登录')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        # 填写用户名
        print("填写用户名...")
        username_input = page.locator('input[placeholder="用户名"]').first
        username_input.click()
        username_input.fill(Config.USERNAME)
        
        # 填写密码
        print("填写密码...")
        password_input = page.locator('input[type="password"]').first
        password_input.click()
        password_input.fill(Config.PASSWORD)
        
        # 识别验证码
        print("识别验证码...")
        captcha_text = captcha_solver.solve_captcha_from_element(
            page, 
            'img[src*="/device/login!get_auth_code.do"]'
        )
        print(f"验证码: {captcha_text}")
        
        captcha_input = page.locator('input[placeholder="验证码"]').first
        captcha_input.click()
        captcha_input.fill(captcha_text)
        
        # 提交登录
        print("提交登录...")
        submit_button = page.locator('button.el-button.el-button--primary:has-text("登录")').first
        submit_button.click()
        
        # 等待登录结果
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        # 检查是否登录成功
        if page.locator('text=学习中心').count() > 0:
            print("✓ 登录成功!")
            return True
        else:
            print("✗ 登录失败")
            return False
            
    except Exception as e:
        print(f"登录过程中发生错误: {str(e)}")
        return False

def analyze_required_courses(page):
    """分析必修课页面"""
    try:
        print(f"访问必修课页面: {Config.REQUIRED_COURSES_URL}")
        page.goto(Config.REQUIRED_COURSES_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        # 截图保存
        page.screenshot(path="data/debug_required_courses.png")
        print("已保存必修课页面截图: data/debug_required_courses.png")
        
        # 分析页面结构
        print("\n=== 必修课页面结构分析 ===")
        
        # 获取页面标题和URL
        print(f"页面标题: {page.title()}")
        print(f"当前URL: {page.url}")
        
        # 尝试找到所有可能的课程容器
        potential_selectors = [
            '[class*="course"]',
            '[class*="study"]',
            '[class*="item"]',
            '[class*="list"]',
            '[class*="card"]',
            'li',
            'tr',
            '.row',
            '.col'
        ]
        
        course_containers = {}
        for selector in potential_selectors:
            try:
                elements = page.locator(selector).all()
                if elements and len(elements) > 1:  # 至少有2个元素才可能是课程列表
                    course_containers[selector] = len(elements)
                    print(f"选择器 '{selector}': {len(elements)} 个元素")
            except:
                continue
        
        # 分析最可能的课程容器
        if course_containers:
            print(f"\n找到 {len(course_containers)} 个可能的课程容器选择器")
            
            # 按元素数量排序，取最合理的几个
            sorted_containers = sorted(course_containers.items(), key=lambda x: x[1])
            
            print("\n详细分析前3个最可能的选择器:")
            for selector, count in sorted_containers[:3]:
                print(f"\n--- 分析选择器: {selector} ({count}个元素) ---")
                analyze_selector_content(page, selector)
        else:
            print("未找到明显的课程容器")
            
        # 分析所有链接
        print(f"\n=== 分析页面中的所有链接 ===")
        analyze_page_links(page, "必修课")
        
    except Exception as e:
        print(f"分析必修课页面失败: {str(e)}")

def analyze_elective_courses(page):
    """分析选修课页面"""
    try:
        print(f"访问选修课页面: {Config.ELECTIVE_COURSES_URL}")
        page.goto(Config.ELECTIVE_COURSES_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        # 截图保存
        page.screenshot(path="data/debug_elective_courses.png")
        print("已保存选修课页面截图: data/debug_elective_courses.png")
        
        # 分析页面结构
        print("\n=== 选修课页面结构分析 ===")
        
        # 获取页面标题和URL
        print(f"页面标题: {page.title()}")
        print(f"当前URL: {page.url}")
        
        # 尝试找到所有可能的课程容器
        potential_selectors = [
            '[class*="course"]',
            '[class*="study"]',
            '[class*="item"]',
            '[class*="list"]',
            '[class*="card"]',
            'li',
            'tr',
            '.row',
            '.col'
        ]
        
        course_containers = {}
        for selector in potential_selectors:
            try:
                elements = page.locator(selector).all()
                if elements and len(elements) > 1:  # 至少有2个元素才可能是课程列表
                    course_containers[selector] = len(elements)
                    print(f"选择器 '{selector}': {len(elements)} 个元素")
            except:
                continue
        
        # 分析最可能的课程容器
        if course_containers:
            print(f"\n找到 {len(course_containers)} 个可能的课程容器选择器")
            
            # 按元素数量排序，取最合理的几个
            sorted_containers = sorted(course_containers.items(), key=lambda x: x[1])
            
            print("\n详细分析前3个最可能的选择器:")
            for selector, count in sorted_containers[:3]:
                print(f"\n--- 分析选择器: {selector} ({count}个元素) ---")
                analyze_selector_content(page, selector)
        else:
            print("未找到明显的课程容器")
            
        # 分析所有链接
        print(f"\n=== 分析页面中的所有链接 ===")
        analyze_page_links(page, "选修课")
        
    except Exception as e:
        print(f"分析选修课页面失败: {str(e)}")

def analyze_selector_content(page, selector):
    """分析指定选择器的内容"""
    try:
        elements = page.locator(selector).all()
        
        # 分析前5个元素的内容
        for i, element in enumerate(elements[:5]):
            try:
                text = element.inner_text().strip()
                html = element.inner_html()
                
                print(f"  元素 {i+1}:")
                print(f"    文本: {text[:100]}{'...' if len(text) > 100 else ''}")
                
                # 查找链接
                links = element.locator('a').all()
                if links:
                    for j, link in enumerate(links):
                        try:
                            href = link.get_attribute('href')
                            link_text = link.inner_text().strip()
                            print(f"    链接 {j+1}: {link_text} -> {href}")
                        except:
                            continue
                
                # 查找可能的进度信息
                progress_indicators = element.locator('[class*="progress"], [class*="percent"], span:has-text("%")').all()
                if progress_indicators:
                    for progress in progress_indicators:
                        try:
                            progress_text = progress.inner_text().strip()
                            print(f"    进度: {progress_text}")
                        except:
                            continue
                            
            except Exception as e:
                print(f"    分析元素 {i+1} 时出错: {str(e)}")
                continue
                
    except Exception as e:
        print(f"分析选择器内容失败: {str(e)}")

def analyze_page_links(page, course_type):
    """分析页面中的所有链接"""
    try:
        all_links = page.locator('a').all()
        course_links = []
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                text = link.inner_text().strip()
                
                if not href or not text or len(text) < 3:
                    continue
                
                # 过滤无关链接
                if any(keyword in text.lower() for keyword in ['登录', '首页', '退出', '帮助', '设置']):
                    continue
                
                # 检查是否是课程相关链接
                if any(keyword in href.lower() for keyword in ['course', 'study', 'video', 'learn']):
                    course_links.append({
                        'text': text,
                        'href': href
                    })
                    
            except:
                continue
        
        print(f"\n找到 {len(course_links)} 个可能的{course_type}链接:")
        for i, link in enumerate(course_links[:10]):  # 只显示前10个
            print(f"  {i+1}. {link['text']} -> {link['href']}")
        
        if len(course_links) > 10:
            print(f"  ... 还有 {len(course_links) - 10} 个链接")
        
        # 保存链接数据到文件
        with open(f'data/{course_type}_links.json', 'w', encoding='utf-8') as f:
            json.dump(course_links, f, ensure_ascii=False, indent=2)
        print(f"\n链接数据已保存到: data/{course_type}_links.json")
        
    except Exception as e:
        print(f"分析页面链接失败: {str(e)}")

if __name__ == "__main__":
    analyze_course_pages()