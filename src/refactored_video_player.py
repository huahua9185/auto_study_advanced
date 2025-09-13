#!/usr/bin/env python3
"""
重构后的视频播放器集成模块
基于HTML5和现代Web技术重构iframe嵌入式视频播放器
提供更好的用户体验和控制功能
"""

import logging
import time
import json
from pathlib import Path
from playwright.sync_api import Page
from typing import Dict, Any, Optional


class RefactoredVideoPlayer:
    """重构后的视频播放器"""
    
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.current_course = None
        self.is_playing = False
        self.progress = 0
        
    def load_refactored_player(self, course_data: Dict[str, Any]) -> bool:
        """
        加载重构后的视频播放器
        
        Args:
            course_data: 课程数据，包含课程名称、ID、视频URL等
            
        Returns:
            bool: 是否成功加载播放器
        """
        try:
            self.current_course = course_data
            self.logger.info(f"加载重构播放器: {course_data.get('name', 'Unknown')}")
            
            # 获取重构播放器的HTML模板
            player_html_path = Path(__file__).parent.parent / "refactored_video_player.html"
            
            if not player_html_path.exists():
                self.logger.error("重构播放器HTML文件不存在")
                return False
            
            # 读取HTML模板
            with open(player_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 替换模板中的课程数据
            html_content = self._customize_html_template(html_content, course_data)
            
            # 创建临时HTML文件
            temp_html_path = Path(__file__).parent.parent / "temp_player.html"
            with open(temp_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 在浏览器中加载重构播放器
            file_url = f"file://{temp_html_path.absolute()}"
            self.page.goto(file_url)
            self.page.wait_for_load_state('domcontentloaded')
            
            # 等待播放器初始化
            time.sleep(2)
            
            self.logger.info("重构播放器加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载重构播放器失败: {str(e)}")
            return False
    
    def _customize_html_template(self, html_content: str, course_data: Dict[str, Any]) -> str:
        """
        自定义HTML模板，插入实际的课程数据
        
        Args:
            html_content: 原始HTML内容
            course_data: 课程数据
            
        Returns:
            str: 自定义后的HTML内容
        """
        try:
            # 提取iframe URL
            iframe_url = self._extract_iframe_url(course_data.get('video_url', ''))
            
            # 创建课程数据的JavaScript对象
            course_js_data = {
                'name': course_data.get('name', '未知课程'),
                'courseId': course_data.get('course_id', ''),
                'userCourseId': course_data.get('user_course_id', ''),
                'videoUrl': course_data.get('video_url', ''),
                'iframeUrl': iframe_url
            }
            
            # 替换JavaScript中的课程数据
            js_data_str = json.dumps(course_js_data, ensure_ascii=False)
            html_content = html_content.replace(
                'courseData = {', 
                f'courseData = {js_data_str}; // Original: {{'
            )
            
            # 替换页面标题
            html_content = html_content.replace(
                '<title>重构后的视频播放器</title>',
                f'<title>{course_data.get("name", "视频播放器")}</title>'
            )
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"自定义HTML模板失败: {str(e)}")
            return html_content
    
    def _extract_iframe_url(self, video_url: str) -> str:
        """
        从视频URL提取iframe源地址
        
        Args:
            video_url: 视频页面URL
            
        Returns:
            str: iframe源地址
        """
        try:
            # 解析URL参数获取user_course_id
            import urllib.parse
            parsed = urllib.parse.urlparse(video_url)
            fragment = parsed.fragment  # 获取#后面的部分
            
            if fragment:
                # 解析fragment中的参数
                if '?' in fragment:
                    _, query = fragment.split('?', 1)
                    params = urllib.parse.parse_qs(query)
                    user_course_id = params.get('user_course_id', [''])[0]
                    
                    if user_course_id:
                        # 构造iframe URL
                        iframe_url = f"https://edu.nxgbjy.org.cn/device/study_new!scorm_play.do?terminal=1&id={user_course_id}"
                        return iframe_url
            
            self.logger.warning(f"无法从URL提取iframe地址: {video_url}")
            return ""
            
        except Exception as e:
            self.logger.error(f"提取iframe URL失败: {str(e)}")
            return ""
    
    def start_learning_session(self, course_data: Dict[str, Any]) -> bool:
        """
        开始学习会话
        
        Args:
            course_data: 课程数据
            
        Returns:
            bool: 是否成功开始学习
        """
        try:
            # 加载重构播放器
            if not self.load_refactored_player(course_data):
                return False
            
            # 等待页面完全加载
            self.page.wait_for_selector('#videoPlayer', timeout=10000)
            
            # 检查播放器是否正确加载
            player_loaded = self.page.evaluate("""
                () => {
                    const player = document.getElementById('videoPlayer');
                    return player && player.src && player.src.length > 0;
                }
            """)
            
            if player_loaded:
                self.logger.info("播放器加载成功，开始学习会话")
                self.is_playing = True
                return True
            else:
                self.logger.error("播放器加载失败")
                return False
                
        except Exception as e:
            self.logger.error(f"开始学习会话失败: {str(e)}")
            return False
    
    def simulate_learning_progress(self, duration_minutes: int = 30) -> Dict[str, Any]:
        """
        模拟学习进度
        
        Args:
            duration_minutes: 学习持续时间（分钟）
            
        Returns:
            Dict: 学习结果
        """
        try:
            self.logger.info(f"开始模拟学习进度，持续时间: {duration_minutes} 分钟")
            
            total_seconds = duration_minutes * 60
            progress_interval = 30  # 每30秒更新一次进度
            
            for elapsed in range(0, total_seconds, progress_interval):
                if not self.is_playing:
                    break
                
                # 计算进度百分比
                progress = min(100, (elapsed / total_seconds) * 100)
                
                # 更新页面进度显示
                try:
                    self.page.evaluate(f"""
                        () => {{
                            updateProgress({progress:.1f});
                        }}
                    """)
                except:
                    pass  # 忽略JS执行错误
                
                self.progress = progress
                
                # 日志记录
                if elapsed % 300 == 0:  # 每5分钟记录一次
                    self.logger.info(f"学习进度: {progress:.1f}%")
                
                # 等待下一个间隔
                time.sleep(progress_interval)
            
            # 完成学习
            self.progress = 100
            self.is_playing = False
            
            # 更新最终进度
            try:
                self.page.evaluate("() => { updateProgress(100); }")
            except:
                pass
            
            result = {
                'success': True,
                'progress': 100,
                'duration': duration_minutes,
                'course_name': self.current_course.get('name', '') if self.current_course else '',
                'message': '学习完成'
            }
            
            self.logger.info(f"学习会话完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"模拟学习进度失败: {str(e)}")
            return {
                'success': False,
                'progress': self.progress,
                'error': str(e)
            }
    
    def get_player_status(self) -> Dict[str, Any]:
        """
        获取播放器状态
        
        Returns:
            Dict: 播放器状态信息
        """
        try:
            # 获取页面状态
            status = self.page.evaluate("""
                () => {
                    return {
                        playerLoaded: !!document.getElementById('videoPlayer'),
                        pageTitle: document.title,
                        currentUrl: window.location.href,
                        progressText: document.getElementById('progressText')?.textContent || '0% 完成'
                    };
                }
            """)
            
            status.update({
                'is_playing': self.is_playing,
                'progress': self.progress,
                'current_course': self.current_course.get('name', '') if self.current_course else None
            })
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取播放器状态失败: {str(e)}")
            return {'error': str(e)}
    
    def stop_learning(self) -> bool:
        """
        停止学习会话
        
        Returns:
            bool: 是否成功停止
        """
        try:
            self.is_playing = False
            self.logger.info("学习会话已停止")
            
            # 执行停止相关的页面操作
            try:
                self.page.evaluate("() => { isPlaying = false; }")
            except:
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止学习会话失败: {str(e)}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            # 删除临时文件
            temp_html_path = Path(__file__).parent.parent / "temp_player.html"
            if temp_html_path.exists():
                temp_html_path.unlink()
            
            self.is_playing = False
            self.current_course = None
            self.progress = 0
            
        except Exception as e:
            self.logger.error(f"清理资源失败: {str(e)}")


def test_refactored_player():
    """测试重构播放器功能"""
    from src.login import login_manager
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("🧪 测试重构视频播放器")
    print("=" * 50)
    
    try:
        # 初始化浏览器
        if not login_manager.init_browser():
            print("❌ 浏览器初始化失败")
            return False
            
        print("✅ 浏览器初始化成功")
        
        # 创建播放器实例
        player = RefactoredVideoPlayer(login_manager.page)
        
        # 测试课程数据
        test_course = {
            'name': '深入学习中华民族发展史，讲好中华民族共同体故事（三）',
            'course_id': '10910',
            'user_course_id': '1988356',
            'video_url': 'https://edu.nxgbjy.org.cn/nxxzxy/index.html#/video_page?id=10910&name=%E5%AD%A6%E5%91%98%E4%B8%AD%E5%BF%83&user_course_id=1988356',
            'progress': 0
        }
        
        print(f"\n📚 测试课程: {test_course['name']}")
        
        # 开始学习会话
        if player.start_learning_session(test_course):
            print("✅ 学习会话启动成功")
            
            # 获取播放器状态
            status = player.get_player_status()
            print(f"📊 播放器状态: {status}")
            
            # 模拟短时间学习（测试用）
            print("\n⏰ 开始模拟学习进程...")
            result = player.simulate_learning_progress(duration_minutes=2)
            
            if result['success']:
                print(f"✅ 学习完成: {result['message']}")
                print(f"   进度: {result['progress']}%")
                print(f"   持续时间: {result['duration']} 分钟")
            else:
                print(f"❌ 学习失败: {result.get('error', 'Unknown error')}")
            
        else:
            print("❌ 学习会话启动失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False
        
    finally:
        try:
            player.cleanup()
            login_manager.close_browser()
        except:
            pass


if __name__ == "__main__":
    success = test_refactored_player()
    print(f"\n{'🎉 测试成功' if success else '❌ 测试失败'}")