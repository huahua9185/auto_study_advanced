#!/usr/bin/env python3
"""
测试增强版课程解析器，验证URL生成功能
"""

import sys
import os
import logging
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from config.config import Config
from src.login import login_manager
from src.enhanced_course_parser import EnhancedCourseParser

class EnhancedParserTester:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def test_enhanced_parser(self):
        """测试增强版课程解析器"""
        self.logger.info("开始测试增强版课程解析器")
        
        try:
            # 登录并获取课程数据
            if not login_manager.login():
                self.logger.error("登录失败")
                return False
            
            # 创建增强版解析器
            parser = EnhancedCourseParser(login_manager.page)
            
            # 解析所有课程
            self.logger.info("开始解析课程...")
            courses_data = parser.parse_all_courses()
            
            # 分析解析结果
            results = {
                'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': {
                    'required_courses_count': len(courses_data.get('required', [])),
                    'elective_courses_count': len(courses_data.get('elective', [])),
                    'total_courses': len(courses_data.get('required', [])) + len(courses_data.get('elective', []))
                },
                'url_format_analysis': {
                    'required_courses': [],
                    'elective_courses': []
                },
                'detailed_courses': courses_data
            }
            
            # 分析必修课URL格式
            self.logger.info("分析必修课URL格式...")
            for course in courses_data.get('required', []):
                url_analysis = self._analyze_url(course.get('video_url', ''), 'required')
                url_analysis['course_name'] = course.get('course_name', '')
                url_analysis['user_course_id'] = course.get('user_course_id', '')
                url_analysis['course_id'] = course.get('course_id', '')
                results['url_format_analysis']['required_courses'].append(url_analysis)
            
            # 分析选修课URL格式
            self.logger.info("分析选修课URL格式...")
            for course in courses_data.get('elective', []):
                url_analysis = self._analyze_url(course.get('video_url', ''), 'elective')
                url_analysis['course_name'] = course.get('course_name', '')
                url_analysis['user_course_id'] = course.get('user_course_id', '')
                url_analysis['course_id'] = course.get('course_id', '')
                results['url_format_analysis']['elective_courses'].append(url_analysis)
            
            # 保存测试结果
            with open('enhanced_parser_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 打印统计信息
            self.logger.info("="*60)
            self.logger.info("测试结果统计:")
            self.logger.info(f"必修课程数量: {results['summary']['required_courses_count']}")
            self.logger.info(f"选修课程数量: {results['summary']['elective_courses_count']}")
            self.logger.info(f"总课程数量: {results['summary']['total_courses']}")
            
            # 分析URL格式符合度
            self.logger.info("="*60)
            self.logger.info("URL格式分析:")
            
            # 必修课URL格式检查
            required_correct = 0
            for url_info in results['url_format_analysis']['required_courses']:
                if url_info['expected_format']:
                    required_correct += 1
                    
            self.logger.info(f"必修课正确格式URL: {required_correct}/{len(results['url_format_analysis']['required_courses'])}")
            
            # 选修课URL格式检查
            elective_correct = 0
            for url_info in results['url_format_analysis']['elective_courses']:
                if url_info['expected_format']:
                    elective_correct += 1
                    
            self.logger.info(f"选修课正确格式URL: {elective_correct}/{len(results['url_format_analysis']['elective_courses'])}")
            
            # 展示几个示例URL
            self.logger.info("="*60)
            self.logger.info("示例URL:")
            
            if results['url_format_analysis']['required_courses']:
                sample_required = results['url_format_analysis']['required_courses'][0]
                self.logger.info(f"必修课示例: {sample_required['url']}")
                self.logger.info(f"  课程名: {sample_required['course_name']}")
                self.logger.info(f"  正确格式: {sample_required['expected_format']}")
            
            if results['url_format_analysis']['elective_courses']:
                sample_elective = results['url_format_analysis']['elective_courses'][0]
                self.logger.info(f"选修课示例: {sample_elective['url']}")
                self.logger.info(f"  课程名: {sample_elective['course_name']}")
                self.logger.info(f"  正确格式: {sample_elective['expected_format']}")
            
            self.logger.info("="*60)
            self.logger.info("测试完成！结果已保存到 enhanced_parser_test_results.json")
            
            return True
            
        except Exception as e:
            self.logger.error(f"测试过程中出错: {str(e)}")
            return False
            
        finally:
            # 清理资源
            if login_manager.page:
                try:
                    login_manager.cleanup()
                except:
                    pass
    
    def _analyze_url(self, url: str, course_type: str) -> dict:
        """分析URL格式是否符合预期"""
        analysis = {
            'url': url,
            'course_type': course_type,
            'expected_format': False,
            'has_video_page': False,
            'has_id': False,
            'has_user_course_id': False,
            'has_name': False,
            'issues': []
        }
        
        if not url:
            analysis['issues'].append('URL为空')
            return analysis
        
        # 检查是否包含video_page
        if '#/video_page' in url:
            analysis['has_video_page'] = True
        else:
            analysis['issues'].append('缺少#/video_page路径')
        
        # 检查是否包含必要的参数
        if 'user_course_id=' in url:
            analysis['has_user_course_id'] = True
        else:
            analysis['issues'].append('缺少user_course_id参数')
        
        if 'name=' in url:
            analysis['has_name'] = True
        else:
            analysis['issues'].append('缺少name参数')
        
        if 'id=' in url and 'user_course_id=' not in url.split('id=')[1].split('&')[0]:
            analysis['has_id'] = True
        
        # 根据课程类型检查预期格式
        if course_type == 'required':
            # 必修课预期格式: #/video_page?id=10598&name=学员中心&user_course_id=1988340
            if (analysis['has_video_page'] and 
                analysis['has_user_course_id'] and 
                analysis['has_name']):
                analysis['expected_format'] = True
        elif course_type == 'elective':
            # 选修课预期格式: #/video_page?id=11362&user_course_id=1991630&name=学习中心
            if (analysis['has_video_page'] and 
                analysis['has_user_course_id'] and 
                analysis['has_name']):
                analysis['expected_format'] = True
        
        return analysis

def main():
    """主函数"""
    tester = EnhancedParserTester()
    success = tester.test_enhanced_parser()
    
    if success:
        print("\n✅ 测试成功完成!")
    else:
        print("\n❌ 测试失败!")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)