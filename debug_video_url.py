#!/usr/bin/env python3
"""
专门测试视频URL构建是否正确的脚本
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager
from src.enhanced_course_parser import EnhancedCourseParser

class VideoURLTester:
    def __init__(self):
        self.test_results = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'required_courses': [],
            'elective_courses': [],
            'url_issues': [],
            'recommendations': []
        }
    
    def test_video_urls(self):
        """测试视频URL构建"""
        print("测试视频URL构建")
        print("=" * 60)
        
        try:
            # 初始化浏览器
            print("1. 初始化浏览器...")
            if not login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            page = login_manager.page
            
            # 登录
            print("2. 登录...")
            if not login_manager.login():
                print("❌ 登录失败")
                return False
            
            # 解析课程
            print("3. 解析课程...")
            parser = EnhancedCourseParser(page)
            courses = parser.parse_all_courses()
            
            # 分析必修课URL
            print("4. 分析必修课URL...")
            for course in courses['required'][:5]:  # 只分析前5门
                self.analyze_course_url(course, 'required')
                
            # 分析选修课URL
            print("5. 分析选修课URL...")
            for course in courses['elective'][:5]:  # 只分析前5门
                self.analyze_course_url(course, 'elective')
            
            # 生成报告
            self.generate_url_report()
            
            # 保存结果
            self.save_test_results()
            
            return True
            
        except Exception as e:
            print(f"❌ 测试过程中出现错误: {str(e)}")
            return False
            
        finally:
            if login_manager:
                login_manager.close_browser()
    
    def analyze_course_url(self, course, course_type):
        """分析课程URL"""
        print(f"   分析课程: {course['course_name']}")
        print(f"   URL: {course['video_url']}")
        
        url_analysis = {
            'course_name': course['course_name'],
            'course_type': course_type,
            'video_url': course['video_url'],
            'user_course_id': course.get('user_course_id', ''),
            'course_id': course.get('course_id', ''),
            'url_valid': True,
            'issues': []
        }
        
        # 检查URL格式
        if not course['video_url']:
            url_analysis['url_valid'] = False
            url_analysis['issues'].append("URL为空")
        elif '##' in course['video_url']:
            url_analysis['url_valid'] = False
            url_analysis['issues'].append("URL包含双#")
        elif '#/course_study?' in course['video_url']:
            url_analysis['url_valid'] = False
            url_analysis['issues'].append("使用了错误的course_study格式")
        elif not course.get('user_course_id'):
            url_analysis['url_valid'] = False
            url_analysis['issues'].append("缺少user_course_id参数")
        
        # 检查预期格式
        if course_type == 'required':
            # 必修课: #/video_page?id=10598&name=学员中心&user_course_id=1988340
            expected_pattern = '#/video_page?id='
            if expected_pattern not in course['video_url']:
                url_analysis['issues'].append(f"不符合必修课格式: {expected_pattern}")
        else:
            # 选修课: #/video_page?id=11362&user_course_id=1991630&name=学习中心
            expected_pattern = '#/video_page?id='
            if expected_pattern not in course['video_url']:
                url_analysis['issues'].append(f"不符合选修课格式: {expected_pattern}")
        
        if url_analysis['issues']:
            print(f"   ⚠️  URL问题: {', '.join(url_analysis['issues'])}")
            self.test_results['url_issues'].append(url_analysis)
        else:
            print(f"   ✅ URL格式正确")
        
        if course_type == 'required':
            self.test_results['required_courses'].append(url_analysis)
        else:
            self.test_results['elective_courses'].append(url_analysis)
    
    def generate_url_report(self):
        """生成URL分析报告"""
        print(f"\n视频URL分析报告:")
        print("=" * 40)
        
        # 统计
        total_required = len(self.test_results['required_courses'])
        total_elective = len(self.test_results['elective_courses'])
        total_issues = len(self.test_results['url_issues'])
        
        print(f"必修课分析数量: {total_required}")
        print(f"选修课分析数量: {total_elective}")
        print(f"发现问题数量: {total_issues}")
        
        # 问题汇总
        if self.test_results['url_issues']:
            print(f"\n发现的URL问题:")
            for i, issue in enumerate(self.test_results['url_issues'], 1):
                print(f"{i}. 课程: {issue['course_name']}")
                print(f"   类型: {issue['course_type']}")
                print(f"   URL: {issue['video_url']}")
                print(f"   问题: {', '.join(issue['issues'])}")
        
        # 生成建议
        recommendations = []
        
        if any('URL包含双#' in str(issue['issues']) for issue in self.test_results['url_issues']):
            recommendations.append("修复URL构建中的双#问题，确保BASE_URL正确处理")
        
        if any('使用了错误的course_study格式' in str(issue['issues']) for issue in self.test_results['url_issues']):
            recommendations.append("将course_study格式改为video_page格式")
        
        if any('缺少user_course_id参数' in str(issue['issues']) for issue in self.test_results['url_issues']):
            recommendations.append("改进ID提取逻辑，确保能正确提取user_course_id")
        
        self.test_results['recommendations'] = recommendations
        
        if recommendations:
            print(f"\n修复建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
    
    def save_test_results(self):
        """保存测试结果"""
        try:
            with open('video_url_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n测试结果已保存到: video_url_test_results.json")
        except Exception as e:
            print(f"❌ 保存测试结果失败: {str(e)}")

def main():
    """主函数"""
    tester = VideoURLTester()
    
    try:
        success = tester.test_video_urls()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 视频URL测试完成!")
            print("详细测试结果请查看: video_url_test_results.json")
            print("=" * 60)
            return 0
        else:
            print("\n❌ 视频URL测试失败!")
            return 1
            
    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)