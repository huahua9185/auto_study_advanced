from playwright.sync_api import Page
import logging
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs, quote
from typing import List, Dict
from config.config import Config
from src.database import db

class EnhancedCourseParser:
    """
    增强版课程解析器，支持不同类型课程的正确URL格式：
    - 必修课格式: #/video_page?id=10598&name=学员中心&user_course_id=1988340
    - 选修课格式: #/video_page?id=11362&user_course_id=1991630&name=学习中心
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
    
    def parse_all_courses(self) -> Dict[str, List[Dict]]:
        """解析所有课程（必修课和选修课）"""
        all_courses = {
            'required': [],
            'elective': []
        }
        
        try:
            # 解析必修课
            self.logger.info("开始解析必修课程")
            required_courses = self.parse_required_courses_enhanced()
            all_courses['required'] = required_courses
            
            # 解析选修课
            self.logger.info("开始解析选修课程")
            elective_courses = self.parse_elective_courses_enhanced()
            all_courses['elective'] = elective_courses
            
            self.logger.info(f"课程解析完成 - 必修课: {len(required_courses)}门, 选修课: {len(elective_courses)}门")
            
        except Exception as e:
            self.logger.error(f"课程解析失败: {str(e)}")
            
        return all_courses
    
    def parse_required_courses_enhanced(self) -> List[Dict]:
        """增强版必修课程解析，提取正确的课程ID和URL"""
        courses = []
        
        try:
            # 访问必修课程页面
            self.logger.info("访问必修课程页面")
            self.page.goto(Config.REQUIRED_COURSES_URL)
            self.page.wait_for_load_state('domcontentloaded')
            time.sleep(3)
            
            # 策略1：分析"继续学习"按钮的点击行为获取真实URL
            continue_buttons = self.page.locator('div.btn:has-text("继续学习"), button:has-text("继续学习"), a:has-text("继续学习")').all()
            self.logger.info(f"找到 {len(continue_buttons)} 个'继续学习'按钮")
            
            for i, button in enumerate(continue_buttons):
                try:
                    # 获取父级li元素中的课程信息
                    parent_li = button.locator('xpath=ancestor::li[1]').first
                    if parent_li.count() == 0:
                        continue
                        
                    # 提取课程名称
                    course_name = ""
                    title_element = parent_li.locator('p.text_title').first
                    if title_element.count() > 0:
                        course_name = title_element.inner_text().strip()
                    
                    # 提取学习进度
                    progress = 0.0
                    progress_elements = parent_li.locator('.el-progress__text').all()
                    for progress_el in progress_elements:
                        progress_text = progress_el.inner_text().strip()
                        progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                        if progress_match:
                            progress = float(progress_match.group(1))
                            break
                    
                    # 提取按钮的各种属性和JavaScript代码
                    button_data = self._extract_button_data(button)
                    
                    # 构造必修课的正确视频URL
                    # 格式: #/video_page?id=课程ID&name=课程名称&user_course_id=用户课程ID
                    video_url, user_course_id, course_id = self._build_required_course_url(
                        course_name, button_data
                    )
                    
                    if course_name and video_url:
                        course_info = {
                            'course_name': course_name,
                            'course_type': 'required',
                            'progress': progress,
                            'video_url': video_url,
                            'user_course_id': user_course_id,
                            'course_id': course_id,
                            'button_data': button_data  # 调试用
                        }
                        courses.append(course_info)
                        self.logger.debug(f"添加必修课: {course_name} (进度: {progress}%)")
                        
                except Exception as e:
                    self.logger.warning(f"解析继续学习按钮 {i} 时出错: {str(e)}")
                    continue
            
            # 策略2：如果策略1没有找到课程，尝试解析页面中的其他链接
            if not courses:
                self.logger.info("策略1未找到课程，尝试策略2")
                courses = self._parse_required_courses_fallback()
                
        except Exception as e:
            self.logger.error(f"解析必修课程失败: {str(e)}")
            
        self.logger.info(f"必修课解析完成，共获取到 {len(courses)} 门课程")
        return courses
    
    def parse_elective_courses_enhanced(self) -> List[Dict]:
        """增强版选修课程解析，提取正确的课程ID和URL"""
        courses = []
        
        try:
            # 访问选修课页面
            self.logger.info("访问选修课页面")
            self.page.goto(Config.ELECTIVE_COURSES_URL)
            self.page.wait_for_load_state('domcontentloaded')
            time.sleep(3)
            
            # 分析表格中的选修课程
            table_rows = self.page.locator('tbody tr').all()
            self.logger.info(f"找到 {len(table_rows)} 个表格行")
            
            for i, row in enumerate(table_rows):
                try:
                    # 获取课程名称
                    title_cell = row.locator('td.td_title').first
                    if title_cell.count() == 0:
                        continue
                    
                    course_name = title_cell.inner_text().strip()
                    if not course_name or len(course_name) < 3:
                        continue
                    
                    # 获取学习进度
                    progress = 0.0
                    progress_element = row.locator('.el-progress__text').first
                    if progress_element.count() > 0:
                        progress_text = progress_element.inner_text().strip()
                        progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                        if progress_match:
                            progress = float(progress_match.group(1))
                    
                    # 分析播放相关的按钮和链接
                    play_data = self._extract_play_data(row)
                    
                    # 构造选修课的正确视频URL
                    # 格式: #/video_page?id=课程ID&user_course_id=用户课程ID&name=课程名称
                    video_url, user_course_id, course_id = self._build_elective_course_url(
                        course_name, play_data
                    )
                    
                    if course_name:
                        course_info = {
                            'course_name': course_name,
                            'course_type': 'elective',
                            'progress': progress,
                            'video_url': video_url,
                            'user_course_id': user_course_id,
                            'course_id': course_id,
                            'play_data': play_data  # 调试用
                        }
                        courses.append(course_info)
                        self.logger.debug(f"添加选修课: {course_name} (进度: {progress}%)")
                        
                except Exception as e:
                    self.logger.warning(f"解析选修课表格行 {i} 时出错: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"解析选修课程失败: {str(e)}")
            
        self.logger.info(f"选修课解析完成，共获取到 {len(courses)} 门课程")
        return courses
    
    def _extract_button_data(self, button) -> Dict:
        """从按钮元素中提取所有相关数据"""
        try:
            data = {
                'href': button.get_attribute('href'),
                'onclick': button.get_attribute('onclick'),
                'data-id': button.get_attribute('data-id'),
                'data-course-id': button.get_attribute('data-course-id'),
                'data-user-course-id': button.get_attribute('data-user-course-id'),
                'id': button.get_attribute('id'),
                'class': button.get_attribute('class'),
                'value': button.get_attribute('value'),
                'name': button.get_attribute('name'),
            }
            
            # 尝试通过点击获取真实的跳转URL
            try:
                current_url = self.page.url
                self.logger.debug(f"点击前URL: {current_url}")
                
                button.click()
                time.sleep(5)  # 增加等待时间
                
                new_url = self.page.url
                self.logger.debug(f"点击后URL: {new_url}")
                
                if new_url != current_url:
                    self.logger.info(f"URL发生变化: {current_url} -> {new_url}")
                    
                    # 检查是否跳转到视频页面或其他学习页面
                    if '#/video_page?' in new_url or '#/elective_course_play?' in new_url or '#/course_study?' in new_url:
                        data['real_url'] = new_url
                        self.logger.info(f"获取到真实跳转URL: {new_url}")
                        
                        # 解析URL中的参数
                        if '?' in new_url:
                            params_str = new_url.split('?')[1]
                            for param in params_str.split('&'):
                                if '=' in param:
                                    key, value = param.split('=', 1)
                                    if key == 'id':
                                        data['data-course-id'] = value
                                        self.logger.info(f"从URL提取到course_id: {value}")
                                    elif key == 'user_course_id':
                                        data['data-user-course-id'] = value
                                        self.logger.info(f"从URL提取到user_course_id: {value}")
                    else:
                        self.logger.warning(f"跳转到了非预期页面: {new_url}")
                    
                    # 返回课程列表页面
                    self.page.go_back()
                    time.sleep(3)
                else:
                    self.logger.debug("点击按钮后URL未发生变化")
                    
            except Exception as e:
                self.logger.warning(f"点击按钮获取URL失败: {str(e)}")
            
            return data
        except Exception as e:
            self.logger.warning(f"提取按钮数据时出错: {str(e)}")
            return {}
    
    def _extract_play_data(self, row) -> Dict:
        """从表格行中提取播放相关的所有数据"""
        play_data = {'elements': []}
        
        try:
            # 查找所有可能的播放相关元素
            play_selectors = [
                'td:has-text("播放")',
                'button:has-text("播放")',
                'a:has-text("播放")',
                '[onclick*="play"]',
                '[onclick*="video"]',
                '[onclick*="study"]',
                'button[type="button"]',
                'a[href*="video"]'
            ]
            
            for selector in play_selectors:
                elements = row.locator(selector).all()
                for element in elements:
                    element_data = {
                        'selector': selector,
                        'tag_name': element.evaluate('el => el.tagName.toLowerCase()'),
                        'href': element.get_attribute('href'),
                        'onclick': element.get_attribute('onclick'),
                        'data-id': element.get_attribute('data-id'),
                        'data-course-id': element.get_attribute('data-course-id'),
                        'data-user-course-id': element.get_attribute('data-user-course-id'),
                        'id': element.get_attribute('id'),
                        'class': element.get_attribute('class'),
                        'inner_text': element.inner_text().strip()
                    }
                    play_data['elements'].append(element_data)
                    
        except Exception as e:
            self.logger.warning(f"提取播放数据时出错: {str(e)}")
            
        return play_data
    
    def _build_required_course_url(self, course_name: str, button_data: Dict) -> tuple:
        """构造必修课的正确视频URL"""
        user_course_id = ""
        course_id = ""
        
        # 如果有真实的跳转URL，直接使用
        if 'real_url' in button_data and button_data['real_url']:
            video_url = button_data['real_url']
            self.logger.info(f"使用真实跳转URL: {video_url}")
            
            # 从URL中提取ID
            if '?' in video_url:
                params_str = video_url.split('?')[1]
                for param in params_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        if key == 'id':
                            course_id = value
                        elif key == 'user_course_id':
                            user_course_id = value
            
            return video_url, user_course_id, course_id
        
        # 从各种属性中提取ID信息
        for attr_name, attr_value in button_data.items():
            if not attr_value:
                continue
                
            # 直接的data属性
            if attr_name == 'data-user-course-id':
                user_course_id = attr_value
            elif attr_name == 'data-course-id':
                course_id = attr_value
            elif attr_name == 'data-id':
                if not user_course_id:
                    user_course_id = attr_value
            # 从onclick等JavaScript代码中提取ID
            elif attr_name == 'onclick' and attr_value:
                # 匹配各种可能的ID模式
                patterns = [
                    r'user_course_id[\s=:\'\"]*(\d+)',
                    r'userCourseId[\s=:\'\"]*(\d+)',
                    r'course_id[\s=:\'\"]*(\d+)',
                    r'courseId[\s=:\'\"]*(\d+)',
                    r'id[\s=:\'\"]*(\d+)',
                    r'[\'\"](\d+)[\'\"]'  # 通用数字模式
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, attr_value)
                    if matches:
                        if 'user_course_id' in pattern.lower() or 'usercourse' in pattern.lower():
                            user_course_id = matches[0]
                        elif 'course_id' in pattern.lower() and 'user' not in pattern.lower():
                            course_id = matches[0]
                        elif not user_course_id and not course_id:
                            user_course_id = matches[0]
        
        # 构造必修课URL: #/video_page?id=课程ID&name=课程名称&user_course_id=用户课程ID
        if user_course_id:
            encoded_name = quote(course_name)
            
            if course_id:
                video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id={course_id}&name={encoded_name}&user_course_id={user_course_id}"
            else:
                video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?name={encoded_name}&user_course_id={user_course_id}"
        else:
            # 如果没有提取到ID，生成临时ID和正确格式的URL  
            import hashlib
            user_course_id = hashlib.md5(course_name.encode('utf-8')).hexdigest()[:8]
            video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?name={quote(course_name)}&user_course_id=temp_{user_course_id}"
            
        return video_url, user_course_id, course_id
    
    def _build_elective_course_url(self, course_name: str, play_data: Dict) -> tuple:
        """构造选修课的正确视频URL"""
        user_course_id = ""
        course_id = ""
        
        # 从播放数据中提取ID信息
        for element_data in play_data.get('elements', []):
            # 检查直接的data属性
            if element_data.get('data-user-course-id'):
                user_course_id = element_data['data-user-course-id']
            if element_data.get('data-course-id'):
                course_id = element_data['data-course-id']
            elif element_data.get('data-id') and not user_course_id:
                user_course_id = element_data['data-id']
            
            # 从onclick中提取ID
            onclick = element_data.get('onclick')
            if onclick:
                patterns = [
                    r'user_course_id[\s=:\'\"]*(\d+)',
                    r'userCourseId[\s=:\'\"]*(\d+)',
                    r'course_id[\s=:\'\"]*(\d+)',
                    r'courseId[\s=:\'\"]*(\d+)',
                    r'[\'\"](\d+)[\'\"]'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, onclick)
                    if matches:
                        if 'user_course_id' in pattern.lower() and not user_course_id:
                            user_course_id = matches[0]
                        elif 'course_id' in pattern.lower() and 'user' not in pattern.lower() and not course_id:
                            course_id = matches[0]
                        elif not user_course_id and not course_id:
                            user_course_id = matches[0]
        
        # 构造选修课URL: #/video_page?id=课程ID&user_course_id=用户课程ID&name=课程名称
        if user_course_id:
            encoded_name = quote(course_name)
            
            if course_id:
                video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id={course_id}&user_course_id={user_course_id}&name={encoded_name}"
            else:
                video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?user_course_id={user_course_id}&name={encoded_name}"
        else:
            # 如果没有提取到ID，生成临时ID和URL
            import hashlib
            user_course_id = f"temp_{hashlib.md5(course_name.encode('utf-8')).hexdigest()[:8]}"
            course_id = f"temp_{hashlib.md5(course_name.encode('utf-8')).hexdigest()[8:16]}"
            # 所有课程统一使用 #/video_page? 格式
            video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?name={quote(course_name)}&user_course_id={user_course_id}&id={course_id}"
            
        return video_url, user_course_id, course_id
    
    def _parse_required_courses_fallback(self) -> List[Dict]:
        """必修课的备用解析方法"""
        courses = []
        
        try:
            # 尝试查找其他可能的课程链接
            course_selectors = [
                'a[href*="course_detail"]',
                'a[href*="video_page"]',
                'a[href*="study"]',
                '.course-item',
                '.course-card',
                '.course-list li'
            ]
            
            for selector in course_selectors:
                elements = self.page.locator(selector).all()
                if elements:
                    self.logger.info(f"使用备用选择器 '{selector}' 找到 {len(elements)} 个元素")
                    
                    for element in elements:
                        try:
                            # 提取课程信息
                            course_info = self._extract_course_info_from_element(element, 'required')
                            if course_info:
                                courses.append(course_info)
                        except Exception as e:
                            continue
                    
                    if courses:
                        break
                        
        except Exception as e:
            self.logger.error(f"备用解析方法失败: {str(e)}")
            
        return courses
    
    def _extract_course_info_from_element(self, element, course_type: str) -> Dict:
        """从单个元素中提取课程信息"""
        try:
            course_name = ""
            video_url = ""
            user_course_id = ""
            course_id = ""
            
            # 提取课程名称
            name_selectors = ['a', '.title', '.name', 'h3', 'h4', 'p']
            for selector in name_selectors:
                try:
                    name_el = element.locator(selector).first
                    if name_el.count() > 0:
                        text = name_el.inner_text().strip()
                        if text and len(text) > 3:
                            course_name = text
                            break
                except:
                    continue
            
            # 提取链接信息
            link_el = element.locator('a').first
            if link_el.count() > 0:
                href = link_el.get_attribute('href')
                if href:
                    if href.startswith('http'):
                        video_url = href
                    else:
                        video_url = Config.BASE_URL.rstrip('#/') + '/' + href.lstrip('#/')
                    
                    # 从URL中提取ID
                    parsed_url = urlparse(href)
                    query_params = parse_qs(parsed_url.query)
                    if 'user_course_id' in query_params:
                        user_course_id = query_params['user_course_id'][0]
                    if 'id' in query_params:
                        course_id = query_params['id'][0]
            
            if course_name:
                return {
                    'course_name': course_name,
                    'course_type': course_type,
                    'progress': 0.0,
                    'video_url': video_url,
                    'user_course_id': user_course_id,
                    'course_id': course_id
                }
                
        except Exception as e:
            self.logger.warning(f"从元素提取课程信息失败: {str(e)}")
            
        return None
    
    def save_courses_to_database(self, courses_data: Dict[str, List[Dict]]) -> bool:
        """将课程信息保存到数据库"""
        try:
            saved_count = 0
            
            for course_type, courses in courses_data.items():
                for course in courses:
                    try:
                        course_id = db.add_or_update_course(
                            course_name=course['course_name'],
                            course_type=course_type,
                            video_url=course.get('video_url', ''),
                            user_course_id=course.get('user_course_id', ''),
                            progress=course.get('progress', 0.0)
                        )
                        saved_count += 1
                        self.logger.debug(f"保存课程: {course['course_name']} (ID: {course_id})")
                        
                    except Exception as e:
                        self.logger.warning(f"保存课程失败 {course['course_name']}: {str(e)}")
                        continue
            
            self.logger.info(f"成功保存 {saved_count} 门课程到数据库")
            return True
            
        except Exception as e:
            self.logger.error(f"保存课程到数据库失败: {str(e)}")
            return False