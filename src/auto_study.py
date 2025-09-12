from playwright.sync_api import Page
import logging
import time
import re
from typing import Dict, List
from config.config import Config
from src.database import db

class AutoStudyManager:
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.current_course_id = None
        self.study_session_start = None
    
    def start_auto_study(self) -> bool:
        """开始自动学习"""
        try:
            self.logger.info("开始自动学习流程")
            
            # 获取未完成的课程
            incomplete_courses = db.get_incomplete_courses()
            
            if not incomplete_courses:
                self.logger.info("没有未完成的课程，学习任务已完成！")
                return True
            
            self.logger.info(f"找到 {len(incomplete_courses)} 门未完成的课程")
            
            # 按优先级排序课程（必修课优先）
            sorted_courses = sorted(incomplete_courses, 
                                  key=lambda x: (x['course_type'] != 'required', x['progress']))
            
            # 逐个学习课程
            for course in sorted_courses:
                try:
                    self.logger.info(f"开始学习课程: {course['course_name']}")
                    
                    success = self.study_single_course(course)
                    
                    if not success:
                        self.logger.warning(f"课程学习中断: {course['course_name']}")
                        break
                        
                    # 检查课程是否已完成
                    if course['progress'] >= 100.0:
                        self.logger.info(f"课程已完成: {course['course_name']}")
                        continue
                    
                except Exception as e:
                    self.logger.error(f"学习课程时发生错误 {course['course_name']}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"自动学习失败: {str(e)}")
            return False
    
    def study_single_course(self, course: Dict) -> bool:
        """学习单个课程"""
        try:
            self.current_course_id = course['id']
            self.study_session_start = time.time()
            
            # 记录学习开始
            initial_progress = course['progress']
            
            # 访问视频页面
            if not course['video_url']:
                self.logger.error(f"课程 {course['course_name']} 没有视频URL")
                return False
            
            self.logger.info(f"访问视频页面: {course['video_url']}")
            self.page.goto(course['video_url'])
            self.page.wait_for_load_state('networkidle')
            
            # 等待页面加载
            time.sleep(3)
            
            # 查找并播放视频
            if not self._play_video():
                self.logger.error("无法播放视频")
                return False
            
            # 监控学习进度
            final_progress = self._monitor_study_progress(course)
            
            # 记录学习结果
            duration = (time.time() - self.study_session_start) / 60  # 转换为分钟
            
            db.add_learning_log(
                course_id=course['id'],
                duration_minutes=duration,
                progress_before=initial_progress,
                progress_after=final_progress,
                status='completed' if final_progress >= 100.0 else 'interrupted',
                notes=f"自动学习完成"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"学习单个课程失败: {str(e)}")
            # 记录错误日志
            if self.current_course_id:
                duration = (time.time() - self.study_session_start) / 60 if self.study_session_start else 0
                db.add_learning_log(
                    course_id=self.current_course_id,
                    duration_minutes=duration,
                    progress_before=course.get('progress', 0),
                    progress_after=course.get('progress', 0),
                    status='error',
                    notes=f"学习过程中发生错误: {str(e)}"
                )
            return False
    
    def _play_video(self) -> bool:
        """查找并播放视频"""
        try:
            # 查找视频播放器的常见选择器
            video_selectors = [
                'video',
                'iframe[src*="video"]',
                '[class*="video-player"]',
                '[class*="player"]',
                '[id*="video"]',
                '[id*="player"]'
            ]
            
            video_element = None
            for selector in video_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    if elements:
                        video_element = elements[0]
                        self.logger.info(f"找到视频元素，使用选择器: {selector}")
                        break
                except:
                    continue
            
            if not video_element:
                self.logger.warning("未找到视频元素，尝试查找播放按钮")
                return self._find_and_click_play_button()
            
            # 尝试播放视频
            if video_element.get_attribute('tagName').lower() == 'video':
                # 如果是HTML5视频元素
                try:
                    # 检查视频是否已经在播放
                    is_paused = self.page.evaluate(
                        f"document.querySelector('{video_selectors[0]}').paused"
                    )
                    
                    if is_paused:
                        self.page.evaluate(
                            f"document.querySelector('{video_selectors[0]}').play()"
                        )
                        self.logger.info("视频开始播放")
                    else:
                        self.logger.info("视频已在播放")
                        
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"直接控制视频播放失败: {str(e)}")
                    return self._find_and_click_play_button()
            else:
                # 如果是iframe或其他元素，查找播放按钮
                return self._find_and_click_play_button()
                
        except Exception as e:
            self.logger.error(f"播放视频失败: {str(e)}")
            return False
    
    def _find_and_click_play_button(self) -> bool:
        """查找并点击播放按钮"""
        try:
            play_button_selectors = [
                'button[class*="play"]',
                'button[id*="play"]',
                '[class*="play-btn"]',
                '[class*="video-play"]',
                'button:has-text("播放")',
                'button:has-text("play")',
                '[class*="control"] button',
                '.vjs-big-play-button',  # Video.js播放器
                '.plyr__control--overlaid',  # Plyr播放器
            ]
            
            for selector in play_button_selectors:
                try:
                    play_buttons = self.page.locator(selector).all()
                    if play_buttons:
                        play_button = play_buttons[0]
                        if play_button.is_visible():
                            play_button.click()
                            self.logger.info(f"点击播放按钮: {selector}")
                            time.sleep(2)  # 等待播放开始
                            return True
                except Exception as e:
                    self.logger.debug(f"尝试播放按钮失败 {selector}: {str(e)}")
                    continue
            
            # 尝试点击视频区域
            try:
                video_area_selectors = [
                    '[class*="video"]',
                    '[class*="player"]',
                    'iframe',
                    'video'
                ]
                
                for selector in video_area_selectors:
                    try:
                        elements = self.page.locator(selector).all()
                        if elements and elements[0].is_visible():
                            elements[0].click()
                            self.logger.info(f"点击视频区域: {selector}")
                            time.sleep(2)
                            return True
                    except:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"点击视频区域失败: {str(e)}")
            
            self.logger.warning("未找到可用的播放按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"查找播放按钮失败: {str(e)}")
            return False
    
    def _monitor_study_progress(self, course: Dict) -> float:
        """监控学习进度"""
        try:
            self.logger.info(f"开始监控课程进度: {course['course_name']}")
            
            initial_progress = course['progress']
            current_progress = initial_progress
            no_progress_count = 0
            max_no_progress = 10  # 最多允许10次没有进度变化
            
            while current_progress < 100.0:
                try:
                    # 等待一段时间
                    time.sleep(Config.VIDEO_CHECK_INTERVAL / 1000)
                    
                    # 检查页面是否还在视频页面
                    current_url = self.page.url
                    if 'video_page' not in current_url:
                        self.logger.warning("页面已跳转，可能出现异常")
                        break
                    
                    # 获取当前进度
                    new_progress = self._get_current_progress()
                    
                    if new_progress > current_progress:
                        current_progress = new_progress
                        no_progress_count = 0
                        
                        # 更新数据库中的进度
                        db.update_course_progress(course['id'], current_progress)
                        
                        self.logger.info(f"学习进度更新: {current_progress:.1f}%")
                    else:
                        no_progress_count += 1
                        
                        if no_progress_count >= max_no_progress:
                            self.logger.warning(f"进度长时间未更新，可能出现问题。当前进度: {current_progress:.1f}%")
                            # 尝试重新播放视频
                            if not self._ensure_video_playing():
                                self.logger.error("视频播放异常，结束学习")
                                break
                            no_progress_count = 0
                    
                    # 检查是否有错误提示
                    if self._check_for_errors():
                        self.logger.error("检测到错误提示，结束学习")
                        break
                    
                except Exception as e:
                    self.logger.warning(f"监控进度时出错: {str(e)}")
                    continue
            
            if current_progress >= 100.0:
                self.logger.info(f"课程学习完成！最终进度: {current_progress:.1f}%")
            
            return current_progress
            
        except Exception as e:
            self.logger.error(f"监控学习进度失败: {str(e)}")
            return course.get('progress', 0)
    
    def _get_current_progress(self) -> float:
        """获取当前学习进度"""
        try:
            # 查找进度指示器
            progress_selectors = [
                '[class*="progress"]',
                '[class*="percent"]',
                'text=/\\d+%/',
                'span:has-text("%")',
                '.video-progress',
                '#progress'
            ]
            
            for selector in progress_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            progress_text = element.inner_text()
                            progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                            if progress_match:
                                return float(progress_match.group(1))
                except:
                    continue
            
            # 尝试从视频元素获取进度
            try:
                video_progress = self.page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (video && video.duration > 0) {
                            return (video.currentTime / video.duration) * 100;
                        }
                        return null;
                    }
                """)
                
                if video_progress is not None:
                    return video_progress
                    
            except:
                pass
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"获取当前进度失败: {str(e)}")
            return 0.0
    
    def _ensure_video_playing(self) -> bool:
        """确保视频正在播放"""
        try:
            # 检查视频是否在播放
            is_playing = self.page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    return video && !video.paused;
                }
            """)
            
            if is_playing:
                return True
            
            # 尝试重新播放
            return self._play_video()
            
        except Exception as e:
            self.logger.error(f"确保视频播放失败: {str(e)}")
            return False
    
    def _check_for_errors(self) -> bool:
        """检查页面是否有错误提示"""
        try:
            error_selectors = [
                'text=错误',
                'text=失败',
                'text=异常',
                '[class*="error"]',
                '[class*="fail"]',
                'text=网络连接失败',
                'text=视频加载失败'
            ]
            
            for selector in error_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        error_element = self.page.locator(selector).first
                        if error_element.is_visible():
                            error_text = error_element.inner_text()
                            self.logger.warning(f"检测到错误提示: {error_text}")
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查错误提示失败: {str(e)}")
            return False
    
    def pause_study(self):
        """暂停学习"""
        try:
            self.logger.info("暂停学习")
            # 这里可以添加暂停逻辑，比如暂停视频播放
            
        except Exception as e:
            self.logger.error(f"暂停学习失败: {str(e)}")
    
    def resume_study(self):
        """恢复学习"""
        try:
            self.logger.info("恢复学习")
            # 这里可以添加恢复逻辑，比如恢复视频播放
            
        except Exception as e:
            self.logger.error(f"恢复学习失败: {str(e)}")
    
    def stop_study(self):
        """停止学习"""
        try:
            self.logger.info("停止学习")
            
            # 记录学习结束日志
            if self.current_course_id and self.study_session_start:
                duration = (time.time() - self.study_session_start) / 60
                db.add_learning_log(
                    course_id=self.current_course_id,
                    duration_minutes=duration,
                    progress_before=0,  # 这里应该传入实际的开始进度
                    progress_after=0,   # 这里应该传入实际的结束进度  
                    status='interrupted',
                    notes="用户主动停止学习"
                )
            
        except Exception as e:
            self.logger.error(f"停止学习失败: {str(e)}")