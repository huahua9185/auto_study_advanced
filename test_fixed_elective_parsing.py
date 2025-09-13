#!/usr/bin/env python3
"""
测试修复后的选修课解析器，验证真实数字ID生成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from src.enhanced_course_parser import EnhancedCourseParser
from src.login import LoginManager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_fixed_elective_parsing():
    """测试修复后的选修课解析器"""
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()

        try:
            # 登录
            login_manager = LoginManager()
            login_manager.browser = browser
            login_manager.page = page
            if not login_manager.login():
                print("登录失败，无法进行测试")
                return

            print("登录成功，开始测试修复后的选修课解析器...")

            # 创建增强课程解析器
            parser = EnhancedCourseParser(page)

            # 解析选修课程
            elective_courses = parser.parse_elective_courses_enhanced()
            print(f"\n成功解析到 {len(elective_courses)} 门选修课程")

            if elective_courses:
                print("\n前3门课程的详细信息:")
                for i, course in enumerate(elective_courses[:3]):
                    course_name = course['course_name']
                    video_url = course['video_url']
                    user_course_id = course['user_course_id']
                    course_id = course['id']

                    print(f"\n=== 课程 {i+1} ===")
                    print(f"课程名称: {course_name}")
                    print(f"User Course ID: {user_course_id}")
                    print(f"Course ID: {course_id}")
                    print(f"完整URL: {video_url}")

                    # 验证ID格式
                    try:
                        # 检查是否为数字ID
                        user_course_id_int = int(user_course_id)
                        course_id_int = int(course_id)
                        print(f"✅ ID格式正确 - 都是数字")

                        # 验证URL格式
                        if 'video_page' in video_url and f'id={course_id}' in video_url and f'user_course_id={user_course_id}' in video_url and 'name=%E5%AD%A6%E4%B9%A0%E4%B8%AD%E5%BF%83' in video_url:
                            print(f"✅ URL格式正确")
                        else:
                            print(f"❌ URL格式错误")

                    except ValueError:
                        print(f"❌ ID格式错误 - 包含非数字字符")

                    print("-" * 60)

                # 检查是否有使用API获取的课程（真实数字ID）
                api_courses = []
                fallback_courses = []

                for course in elective_courses:
                    user_course_id = int(course['user_course_id'])
                    if user_course_id >= 2000000:  # 备用方案的ID范围
                        fallback_courses.append(course)
                    else:
                        api_courses.append(course)

                print(f"\n=== 数据源分析 ===")
                print(f"API获取的课程: {len(api_courses)} 门")
                print(f"备用方案课程: {len(fallback_courses)} 门")

                if api_courses:
                    print("✅ 成功使用API获取真实数字ID")
                    sample_api_course = api_courses[0]
                    print(f"示例API课程URL: {sample_api_course['video_url']}")
                else:
                    print("⚠️  使用了备用方案，未能通过API获取真实ID")

            else:
                print("❌ 未能获取到任何选修课程")

            print("\n测试完成！")

        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    test_fixed_elective_parsing()