from playwright.sync_api import Page
import logging
import time
import re
import sys
from pathlib import Path
from typing import Dict, List
from config.config import Config
from src.database import db

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_video_monitor import EnhancedVideoMonitor

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
            
            # 增强版"继续学习"按钮处理逻辑
            button_clicked = self._enhanced_continue_button_handling()
            
            if not button_clicked:
                self.logger.warning("所有'继续学习'按钮策略都失败，尝试直接播放视频")
                # 如果所有按钮策略都失败，尝试直接播放视频
                if not self._play_video():
                    self.logger.error("无法播放视频")
                    return False
            else:
                # 如果成功点击了继续学习按钮，等待视频iframe加载
                time.sleep(5)
                self.logger.info("✅ 继续学习按钮已点击，视频应已开始加载")
            
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
            tag_name = video_element.get_attribute('tagName')
            if tag_name and tag_name.lower() == 'video':
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
            
            # 注释掉点击视频区域的代码，因为点击视频可能会导致暂停
            # 现在通过"继续学习"按钮已经可以启动视频了
            # try:
            #     video_area_selectors = [
            #         '[class*="video"]',
            #         '[class*="player"]',
            #         'iframe',
            #         'video'
            #     ]
            #     
            #     for selector in video_area_selectors:
            #         try:
            #             elements = self.page.locator(selector).all()
            #             if elements and elements[0].is_visible():
            #                 elements[0].click()
            #                 self.logger.info(f"点击视频区域: {selector}")
            #                 time.sleep(2)
            #                 return True
            #         except:
            #             continue
            #             
            # except Exception as e:
            #     self.logger.warning(f"点击视频区域失败: {str(e)}")
            
            self.logger.warning("未找到可用的播放按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"查找播放按钮失败: {str(e)}")
            return False
    
    def _monitor_study_progress(self, course: Dict) -> float:
        """监控学习进度 - 使用增强版视频监控器"""
        try:
            self.logger.info(f"🎯 开始增强版课程进度监控: {course['course_name']}")
            
            # 创建增强版视频监控器
            video_monitor = EnhancedVideoMonitor(self.page)
            
            # 启动监控
            success = video_monitor.start_monitoring(course)
            
            if success:
                # 监控完成后获取最终进度
                final_progress = self._get_current_progress()
                if final_progress >= 100.0:
                    self.logger.info(f"✅ 课程学习完成！最终进度: {final_progress:.1f}%")
                    # 更新数据库中的进度
                    db.update_course_progress(course['id'], final_progress)
                    return final_progress
                else:
                    self.logger.warning(f"⚠️ 监控结束但进度未完成: {final_progress:.1f}%")
                    return final_progress
            else:
                self.logger.error("❌ 增强版监控器失败，回退到传统监控方法")
                return self._fallback_monitor_progress(course)
                
        except Exception as e:
            self.logger.error(f"增强版监控失败: {str(e)}，回退到传统监控")
            return self._fallback_monitor_progress(course)
    
    def _fallback_monitor_progress(self, course: Dict) -> float:
        """传统的监控方法作为备用"""
        try:
            self.logger.info(f"📊 使用传统方法监控课程进度: {course['course_name']}")
            
            initial_progress = course['progress']
            current_progress = initial_progress
            no_progress_count = 0
            max_no_progress = 10
            
            while current_progress < 100.0:
                try:
                    time.sleep(Config.VIDEO_CHECK_INTERVAL / 1000)
                    
                    current_url = self.page.url
                    if 'video_page' not in current_url:
                        self.logger.warning("页面已跳转，可能出现异常")
                        break
                    
                    new_progress = self._get_current_progress()
                    
                    if new_progress > current_progress:
                        current_progress = new_progress
                        no_progress_count = 0
                        db.update_course_progress(course['id'], current_progress)
                        self.logger.info(f"学习进度更新: {current_progress:.1f}%")
                    else:
                        no_progress_count += 1
                        
                        if no_progress_count >= max_no_progress:
                            self.logger.warning(f"进度长时间未更新，当前进度: {current_progress:.1f}%")
                            if not self._ensure_video_playing():
                                self.logger.error("视频播放异常，结束学习")
                                break
                            no_progress_count = 0
                    
                    if self._check_for_errors():
                        self.logger.error("检测到错误提示，结束学习")
                        break
                    
                except Exception as e:
                    self.logger.warning(f"监控进度时出错: {str(e)}")
                    continue
            
            return current_progress
            
        except Exception as e:
            self.logger.error(f"传统监控方法失败: {str(e)}")
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