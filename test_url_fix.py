#!/usr/bin/env python3
"""
测试URL修复效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.enhanced_course_parser import EnhancedCourseParser

def test_url_construction():
    """测试URL构建逻辑"""
    print("测试URL构建修复")
    print("=" * 50)
    
    # 创建一个模拟的parser实例（不需要实际page）
    parser = EnhancedCourseParser(None)
    
    # 测试必修课URL构建
    print("1. 测试必修课URL构建（无ID情况）:")
    test_course_name = "中国特色社会主义理论体系文献导读（上）"
    empty_button_data = {}
    
    video_url, user_course_id, course_id = parser._build_required_course_url(
        test_course_name, empty_button_data
    )
    
    print(f"   课程名: {test_course_name}")
    print(f"   生成URL: {video_url}")
    print(f"   user_course_id: {user_course_id}")
    print(f"   course_id: {course_id}")
    
    # 检查URL格式
    if "#/video_page?" in video_url:
        print("   ✅ URL格式正确 (使用video_page)")
    else:
        print("   ❌ URL格式错误")
    
    if "user_course_id=" in video_url:
        print("   ✅ 包含user_course_id参数")
    else:
        print("   ❌ 缺少user_course_id参数")
    
    if "#/course_study?" in video_url:
        print("   ❌ 仍然使用错误的course_study格式")
    else:
        print("   ✅ 不再使用错误的course_study格式")
    
    # 测试有ID的情况
    print("\n2. 测试必修课URL构建（有ID情况）:")
    button_data_with_id = {
        'data-user-course-id': '1988340',
        'data-course-id': '10598'
    }
    
    video_url2, user_course_id2, course_id2 = parser._build_required_course_url(
        test_course_name, button_data_with_id
    )
    
    print(f"   课程名: {test_course_name}")
    print(f"   生成URL: {video_url2}")
    print(f"   user_course_id: {user_course_id2}")
    print(f"   course_id: {course_id2}")
    
    # 测试选修课URL构建
    print("\n3. 测试选修课URL构建:")
    elective_course_name = "2025年《政府工作报告》学习解读（上）"
    empty_play_data = {'elements': []}
    
    video_url3, user_course_id3, course_id3 = parser._build_elective_course_url(
        elective_course_name, empty_play_data
    )
    
    print(f"   课程名: {elective_course_name}")
    print(f"   生成URL: {video_url3}")
    print(f"   user_course_id: {user_course_id3}")
    print(f"   course_id: {course_id3}")
    
    print(f"\n修复效果总结:")
    print("=" * 30)
    
    fixes_working = True
    
    # 检查必修课修复
    if "#/video_page?" in video_url and "user_course_id=" in video_url:
        print("✅ 必修课URL格式已修复")
    else:
        print("❌ 必修课URL格式仍有问题")
        fixes_working = False
    
    if "#/course_study?" not in video_url:
        print("✅ 不再使用错误的course_study格式")
    else:
        print("❌ 仍然使用错误的course_study格式")
        fixes_working = False
    
    if fixes_working:
        print(f"\n🎉 URL修复成功！所有必修课现在都将使用正确的video_page格式")
    else:
        print(f"\n⚠️  URL修复可能不完整，需要进一步检查")

if __name__ == "__main__":
    test_url_construction()