from playwright.sync_api import Page
import logging
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict
from config.config import Config
from src.database import db

class CourseParser:
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
            required_courses = self.parse_required_courses()
            all_courses['required'] = required_courses
            
            # 解析选修课
            self.logger.info("开始解析选修课程")
            elective_courses = self.parse_elective_courses()
            all_courses['elective'] = elective_courses
            
            self.logger.info(f"课程解析完成 - 必修课: {len(required_courses)}门, 选修课: {len(elective_courses)}门")
            
        except Exception as e:
            self.logger.error(f"课程解析失败: {str(e)}")
            
        return all_courses
    
    def parse_required_courses(self) -> List[Dict]:
        """解析必修课程列表（网络培训班）"""
        courses = []
        
        try:
            # 访问必修课程页面
            self.logger.info("访问必修课程页面获取课程")
            self.page.goto(Config.REQUIRED_COURSES_URL)
            self.page.wait_for_load_state('domcontentloaded')
            time.sleep(3)
            
            # 等待页面完全加载
            try:
                self.page.wait_for_selector('body', timeout=10000)
            except:
                pass
            
            self.logger.info("尝试多种选择器策略解析必修课程")
            
            # 策略1：查找"继续学习"按钮对应的课程
            continue_buttons = self.page.locator('div.btn:has-text("继续学习"), button:has-text("继续学习"), a:has-text("继续学习")').all()
            self.logger.info(f"找到 {len(continue_buttons)} 个'继续学习'按钮")
            
            for button in continue_buttons:
                try:
                    # 查找按钮所在的列表项（li元素）
                    parent_li = button.locator('xpath=ancestor::li[1]').first
                    if parent_li.count() > 0:
                        # 从同一li中提取课程名称
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
                        
                        # 获取按钮的点击链接或ID（目前这些按钮可能没有直接的href）
                        href = button.get_attribute('href')
                        onclick = button.get_attribute('onclick') 
                        data_id = button.get_attribute('data-id')
                        
                        # 尝试构造视频链接
                        video_url = ""
                        user_course_id = ""
                        
                        if href:
                            video_url = href if href.startswith('http') else Config.BASE_URL.rstrip('#/') + href.lstrip('#/')
                        elif onclick:
                            # 从onclick中提取ID或链接
                            id_match = re.search(r'[\'""](\d+)[\'\""]', onclick)
                            if id_match:
                                user_course_id = id_match.group(1)
                                video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?user_course_id={user_course_id}"
                        elif data_id:
                            user_course_id = data_id
                            video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?user_course_id={data_id}"
                        else:
                            # 如果没有直接的链接信息，尝试用课程名称构造一个临时的URL
                            # 这可能需要后续通过点击按钮来获取实际的链接
                            video_url = f"{Config.BASE_URL.rstrip('#/')}#/course_study?name={course_name}"
                        
                        if course_name:
                            course_info = {
                                'course_name': course_name,
                                'course_type': 'required',
                                'progress': progress,
                                'video_url': video_url,
                                'user_course_id': user_course_id
                            }
                            courses.append(course_info)
                            self.logger.debug(f"添加必修课: {course_name} (进度: {progress}%)")
                        
                except Exception as e:
                    self.logger.warning(f"解析继续学习按钮时出错: {str(e)}")
                    continue
            
            # 策略2：查找课程详情链接 (保留原有逻辑作为备用)
            if not courses:
                self.logger.info("策略1未找到课程，尝试策略2：查找课程详情链接")
                course_detail_selectors = [
                    'a[href*="course_detail"]',
                    'a[href*="video_page"]',
                    'a[href*="study"]',
                    'a[href*="learn"]'
                ]
                
                for selector in course_detail_selectors:
                    course_links = self.page.locator(selector).all()
                    self.logger.info(f"使用选择器 '{selector}' 找到 {len(course_links)} 个链接")
                    
                    if course_links:
                        processed_course_ids = set()
                        
                        for link in course_links:
                            try:
                                href = link.get_attribute('href')
                                text = link.inner_text().strip()
                                
                                if not href or not text or text == '加载中...':
                                    continue
                                
                                # 提取course_id避免重复
                                course_id_match = re.search(r'id=(\d+)', href)
                                if course_id_match:
                                    course_id = course_id_match.group(1)
                                    if course_id in processed_course_ids:
                                        continue
                                    processed_course_ids.add(course_id)
                                
                                # 处理相对URL
                                if href.startswith('#/'):
                                    full_url = Config.BASE_URL.rstrip('#/') + href
                                else:
                                    full_url = href
                                
                                course_info = {
                                    'course_name': text,
                                    'course_type': 'required',
                                    'progress': 0.0,
                                    'video_url': full_url,
                                    'user_course_id': course_id if course_id_match else ''
                                }
                                
                                courses.append(course_info)
                                self.logger.debug(f"添加必修课: {text}")
                                
                            except Exception as e:
                                self.logger.warning(f"解析课程详情链接时出错: {str(e)}")
                                continue
                        
                        if courses:
                            break
            
            # 策略3：解析表格行数据
            if not courses:
                self.logger.info("前两个策略未找到课程，尝试策略3：解析表格数据")
                table_rows = self.page.locator('tbody tr, .el-table__row').all()
                self.logger.info(f"找到 {len(table_rows)} 个表格行")
                
                for row in table_rows:
                    try:
                        cells = row.locator('td, .el-table__cell').all()
                        if len(cells) >= 2:
                            # 假设第一列或第二列是课程名称
                            course_name = ""
                            for i, cell in enumerate(cells[:3]):
                                cell_text = cell.inner_text().strip()
                                if cell_text and len(cell_text) > 5 and '继续学习' not in cell_text:
                                    course_name = cell_text
                                    break
                            
                            # 查找该行中的继续学习按钮
                            learn_button = row.locator('button:has-text("继续学习"), a:has-text("继续学习")').first
                            if learn_button.count() > 0 and course_name:
                                href = learn_button.get_attribute('href')
                                onclick = learn_button.get_attribute('onclick')
                                
                                video_url = ""
                                user_course_id = ""
                                
                                if href:
                                    video_url = href if href.startswith('http') else Config.BASE_URL.rstrip('#/') + '/' + href.lstrip('#/')
                                elif onclick:
                                    id_match = re.search(r'[\'""](\d+)[\'\""]', onclick)
                                    if id_match:
                                        user_course_id = id_match.group(1)
                                        video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?user_course_id={user_course_id}"
                                
                                course_info = {
                                    'course_name': course_name,
                                    'course_type': 'required',
                                    'progress': 0.0,
                                    'video_url': video_url,
                                    'user_course_id': user_course_id
                                }
                                courses.append(course_info)
                                self.logger.debug(f"从表格添加必修课: {course_name}")
                    
                    except Exception as e:
                        self.logger.warning(f"解析表格行时出错: {str(e)}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"解析必修课程失败: {str(e)}")
            
        self.logger.info(f"必修课解析完成，共获取到 {len(courses)} 门课程")
        return courses
    
    def parse_elective_courses(self) -> List[Dict]:
        """解析选修课程列表（单节课程）"""
        courses = []
        
        try:
            # 直接访问选修课页面
            self.logger.info("访问选修课页面获取课程")
            self.page.goto(Config.ELECTIVE_COURSES_URL)
            self.page.wait_for_load_state('domcontentloaded')
            time.sleep(3)
            
            # 等待页面完全加载
            try:
                self.page.wait_for_selector('body', timeout=10000)
            except:
                pass
            
            self.logger.info("尝试多种选择器策略解析选修课程")
            
            # 策略1：解析表格中的选修课程（选修课页面是表格形式）
            table_rows = self.page.locator('tbody tr').all()
            self.logger.info(f"找到 {len(table_rows)} 个表格行")
            
            for row in table_rows:
                try:
                    # 获取课程名称（第一列，td.td_title）
                    title_cell = row.locator('td.td_title').first
                    if title_cell.count() == 0:
                        continue
                    
                    course_name = title_cell.inner_text().strip()
                    if not course_name or len(course_name) < 3:
                        continue
                    
                    # 获取学习进度（第二列中的百分比）
                    progress = 0.0
                    progress_element = row.locator('.el-progress__text').first
                    if progress_element.count() > 0:
                        progress_text = progress_element.inner_text().strip()
                        progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                        if progress_match:
                            progress = float(progress_match.group(1))
                    
                    # 检查播放按钮是否存在（表示可以学习），所有行都应该有播放功能
                    play_button = row.locator('td:has-text("播放")').first
                    has_play_button = play_button.count() > 0
                    
                    # 构造一个临时的视频URL（因为这种页面结构可能需要JavaScript交互）
                    # 实际的播放可能需要点击播放按钮来获取真实的URL
                    video_url = f"{Config.BASE_URL.rstrip('#/')}#/elective_course_play?name={course_name}"
                    
                    # 生成一个基于课程名称的临时ID
                    import hashlib
                    user_course_id = hashlib.md5(course_name.encode('utf-8')).hexdigest()[:8]
                    
                    course_info = {
                        'course_name': course_name,
                        'course_type': 'elective',
                        'progress': progress,
                        'video_url': video_url,
                        'user_course_id': user_course_id
                    }
                    
                    courses.append(course_info)
                    self.logger.debug(f"添加选修课: {course_name} (进度: {progress}%, 播放: {'是' if has_play_button else '否'})")
                    
                except Exception as e:
                    self.logger.warning(f"解析表格行时出错: {str(e)}")
                    continue
            
            # 策略2：如果策略1失败，尝试查找其他可能的课程元素
            if not courses:
                self.logger.info("策略1未找到课程，尝试策略2：查找其他课程元素")
                alternative_selectors = [
                    'a[href*="video_page"]',
                    'a[href*="study"]',
                    'a[href*="learn"]',
                    'button:has-text("学习")',
                    'button:has-text("观看")'
                ]
                
                for selector in alternative_selectors:
                    elements = self.page.locator(selector).all()
                    self.logger.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                    
                    if elements:
                        for element in elements:
                            try:
                                href = element.get_attribute('href')
                                text = element.inner_text().strip()
                                
                                if not href or not text or len(text) < 3:
                                    continue
                                
                                course_id_match = re.search(r'id=(\d+)', href) if href else None
                                course_id = course_id_match.group(1) if course_id_match else ''
                                
                                if href and href.startswith('#/'):
                                    full_url = Config.BASE_URL.rstrip('#/') + href
                                else:
                                    full_url = href or ''
                                
                                course_info = {
                                    'course_name': text,
                                    'course_type': 'elective',
                                    'progress': 0.0,
                                    'video_url': full_url,
                                    'user_course_id': course_id
                                }
                                
                                courses.append(course_info)
                                self.logger.debug(f"添加选修课: {text}")
                                
                            except Exception as e:
                                self.logger.warning(f"解析选修课元素时出错: {str(e)}")
                                continue
                        
                        if courses:
                            break
                    
        except Exception as e:
            self.logger.error(f"解析选修课程失败: {str(e)}")
            
        self.logger.info(f"选修课解析完成，共获取到 {len(courses)} 门课程")
        return courses
    
    def _extract_course_info(self, element, course_type: str) -> Dict:
        """从课程元素中提取课程信息"""
        try:
            course_info = {
                'course_name': '',
                'course_type': course_type,
                'progress': 0.0,
                'video_url': '',
                'user_course_id': ''
            }
            
            # 提取课程名称
            name_selectors = [
                '.course-title',
                '.course-name', 
                'h3',
                'h4',
                '[class*="title"]',
                '[class*="name"]'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = element.locator(selector).first
                    if name_element.count() > 0:
                        course_info['course_name'] = name_element.inner_text().strip()
                        break
                except:
                    continue
            
            # 如果没有找到标题，尝试获取链接文本或整个元素的文本
            if not course_info['course_name']:
                try:
                    # 尝试获取链接文本
                    link_element = element.locator('a').first
                    if link_element.count() > 0:
                        course_info['course_name'] = link_element.inner_text().strip()
                    else:
                        # 使用整个元素的文本
                        full_text = element.inner_text().strip()
                        # 取前50个字符作为课程名
                        course_info['course_name'] = full_text[:50] if full_text else ''
                except:
                    pass
            
            # 提取学习进度
            progress_selectors = [
                '[class*="progress"]',
                '[class*="percent"]',
                'text=/\\d+%/',
                'span:has-text("%")'
            ]
            
            for selector in progress_selectors:
                try:
                    progress_element = element.locator(selector).first
                    if progress_element.count() > 0:
                        progress_text = progress_element.inner_text()
                        # 提取百分比数字
                        progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                        if progress_match:
                            course_info['progress'] = float(progress_match.group(1))
                            break
                except:
                    continue
            
            # 提取视频链接和user_course_id
            link_selectors = [
                'a[href*="video_page"]',
                'a[href*="study"]',
                'a[href*="course"]',
                'a'
            ]
            
            for selector in link_selectors:
                try:
                    link_element = element.locator(selector).first
                    if link_element.count() > 0:
                        href = link_element.get_attribute('href')
                        if href:
                            # 处理相对URL
                            if href.startswith('#/'):
                                href = Config.BASE_URL.rstrip('#/') + href
                            elif href.startswith('/'):
                                base_url = '/'.join(Config.BASE_URL.split('/')[:3])
                                href = base_url + href
                            
                            course_info['video_url'] = href
                            
                            # 从URL中提取user_course_id
                            parsed_url = urlparse(href)
                            query_params = parse_qs(parsed_url.query)
                            if 'user_course_id' in query_params:
                                course_info['user_course_id'] = query_params['user_course_id'][0]
                            break
                except:
                    continue
            
            # 验证课程信息的有效性
            if course_info['course_name'] and len(course_info['course_name']) > 3:
                return course_info
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"提取课程信息失败: {str(e)}")
            return None
    
    def _parse_courses_generic(self, course_type: str) -> List[Dict]:
        """通用的课程解析方法"""
        courses = []
        
        try:
            # 获取页面中所有的链接
            links = self.page.locator('a').all()
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().strip()
                    
                    # 过滤掉明显不是课程的链接
                    if not href or not text or len(text) < 3:
                        continue
                        
                    if any(keyword in text.lower() for keyword in ['登录', '首页', '退出', '帮助']):
                        continue
                    
                    # 检查是否是视频页面链接
                    if 'video_page' in href or 'study' in href:
                        course_info = {
                            'course_name': text,
                            'course_type': course_type,
                            'progress': 0.0,
                            'video_url': href,
                            'user_course_id': ''
                        }
                        
                        # 处理相对URL
                        if href.startswith('#/'):
                            course_info['video_url'] = Config.BASE_URL.rstrip('#/') + href
                        
                        # 提取user_course_id
                        parsed_url = urlparse(href)
                        query_params = parse_qs(parsed_url.query)
                        if 'user_course_id' in query_params:
                            course_info['user_course_id'] = query_params['user_course_id'][0]
                        
                        courses.append(course_info)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.error(f"通用课程解析失败: {str(e)}")
            
        return courses
    
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
    
    def update_course_progress_from_page(self, course_id: int, video_url: str) -> float:
        """从视频页面更新课程进度"""
        try:
            self.page.goto(video_url)
            self.page.wait_for_load_state('networkidle')
            
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
                    progress_element = self.page.locator(selector).first
                    if progress_element.count() > 0:
                        progress_text = progress_element.inner_text()
                        progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                        if progress_match:
                            progress = float(progress_match.group(1))
                            db.update_course_progress(course_id, progress)
                            return progress
                except:
                    continue
            
            # 如果没有找到进度指示器，返回当前数据库中的进度
            courses = db.get_all_courses()
            for course in courses:
                if course['id'] == course_id:
                    return course['progress']
                    
            return 0.0
            
        except Exception as e:
            self.logger.error(f"更新课程进度失败: {str(e)}")
            return 0.0