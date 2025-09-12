#!/usr/bin/env python
"""
离线测试选修课解析逻辑
"""

import sys
import re
import hashlib
import time
from pathlib import Path

# 添加src目录到系统路径
sys.path.insert(0, 'src')

from playwright.sync_api import sync_playwright
from config.config import Config

def test_elective_parsing_offline():
    """使用保存的HTML文件测试选修课解析逻辑"""
    
    print("=" * 80)
    print("选修课离线解析测试")
    print("=" * 80)
    
    html_file = "elective_course_debug.html"
    if not Path(html_file).exists():
        print(f"❌ HTML文件 {html_file} 不存在")
        return
    
    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 加载HTML文件
            html_path = Path(html_file).absolute().as_uri()
            page.goto(html_path)
            time.sleep(2)
            
            print(f"✅ 成功加载HTML文件")
            
            # 测试解析逻辑
            courses = parse_elective_courses_from_page(page)
            
            print(f"\n解析结果:")
            print(f"  获取到课程数量: {len(courses)}")
            
            if courses:
                print(f"\n课程详情:")
                for i, course in enumerate(courses, 1):
                    print(f"  课程 {i}:")
                    print(f"    名称: {course['course_name'][:50]}...")
                    print(f"    进度: {course['progress']}%")
                    print(f"    ID: {course['user_course_id']}")
                    print()
            else:
                print("  ❌ 未解析到任何课程")
                # 调试信息
                debug_page_structure(page)
            
            browser.close()
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def parse_elective_courses_from_page(page):
    """从页面解析选修课程"""
    courses = []
    
    try:
        # 等待页面加载
        page.wait_for_selector('body', timeout=5000)
        
        # 策略1：解析表格中的选修课程
        table_rows = page.locator('tbody tr').all()
        print(f"找到 {len(table_rows)} 个表格行")
        
        for row in table_rows:
            try:
                # 获取课程名称（第一列，td.td_title）
                title_cell = row.locator('td.td_title').first
                if title_cell.count() == 0:
                    continue
                
                course_name = title_cell.inner_text().strip()
                if not course_name or len(course_name) < 3:
                    continue
                
                # 获取学习进度（第二列中的百分比）
                progress = 0.0
                progress_element = row.locator('.el-progress__text').first
                if progress_element.count() > 0:
                    progress_text = progress_element.inner_text().strip()
                    progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                    if progress_match:
                        progress = float(progress_match.group(1))
                
                # 检查播放按钮是否存在（表示可以学习）
                play_button = row.locator('td:has-text("播放")').first
                has_play_button = play_button.count() > 0
                
                # 构造一个临时的视频URL
                video_url = f"{Config.BASE_URL}#/elective_course_play?name={course_name}"
                
                # 生成一个基于课程名称的临时ID
                user_course_id = hashlib.md5(course_name.encode('utf-8')).hexdigest()[:8]
                
                course_info = {
                    'course_name': course_name,
                    'course_type': 'elective',
                    'progress': progress,
                    'video_url': video_url,
                    'user_course_id': user_course_id
                }
                
                courses.append(course_info)
                print(f"解析课程: {course_name[:30]}... (进度: {progress}%, 播放: {'是' if has_play_button else '否'})")
                
            except Exception as e:
                print(f"解析表格行时出错: {str(e)}")
                continue
                
    except Exception as e:
        print(f"解析课程失败: {str(e)}")
    
    return courses

def debug_page_structure(page):
    """调试页面结构"""
    print("\n调试信息:")
    
    # 检查基本元素
    tbody_count = page.locator('tbody').count()
    tr_count = page.locator('tbody tr').count()
    td_title_count = page.locator('td.td_title').count()
    progress_count = page.locator('.el-progress__text').count()
    play_count = page.locator('td:has-text("播放")').count()
    
    print(f"  tbody 元素: {tbody_count} 个")
    print(f"  tbody tr 元素: {tr_count} 个")
    print(f"  td.td_title 元素: {td_title_count} 个")
    print(f"  .el-progress__text 元素: {progress_count} 个")
    print(f"  包含'播放'的td 元素: {play_count} 个")
    
    # 打印第一行的内容作为示例
    if tr_count > 0:
        first_row = page.locator('tbody tr').first
        print(f"\n第一行内容示例:")
        try:
            first_title = first_row.locator('td.td_title').first
            if first_title.count() > 0:
                print(f"  课程名称: {first_title.inner_text()[:50]}...")
            
            first_progress = first_row.locator('.el-progress__text').first
            if first_progress.count() > 0:
                print(f"  进度文本: {first_progress.inner_text()}")
                
            first_play = first_row.locator('td:has-text("播放")').first
            print(f"  有播放按钮: {first_play.count() > 0}")
                
        except Exception as e:
            print(f"  获取示例失败: {str(e)}")

if __name__ == "__main__":
    test_elective_parsing_offline()