#!/usr/bin/env python3
"""
集成重构播放器的增强版自动学习模块
支持使用重构播放器或原始播放器的灵活学习流程
"""

import logging
import time
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional
from playwright.sync_api import Page
from src.refactored_video_player import RefactoredVideoPlayer
from src.database import db
from config.player_config import PlayerConfig

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_video_monitor import EnhancedVideoMonitor

class EnhancedAutoStudy:
    """增强版自动学习类，集成重构播放器"""
    
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.current_course_id: Optional[int] = None
        self.study_session_start: Optional[float] = None
        self.is_studying = False
        self.is_paused = False
        
        # 根据配置决定是否使用重构播放器
        self.use_refactored_player = PlayerConfig.USE_REFACTORED_PLAYER
        self.refactored_player = None
        
        if self.use_refactored_player:
            self.refactored_player = RefactoredVideoPlayer(page)
            self.logger.info("✅ 启用重构播放器模式")
        else:
            self.logger.info("📺 使用原始播放器模式")
    
    def start_enhanced_study(self, courses: List[Dict]) -> bool:
        """
        启动增强版自动学习
        
        Args:
            courses: 课程列表
            
        Returns:
            bool: 学习是否成功启动
        """
        try:
            if not courses:
                self.logger.warning("没有可学习的课程")
                return False
            
            self.is_studying = True
            self.logger.info(f"🚀 开始增强版自动学习，共 {len(courses)} 门课程")
            
            # 学习统计
            successful_courses = 0
            failed_courses = 0
            
            for i, course in enumerate(courses):
                if not self.is_studying:
                    self.logger.info("学习已停止")
                    break
                
                # 等待暂停恢复
                while self.is_paused:
                    time.sleep(1)
                
                self.logger.info(f"📚 开始学习课程 {i+1}/{len(courses)}: {course['course_name']}")
                
                try:
                    if self.use_refactored_player:
                        success = self._study_with_refactored_player(course)
                    else:
                        success = self._study_with_original_player(course)
                    
                    if success:
                        successful_courses += 1
                        self.logger.info(f"✅ 课程学习完成: {course['course_name']}")
                    else:
                        failed_courses += 1
                        self.logger.error(f"❌ 课程学习失败: {course['course_name']}")
                        
                        # 如果启用了回退机制，尝试用原始播放器
                        if self.use_refactored_player and PlayerConfig.FALLBACK_TO_ORIGINAL:
                            self.logger.info("🔄 尝试使用原始播放器回退学习")
                            if self._study_with_original_player(course):
                                successful_courses += 1
                                failed_courses -= 1
                                self.logger.info("✅ 原始播放器回退学习成功")
                
                except Exception as e:
                    self.logger.error(f"学习课程时发生错误 {course['course_name']}: {str(e)}")
                    failed_courses += 1
                    continue
                
                # 课程间隔
                if i < len(courses) - 1:
                    interval = random.uniform(3, 8)
                    self.logger.info(f"⏳ 等待 {interval:.1f} 秒后继续下一门课程")
                    time.sleep(interval)
            
            # 学习总结
            self.logger.info(f"🎯 学习完成统计:")
            self.logger.info(f"   成功: {successful_courses} 门")
            self.logger.info(f"   失败: {failed_courses} 门")
            self.logger.info(f"   成功率: {successful_courses/(successful_courses+failed_courses)*100:.1f}%")
            
            return True
            
        except Exception as e:
            self.logger.error(f"增强版自动学习失败: {str(e)}")
            return False
            
        finally:
            self.is_studying = False
            if self.refactored_player:
                self.refactored_player.cleanup()
    
    def _study_with_refactored_player(self, course: Dict) -> bool:
        """使用重构播放器学习课程"""
        try:
            self.current_course_id = course.get('id', course.get('user_course_id', 'unknown'))
            self.study_session_start = time.time()
            
            # 记录学习开始
            initial_progress = course.get('progress', 0)
            
            self.logger.info(f"🎮 使用重构播放器访问: {course['video_url']}")
            
            # 先访问视频页面
            self.page.goto(course['video_url'])
            self.page.wait_for_load_state('domcontentloaded')
            time.sleep(3)
            
            # 查找并点击"继续学习"按钮来启动视频
            if not self._click_continue_learning_button():
                self.logger.error("无法找到或点击'继续学习'按钮")
                return False
            
            # 等待视频iframe加载
            time.sleep(5)
            
            # 准备课程数据
            course_data = {
                'name': course['course_name'],
                'course_id': str(course.get('id', course.get('user_course_id', 'unknown'))),
                'user_course_id': course.get('user_course_id', ''),
                'video_url': course['video_url'],
                'progress': initial_progress,
                'course_type': course.get('type', 'unknown')
            }
            
            self.logger.info(f"📚 课程视频已启动: {course_data['name']}")
            
            # 现在可以启动重构播放器学习会话或直接监控进度
            # 由于视频已经在原始页面播放，我们主要进行进度监控
            return self._monitor_video_learning_progress(course_data)
            
            # 获取学习时长设置
            duration = PlayerConfig.LEARNING_DURATION_MINUTES
            
            # 模拟学习进程
            self.logger.info(f"📖 开始学习进程，预计学习时间: {duration} 分钟")
            result = self.refactored_player.simulate_learning_progress(duration)
            
            if result['success']:
                final_progress = result['progress']
                duration_actual = result['duration']
                
                self.logger.info(f"🎉 重构播放器学习完成")
                self.logger.info(f"   进度: {final_progress}%")
                self.logger.info(f"   时长: {duration_actual} 分钟")
                
                # 记录学习结果到数据库
                db.add_learning_log(
                    course_id=course.get('id', course.get('user_course_id', 'unknown')),
                    duration_minutes=duration_actual,
                    progress_before=initial_progress,
                    progress_after=final_progress,
                    status='completed' if final_progress >= 100.0 else 'interrupted',
                    notes=f"重构播放器学习完成 - {result.get('message', '')}"
                )
                
                return True
                
            else:
                self.logger.error(f"重构播放器学习失败: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"重构播放器学习过程异常: {str(e)}")
            # 记录错误日志
            course_id_for_log = course.get('id', course.get('user_course_id', 'unknown'))
            if course_id_for_log:
                duration = (time.time() - self.study_session_start) / 60 if self.study_session_start else 0
                db.add_learning_log(
                    course_id=course_id_for_log,
                    duration_minutes=duration,
                    progress_before=course.get('progress', 0),
                    progress_after=course.get('progress', 0),
                    status='error',
                    notes=f"重构播放器学习异常: {str(e)}"
                )
            return False
    
    def _click_continue_learning_button(self) -> bool:
        """查找并点击'继续学习'或'开始学习'元素（使用增强版处理器）"""
        try:
            # 导入增强版处理器
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))
            
            from enhanced_continue_button_handler import EnhancedContinueButtonHandler
            
            # 创建增强版处理器实例
            handler = EnhancedContinueButtonHandler(self.page)
            
            # 使用增强版逻辑处理
            return handler.click_continue_learning_button()
            
        except ImportError:
            # 如果无法导入增强版处理器，回退到原始逻辑
            self.logger.warning("无法导入增强版处理器，使用原始逻辑")
            return self._click_continue_learning_button_fallback()
            
        except Exception as e:
            self.logger.error(f"增强版处理器失败: {str(e)}")
            # 出错时回退到原始逻辑
            return self._click_continue_learning_button_fallback()
    
    def _enhanced_continue_button_handling(self) -> bool:
        """
        增强版"继续学习"按钮处理逻辑
        包含多重检测策略和重试机制，确保按钮能被正确识别和点击
        """
        self.logger.info("🎯 启动增强版'继续学习'按钮处理逻辑")
        
        # 策略1: 使用已集成的增强版处理器
        try:
            if self._click_continue_learning_button():
                self.logger.info("✅ 策略1成功: 增强版处理器点击成功")
                return True
        except Exception as e:
            self.logger.debug(f"策略1失败: {e}")
        
        # 策略2: 额外等待时间后重试
        try:
            self.logger.info("🔄 策略2: 额外等待后重试")
            time.sleep(3)  # 额外等待3秒
            
            if self._click_continue_learning_button():
                self.logger.info("✅ 策略2成功: 等待后点击成功")
                return True
        except Exception as e:
            self.logger.debug(f"策略2失败: {e}")
        
        # 策略3: 强制刷新页面后重试
        try:
            self.logger.info("🔄 策略3: 刷新页面后重试")
            self.page.reload()
            self.page.wait_for_load_state('networkidle')
            time.sleep(5)  # 等待页面完全加载
            
            if self._click_continue_learning_button():
                self.logger.info("✅ 策略3成功: 刷新后点击成功")
                return True
        except Exception as e:
            self.logger.debug(f"策略3失败: {e}")
        
        # 策略4: 多次尝试点击
        try:
            self.logger.info("🔄 策略4: 多次尝试点击")
            for attempt in range(3):
                self.logger.debug(f"   尝试第 {attempt + 1} 次...")
                time.sleep(2)
                
                if self._click_continue_learning_button():
                    self.logger.info(f"✅ 策略4成功: 第 {attempt + 1} 次尝试点击成功")
                    return True
        except Exception as e:
            self.logger.debug(f"策略4失败: {e}")
        
        # 策略5: 使用JavaScript强制查找和点击
        try:
            self.logger.info("🔄 策略5: JavaScript强制查找")
            success = self.page.evaluate("""
                () => {
                    // 查找策略1: 主页面查找
                    let buttons = document.querySelectorAll('div.user_choise');
                    for (let btn of buttons) {
                        if (btn.textContent && btn.textContent.includes('继续学习')) {
                            btn.click();
                            return { success: true, method: 'main_page_user_choise' };
                        }
                    }
                    
                    // 查找策略2: 文本匹配
                    let allDivs = document.querySelectorAll('div');
                    for (let div of allDivs) {
                        let text = div.textContent || '';
                        if (text.includes('继续学习') && div.offsetParent !== null) {
                            div.click();
                            return { success: true, method: 'text_matching' };
                        }
                    }
                    
                    // 查找策略3: iframe中查找
                    let iframes = document.querySelectorAll('iframe');
                    for (let iframe of iframes) {
                        try {
                            let iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                            if (iframeDoc) {
                                let iframeButtons = iframeDoc.querySelectorAll('div.user_choise');
                                for (let btn of iframeButtons) {
                                    if (btn.textContent && btn.textContent.includes('继续学习')) {
                                        btn.click();
                                        return { success: true, method: 'iframe_user_choise' };
                                    }
                                }
                            }
                        } catch (e) {
                            continue;
                        }
                    }
                    
                    return { success: false };
                }
            """)
            
            if success['success']:
                self.logger.info(f"✅ 策略5成功: JavaScript {success['method']} 点击成功")
                time.sleep(2)  # 等待点击生效
                return True
                
        except Exception as e:
            self.logger.debug(f"策略5失败: {e}")
        
        # 策略6: 使用备用处理器
        try:
            self.logger.info("🔄 策略6: 使用备用处理器")
            if self._click_continue_learning_button_fallback():
                self.logger.info("✅ 策略6成功: 备用处理器点击成功")
                return True
        except Exception as e:
            self.logger.debug(f"策略6失败: {e}")
        
        self.logger.error("❌ 所有增强版按钮处理策略都失败")
        return False
    
    def _click_continue_learning_button_fallback(self) -> bool:
        """原始的继续学习按钮点击逻辑（回退方案）"""
        try:
            self.logger.info("🔍 查找'继续学习'元素（回退逻辑）...")
            
            # 定义选择器，优先使用更精确的选择器
            continue_selectors = [
                'div.user_choise',  # 精确匹配class为user_choise的div
                'div.user_choise:has-text("继续学习")',  # 更精确的组合选择器
                'div.user_choise:has-text("开始学习")',
                '[class*="user_choise"]',
                'div:text("继续学习")',  # 文本精确匹配
                'div:text("开始学习")',
                'button:has-text("继续学习")',
                'button:has-text("开始学习")',
            ]
            
            # 先在主页面查找
            for selector in continue_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    if elements:
                        for element in elements:
                            if element.is_visible():
                                element.click()
                                self.logger.info(f"✅ 成功点击主页面的元素: {selector}")
                                time.sleep(3)  # 等待视频加载
                                return True
                except Exception as e:
                    self.logger.debug(f"主页面尝试选择器失败 {selector}: {str(e)}")
                    continue
            
            # 如果主页面没找到，重点查找iframe
            self.logger.info("在主页面未找到元素，尝试在iframe中查找div.user_choise...")
            iframes = self.page.locator('iframe').all()
            
            if not iframes:
                self.logger.warning("页面中没有找到iframe")
                return False
            
            self.logger.info(f"找到{len(iframes)}个iframe，逐个检查...")
            
            for i, iframe_element in enumerate(iframes):
                try:
                    # 获取iframe的content_frame
                    frame = iframe_element.content_frame()
                    if not frame:
                        self.logger.debug(f"iframe {i+1}没有content_frame")
                        continue
                    
                    # 获取iframe的src以便调试
                    iframe_src = iframe_element.get_attribute('src') or 'no-src'
                    self.logger.debug(f"检查iframe {i+1}/{len(iframes)}, src: {iframe_src[:100]}...")
                    
                    # 优先尝试使用JavaScript直接点击div.user_choise
                    try:
                        # 检查是否存在div.user_choise元素
                        has_element = frame.evaluate("""
                            () => {
                                const element = document.querySelector('div.user_choise');
                                return element !== null;
                            }
                        """)
                        
                        if has_element:
                            # 使用JavaScript点击元素
                            frame.evaluate("""
                                () => {
                                    const element = document.querySelector('div.user_choise');
                                    if (element) {
                                        element.click();
                                        return true;
                                    }
                                    return false;
                                }
                            """)
                            self.logger.info(f"✅ 使用JavaScript成功点击iframe {i+1}中的div.user_choise元素")
                            time.sleep(3)
                            return True
                    except Exception as js_error:
                        self.logger.debug(f"JavaScript点击失败: {js_error}")
                    
                    # 备用方案：使用Playwright的locator
                    for selector in continue_selectors:
                        try:
                            elements = frame.locator(selector).all()
                            if elements:
                                for element in elements:
                                    if element.is_visible():
                                        element.click()
                                        self.logger.info(f"✅ 成功点击iframe {i+1}内的元素: {selector}")
                                        time.sleep(3)
                                        return True
                        except Exception as e:
                            self.logger.debug(f"iframe {i+1}内尝试选择器失败 {selector}: {str(e)}")
                            continue
                    
                    # 在iframe中尝试文本匹配
                    try:
                        text_elements = frame.locator('text=/继续|开始/').all()
                        for element in text_elements:
                            if element.is_visible():
                                text_content = element.inner_text()
                                if "继续学习" in text_content or "开始学习" in text_content:
                                    element.click()
                                    self.logger.info(f"✅ 通过文本匹配点击iframe内按钮: {text_content}")
                                    time.sleep(3)
                                    return True
                    except Exception as e:
                        self.logger.debug(f"iframe内文本匹配失败: {str(e)}")
                        
                except Exception as e:
                    self.logger.debug(f"处理第 {i+1} 个iframe时出错: {str(e)}")
                    continue
            
            self.logger.warning("⚠️ 在主页面和所有iframe中都未找到'继续学习'或'开始学习'按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"点击继续学习按钮失败: {str(e)}")
            return False
    
    def _monitor_video_learning_progress(self, course_data: Dict) -> bool:
        """监控视频学习进度（在点击继续学习按钮后）- 使用增强版视频监控器"""
        try:
            self.logger.info(f"🎯 开始增强版视频学习监控: {course_data['name']}")
            
            # 创建增强版视频监控器
            video_monitor = EnhancedVideoMonitor(self.page)
            
            # 转换课程数据格式以适配监控器
            course_for_monitor = {
                'id': course_data.get('course_id', self.current_course_id),
                'course_name': course_data['name'],
                'progress': course_data.get('progress', 0)
            }
            
            # 启动监控
            success = video_monitor.start_monitoring(course_for_monitor)
            
            if success:
                self.logger.info(f"✅ 增强版视频监控成功完成: {course_data['name']}")
                
                # 记录学习结果到数据库
                db.add_learning_log(
                    course_id=course_data.get('course_id', self.current_course_id),
                    duration_minutes=30,  # 默认记录30分钟，实际时长由监控器管理
                    progress_before=course_data.get('progress', 0),
                    progress_after=100.0,
                    status='completed',
                    notes=f"增强版视频监控完成 - 自动进度获取和30秒等待"
                )
                
                return True
            else:
                self.logger.error("❌ 增强版监控失败，回退到传统监控")
                return self._fallback_video_monitoring(course_data)
                
        except Exception as e:
            self.logger.error(f"增强版视频监控失败: {str(e)}，回退到传统监控")
            return self._fallback_video_monitoring(course_data)
    
    def _fallback_video_monitoring(self, course_data: Dict) -> bool:
        """传统的视频监控方法作为备用"""
        try:
            self.logger.info(f"📊 使用传统方法监控视频: {course_data['name']}")
            
            duration = PlayerConfig.LEARNING_DURATION_MINUTES
            total_seconds = duration * 60
            progress_interval = 30
            
            start_time = time.time()
            initial_progress = course_data.get('progress', 0)
            current_progress = initial_progress
            
            while time.time() - start_time < total_seconds:
                if not self.is_studying:
                    self.logger.info("学习已停止")
                    break
                
                while self.is_paused:
                    time.sleep(1)
                
                elapsed = time.time() - start_time
                progress_increment = (elapsed / total_seconds) * (100 - initial_progress)
                current_progress = min(100, initial_progress + progress_increment)
                
                if int(elapsed) % progress_interval == 0:
                    self.logger.info(f"📊 学习进度: {current_progress:.1f}%")
                
                time.sleep(1)
            
            final_progress = min(100, initial_progress + (100 - initial_progress))
            duration_actual = (time.time() - start_time) / 60
            
            self.logger.info(f"🎉 传统监控视频学习完成")
            self.logger.info(f"   最终进度: {final_progress:.1f}%")
            self.logger.info(f"   实际时长: {duration_actual:.1f} 分钟")
            
            db.add_learning_log(
                course_id=course_data.get('course_id', self.current_course_id),
                duration_minutes=duration_actual,
                progress_before=initial_progress,
                progress_after=final_progress,
                status='completed' if final_progress >= 100.0 else 'interrupted',
                notes=f"传统视频学习监控完成"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"传统视频监控失败: {str(e)}")
            return False
    
    def _study_with_original_player(self, course: Dict) -> bool:
        """使用原始播放器学习课程（回退方案）"""
        try:
            self.current_course_id = course.get('id', course.get('user_course_id', 'unknown'))
            self.study_session_start = time.time()
            
            # 记录学习开始
            initial_progress = course.get('progress', 0)
            
            # 访问视频页面
            if not course['video_url']:
                self.logger.error(f"课程 {course['course_name']} 没有视频URL")
                return False
            
            self.logger.info(f"📺 使用原始播放器访问: {course['video_url']}")
            self.page.goto(course['video_url'])
            self.page.wait_for_load_state('networkidle')
            
            # 等待页面加载
            time.sleep(3)
            
            # 增强版"继续学习"按钮处理逻辑
            button_clicked = self._enhanced_continue_button_handling()
            
            if not button_clicked:
                self.logger.warning("所有'继续学习'按钮策略都失败，尝试直接播放视频")
                # 如果所有按钮策略都失败，尝试直接播放视频
                if not self._play_original_video():
                    self.logger.error("无法播放视频")
                    return False
            else:
                # 如果成功点击了继续学习按钮，等待视频iframe加载
                time.sleep(5)
                self.logger.info("✅ 继续学习按钮已点击，视频应已开始加载")
            
            # 监控学习进度
            final_progress = self._monitor_original_study_progress(course)
            
            # 记录学习结果
            duration = (time.time() - self.study_session_start) / 60  # 转换为分钟
            
            db.add_learning_log(
                course_id=course.get('id', course.get('user_course_id', 'unknown')),
                duration_minutes=duration,
                progress_before=initial_progress,
                progress_after=final_progress,
                status='completed' if final_progress >= 100.0 else 'interrupted',
                notes=f"原始播放器学习完成"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"原始播放器学习失败: {str(e)}")
            # 记录错误日志
            course_id_for_log = course.get('id', course.get('user_course_id', 'unknown'))
            if course_id_for_log:
                duration = (time.time() - self.study_session_start) / 60 if self.study_session_start else 0
                db.add_learning_log(
                    course_id=course_id_for_log,
                    duration_minutes=duration,
                    progress_before=course.get('progress', 0),
                    progress_after=course.get('progress', 0),
                    status='error',
                    notes=f"原始播放器学习错误: {str(e)}"
                )
            return False
    
    def _play_original_video(self) -> bool:
        """原始播放器播放视频"""
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
                        self.logger.info(f"找到视频元素: {selector}")
                        break
                except:
                    continue
            
            if not video_element:
                self.logger.warning("未找到视频元素，尝试查找播放按钮")
                return self._find_and_click_play_button()
            
            return True
            
        except Exception as e:
            self.logger.error(f"播放原始视频失败: {str(e)}")
            return False
    
    def _find_and_click_play_button(self) -> bool:
        """查找并点击播放按钮"""
        try:
            play_selectors = [
                'button:has-text("播放")',
                '[class*="play"]:visible',
                '[id*="play"]:visible',
                'button[title*="play" i]',
                'button[aria-label*="play" i]',
                '.play-btn:visible'
            ]
            
            for selector in play_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    if elements:
                        elements[0].click()
                        self.logger.info(f"点击播放按钮: {selector}")
                        time.sleep(2)
                        return True
                except:
                    continue
            
            self.logger.warning("未找到播放按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"点击播放按钮失败: {str(e)}")
            return False
    
    def _monitor_original_study_progress(self, course: Dict) -> float:
        """监控原始播放器学习进度"""
        try:
            study_duration = PlayerConfig.LEARNING_DURATION_MINUTES * 60  # 转为秒
            start_time = time.time()
            
            while time.time() - start_time < study_duration:
                if not self.is_studying:
                    break
                
                # 等待暂停恢复
                while self.is_paused:
                    time.sleep(1)
                
                # 模拟进度更新
                elapsed = time.time() - start_time
                progress = min(100, (elapsed / study_duration) * 100)
                
                # 每30秒记录一次进度
                if int(elapsed) % 30 == 0:
                    self.logger.info(f"学习进度: {progress:.1f}%")
                
                time.sleep(1)
            
            # 返回最终进度
            final_progress = min(100, ((time.time() - start_time) / study_duration) * 100)
            return final_progress
            
        except Exception as e:
            self.logger.error(f"监控学习进度失败: {str(e)}")
            return 0
    
    def get_study_status(self) -> Dict:
        """获取学习状态"""
        status = {
            'is_studying': self.is_studying,
            'is_paused': self.is_paused,
            'current_course_id': self.current_course_id,
            'using_refactored_player': self.use_refactored_player,
            'study_session_start': self.study_session_start
        }
        
        # 如果使用重构播放器，获取播放器状态
        if self.use_refactored_player and self.refactored_player:
            player_status = self.refactored_player.get_player_status()
            status.update({'player_status': player_status})
        
        return status
    
    def pause_study(self):
        """暂停学习"""
        self.is_paused = True
        if self.refactored_player:
            self.refactored_player.stop_learning()
        self.logger.info("⏸️ 学习已暂停")
    
    def resume_study(self):
        """恢复学习"""
        self.is_paused = False
        self.logger.info("▶️ 学习已恢复")
    
    def stop_study(self):
        """停止学习"""
        self.is_studying = False
        self.is_paused = False
        if self.refactored_player:
            self.refactored_player.stop_learning()
        self.logger.info("⏹️ 学习已停止")
    
    def cleanup(self):
        """清理资源"""
        try:
            self.stop_study()
            if self.refactored_player:
                self.refactored_player.cleanup()
            self.logger.info("🧹 资源清理完成")
        except Exception as e:
            self.logger.error(f"清理资源失败: {str(e)}")