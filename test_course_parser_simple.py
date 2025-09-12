#!/usr/bin/env python
"""
简化的课程解析器测试 - 使用已有的HTML文件测试
"""

import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加src目录到系统路径
sys.path.insert(0, 'src')

from playwright.sync_api import sync_playwright
from course_parser import CourseParser

def test_course_parser_with_local_html():
    """使用本地HTML文件测试课程解析器"""
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("加载本地HTML文件...")
            # 加载之前保存的调试HTML文件
            import os
            html_path = os.path.abspath("debug_required_courses.html")
            page.goto(f"file://{html_path}")
            
            print("初始化课程解析器...")
            parser = CourseParser(page)
            
            print("测试课程详情链接查找...")
            # 直接测试新的选择器
            course_links = page.locator('a[href*="course_detail"]').all()
            print(f"找到 {len(course_links)} 个课程详情链接")
            
            if course_links:
                print("\n前5个课程链接:")
                for i, link in enumerate(course_links[:5]):
                    href = link.get_attribute('href')
                    text = link.inner_text().strip()
                    print(f"  {i+1}. {text} -> {href}")
            
            print("\n测试完整的解析逻辑...")
            # 模拟parse_required_courses的核心逻辑
            courses = []
            processed_course_ids = set()
            
            for link in course_links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().strip()
                    
                    if not href or not text or text == '加载中...':
                        continue
                    
                    # 提取course_id避免重复
                    import re
                    course_id_match = re.search(r'id=(\d+)', href)
                    if course_id_match:
                        course_id = course_id_match.group(1)
                        if course_id in processed_course_ids:
                            continue
                        processed_course_ids.add(course_id)
                    
                    # 处理相对URL
                    from config.config import Config
                    if href.startswith('#/'):
                        full_url = Config.BASE_URL.rstrip('#/') + href
                    else:
                        full_url = href
                    
                    course_info = {
                        'course_name': text,
                        'course_type': 'required',
                        'progress': 0.0,
                        'video_url': full_url,
                        'user_course_id': course_id if course_id_match else ''
                    }
                    
                    courses.append(course_info)
                    print(f"  添加课程: {text[:50]}{'...' if len(text) > 50 else ''}")
                    
                except Exception as e:
                    print(f"  解析链接时出错: {str(e)}")
                    continue
            
            print(f"\n解析完成！共获取到 {len(courses)} 门课程")
            
            if courses:
                print("\n课程详情:")
                for i, course in enumerate(courses[:3]):  # 显示前3门课程
                    print(f"  {i+1}. 课程名: {course['course_name']}")
                    print(f"     ID: {course['user_course_id']}")
                    print(f"     URL: {course['video_url']}")
                    print()
            
        except Exception as e:
            print(f"测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_course_parser_with_local_html()