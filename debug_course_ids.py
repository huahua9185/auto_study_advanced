#!/usr/bin/env python3
"""
调试脚本：分析课程页面结构，提取真实的课程ID和参数
用于理解必修课和选修课的不同URL格式
"""

import asyncio
import logging
import json
import time
from playwright.async_api import async_playwright, Page, Browser
from config.config import Config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CourseIDAnalyzer:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
    
    async def login(self):
        """登录系统"""
        try:
            logger.info("开始登录...")
            await self.page.goto(Config.LOGIN_URL)
            await self.page.wait_for_load_state('domcontentloaded')
            
            # 填写用户名和密码
            await self.page.fill('#username', Config.USERNAME)
            await self.page.fill('#password', Config.PASSWORD)
            
            # 等待验证码加载
            await asyncio.sleep(2)
            
            # 尝试识别并处理验证码
            captcha_attempts = 0
            max_attempts = 10
            
            while captcha_attempts < max_attempts:
                try:
                    # 检查验证码图片
                    captcha_img = self.page.locator('img[src*="captcha"], img[src*="verify"], img[src*="code"]')
                    if await captcha_img.count() > 0:
                        logger.info(f"第 {captcha_attempts + 1} 次验证码识别尝试")
                        
                        # 让用户手动输入验证码
                        input("请在浏览器中手动输入验证码，然后按回车继续...")
                        
                        # 点击登录按钮
                        login_btn = self.page.locator('button[type="submit"], input[type="submit"], button:has-text("登录")')
                        await login_btn.click()
                        await asyncio.sleep(3)
                        
                        # 检查是否登录成功
                        current_url = self.page.url
                        if 'login' not in current_url.lower():
                            logger.info("登录成功!")
                            return True
                            
                    captcha_attempts += 1
                    
                except Exception as e:
                    logger.warning(f"验证码处理出错: {str(e)}")
                    captcha_attempts += 1
                    continue
                    
            logger.error("登录失败，验证码尝试次数已达上限")
            return False
            
        except Exception as e:
            logger.error(f"登录过程出错: {str(e)}")
            return False
    
    async def analyze_required_courses(self):
        """分析必修课页面结构"""
        logger.info("分析必修课页面...")
        
        try:
            await self.page.goto(Config.REQUIRED_COURSES_URL)
            await self.page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)
            
            # 保存页面快照
            await self.page.screenshot(path='required_courses_debug.png')
            html = await self.page.content()
            with open('required_courses_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            analysis_results = {
                'page_type': 'required_courses',
                'url': self.page.url,
                'courses': []
            }
            
            # 分析继续学习按钮
            continue_buttons = await self.page.locator('div.btn:has-text("继续学习"), button:has-text("继续学习"), a:has-text("继续学习")').all()
            logger.info(f"找到 {len(continue_buttons)} 个'继续学习'按钮")
            
            for i, button in enumerate(continue_buttons):
                try:
                    # 获取父级元素
                    parent_li = button.locator('xpath=ancestor::li[1]')
                    if await parent_li.count() > 0:
                        # 获取课程名称
                        title_element = parent_li.locator('p.text_title')
                        course_name = ""
                        if await title_element.count() > 0:
                            course_name = await title_element.inner_text()
                        
                        # 获取所有属性
                        button_attrs = {
                            'href': await button.get_attribute('href'),
                            'onclick': await button.get_attribute('onclick'),
                            'data-id': await button.get_attribute('data-id'),
                            'data-course-id': await button.get_attribute('data-course-id'),
                            'data-user-course-id': await button.get_attribute('data-user-course-id'),
                            'id': await button.get_attribute('id'),
                            'class': await button.get_attribute('class')
                        }
                        
                        # 尝试点击按钮获取真实的URL
                        logger.info(f"尝试点击第 {i+1} 个按钮: {course_name}")
                        
                        # 监听页面导航
                        navigation_url = None
                        try:
                            # 记录点击前的URL
                            old_url = self.page.url
                            
                            # 点击按钮
                            await button.click()
                            await asyncio.sleep(2)
                            
                            # 检查URL变化
                            new_url = self.page.url
                            if new_url != old_url:
                                navigation_url = new_url
                                logger.info(f"点击后跳转到: {navigation_url}")
                                
                                # 返回到课程列表页面
                                await self.page.go_back()
                                await asyncio.sleep(2)
                            
                        except Exception as e:
                            logger.warning(f"点击按钮出错: {str(e)}")
                        
                        course_info = {
                            'course_name': course_name.strip(),
                            'button_index': i,
                            'button_attributes': button_attrs,
                            'navigation_url': navigation_url
                        }
                        
                        analysis_results['courses'].append(course_info)
                        
                except Exception as e:
                    logger.warning(f"分析按钮 {i} 时出错: {str(e)}")
                    continue
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"分析必修课页面失败: {str(e)}")
            return None
    
    async def analyze_elective_courses(self):
        """分析选修课页面结构"""
        logger.info("分析选修课页面...")
        
        try:
            await self.page.goto(Config.ELECTIVE_COURSES_URL)
            await self.page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)
            
            # 保存页面快照
            await self.page.screenshot(path='elective_courses_debug.png')
            html = await self.page.content()
            with open('elective_courses_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            analysis_results = {
                'page_type': 'elective_courses',
                'url': self.page.url,
                'courses': []
            }
            
            # 分析表格中的播放按钮
            table_rows = await self.page.locator('tbody tr').all()
            logger.info(f"找到 {len(table_rows)} 个表格行")
            
            for i, row in enumerate(table_rows[:5]):  # 只分析前5个
                try:
                    # 获取课程名称
                    title_cell = row.locator('td.td_title')
                    course_name = ""
                    if await title_cell.count() > 0:
                        course_name = await title_cell.inner_text()
                    
                    # 查找播放按钮或链接
                    play_elements = await row.locator('td:has-text("播放"), button:has-text("播放"), a:has-text("播放"), [onclick*="play"], [onclick*="video"]').all()
                    
                    course_info = {
                        'course_name': course_name.strip(),
                        'row_index': i,
                        'play_elements': []
                    }
                    
                    for j, element in enumerate(play_elements):
                        element_attrs = {
                            'tag_name': await element.evaluate('el => el.tagName.toLowerCase()'),
                            'href': await element.get_attribute('href'),
                            'onclick': await element.get_attribute('onclick'),
                            'data-id': await element.get_attribute('data-id'),
                            'data-course-id': await element.get_attribute('data-course-id'),
                            'data-user-course-id': await element.get_attribute('data-user-course-id'),
                            'id': await element.get_attribute('id'),
                            'class': await element.get_attribute('class'),
                            'inner_text': await element.inner_text()
                        }
                        
                        # 尝试点击获取真实URL
                        navigation_url = None
                        try:
                            old_url = self.page.url
                            await element.click()
                            await asyncio.sleep(2)
                            
                            new_url = self.page.url
                            if new_url != old_url:
                                navigation_url = new_url
                                logger.info(f"点击后跳转到: {navigation_url}")
                                
                                await self.page.go_back()
                                await asyncio.sleep(2)
                                
                        except Exception as e:
                            logger.warning(f"点击播放元素出错: {str(e)}")
                        
                        course_info['play_elements'].append({
                            'element_index': j,
                            'attributes': element_attrs,
                            'navigation_url': navigation_url
                        })
                    
                    analysis_results['courses'].append(course_info)
                    
                except Exception as e:
                    logger.warning(f"分析表格行 {i} 时出错: {str(e)}")
                    continue
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"分析选修课页面失败: {str(e)}")
            return None

async def main():
    """主函数"""
    analyzer = CourseIDAnalyzer()
    
    try:
        await analyzer.setup()
        
        # 登录
        if not await analyzer.login():
            logger.error("登录失败，无法继续分析")
            return
        
        results = {
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'required_courses': None,
            'elective_courses': None
        }
        
        # 分析必修课
        logger.info("=" * 50)
        required_analysis = await analyzer.analyze_required_courses()
        if required_analysis:
            results['required_courses'] = required_analysis
            logger.info(f"必修课分析完成，找到 {len(required_analysis['courses'])} 门课程")
        
        # 分析选修课
        logger.info("=" * 50)
        elective_analysis = await analyzer.analyze_elective_courses()
        if elective_analysis:
            results['elective_courses'] = elective_analysis
            logger.info(f"选修课分析完成，找到 {len(elective_analysis['courses'])} 门课程")
        
        # 保存分析结果
        with open('course_ids_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info("分析完成！结果已保存到 course_ids_analysis.json")
        
        # 等待用户查看结果
        input("分析完成，按回车关闭浏览器...")
        
    except Exception as e:
        logger.error(f"分析过程出错: {str(e)}")
        
    finally:
        await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())