#!/usr/bin/env python3
"""
检查数据库中现有的视频URL
"""

import sys
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_video_urls():
    """检查数据库中的视频URL"""
    db_path = 'data/courses.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询所有课程的URL
        cursor.execute("""
            SELECT course_name, course_type, video_url, user_course_id 
            FROM courses 
            WHERE video_url IS NOT NULL AND video_url != ''
            ORDER BY course_type, course_name
        """)
        
        courses = cursor.fetchall()
        
        print("数据库中的视频URL分析:")
        print("=" * 80)
        
        if not courses:
            print("❌ 数据库中没有视频URL数据")
            return
        
        required_urls = []
        elective_urls = []
        problem_urls = []
        
        for course_name, course_type, video_url, user_course_id in courses:
            url_info = {
                'name': course_name,
                'type': course_type,
                'url': video_url,
                'user_course_id': user_course_id
            }
            
            # 检查URL问题
            issues = []
            if '##' in video_url:
                issues.append("包含双#")
            if '#/course_study?' in video_url:
                issues.append("错误格式course_study")
            if not user_course_id:
                issues.append("缺少user_course_id")
            
            if issues:
                url_info['issues'] = issues
                problem_urls.append(url_info)
            
            if course_type == 'required':
                required_urls.append(url_info)
            else:
                elective_urls.append(url_info)
        
        print(f"总课程数量: {len(courses)}")
        print(f"必修课数量: {len(required_urls)}")
        print(f"选修课数量: {len(elective_urls)}")
        print(f"问题URL数量: {len(problem_urls)}")
        
        if problem_urls:
            print(f"\n发现的URL问题:")
            print("-" * 60)
            for i, url_info in enumerate(problem_urls, 1):
                print(f"{i}. 课程: {url_info['name']} ({url_info['type']})")
                print(f"   URL: {url_info['url']}")
                print(f"   问题: {', '.join(url_info['issues'])}")
                print()
        
        # 显示几个正确的URL示例
        good_required = [u for u in required_urls if u not in problem_urls][:3]
        good_elective = [u for u in elective_urls if u not in problem_urls][:3]
        
        if good_required:
            print(f"\n必修课URL示例:")
            print("-" * 40)
            for url_info in good_required:
                print(f"课程: {url_info['name']}")
                print(f"URL: {url_info['url']}")
                print()
        
        if good_elective:
            print(f"\n选修课URL示例:")
            print("-" * 40)
            for url_info in good_elective:
                print(f"课程: {url_info['name']}")
                print(f"URL: {url_info['url']}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {str(e)}")

if __name__ == "__main__":
    check_video_urls()