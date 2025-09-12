#!/usr/bin/env python
"""
测试选修课页面解析结果的脚本
"""

import logging
import sys
import time
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 添加src目录到系统路径
sys.path.insert(0, 'src')

from playwright.sync_api import sync_playwright
from course_parser import CourseParser
from login import LoginManager
from config.config import Config

def test_elective_course_parsing():
    """测试选修课页面解析功能"""
    
    print("=" * 80)
    print("选修课页面解析测试")
    print("=" * 80)
    
    login_manager = LoginManager()
    
    try:
        # 1. 初始化和登录
        print("\n【步骤1】初始化浏览器并登录...")
        login_manager.init_browser()
        
        login_success = login_manager.login()
        if not login_success:
            print("❌ 登录失败，无法进行测试")
            return
        
        print("✅ 登录成功")
        
        # 2. 初始化课程解析器
        print("\n【步骤2】初始化课程解析器...")
        parser = CourseParser(login_manager.page)
        
        # 3. 测试选修课页面访问
        print(f"\n【步骤3】访问选修课页面...")
        print(f"URL: {Config.ELECTIVE_COURSES_URL}")
        
        login_manager.page.goto(Config.ELECTIVE_COURSES_URL)
        login_manager.page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        current_url = login_manager.page.url
        page_title = login_manager.page.title()
        
        print(f"✅ 页面访问成功")
        print(f"   当前URL: {current_url}")
        print(f"   页面标题: {page_title}")
        
        # 4. 分析页面结构
        print(f"\n【步骤4】分析页面结构...")
        page_analysis = analyze_page_structure(login_manager.page)
        print_page_analysis(page_analysis)
        
        # 5. 测试当前解析逻辑
        print(f"\n【步骤5】测试当前的选修课解析逻辑...")
        courses = parser.parse_elective_courses()
        
        print(f"解析结果概览:")
        print(f"  获取到课程数量: {len(courses)}")
        
        if courses:
            print(f"\n解析到的课程详情:")
            for i, course in enumerate(courses, 1):
                print(f"  课程 {i}:")
                print(f"    名称: {course['course_name']}")
                print(f"    类型: {course['course_type']}")
                print(f"    ID: {course['user_course_id']}")
                print(f"    链接: {course['video_url'][:80]}...")
                print(f"    进度: {course['progress']}%")
                print()
        else:
            print("  ❌ 未解析到任何课程")
        
        # 6. 测试不同的解析策略
        print(f"\n【步骤6】测试其他可能的解析策略...")
        test_alternative_parsing(login_manager.page)
        
        # 7. 保存调试信息
        print(f"\n【步骤7】保存调试信息...")
        save_debug_info(login_manager.page, courses)
        
        # 8. 生成测试报告
        print(f"\n【步骤8】生成测试报告...")
        generate_test_report(page_analysis, courses)
        
        print(f"\n{'='*80}")
        print(f"测试完成！请查看生成的文件:")
        print(f"- elective_course_debug.png (页面截图)")
        print(f"- elective_course_debug.html (页面HTML)")
        print(f"- elective_course_test_report.json (测试报告)")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if hasattr(login_manager, 'browser') and login_manager.browser:
            login_manager.close_browser()
            print("\n浏览器已关闭")

def analyze_page_structure(page):
    """分析页面结构"""
    
    analysis = {
        'basic_info': {
            'url': page.url,
            'title': page.title()
        },
        'course_elements': {},
        'buttons': [],
        'links': [],
        'navigation': []
    }
    
    # 查找课程相关元素
    course_selectors = [
        'a[href*="course_detail"]',
        'a[href*="video_page"]',
        'button:has-text("继续学习")',
        'button:has-text("开始学习")',
        'div.btn:has-text("继续学习")',
        'div.btn:has-text("开始学习")',
        '.course-item',
        '.course-card',
        '[class*="course"]'
    ]
    
    for selector in course_selectors:
        try:
            elements = page.locator(selector)
            count = elements.count()
            if count > 0:
                analysis['course_elements'][selector] = {
                    'count': count,
                    'sample_text': elements.first.inner_text()[:100] if count > 0 else ''
                }
        except:
            analysis['course_elements'][selector] = {'count': 0, 'error': True}
    
    # 查找导航元素
    nav_selectors = [
        'text=选课中心',
        'text=我的学习', 
        'text=本年选修',
        'text=选修课'
    ]
    
    for selector in nav_selectors:
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                analysis['navigation'].append({
                    'text': selector,
                    'visible': element.is_visible(),
                    'enabled': element.is_enabled()
                })
        except:
            pass
    
    return analysis

def print_page_analysis(analysis):
    """打印页面分析结果"""
    
    print(f"页面基本信息:")
    print(f"  URL: {analysis['basic_info']['url']}")
    print(f"  标题: {analysis['basic_info']['title']}")
    
    print(f"\n课程相关元素:")
    for selector, info in analysis['course_elements'].items():
        if info['count'] > 0:
            print(f"  {selector}: {info['count']}个")
            if info.get('sample_text'):
                print(f"    示例: {info['sample_text'][:50]}...")
    
    print(f"\n导航元素:")
    for nav in analysis['navigation']:
        status = "可见" if nav['visible'] else "隐藏"
        print(f"  {nav['text']}: {status}")

def test_alternative_parsing(page):
    """测试其他可能的解析策略"""
    
    print("测试替代解析策略:")
    
    # 策略1：查找"本年选修"链接
    print("\n策略1: 查找'本年选修'导航")
    try:
        elective_selectors = [
            'text=本年选修',
            'a:has-text("本年选修")',
            'li:has-text("本年选修")',
            '[href*="elective"]'
        ]
        
        for selector in elective_selectors:
            elements = page.locator(selector)
            if elements.count() > 0:
                print(f"  找到: {selector} ({elements.count()}个)")
                print(f"    第一个元素: {elements.first.inner_text()[:30]}")
                break
        else:
            print("  ❌ 未找到'本年选修'导航")
    except Exception as e:
        print(f"  ❌ 策略1失败: {str(e)}")
    
    # 策略2：查找学习进度相关元素
    print("\n策略2: 查找学习进度元素")
    try:
        progress_selectors = [
            '[class*="progress"]',
            'text=/%/',
            'text=/\\d+%/',
            'span:has-text("%")'
        ]
        
        progress_found = False
        for selector in progress_selectors:
            elements = page.locator(selector)
            count = elements.count()
            if count > 0:
                print(f"  找到进度元素: {selector} ({count}个)")
                progress_found = True
        
        if not progress_found:
            print("  ❌ 未找到学习进度元素")
    except Exception as e:
        print(f"  ❌ 策略2失败: {str(e)}")
    
    # 策略3：查找学习状态相关文本
    print("\n策略3: 查找学习状态文本")
    try:
        status_texts = [
            '未开始',
            '学习中',
            '已完成',
            '继续学习',
            '开始学习'
        ]
        
        for text in status_texts:
            elements = page.locator(f'text={text}')
            count = elements.count()
            if count > 0:
                print(f"  找到状态文本: '{text}' ({count}个)")
    except Exception as e:
        print(f"  ❌ 策略3失败: {str(e)}")
    
    # 策略4：查找课程列表容器
    print("\n策略4: 查找课程列表容器")
    try:
        list_selectors = [
            'ul.gj_top_list_box',
            '.course-list',
            '.el-table',
            'tbody',
            '[class*="list"]'
        ]
        
        for selector in list_selectors:
            elements = page.locator(selector)
            count = elements.count()
            if count > 0:
                print(f"  找到列表容器: {selector} ({count}个)")
                # 查找子元素
                children = elements.first.locator('li, tr, .course-item, [class*="course"]')
                child_count = children.count()
                if child_count > 0:
                    print(f"    包含 {child_count} 个子元素")
    except Exception as e:
        print(f"  ❌ 策略4失败: {str(e)}")

def save_debug_info(page, courses):
    """保存调试信息"""
    
    try:
        # 保存截图
        page.screenshot(path="elective_course_debug.png")
        print("✅ 截图已保存: elective_course_debug.png")
        
        # 保存HTML
        html_content = page.content()
        with open("elective_course_debug.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ HTML已保存: elective_course_debug.html")
        
        # 保存解析结果
        with open("elective_course_parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print("✅ 解析数据已保存: elective_course_parsed_data.json")
        
    except Exception as e:
        print(f"❌ 保存调试信息失败: {str(e)}")

def generate_test_report(page_analysis, courses):
    """生成测试报告"""
    
    report = {
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'page_info': page_analysis['basic_info'],
        'parsing_results': {
            'course_count': len(courses),
            'courses': courses
        },
        'page_elements': page_analysis['course_elements'],
        'navigation': page_analysis['navigation'],
        'issues_found': []
    }
    
    # 检查问题
    if len(courses) == 0:
        report['issues_found'].append("未解析到任何课程")
    
    if not any(nav['visible'] for nav in page_analysis['navigation'] if '本年选修' in nav['text']):
        report['issues_found'].append("未找到'本年选修'导航")
    
    if page_analysis['basic_info']['url'].find('my_elective') == -1:
        report['issues_found'].append("当前页面URL不包含'my_elective'，可能不是选修课页面")
    
    # 保存报告
    with open("elective_course_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("✅ 测试报告已生成: elective_course_test_report.json")
    
    # 打印总结
    print(f"\n测试总结:")
    print(f"  解析到课程: {report['parsing_results']['course_count']}门")
    print(f"  发现问题: {len(report['issues_found'])}个")
    if report['issues_found']:
        for issue in report['issues_found']:
            print(f"    - {issue}")

if __name__ == "__main__":
    test_elective_course_parsing()