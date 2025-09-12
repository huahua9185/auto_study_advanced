#!/usr/bin/env python3
"""
视频播放页面测试脚本
测试必修课和选修课的视频播放功能
"""

import sys
import os
import logging
import json
import time
from pathlib import Path
from urllib.parse import unquote

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import Config
from src.login import login_manager
from src.enhanced_course_parser import EnhancedCourseParser
from src.database import db

class VideoPlayerTester:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.test_results = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'required_courses_tested': 0,
                'elective_courses_tested': 0,
                'successful_video_loads': 0,
                'failed_video_loads': 0,
                'total_tests': 0
            },
            'video_analysis': {
                'required_courses': [],
                'elective_courses': []
            },
            'errors': []
        }
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/video_player_test.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 确保日志目录存在
        log_dir = Path('data')
        log_dir.mkdir(exist_ok=True)
    
    def test_video_player(self):
        """测试视频播放页面"""
        self.logger.info("开始测试视频播放页面")
        
        try:
            # 登录系统
            if not self.login_and_init():
                return False
            
            # 获取课程数据
            courses_data = self.get_courses_data()
            if not courses_data:
                return False
            
            # 测试必修课视频
            self.test_required_courses(courses_data.get('required', []))
            
            # 测试选修课视频
            self.test_elective_courses(courses_data.get('elective', []))
            
            # 保存测试结果
            self.save_test_results()
            
            # 显示测试总结
            self.show_test_summary()
            
            return True
            
        except Exception as e:
            self.logger.error(f"测试过程中出错: {str(e)}")
            self.test_results['errors'].append(f"测试过程异常: {str(e)}")
            return False
            
        finally:
            # 清理资源
            self.cleanup()
    
    def login_and_init(self):
        """登录和初始化"""
        try:
            self.logger.info("初始化浏览器和登录...")
            
            if not login_manager.init_browser():
                self.logger.error("浏览器初始化失败")
                return False
            
            if not login_manager.check_login_status():
                self.logger.info("执行登录...")
                if not login_manager.login():
                    self.logger.error("登录失败")
                    return False
            
            self.logger.info("登录成功")
            return True
            
        except Exception as e:
            self.logger.error(f"登录初始化失败: {str(e)}")
            return False
    
    def get_courses_data(self):
        """获取课程数据"""
        try:
            self.logger.info("获取课程数据...")
            
            # 先尝试从数据库获取
            courses = db.get_all_courses()
            if courses:
                self.logger.info(f"从数据库获取到 {len(courses)} 门课程")
                
                # 转换为按类型分组的格式
                required_courses = [c for c in courses if c['course_type'] == 'required']
                elective_courses = [c for c in courses if c['course_type'] == 'elective']
                
                return {
                    'required': required_courses,
                    'elective': elective_courses
                }
            
            # 如果数据库没有数据，从网页解析
            self.logger.info("数据库无数据，从网页解析课程...")
            parser = EnhancedCourseParser(login_manager.page)
            courses_data = parser.parse_all_courses()
            
            if not courses_data or (not courses_data.get('required') and not courses_data.get('elective')):
                self.logger.error("无法获取课程数据")
                return None
            
            return courses_data
            
        except Exception as e:
            self.logger.error(f"获取课程数据失败: {str(e)}")
            return None
    
    def test_required_courses(self, required_courses):
        """测试必修课视频"""
        self.logger.info(f"开始测试 {len(required_courses)} 门必修课...")
        
        test_count = min(3, len(required_courses))  # 最多测试3门课程
        
        for i, course in enumerate(required_courses[:test_count]):
            try:
                self.logger.info(f"测试必修课 {i+1}/{test_count}: {course.get('course_name', 'Unknown')}")
                
                video_result = self.test_video_page(course, 'required')
                self.test_results['video_analysis']['required_courses'].append(video_result)
                
                self.test_results['summary']['required_courses_tested'] += 1
                self.test_results['summary']['total_tests'] += 1
                
                if video_result['video_loaded']:
                    self.test_results['summary']['successful_video_loads'] += 1
                else:
                    self.test_results['summary']['failed_video_loads'] += 1
                
                # 等待一下避免过快请求
                time.sleep(2)
                
            except Exception as e:
                error_msg = f"测试必修课失败: {course.get('course_name', 'Unknown')} - {str(e)}"
                self.logger.error(error_msg)
                self.test_results['errors'].append(error_msg)
    
    def test_elective_courses(self, elective_courses):
        """测试选修课视频"""
        self.logger.info(f"开始测试 {len(elective_courses)} 门选修课...")
        
        test_count = min(3, len(elective_courses))  # 最多测试3门课程
        
        for i, course in enumerate(elective_courses[:test_count]):
            try:
                self.logger.info(f"测试选修课 {i+1}/{test_count}: {course.get('course_name', 'Unknown')}")
                
                video_result = self.test_video_page(course, 'elective')
                self.test_results['video_analysis']['elective_courses'].append(video_result)
                
                self.test_results['summary']['elective_courses_tested'] += 1
                self.test_results['summary']['total_tests'] += 1
                
                if video_result['video_loaded']:
                    self.test_results['summary']['successful_video_loads'] += 1
                else:
                    self.test_results['summary']['failed_video_loads'] += 1
                
                # 等待一下避免过快请求
                time.sleep(2)
                
            except Exception as e:
                error_msg = f"测试选修课失败: {course.get('course_name', 'Unknown')} - {str(e)}"
                self.logger.error(error_msg)
                self.test_results['errors'].append(error_msg)
    
    def test_video_page(self, course, course_type):
        """测试单个视频页面"""
        video_result = {
            'course_name': course.get('course_name', 'Unknown'),
            'course_type': course_type,
            'video_url': course.get('video_url', ''),
            'user_course_id': course.get('user_course_id', ''),
            'course_id': course.get('course_id', ''),
            'video_loaded': False,
            'video_elements': [],
            'controls_found': {},
            'page_title': '',
            'current_url': '',
            'screenshot_saved': False,
            'html_saved': False,
            'issues': []
        }
        
        try:
            page = login_manager.page
            video_url = course.get('video_url', '')
            
            if not video_url:
                video_result['issues'].append('视频URL为空')
                return video_result
            
            # 访问视频页面
            self.logger.info(f"访问视频页面: {video_url}")
            page.goto(video_url, wait_until='networkidle', timeout=15000)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取页面信息
            video_result['current_url'] = page.url
            video_result['page_title'] = page.title()
            
            # 检查是否成功到达视频页面（而不是重定向到首页）
            if '#/video_page' not in video_result['current_url']:
                video_result['issues'].append('页面重定向到非视频页面')
                return video_result
            
            # 分析视频元素
            video_result.update(self.analyze_video_page(page))
            
            # 保存调试文件
            self.save_debug_files(page, course, course_type, video_result)
            
        except Exception as e:
            error_msg = f"访问视频页面失败: {str(e)}"
            video_result['issues'].append(error_msg)
            self.logger.warning(error_msg)
        
        return video_result
    
    def analyze_video_page(self, page):
        """分析视频页面内容"""
        analysis = {
            'video_loaded': False,
            'video_elements': [],
            'controls_found': {
                'play_button': False,
                'progress_bar': False,
                'volume_control': False,
                'fullscreen_button': False,
                'speed_control': False
            }
        }
        
        try:
            # 等待可能的动态加载
            time.sleep(2)
            
            # 查找视频元素
            video_selectors = [
                'video',
                'iframe[src*="video"]',
                'iframe[src*="player"]',
                '.video-player',
                '.dplayer',
                '.jwplayer',
                '[class*="video"]',
                '[id*="video"]',
                'embed[type*="video"]'
            ]
            
            for selector in video_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        for element in elements:
                            try:
                                # 获取元素信息
                                tag_name = element.evaluate('el => el.tagName.toLowerCase()')
                                src = element.get_attribute('src') or ''
                                class_name = element.get_attribute('class') or ''
                                id_attr = element.get_attribute('id') or ''
                                
                                video_info = {
                                    'selector': selector,
                                    'tag': tag_name,
                                    'src': src,
                                    'class': class_name,
                                    'id': id_attr,
                                    'visible': element.is_visible()
                                }
                                
                                analysis['video_elements'].append(video_info)
                                
                                if video_info['visible']:
                                    analysis['video_loaded'] = True
                                    
                            except:
                                continue
                except:
                    continue
            
            # 查找播放控制元素
            control_selectors = {
                'play_button': ['.dplayer-play-icon', '.play-btn', '[title*="播放"]', '[aria-label*="play"]', '.video-play'],
                'progress_bar': ['.dplayer-bar', '.progress-bar', '[role="slider"]', '.video-progress'],
                'volume_control': ['.dplayer-volume', '.volume-control', '[title*="音量"]'],
                'fullscreen_button': ['.dplayer-full', '.fullscreen-btn', '[title*="全屏"]'],
                'speed_control': ['.dplayer-setting', '.speed-control', '[title*="速度"]', '[title*="倍速"]']
            }
            
            for control_type, selectors in control_selectors.items():
                for selector in selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            analysis['controls_found'][control_type] = True
                            break
                    except:
                        continue
            
            # 检查页面是否有学习相关的元素
            learning_selectors = [
                '.course-content',
                '.video-content', 
                '.learning-page',
                '[class*="study"]',
                '[class*="course"]'
            ]
            
            learning_elements_count = 0
            for selector in learning_selectors:
                try:
                    learning_elements_count += page.locator(selector).count()
                except:
                    continue
            
            if learning_elements_count > 0:
                analysis['video_loaded'] = True  # 如果有学习相关元素，认为页面加载成功
            
        except Exception as e:
            self.logger.warning(f"分析视频页面时出错: {str(e)}")
        
        return analysis
    
    def save_debug_files(self, page, course, course_type, video_result):
        """保存调试文件"""
        try:
            # 生成安全的文件名
            course_name = course.get('course_name', 'unknown')
            safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name[:20] if safe_name else 'unnamed'
            
            timestamp = int(time.time())
            base_filename = f"video_{course_type}_{safe_name}_{timestamp}"
            
            # 保存截图
            try:
                screenshot_path = f"data/{base_filename}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                video_result['screenshot_saved'] = True
                self.logger.info(f"截图已保存: {screenshot_path}")
            except Exception as e:
                self.logger.warning(f"保存截图失败: {str(e)}")
            
            # 保存HTML
            try:
                html_path = f"data/{base_filename}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(page.content())
                video_result['html_saved'] = True
                self.logger.info(f"HTML已保存: {html_path}")
            except Exception as e:
                self.logger.warning(f"保存HTML失败: {str(e)}")
                
        except Exception as e:
            self.logger.warning(f"保存调试文件时出错: {str(e)}")
    
    def save_test_results(self):
        """保存测试结果"""
        try:
            with open('video_player_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            self.logger.info("测试结果已保存到 video_player_test_results.json")
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {str(e)}")
    
    def show_test_summary(self):
        """显示测试总结"""
        self.logger.info("="*60)
        self.logger.info("视频播放页面测试结果总结")
        self.logger.info("="*60)
        
        summary = self.test_results['summary']
        self.logger.info(f"总测试数量: {summary['total_tests']}")
        self.logger.info(f"必修课测试: {summary['required_courses_tested']}")
        self.logger.info(f"选修课测试: {summary['elective_courses_tested']}")
        self.logger.info(f"视频加载成功: {summary['successful_video_loads']}")
        self.logger.info(f"视频加载失败: {summary['failed_video_loads']}")
        
        if summary['total_tests'] > 0:
            success_rate = (summary['successful_video_loads'] / summary['total_tests']) * 100
            self.logger.info(f"成功率: {success_rate:.1f}%")
        
        # 显示详细分析
        self.logger.info("\n详细分析:")
        
        # 必修课分析
        if self.test_results['video_analysis']['required_courses']:
            self.logger.info("\n必修课视频测试:")
            for result in self.test_results['video_analysis']['required_courses']:
                status = "✅" if result['video_loaded'] else "❌"
                self.logger.info(f"  {status} {result['course_name']}")
                if result['issues']:
                    for issue in result['issues']:
                        self.logger.info(f"    问题: {issue}")
        
        # 选修课分析
        if self.test_results['video_analysis']['elective_courses']:
            self.logger.info("\n选修课视频测试:")
            for result in self.test_results['video_analysis']['elective_courses']:
                status = "✅" if result['video_loaded'] else "❌"
                self.logger.info(f"  {status} {result['course_name']}")
                if result['issues']:
                    for issue in result['issues']:
                        self.logger.info(f"    问题: {issue}")
        
        # 显示错误
        if self.test_results['errors']:
            self.logger.info(f"\n错误记录 ({len(self.test_results['errors'])}):")
            for error in self.test_results['errors']:
                self.logger.info(f"  ❌ {error}")
        
        self.logger.info("="*60)
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理资源...")
            if login_manager:
                login_manager.close_browser()
            self.logger.info("资源清理完成")
        except Exception as e:
            self.logger.warning(f"清理资源时出错: {str(e)}")

def main():
    """主函数"""
    print("视频播放页面测试工具")
    print("=" * 50)
    
    tester = VideoPlayerTester()
    
    try:
        success = tester.test_video_player()
        
        if success:
            print("\n✅ 视频播放页面测试完成!")
            print("详细结果请查看: video_player_test_results.json")
            return 0
        else:
            print("\n❌ 视频播放页面测试失败!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断测试")
        tester.cleanup()
        return 2
    except Exception as e:
        print(f"\n💥 测试过程异常: {str(e)}")
        tester.cleanup()
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)