#!/usr/bin/env python3
"""
学习中心页面分析调试工具
专门寻找"进入班级"和"本年选修"链接
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
from src.captcha_solver_enhanced import enhanced_captcha_solver as captcha_solver

def analyze_study_center():
    """分析学习中心页面，寻找课程入口"""
    print("=== 学习中心页面分析工具 ===")
    
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
            
            # 分析学习中心页面
            print("\n【阶段2：分析学习中心页面】")
            analyze_main_page(page)
            
        except Exception as e:
            print(f"分析过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            print("\n分析完成，2秒后自动关闭浏览器...")
            time.sleep(2)
            browser.close()

def login_to_system(page, max_retries=3):
    """登录到系统"""
    for attempt in range(max_retries):
        try:
            print(f"\n【登录尝试 {attempt + 1}/{max_retries}】")
            
            page.goto(Config.BASE_URL)
            page.wait_for_load_state('networkidle')
            time.sleep(1)
            
            # 点击登录 - 使用更具体的选择器
            print("点击登录按钮...")
            try:
                # 尝试多个登录按钮选择器
                login_selectors = [
                    'div.header_login:has-text("登录")',
                    'a:has-text("登录")',
                    'button:has-text("登录")',
                    '.header_login',
                    'text=登录'
                ]
                
                login_clicked = False
                for selector in login_selectors:
                    try:
                        login_btn = page.locator(selector).first
                        if login_btn.count() > 0 and login_btn.is_visible():
                            login_btn.click()
                            login_clicked = True
                            print(f"  使用选择器成功点击登录: {selector}")
                            break
                    except:
                        continue
                
                if not login_clicked:
                    print("  所有登录按钮选择器都失败，跳过此次尝试")
                    continue
                    
                page.wait_for_load_state('networkidle')
                time.sleep(0.5)  # 等待登录对话框完全加载
            except Exception as e:
                print(f"点击登录按钮失败: {str(e)}")
                continue
            
            # 填写用户名
            print("填写用户名...")
            username_input = page.locator('input[placeholder="用户名"]').first
            username_input.click()
            username_input.fill(Config.USERNAME)
            time.sleep(0.3)
            
            # 填写密码
            print("填写密码...")
            password_input = page.locator('input[type="password"]').first
            password_input.click()
            password_input.fill(Config.PASSWORD)
            time.sleep(0.3)
            
            # 识别验证码 - 多次尝试
            captcha_success = False
            for captcha_attempt in range(3):
                print(f"识别验证码 (尝试 {captcha_attempt + 1}/3)...")
                try:
                    captcha_text = captcha_solver.solve_captcha_from_element(
                        page, 
                        'img[src*="/device/login!get_auth_code.do"]'
                    )
                    print(f"验证码: {captcha_text}")
                    
                    # 验证是否为4位数字
                    if captcha_text and len(captcha_text) == 4 and captcha_text.isdigit():
                        captcha_input = page.locator('input[placeholder="验证码"]').first
                        captcha_input.click()
                        captcha_input.clear()
                        captcha_input.fill(captcha_text)
                        captcha_success = True
                        break
                    else:
                        print(f"验证码格式不正确: {captcha_text}, 刷新重试...")
                        # 点击验证码图片刷新
                        captcha_img = page.locator('img[src*="/device/login!get_auth_code.do"]')
                        if captcha_img.count() > 0:
                            captcha_img.click()
                            time.sleep(0.5)
                        continue
                except Exception as e:
                    print(f"验证码识别失败: {str(e)}")
                    continue
            
            if not captcha_success:
                print("验证码识别失败，尝试下一轮登录...")
                continue
            
            # 提交登录
            print("提交登录...")
            submit_button = page.locator('button.el-button.el-button--primary:has-text("登录")').first
            submit_button.click()
        
            # 等待登录结果
            page.wait_for_load_state('networkidle')
            time.sleep(1)
            
            # 检查登录是否成功 - 使用多重验证
            print("验证登录状态...")
            
            # 检查是否有错误提示
            error_indicators = [
                'text=用户名或密码错误',
                'text=验证码错误', 
                'text=登录失败',
                '.el-message--error',
                '.el-notification--error'
            ]
            
            has_error = False
            error_text = ""
            for indicator in error_indicators:
                try:
                    if page.locator(indicator).count() > 0:
                        error_element = page.locator(indicator).first
                        if error_element.is_visible():
                            error_text = error_element.inner_text()
                            print(f"✗ 登录失败: {error_text}")
                            has_error = True
                            break
                except:
                    continue
            
            if has_error:
                if "验证码错误" in error_text:
                    print("验证码错误，刷新重试...")
                    continue
                elif attempt < max_retries - 1:
                    print(f"登录失败，1秒后重试...")
                    time.sleep(1)
                    continue
                else:
                    return False
            
            # 检查登录表单是否还存在
            login_form_indicators = [
                'input[placeholder="用户名"]',
                'input[placeholder="密码"]', 
                'input[placeholder="验证码"]',
                'button:has-text("登录")'
            ]
            
            visible_form_elements = 0
            for indicator in login_form_indicators:
                try:
                    elements = page.locator(indicator).all()
                    for element in elements:
                        if element.is_visible():
                            visible_form_elements += 1
                            break
                except:
                    continue
            
            if visible_form_elements >= 3:
                print("✗ 登录失败: 登录表单仍然可见")
                if attempt < max_retries - 1:
                    continue
                else:
                    return False
            
            # 检查Cookie中是否有登录会话
            cookies = page.context.cookies()
            has_session = any('JSESSIONID' in cookie.get('name', '') or 
                            'token' in cookie.get('name', '').lower() or
                            'session' in cookie.get('name', '').lower()
                            for cookie in cookies)
            
            # 尝试访问需要登录的页面来最终确认
            try:
                page.goto('https://edu.nxgbjy.org.cn/nxxzxy/index.html#/study_center')
                page.wait_for_load_state('networkidle')
                time.sleep(1)
                
                # 如果页面包含学习相关内容且没有登录表单，说明登录成功
                study_indicators = [
                    'text=学习中心',
                    'text=我的学习',
                    'text=课程',
                    'text=班级',
                    'text=进入班级',
                    'text=本年选修'
                ]
                
                found_study_content = False
                for indicator in study_indicators:
                    try:
                        if page.locator(indicator).count() > 0:
                            found_study_content = True
                            print(f"  找到学习内容: {indicator}")
                            break
                    except:
                        continue
                
                # 检查当前页面URL，如果已经在学习中心页面，不需要检查表单
                current_url = page.url
                is_in_study_center = 'study_center' in current_url
                
                # 如果找到学习内容且有会话，很可能已经登录成功
                if found_study_content and has_session:
                    # 再次检查是否还有可见的登录表单  
                    visible_form_count = 0
                    for indicator in login_form_indicators:
                        try:
                            elements = page.locator(indicator).all()
                            for element in elements:
                                if element.is_visible():
                                    visible_form_count += 1
                                    break
                        except:
                            continue
                    
                    # 如果在学习中心页面或者表单不可见，认为登录成功
                    if is_in_study_center or visible_form_count <= 1:
                        print("✓ 登录成功! (学习内容可见, 有会话Cookie, 在学习中心页面)")
                        return True
                    else:
                        print(f"✗ 登录可能成功但仍有表单: 学习内容={found_study_content}, 可见表单={visible_form_count}, 会话Cookie={has_session}")
                        # 如果有学习内容和会话，可以认为是成功的
                        if found_study_content and has_session:
                            print("✓ 基于学习内容和会话判断为登录成功")
                            return True
                
                print(f"✗ 登录失败: 学习内容={found_study_content}, 会话Cookie={has_session}, 在学习中心={is_in_study_center}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return False
                        
            except Exception as e:
                print(f"✗ 登录验证失败: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return False
                    
        except Exception as e:
            print(f"登录尝试 {attempt + 1} 发生错误: {str(e)}")
            if attempt < max_retries - 1:
                continue
            else:
                return False
    
    print("所有登录尝试都失败了")
    return False

def analyze_main_page(page):
    """分析学习中心主页"""
    try:
        print(f"访问学习中心主页: {Config.STUDY_CENTER_URL}")
        page.goto(Config.STUDY_CENTER_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # 截图保存
        page.screenshot(path="data/debug_study_center.png")
        print("已保存学习中心页面截图: data/debug_study_center.png")
        
        print("\n=== 搜索关键导航链接 ===")
        
        # 重点搜索"进入班级"和"本年选修"
        priority_keywords = ["进入班级", "本年选修"]
        secondary_keywords = ["班级", "必修", "选修", "我的课程", "我的学习", "课程列表"]
        
        found_links = {}
        important_links = {}
        
        # 首先搜索优先级关键词
        for keyword in priority_keywords:
            print(f"\n【重点搜索】关键词: {keyword}")
            
            # 更全面的选择器
            selectors_to_try = [
                f'text={keyword}',
                f'text*={keyword}',
                f'a:has-text("{keyword}")',
                f'button:has-text("{keyword}")',
                f'div:has-text("{keyword}")',
                f'span:has-text("{keyword}")',
                f'[title*="{keyword}"]',
                f'[alt*="{keyword}"]',
                f':text("{keyword}")',
                f':text-matches("{keyword}", "i")'
            ]
            
            keyword_found = False
            for selector in selectors_to_try:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        print(f"  ✓ 使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                        
                        for i, element in enumerate(elements):
                            try:
                                text = element.inner_text().strip()
                                if len(text) > 100:  # 跳过太长的文本
                                    continue
                                
                                # 获取链接信息
                                href = None
                                onclick = None
                                
                                # 检查是否是链接元素
                                if element.locator('a').count() > 0:
                                    href = element.locator('a').first.get_attribute('href')
                                elif element.tag_name == 'a':
                                    href = element.get_attribute('href')
                                
                                # 检查是否有点击事件
                                onclick = element.get_attribute('onclick')
                                
                                print(f"    元素 {i+1}: '{text}'")
                                if href:
                                    print(f"      链接: {href}")
                                if onclick:
                                    print(f"      点击事件: {onclick}")
                                
                                # 保存重要链接
                                if keyword not in important_links:
                                    important_links[keyword] = []
                                
                                important_links[keyword].append({
                                    'text': text,
                                    'href': href,
                                    'onclick': onclick,
                                    'selector': selector,
                                    'tag_name': element.tag_name
                                })
                                
                                keyword_found = True
                                
                            except Exception as e:
                                continue
                                
                except Exception as e:
                    continue
            
            if not keyword_found:
                print(f"  ⚠️ 未找到关键词: {keyword}")
        
        # 然后搜索次要关键词
        for keyword in secondary_keywords:
            print(f"\n--- 搜索关键词: {keyword} ---")
            
            selectors_to_try = [
                f'text={keyword}',
                f'a:has-text("{keyword}")',
                f'button:has-text("{keyword}")',
                f'div:has-text("{keyword}")',
                f'span:has-text("{keyword}")'
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        print(f"  找到 {len(elements)} 个元素")
                        
                        for i, element in enumerate(elements[:3]):  # 只显示前3个
                            try:
                                text = element.inner_text().strip()
                                if len(text) > 50:  # 跳过太长的文本
                                    continue
                                
                                href = None
                                if element.locator('a').count() > 0:
                                    href = element.locator('a').first.get_attribute('href')
                                elif element.tag_name == 'a':
                                    href = element.get_attribute('href')
                                
                                print(f"    元素 {i+1}: '{text}'")
                                if href:
                                    print(f"      链接: {href}")
                                
                                # 保存找到的链接
                                if keyword not in found_links:
                                    found_links[keyword] = []
                                
                                found_links[keyword].append({
                                    'text': text,
                                    'href': href,
                                    'selector': selector
                                })
                                
                            except Exception as e:
                                continue
                                
                except Exception as e:
                    continue
        
        # 保存重要链接
        with open('data/important_links.json', 'w', encoding='utf-8') as f:
            json.dump(important_links, f, ensure_ascii=False, indent=2)
        print(f"\n重要链接已保存到: data/important_links.json")
        
        # 保存所有找到的链接
        with open('data/study_center_links.json', 'w', encoding='utf-8') as f:
            json.dump(found_links, f, ensure_ascii=False, indent=2)
        print(f"所有链接已保存到: data/study_center_links.json")
        
        # 总结重要发现
        print("\n=== 重要发现总结 ===")
        for keyword in priority_keywords:
            if keyword in important_links and important_links[keyword]:
                print(f"\n✓ 找到 '{keyword}' 链接:")
                for i, link in enumerate(important_links[keyword]):
                    print(f"  {i+1}. {link['text']}")
                    if link['href']:
                        print(f"     URL: {link['href']}")
                    if link['onclick']:
                        print(f"     点击事件: {link['onclick']}")
            else:
                print(f"\n✗ 未找到 '{keyword}' 链接")
        
        # 分析导航菜单
        print("\n=== 分析导航菜单 ===")
        analyze_navigation_menu(page)
        
        # 分析所有按钮和链接
        print("\n=== 分析所有按钮和链接 ===")
        analyze_all_clickable_elements(page)
        
    except Exception as e:
        print(f"分析学习中心页面失败: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_navigation_menu(page):
    """分析导航菜单"""
    try:
        # 查找常见的导航菜单选择器
        nav_selectors = [
            'nav',
            '.nav',
            '.navigation',
            '.menu',
            '.sidebar',
            '.left-menu',
            'ul.el-menu',
            '.el-menu-item'
        ]
        
        for selector in nav_selectors:
            try:
                elements = page.locator(selector).all()
                if elements:
                    print(f"\n使用导航选择器 '{selector}' 找到 {len(elements)} 个元素")
                    
                    for i, element in enumerate(elements[:3]):  # 只显示前3个
                        try:
                            text = element.inner_text().strip()
                            if text and len(text) < 200:  # 避免太长的文本
                                print(f"  导航项 {i+1}: {text}")
                        except:
                            continue
            except:
                continue
                
    except Exception as e:
        print(f"分析导航菜单失败: {str(e)}")

def analyze_all_clickable_elements(page):
    """分析所有可点击的元素"""
    try:
        clickable_selectors = [
            'a',
            'button',
            '[onclick]',
            '[role="button"]',
            '.btn',
            '.el-button'
        ]
        
        all_clickable = []
        
        for selector in clickable_selectors:
            try:
                elements = page.locator(selector).all()
                
                for element in elements:
                    try:
                        text = element.inner_text().strip()
                        href = element.get_attribute('href')
                        onclick = element.get_attribute('onclick')
                        
                        if text and len(text) < 50:  # 只要短文本
                            all_clickable.append({
                                'text': text,
                                'href': href,
                                'onclick': onclick,
                                'selector': selector
                            })
                    except:
                        continue
            except:
                continue
        
        # 按文本排序并去重
        unique_clickable = {}
        for item in all_clickable:
            text = item['text']
            if text not in unique_clickable:
                unique_clickable[text] = item
        
        print(f"\n找到 {len(unique_clickable)} 个不重复的可点击元素:")
        for i, (text, item) in enumerate(sorted(unique_clickable.items())[:20]):  # 只显示前20个
            print(f"  {i+1:2d}. {text}")
            if item['href']:
                print(f"      链接: {item['href']}")
            if item['onclick']:
                print(f"      点击: {item['onclick'][:50]}...")
        
        # 保存到文件
        with open('data/clickable_elements.json', 'w', encoding='utf-8') as f:
            json.dump(list(unique_clickable.values()), f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"分析可点击元素失败: {str(e)}")

if __name__ == "__main__":
    analyze_study_center()