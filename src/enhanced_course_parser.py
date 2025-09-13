from playwright.sync_api import Page
import logging
import re
import time
import requests
import json
from urllib.parse import urljoin, urlparse, parse_qs, quote
from typing import List, Dict
from config.config import Config
from src.database import db

class EnhancedCourseParser:
    """
    增强版课程解析器，支持不同类型课程的正确URL格式：
    - 必修课格式: #/video_page?id=10598&name=学员中心&user_course_id=1988340
    - 选修课格式: #/video_page?id=11362&user_course_id=1991630&name=学习中心
    
    解决了多标签页问题：
    - 默认情况下不点击按钮获取URL，避免打开多个标签页
    - 通过解析按钮属性（href, onclick, data-*）来获取必要的课程信息
    - 只在必要时才点击按钮获取真实URL
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        # 配置选项：是否允许点击按钮获取真实URL（默认关闭以避免多标签页）
        self.allow_button_click = False
        # 智能按钮点击模式：只对无法提取真实ID的课程启用点击
        self.smart_button_click = True
    
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
                    
                    # 提取按钮的各种属性和JavaScript代码（不点击按钮避免打开多个标签页）
                    button_data = self._extract_button_data(button, click_to_get_url=self.allow_button_click)
                    
                    # 构造必修课的正确视频URL
                    # 格式: #/video_page?id=课程ID&name=课程名称&user_course_id=用户课程ID
                    video_url, user_course_id, course_id = self._build_required_course_url(
                        course_name, button_data
                    )
                    
                    # 智能按钮点击模式：如果无法提取真实ID，则尝试点击按钮获取
                    if (self.smart_button_click and 
                        user_course_id and user_course_id.startswith('temp_')):
                        self.logger.info(f"课程 {course_name} 使用临时ID，尝试点击按钮获取真实ID")
                        try:
                            # 记录当前标签页数量
                            initial_pages = len(self.page.context.pages)
                            
                            # 使用按钮点击模式重新获取数据
                            button_data_with_click = self._extract_button_data(button, click_to_get_url=True)
                            
                            # 重新构造URL
                            new_video_url, new_user_course_id, new_course_id = self._build_required_course_url(
                                course_name, button_data_with_click
                            )
                            
                            # 如果获取到了真实ID，则使用新的数据
                            if (new_user_course_id and 
                                not new_user_course_id.startswith('temp_') and 
                                new_video_url):
                                video_url = new_video_url
                                user_course_id = new_user_course_id 
                                course_id = new_course_id
                                self.logger.info(f"成功获取课程 {course_name} 的真实ID: {user_course_id}")
                            
                            # 关闭可能打开的额外标签页（更安全的方式）
                            current_pages = len(self.page.context.pages)
                            if current_pages > initial_pages:
                                closed_count = 0
                                # 从最新的标签页开始关闭，保留原始标签页
                                for page_to_close in self.page.context.pages[initial_pages:]:
                                    try:
                                        if not page_to_close.is_closed():
                                            page_to_close.close()
                                            closed_count += 1
                                    except Exception as e:
                                        self.logger.debug(f"关闭标签页失败: {str(e)}")
                                        continue
                                
                                if closed_count > 0:
                                    self.logger.info(f"关闭了 {closed_count} 个额外标签页")
                                    time.sleep(1)  # 等待标签页完全关闭
                        
                        except Exception as e:
                            self.logger.warning(f"智能按钮点击失败: {str(e)}")
                    
                    if course_name and video_url:
                        course_info = {
                            'course_name': course_name,
                            'course_type': 'required',
                            'progress': progress,
                            'video_url': video_url,
                            'user_course_id': user_course_id,
                            'id': course_id,  # 修复：使用 'id' 作为字段名
                            'course_id': course_id,  # 保持兼容性
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
        """增强版选修课程解析，通过API获取真实的数字ID"""
        courses = []

        try:
            # 首先调用API获取所有选修课的真实数据
            api_courses = self._fetch_elective_courses_from_api()

            if api_courses:
                # 使用API数据构造课程信息
                for course_data in api_courses:
                    try:
                        course_name = course_data.get('course_name', '')
                        if not course_name:
                            continue

                        # 获取真实的数字ID
                        user_course_id = str(course_data.get('id', ''))  # API中的id字段是user_course_id
                        course_id = str(course_data.get('course_id', ''))  # API中的course_id字段

                        # 获取学习进度
                        progress = float(course_data.get('process', 0.0))

                        # 构造正确格式的视频URL
                        video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id={course_id}&user_course_id={user_course_id}&name=%E5%AD%A6%E4%B9%A0%E4%B8%AD%E5%BF%83"

                        course_info = {
                            'course_name': course_name,
                            'course_type': 'elective',
                            'progress': progress,
                            'video_url': video_url,
                            'user_course_id': user_course_id,
                            'id': course_id,  # 使用真实的course_id
                            'course_id': course_id,  # 保持兼容性
                        }
                        courses.append(course_info)
                        self.logger.debug(f"添加选修课: {course_name} (进度: {progress}%)")

                    except Exception as e:
                        self.logger.warning(f"处理API课程数据时出错: {str(e)}")
                        continue
            else:
                # API失败时的备用方案：使用原有的页面解析方法
                self.logger.warning("API获取失败，使用备用页面解析方案")
                return self._parse_elective_courses_fallback()

        except Exception as e:
            self.logger.error(f"解析选修课程失败: {str(e)}")

        self.logger.info(f"选修课解析完成，共获取到 {len(courses)} 门课程")
        return courses

    def _fetch_elective_courses_from_api(self) -> List[Dict]:
        """通过API获取选修课的真实数据"""
        try:
            # 获取cookies和headers
            cookies = self.page.context.cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

            # 构造请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://edu.nxgbjy.org.cn/nxxzxy/index.html',
                'token': '3ee5648315e911e7b2f200fff6167960',
                'Cache-Control': 'no-cache',
            }

            # API URL
            api_url = "https://edu.nxgbjy.org.cn/device/course!optional_course_list.do?course_type=1&current=1&limit=99999&terminal=1"

            self.logger.info("调用选修课API获取真实数据...")
            response = requests.get(api_url, headers=headers, cookies=cookie_dict, timeout=30)

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"API调用成功，响应状态: {response.status_code}")

                # 检查数据结构 - API返回的实际结构是 {"courses": [...]}
                if 'courses' in data and isinstance(data['courses'], list):
                    courses = data['courses']
                    self.logger.info(f"API返回 {len(courses)} 门选修课程")
                    return courses
                else:
                    self.logger.warning(f"API响应数据结构异常: {data.keys() if isinstance(data, dict) else 'non-dict response'}")
                    return []
            else:
                self.logger.error(f"API调用失败: {response.status_code} - {response.text}")
                return []

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API请求异常: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"API响应JSON解析失败: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"获取API数据时发生未知错误: {str(e)}")
            return []

    def _parse_elective_courses_fallback(self) -> List[Dict]:
        """API失败时的备用方案：使用原有的页面解析方法"""
        courses = []
        try:
            # 访问选修课程页面
            self.logger.info("使用备用方案访问选修课程页面")
            self.page.goto(Config.ELECTIVE_COURSES_URL)
            self.page.wait_for_load_state('domcontentloaded')
            time.sleep(3)

            # 等待表格加载
            self.page.wait_for_selector('tbody', timeout=10000)

            # 查找所有课程行
            table_rows = self.page.locator('tbody tr').all()
            self.logger.info(f"备用方案找到 {len(table_rows)} 行课程数据")

            for i, row in enumerate(table_rows):
                try:
                    # 提取课程名称
                    course_name_cell = row.locator('td.td_title').first
                    course_name = course_name_cell.inner_text().strip() if course_name_cell.count() > 0 else ""

                    if not course_name:
                        continue

                    # 提取学习进度
                    progress = 0.0
                    progress_cell = row.locator('td').nth(3)  # 第4列通常是进度
                    if progress_cell.count() > 0:
                        progress_text = progress_cell.inner_text().strip()
                        progress_match = re.search(r'(\d+(?:\.\d+)?)%', progress_text)
                        if progress_match:
                            progress = float(progress_match.group(1))

                    # 使用备用方法生成课程ID（基于行索引和课程名的哈希）
                    import hashlib
                    course_id = str(10000 + i)  # 简单的数字ID生成
                    user_course_id = str(2000000 + i)  # 简单的user_course_id生成

                    # 构造正确格式的视频URL
                    video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id={course_id}&user_course_id={user_course_id}&name=%E5%AD%A6%E4%B9%A0%E4%B8%AD%E5%BF%83"

                    course_info = {
                        'course_name': course_name,
                        'course_type': 'elective',
                        'progress': progress,
                        'video_url': video_url,
                        'user_course_id': user_course_id,
                        'id': course_id,
                        'course_id': course_id,
                    }
                    courses.append(course_info)
                    self.logger.debug(f"备用方案添加选修课: {course_name} (进度: {progress}%)")

                except Exception as e:
                    self.logger.warning(f"备用方案处理第{i+1}行课程时出错: {str(e)}")
                    continue

        except Exception as e:
            self.logger.error(f"备用方案解析选修课程失败: {str(e)}")

        self.logger.info(f"备用方案选修课解析完成，共获取到 {len(courses)} 门课程")
        return courses

    def _extract_button_data(self, button, click_to_get_url: bool = False) -> Dict:
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
            
            # 只在明确需要时才点击按钮获取URL（避免打开多个标签页）
            if click_to_get_url:
                try:
                    # 记录初始状态
                    initial_pages = len(self.page.context.pages)
                    current_url = self.page.url
                    current_page = self.page
                    
                    self.logger.debug(f"点击前URL: {current_url}, 标签页数: {initial_pages}")
                    
                    # 点击按钮
                    button.click()
                    time.sleep(3)
                    
                    # 检查是否创建了新标签页
                    current_pages = len(self.page.context.pages)
                    
                    if current_pages > initial_pages:
                        # 有新标签页被创建，切换到新标签页获取URL
                        new_page = self.page.context.pages[-1]
                        new_url = new_page.url
                        self.logger.info(f"新标签页URL: {new_url}")
                        
                        # 检查是否是学习页面
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
                        
                        # 关闭新标签页
                        new_page.close()
                        self.logger.debug("已关闭新标签页")
                        
                    else:
                        # 在当前页面跳转
                        new_url = current_page.url
                        if new_url != current_url:
                            self.logger.info(f"当前页面URL发生变化: {current_url} -> {new_url}")
                            
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
                            
                            # 返回课程列表页面
                            current_page.go_back()
                            time.sleep(2)
                        else:
                            self.logger.debug("点击按钮后URL未发生变化")
                        
                except Exception as e:
                    self.logger.warning(f"点击按钮获取URL失败: {str(e)}")
            else:
                # 不点击，仅从按钮属性中提取信息
                self.logger.debug("跳过点击按钮，仅从属性中提取信息")
            
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
            # 从href链接中提取ID
            elif attr_name == 'href' and attr_value and '#/video_page?' in attr_value:
                try:
                    if '?' in attr_value:
                        params_str = attr_value.split('?')[1]
                        for param in params_str.split('&'):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                if key == 'id':
                                    course_id = value
                                elif key == 'user_course_id':
                                    user_course_id = value
                except Exception as e:
                    self.logger.debug(f"解析href参数失败: {str(e)}")
            # 从onclick等JavaScript代码中提取ID
            elif attr_name == 'onclick' and attr_value:
                # 匹配各种可能的ID模式
                patterns = [
                    r'user_course_id[\s=:\'\"]*(\d+)',
                    r'userCourseId[\s=:\'\"]*(\d+)',
                    r'course_id[\s=:\'\"]*(\d+)',
                    r'courseId[\s=:\'\"]*(\d+)',
                    r'toVideoPage\([\'\"]?(\d+)[\'\"]?,?\s*[\'\"]?(\d+)?[\'\"]?\)',  # toVideoPage(id, user_course_id)
                    r'goToVideo\([\'\"]?(\d+)[\'\"]?,?\s*[\'\"]?(\d+)?[\'\"]?\)',   # goToVideo(id, user_course_id)
                    r'[\'\"](\d+)[\'\"]'  # 通用数字模式
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, attr_value)
                    if matches:
                        if 'user_course_id' in pattern.lower() or 'usercourse' in pattern.lower():
                            user_course_id = matches[0]
                        elif 'course_id' in pattern.lower() and 'user' not in pattern.lower():
                            course_id = matches[0]
                        elif 'toVideoPage' in pattern.lower() or 'goToVideo' in pattern.lower():
                            # 对于函数调用，第一个参数通常是course_id，第二个是user_course_id
                            if len(matches) >= 1 and matches[0] and len(matches[0]) >= 2:
                                if isinstance(matches[0], tuple):
                                    course_id = matches[0][0] if matches[0][0] else course_id
                                    user_course_id = matches[0][1] if matches[0][1] else user_course_id
                                else:
                                    course_id = matches[0] if not course_id else course_id
                        elif not user_course_id and not course_id:
                            user_course_id = matches[0] if isinstance(matches[0], str) else matches[0][0]
        
        # 构造必修课URL: #/video_page?id=课程ID&name=课程名称&user_course_id=用户课程ID
        if user_course_id and not user_course_id.startswith('temp_'):
            encoded_name = quote(course_name)
            
            if course_id:
                video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id={course_id}&name={encoded_name}&user_course_id={user_course_id}"
            else:
                video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?name={encoded_name}&user_course_id={user_course_id}"
        else:
            # 如果没有提取到真实ID，记录调试信息
            if not self.allow_button_click and not self.smart_button_click:
                self.logger.warning(f"课程 {course_name} 无法提取到真实ID，建议启用按钮点击模式")
            else:
                self.logger.debug(f"课程 {course_name} 将生成临时ID，智能按钮点击模式将尝试获取真实ID")
            
            # 生成临时ID和正确格式的URL作为后备方案 
            import hashlib
            temp_user_course_id = hashlib.md5(course_name.encode('utf-8')).hexdigest()[:8]
            video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?name={quote(course_name)}&user_course_id=temp_{temp_user_course_id}"
            user_course_id = f"temp_{temp_user_course_id}"
            
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
    
    def _get_elective_real_url(self, row, course_name: str, row_index: int) -> tuple:
        """获取选修课的真实URL - 改进版，避免点击按钮造成多标签页问题"""
        try:
            # 查找播放单元格（选修课的"播放"是span元素，不是真正的按钮）
            play_cell = row.locator('td.course_btn').first
            if play_cell.count() == 0:
                self.logger.warning(f"课程 {course_name} 未找到播放单元格")
                return self._generate_fallback_url(course_name)

            # 检查是否有播放span元素
            play_span = play_cell.locator('span:has-text("播放")').first
            if play_span.count() == 0:
                self.logger.warning(f"课程 {course_name} 未找到播放span元素")
                return self._generate_fallback_url(course_name)

            self.logger.debug(f"找到第 {row_index} 行的播放元素: {course_name}")

            # 尝试通过点击span获取真实URL，但使用更安全的方式
            navigation_url = None

            # 监听页面导航
            def capture_navigation(request):
                nonlocal navigation_url
                if 'video_page' in request.url:
                    navigation_url = request.url
                    self.logger.info(f"捕获到视频页面URL: {request.url}")

            self.page.on('request', capture_navigation)

            try:
                # 尝试点击播放span
                play_span.click(timeout=3000)
                time.sleep(2)

                # 检查当前页面URL是否变化
                current_url = self.page.url
                if 'video_page' in current_url:
                    navigation_url = current_url

            except Exception as click_error:
                self.logger.warning(f"点击播放元素失败: {click_error}")

            # 移除事件监听器
            try:
                self.page.remove_listener('request', capture_navigation)
            except:
                pass

            if navigation_url:
                self.logger.info(f"成功获取真实URL: {navigation_url}")
                user_course_id, course_id = self._extract_ids_from_url(navigation_url)

                # 如果当前页面已经跳转，返回选修课列表页面
                if 'video_page' in self.page.url:
                    self.page.goto(Config.ELECTIVE_COURSES_URL)
                    self.page.wait_for_load_state('domcontentloaded')
                    time.sleep(1)

                return navigation_url, user_course_id, course_id
            else:
                self.logger.warning(f"点击播放后未获取到有效URL，使用备用方案")
                return self._generate_fallback_url(course_name)

        except Exception as e:
            self.logger.warning(f"点击播放元素失败 {course_name}: {str(e)}")
            return self._generate_fallback_url(course_name)
    
    def _extract_ids_from_url(self, url: str) -> tuple:
        """从URL中提取user_course_id和course_id"""
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(url)
            # 处理hash片段中的查询参数
            if parsed.fragment:
                # 例如: #/video_page?id=123&user_course_id=456
                if '?' in parsed.fragment:
                    query_part = parsed.fragment.split('?', 1)[1]
                    params = parse_qs(query_part)
                    
                    user_course_id = params.get('user_course_id', [''])[0]
                    course_id = params.get('id', [''])[0]
                    
                    return user_course_id, course_id
            
            # 处理普通查询参数
            params = parse_qs(parsed.query)
            user_course_id = params.get('user_course_id', [''])[0]
            course_id = params.get('id', [''])[0]
            
            return user_course_id, course_id
            
        except Exception as e:
            self.logger.warning(f"从URL提取ID失败 {url}: {str(e)}")
            return "", ""
    
    def _generate_fallback_url(self, course_name: str) -> tuple:
        """生成备用的课程URL - 使用正确的选修课URL格式"""
        import hashlib

        # 生成基于课程名的唯一ID
        name_hash = hashlib.md5(course_name.encode('utf-8')).hexdigest()
        course_id = name_hash[:8]  # 简化ID，去掉前缀
        user_course_id = name_hash[8:16]

        # 构造选修课正确格式的URL: id在前，user_course_id在后，name固定为"学习中心"
        video_url = f"{Config.BASE_URL.rstrip('#/')}#/video_page?id={course_id}&user_course_id={user_course_id}&name=%E5%AD%A6%E4%B9%A0%E4%B8%AD%E5%BF%83"

        self.logger.info(f"生成备用URL: {video_url}")
        return video_url, user_course_id, course_id