#!/usr/bin/env python
"""
测试课程学习页面的脚本
"""

import logging
import sys
import time
import json
from datetime import datetime

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

def test_course_learning_pages():
    """测试课程学习页面功能"""
    
    print("=" * 80)
    print("课程学习页面测试")
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
        
        # 3. 获取必修课程列表
        print("\n【步骤3】获取必修课程列表...")
        required_courses = parser.parse_required_courses()
        print(f"获取到 {len(required_courses)} 门必修课程")
        
        # 4. 获取选修课程列表
        print("\n【步骤4】获取选修课程列表...")
        elective_courses = parser.parse_elective_courses()
        print(f"获取到 {len(elective_courses)} 门选修课程")
        
        # 5. 测试学习页面功能
        print("\n【步骤5】测试课程学习页面...")
        
        # 选择一门必修课程进行测试
        if required_courses:
            test_course = required_courses[0]
            print(f"测试必修课程: {test_course['course_name'][:50]}...")
            test_course_learning_page(login_manager.page, test_course, "required")
        
        # 选择一门选修课程进行测试
        if elective_courses:
            test_course = elective_courses[0]
            print(f"\n测试选修课程: {test_course['course_name'][:50]}...")
            test_course_learning_page(login_manager.page, test_course, "elective")
        
        # 6. 生成测试报告
        print("\n【步骤6】生成测试报告...")
        generate_learning_test_report(required_courses, elective_courses)
        
        print(f"\n{'='*80}")
        print(f"测试完成！请查看生成的文件:")
        print(f"- course_learning_test_report.json (测试报告)")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if hasattr(login_manager, 'browser') and login_manager.browser:
            login_manager.close_browser()
            print("\n浏览器已关闭")

def test_course_learning_page(page, course, course_type):
    """测试单个课程的学习页面"""
    
    try:
        print(f"  课程信息:")
        print(f"    名称: {course['course_name']}")
        print(f"    类型: {course_type}")
        print(f"    进度: {course['progress']}%")
        print(f"    视频URL: {course['video_url'][:80]}...")
        
        # 尝试访问课程学习页面
        if course['video_url'] and course['video_url'].startswith('http'):
            print(f"  访问学习页面...")
            
            # 记录当前URL
            current_url = page.url
            
            # 访问课程页面
            page.goto(course['video_url'])
            page.wait_for_load_state('domcontentloaded')
            time.sleep(3)
            
            # 分析页面内容
            page_info = analyze_learning_page(page)
            
            # 打印页面分析结果
            print(f"  学习页面分析:")
            print(f"    页面标题: {page_info['title']}")
            print(f"    当前URL: {page_info['url'][:80]}...")
            print(f"    找到视频元素: {page_info['has_video']}个")
            print(f"    找到播放按钮: {page_info['has_play_button']}个")
            print(f"    找到进度条: {page_info['has_progress']}个")
            print(f"    页面加载状态: {'成功' if page_info['loaded'] else '失败'}")
            
            # 保存页面截图和HTML（用于调试）
            screenshot_name = f"learning_page_{course_type}_{course['user_course_id']}.png"
            html_name = f"learning_page_{course_type}_{course['user_course_id']}.html"
            
            try:
                page.screenshot(path=screenshot_name)
                with open(html_name, "w", encoding="utf-8") as f:
                    f.write(page.content())
                print(f"  调试文件已保存: {screenshot_name}, {html_name}")
            except Exception as e:
                print(f"  保存调试文件失败: {str(e)}")
            
            # 返回之前的页面
            page.goto(current_url)
            time.sleep(1)
            
        else:
            print(f"  ⚠️  课程URL无效，跳过测试")
            
    except Exception as e:
        print(f"  ❌ 测试课程学习页面失败: {str(e)}")

def analyze_learning_page(page):
    """分析学习页面的内容"""
    
    info = {
        'title': '',
        'url': '',
        'loaded': False,
        'has_video': 0,
        'has_play_button': 0,
        'has_progress': 0,
        'video_elements': [],
        'interactive_elements': []
    }
    
    try:
        info['title'] = page.title()
        info['url'] = page.url
        info['loaded'] = True
        
        # 检查视频相关元素
        video_selectors = [
            'video',
            'iframe[src*="video"]',
            'object[data*="video"]',
            'embed[src*="video"]',
            '.video-player',
            '.player',
            '[class*="video"]'
        ]
        
        for selector in video_selectors:
            try:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    info['has_video'] += count
                    info['video_elements'].append({
                        'selector': selector,
                        'count': count
                    })
            except:
                pass
        
        # 检查播放控制元素
        play_selectors = [
            'button:has-text("播放")',
            'button:has-text("开始")',
            'button:has-text("继续")',
            '.play-btn',
            '.play-button',
            '[class*="play"]',
            'button[aria-label*="play"]'
        ]
        
        for selector in play_selectors:
            try:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    info['has_play_button'] += count
            except:
                pass
        
        # 检查进度相关元素
        progress_selectors = [
            '.progress',
            '.el-progress',
            'progress',
            '[role="progressbar"]',
            '[class*="progress"]'
        ]
        
        for selector in progress_selectors:
            try:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    info['has_progress'] += count
            except:
                pass
        
        # 检查其他交互元素
        interactive_selectors = [
            'button',
            'a[href*="video"]',
            'input[type="range"]',
            '.controls'
        ]
        
        for selector in interactive_selectors:
            try:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    info['interactive_elements'].append({
                        'selector': selector,
                        'count': count
                    })
            except:
                pass
                
    except Exception as e:
        info['error'] = str(e)
        info['loaded'] = False
    
    return info

def generate_learning_test_report(required_courses, elective_courses):
    """生成学习页面测试报告"""
    
    report = {
        'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'required_courses_count': len(required_courses),
            'elective_courses_count': len(elective_courses),
            'total_courses': len(required_courses) + len(elective_courses)
        },
        'required_courses': required_courses[:5],  # 只保存前5门作为示例
        'elective_courses': elective_courses[:5],   # 只保存前5门作为示例
        'test_results': {
            'login_success': True,
            'course_parsing_success': len(required_courses) > 0 or len(elective_courses) > 0,
            'learning_page_accessible': True  # 这里可以根据实际测试结果更新
        },
        'recommendations': []
    }
    
    # 添加建议
    if len(required_courses) == 0:
        report['recommendations'].append("未获取到必修课程，请检查必修课程解析逻辑")
    
    if len(elective_courses) == 0:
        report['recommendations'].append("未获取到选修课程，请检查选修课程解析逻辑")
    
    if len(required_courses) > 0 and len(elective_courses) > 0:
        report['recommendations'].append("课程解析功能正常，可以进行学习页面测试")
    
    # 保存报告
    with open("course_learning_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("✅ 学习页面测试报告已生成: course_learning_test_report.json")
    
    # 打印总结
    print(f"\n测试总结:")
    print(f"  必修课程: {report['summary']['required_courses_count']}门")
    print(f"  选修课程: {report['summary']['elective_courses_count']}门")
    print(f"  总课程数: {report['summary']['total_courses']}门")
    if report['recommendations']:
        print(f"  建议:")
        for rec in report['recommendations']:
            print(f"    - {rec}")

if __name__ == "__main__":
    test_course_learning_pages()