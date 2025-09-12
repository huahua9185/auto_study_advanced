#!/usr/bin/env python
"""
测试必修课程获取逻辑
"""

import logging
import sys
import time
import json

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加src目录到系统路径
sys.path.insert(0, 'src')

from login import LoginManager
from course_parser import CourseParser
from config.config import Config

def test_course_fetch():
    """测试课程获取功能"""
    login_manager = LoginManager()
    course_parser = None
    
    try:
        print("=" * 60)
        print("开始测试必修课程获取")
        print("=" * 60)
        
        # 1. 初始化并登录
        print("\n1. 初始化浏览器并登录...")
        login_manager.init_browser()
        print("✅ 浏览器初始化成功")
        
        # 执行登录
        login_success = login_manager.login()
        if not login_success:
            print("❌ 登录失败，无法继续测试")
            return
        
        print("✅ 登录成功")
        
        # 2. 初始化课程解析器
        print("\n2. 初始化课程解析器...")
        course_parser = CourseParser(login_manager.page)
        print("✅ 课程解析器初始化成功")
        
        # 3. 测试导航到必修课页面
        print(f"\n3. 导航到必修课页面: {Config.REQUIRED_COURSES_URL}")
        try:
            login_manager.page.goto(Config.REQUIRED_COURSES_URL)
            time.sleep(3)  # 等待页面加载
            
            current_url = login_manager.page.url
            print(f"✅ 当前页面URL: {current_url}")
            
            # 检查页面标题
            title = login_manager.page.title()
            print(f"   页面标题: {title}")
            
        except Exception as e:
            print(f"❌ 导航到必修课页面失败: {str(e)}")
            return
        
        # 4. 分析页面结构
        print("\n4. 分析页面结构...")
        page_info = login_manager.page.evaluate("""
            () => {
                const result = {
                    title: document.title,
                    url: window.location.href,
                    courseElements: [],
                    tables: [],
                    buttons: [],
                    links: []
                };
                
                // 查找可能的课程元素
                const courseSelectors = [
                    '.course-item',
                    '.course-card',
                    '.course-list',
                    '[class*="course"]',
                    '.el-table',
                    'tbody tr',
                    '.required-course',
                    '.study-item'
                ];
                
                courseSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        result.courseElements.push({
                            selector: selector,
                            count: elements.length,
                            sample: elements[0] ? elements[0].textContent.substring(0, 100) : ''
                        });
                    }
                });
                
                // 查找表格
                const tables = document.querySelectorAll('table');
                tables.forEach((table, index) => {
                    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
                    const rows = table.querySelectorAll('tbody tr').length;
                    result.tables.push({
                        index: index,
                        headers: headers,
                        rowCount: rows
                    });
                });
                
                // 查找按钮
                const buttons = document.querySelectorAll('button, .btn, [class*="button"]');
                buttons.forEach(btn => {
                    if (btn.textContent.trim()) {
                        result.buttons.push(btn.textContent.trim());
                    }
                });
                
                // 查找链接
                const links = document.querySelectorAll('a[href]');
                links.forEach(link => {
                    const text = link.textContent.trim();
                    const href = link.href;
                    if (text && href && text.length < 50) {
                        result.links.push({ text: text, href: href });
                    }
                });
                
                return result;
            }
        """)
        
        print(f"   页面标题: {page_info['title']}")
        print(f"   当前URL: {page_info['url']}")
        print(f"\n   发现的可能课程元素:")
        for element in page_info['courseElements']:
            print(f"     - {element['selector']}: {element['count']}个元素")
            if element['sample']:
                print(f"       示例内容: {element['sample'][:50]}...")
        
        print(f"\n   发现的表格:")
        for table in page_info['tables']:
            print(f"     - 表格 {table['index']}: {table['rowCount']}行")
            print(f"       表头: {table['headers']}")
        
        print(f"\n   发现的按钮:")
        for i, btn in enumerate(page_info['buttons'][:10]):  # 只显示前10个
            print(f"     - {btn}")
        
        print(f"\n   发现的链接:")
        for i, link in enumerate(page_info['links'][:10]):  # 只显示前10个
            print(f"     - {link['text']} -> {link['href']}")
        
        # 5. 尝试使用当前的课程获取逻辑
        print("\n5. 测试当前的课程获取逻辑...")
        try:
            courses = course_parser.parse_required_courses()
            print(f"✅ 获取到 {len(courses)} 门必修课程")
            
            if courses:
                print("\n   课程列表:")
                for i, course in enumerate(courses[:5]):  # 显示前5门课程
                    print(f"     {i+1}. {course}")
            else:
                print("❌ 未获取到任何课程")
                
        except Exception as e:
            print(f"❌ 课程获取失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 6. 手动尝试不同的选择器
        print("\n6. 手动测试不同的课程选择器...")
        test_selectors = [
            'tr',
            'tbody tr',
            '.el-table__row',
            '.course-item',
            '.study-item',
            'a[href*="study"]',
            'a[href*="course"]',
            'a[href*="learn"]',
            '[class*="course"]',
            '[class*="study"]'
        ]
        
        for selector in test_selectors:
            try:
                elements = login_manager.page.locator(selector)
                count = elements.count()
                if count > 0:
                    first_text = elements.first.text_content() if count > 0 else ""
                    print(f"   {selector}: {count}个元素")
                    if first_text:
                        print(f"     第一个元素内容: {first_text[:100]}...")
            except Exception as e:
                print(f"   {selector}: 查询失败 - {str(e)}")
        
        # 7. 保存页面截图和HTML
        print("\n7. 保存调试信息...")
        try:
            # 截图
            login_manager.page.screenshot(path="debug_required_courses.png")
            print("✅ 页面截图保存为: debug_required_courses.png")
            
            # 保存HTML
            html_content = login_manager.page.content()
            with open("debug_required_courses.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("✅ 页面HTML保存为: debug_required_courses.html")
            
        except Exception as e:
            print(f"❌ 保存调试信息失败: {str(e)}")
        
        # 8. 等待用户观察
        print("\n8. 浏览器将保持打开30秒，你可以手动查看页面...")
        time.sleep(30)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        if login_manager and hasattr(login_manager, 'browser') and login_manager.browser:
            login_manager.close_browser()
            print("\n浏览器已关闭")

if __name__ == "__main__":
    test_course_fetch()