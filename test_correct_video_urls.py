#!/usr/bin/env python3
"""
测试正确URL格式的视频播放页面
基于用户提供的正确URL格式进行测试
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

from config.config import Config
from src.login import login_manager
from src.database import db

class CorrectVideoUrlTester:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.test_results = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'url_format_tests': {
                'required_course': None,
                'elective_course': None
            },
            'errors': []
        }
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/correct_video_url_test.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 确保日志目录存在
        log_dir = Path('data')
        log_dir.mkdir(exist_ok=True)
    
    def test_correct_video_urls(self):
        """测试正确的视频URL格式"""
        self.logger.info("开始测试正确的视频URL格式")
        
        try:
            # 登录系统
            if not self.login_and_init():
                return False
            
            # 测试必修课正确URL格式
            self.test_required_course_url()
            
            # 测试选修课正确URL格式  
            self.test_elective_course_url()
            
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
    
    def test_required_course_url(self):
        """测试必修课正确URL格式"""
        self.logger.info("测试必修课URL格式...")
        
        # 根据用户提供的正确格式构造测试URL
        # 必修课格式: #/video_page?id=10598&name=学员中心&user_course_id=1988340
        test_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id=10598&name=%E5%AD%A6%E5%91%98%E4%B8%AD%E5%BF%83&user_course_id=1988340"
        
        result = self.test_single_video_url(test_url, "required", "测试必修课")
        self.test_results['url_format_tests']['required_course'] = result
    
    def test_elective_course_url(self):
        """测试选修课正确URL格式"""
        self.logger.info("测试选修课URL格式...")
        
        # 根据用户提供的正确格式构造测试URL  
        # 选修课格式: #/video_page?id=11362&user_course_id=1991630&name=学习中心
        test_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id=11362&user_course_id=1991630&name=%E5%AD%A6%E4%B9%A0%E4%B8%AD%E5%BF%83"
        
        result = self.test_single_video_url(test_url, "elective", "测试选修课")
        self.test_results['url_format_tests']['elective_course'] = result
    
    def test_single_video_url(self, test_url, course_type, course_name):
        """测试单个视频URL"""
        video_result = {
            'course_name': course_name,
            'course_type': course_type,
            'test_url': test_url,
            'video_loaded': False,
            'page_reached_correctly': False,
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
            
            self.logger.info(f"访问测试URL: {test_url}")
            page.goto(test_url, wait_until='networkidle', timeout=15000)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取页面信息
            video_result['current_url'] = page.url
            video_result['page_title'] = page.title()
            
            self.logger.info(f"当前URL: {video_result['current_url']}")
            self.logger.info(f"页面标题: {video_result['page_title']}")
            
            # 检查是否成功到达视频页面
            if '#/video_page' in video_result['current_url']:
                video_result['page_reached_correctly'] = True
                self.logger.info("✅ 成功到达video_page页面")
            else:
                video_result['issues'].append('页面未到达video_page路径')
                self.logger.warning(f"❌ 页面重定向到: {video_result['current_url']}")
            
            # 分析页面内容
            video_analysis = self.analyze_video_page(page)
            video_result.update(video_analysis)
            
            # 保存调试文件
            self.save_debug_files(page, course_type, course_name, video_result)
            
        except Exception as e:
            error_msg = f"访问视频页面失败: {str(e)}"
            video_result['issues'].append(error_msg)
            self.logger.error(error_msg)
        
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
            
            # 查找视频相关元素
            video_selectors = [
                'video',
                'iframe[src*="video"]',
                'iframe[src*="player"]',
                'iframe[src*="play"]',
                '.video-player',
                '.dplayer',
                '.jwplayer',
                '[class*="video"]',
                '[id*="video"]',
                '[id*="player"]',
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
                                
                                if video_info['visible'] or video_info['src']:
                                    analysis['video_loaded'] = True
                                    self.logger.info(f"找到视频元素: {selector} - {video_info}")
                                    
                            except:
                                continue
                except:
                    continue
            
            # 查找播放控制元素
            control_selectors = {
                'play_button': [
                    '.dplayer-play-icon', '.play-btn', '[title*="播放"]', 
                    '[aria-label*="play"]', '.video-play', 'button[class*="play"]',
                    '[class*="play-button"]', '[id*="play"]'
                ],
                'progress_bar': [
                    '.dplayer-bar', '.progress-bar', '[role="slider"]', 
                    '.video-progress', '[class*="progress"]', '.seek-bar'
                ],
                'volume_control': [
                    '.dplayer-volume', '.volume-control', '[title*="音量"]',
                    '[class*="volume"]', '.audio-control'
                ],
                'fullscreen_button': [
                    '.dplayer-full', '.fullscreen-btn', '[title*="全屏"]',
                    '[class*="fullscreen"]', '.full-screen'
                ],
                'speed_control': [
                    '.dplayer-setting', '.speed-control', '[title*="速度"]', 
                    '[title*="倍速"]', '[class*="speed"]', '.playback-rate'
                ]
            }
            
            for control_type, selectors in control_selectors.items():
                for selector in selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            analysis['controls_found'][control_type] = True
                            self.logger.info(f"找到控制元素 {control_type}: {selector} ({count}个)")
                            break
                    except:
                        continue
            
            # 检查学习相关元素
            learning_selectors = [
                '.course-content', '.video-content', '.learning-page',
                '[class*="study"]', '[class*="course"]', '[class*="learn"]',
                '.main-content', '.content-wrapper'
            ]
            
            learning_elements_count = 0
            for selector in learning_selectors:
                try:
                    count = page.locator(selector).count()
                    learning_elements_count += count
                    if count > 0:
                        self.logger.info(f"找到学习相关元素: {selector} ({count}个)")
                except:
                    continue
            
            if learning_elements_count > 0:
                analysis['video_loaded'] = True  # 如果有学习相关元素，认为页面正确加载
            
        except Exception as e:
            self.logger.warning(f"分析视频页面时出错: {str(e)}")
        
        return analysis
    
    def save_debug_files(self, page, course_type, course_name, video_result):
        """保存调试文件"""
        try:
            timestamp = int(time.time())
            base_filename = f"correct_video_{course_type}_{timestamp}"
            
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
            with open('correct_video_url_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            self.logger.info("测试结果已保存到 correct_video_url_test_results.json")
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {str(e)}")
    
    def show_test_summary(self):
        """显示测试总结"""
        self.logger.info("="*60)
        self.logger.info("正确视频URL格式测试结果总结")
        self.logger.info("="*60)
        
        # 必修课测试结果
        required_result = self.test_results['url_format_tests']['required_course']
        if required_result:
            self.logger.info("必修课测试结果:")
            self.logger.info(f"  URL: {required_result['test_url']}")
            self.logger.info(f"  页面到达正确: {'✅' if required_result['page_reached_correctly'] else '❌'}")
            self.logger.info(f"  视频加载成功: {'✅' if required_result['video_loaded'] else '❌'}")
            self.logger.info(f"  当前URL: {required_result['current_url']}")
            if required_result['issues']:
                for issue in required_result['issues']:
                    self.logger.info(f"    问题: {issue}")
        
        # 选修课测试结果
        elective_result = self.test_results['url_format_tests']['elective_course']
        if elective_result:
            self.logger.info("选修课测试结果:")
            self.logger.info(f"  URL: {elective_result['test_url']}")
            self.logger.info(f"  页面到达正确: {'✅' if elective_result['page_reached_correctly'] else '❌'}")
            self.logger.info(f"  视频加载成功: {'✅' if elective_result['video_loaded'] else '❌'}")
            self.logger.info(f"  当前URL: {elective_result['current_url']}")
            if elective_result['issues']:
                for issue in elective_result['issues']:
                    self.logger.info(f"    问题: {issue}")
        
        # 显示控制元素统计
        for test_name, result in self.test_results['url_format_tests'].items():
            if result and result['controls_found']:
                found_controls = [k for k, v in result['controls_found'].items() if v]
                if found_controls:
                    self.logger.info(f"{test_name} 找到的控制元素: {', '.join(found_controls)}")
        
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
    print("正确视频URL格式测试工具")
    print("=" * 50)
    
    tester = CorrectVideoUrlTester()
    
    try:
        success = tester.test_correct_video_urls()
        
        if success:
            print("\n✅ 正确视频URL格式测试完成!")
            print("详细结果请查看: correct_video_url_test_results.json")
            return 0
        else:
            print("\n❌ 正确视频URL格式测试失败!")
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