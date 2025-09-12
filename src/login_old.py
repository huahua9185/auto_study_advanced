from playwright.sync_api import Browser, Page, sync_playwright
import logging
import time
from config.config import Config
from src.captcha_solver import captcha_solver

class LoginManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.browser = None
        self.page = None
        self.is_logged_in = False
        
    def init_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = sync_playwright().start()
            
            # 浏览器启动参数，增加反检测选项
            launch_options = {
                'headless': Config.HEADLESS,
                'slow_mo': 1000,  # 降低操作速度，更像人类行为
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-sandbox'
                ]
            }
            
            self.browser = self.playwright.firefox.launch(**launch_options)
            self.page = self.browser.new_page()
            
            # 设置页面超时
            self.page.set_default_timeout(Config.PAGE_LOAD_TIMEOUT)
            
            # 设置更真实的用户代理和viewport
            self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # 设置viewport
            self.page.set_viewport_size({"width": 1366, "height": 768})
            
            # 注入反检测脚本
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });
            """)
            
            self.logger.info("浏览器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {str(e)}")
            return False
    
    def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            if not self.page:
                return False
                
            # 访问主页
            self.page.goto(Config.BASE_URL)
            self.page.wait_for_load_state('networkidle')
            
            # 检查是否有登录相关的元素
            # 如果页面包含用户信息或者能访问需要登录的页面，说明已登录
            login_indicators = [
                'text=退出登录',
                'text=个人中心', 
                'text=我的学习',
                '[class*="user-info"]',
                '[class*="logout"]'
            ]
            
            for indicator in login_indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        self.is_logged_in = True
                        self.logger.info("检测到已登录状态")
                        return True
                except:
                    continue
            
            # 检查是否在登录页面
            login_page_indicators = [
                'input[name="username"]',
                'input[name="password"]', 
                'text=用户名',
                'text=密码',
                '[class*="captcha"]'
            ]
            
            for indicator in login_page_indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        self.logger.info("检测到登录页面，需要登录")
                        self.is_logged_in = False
                        return False
                except:
                    continue
                    
            # 尝试访问需要登录的页面来确认状态
            try:
                self.page.goto(Config.REQUIRED_COURSES_URL)
                self.page.wait_for_load_state('networkidle', timeout=10000)
                
                # 如果页面重定向到登录页面或显示未登录信息，说明未登录
                current_url = self.page.url
                if 'login' in current_url.lower() or '登录' in self.page.content():
                    self.is_logged_in = False
                    return False
                else:
                    self.is_logged_in = True
                    return True
                    
            except Exception as e:
                self.logger.warning(f"检查登录状态时发生错误: {str(e)}")
                self.is_logged_in = False
                return False
            
        except Exception as e:
            self.logger.error(f"检查登录状态失败: {str(e)}")
            return False
    
    def login(self, max_retries: int = 3) -> bool:
        """执行登录操作，带重试机制"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"开始登录流程 (尝试 {attempt + 1}/{max_retries})")
                
                if self._try_login():
                    return True
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"登录失败，{3}秒后重试...")
                        import time
                        time.sleep(3)
                    else:
                        self.logger.error("所有登录尝试都失败了")
                        return False
                        
            except Exception as e:
                self.logger.error(f"第 {attempt + 1} 次登录尝试发生错误: {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                continue
                
        return False
    
    def _try_login(self) -> bool:
        """单次登录尝试"""
        try:
            import random
            import time
            
            # 随机延时，模拟人类行为
            time.sleep(random.uniform(1, 3))
            
            # 访问主页，寻找登录入口
            self.page.goto(Config.BASE_URL)
            self.page.wait_for_load_state('networkidle')
            
            # 查找并点击登录按钮
            login_button_selectors = [
                'text=登录',
                'a[href*="login"]',
                '[class*="login"]',
                'button:has-text("登录")',
                '[title*="登录"]',
                '[id*="login"]'
            ]
            
            login_button_found = False
            for selector in login_button_selectors:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            # 模拟人类点击行为
                            element.hover()
                            time.sleep(random.uniform(0.5, 1.5))
                            element.click()
                            self.page.wait_for_load_state('networkidle')
                            login_button_found = True
                            self.logger.info(f"点击登录按钮: {selector}")
                            break
                    if login_button_found:
                        break
                except:
                    continue
            
            if not login_button_found:
                self.logger.warning("未找到登录按钮，可能已在登录页面")
            
            # 等待登录表单出现
            time.sleep(random.uniform(1, 2))
            
            # 查找并填写登录表单
            return self._fill_login_form()
            
        except Exception as e:
            self.logger.error(f"登录尝试失败: {str(e)}")
            return False
    
    def _fill_login_form(self) -> bool:
        """填写登录表单"""
        try:
            import random
            import time
            
            # 等待登录表单出现
            self.page.wait_for_selector('input[name="username"], input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]', timeout=10000)
            
            # 查找用户名输入框
            username_selectors = [
                'input[name="username"]',
                'input[name="user"]',
                'input[name="account"]', 
                'input[name="loginname"]',
                'input[placeholder*="用户名"]',
                'input[placeholder*="账号"]',
                'input[placeholder*="手机号"]',
                'input[placeholder*="邮箱"]'
            ]
            
            username_element = None
            for selector in username_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            username_element = element
                            self.logger.info(f"找到用户名输入框: {selector}")
                            break
                    if username_element:
                        break
                except:
                    continue
            
            if not username_element:
                raise Exception("未找到用户名输入框")
            
            # 模拟人类输入用户名
            username_element.click()
            time.sleep(random.uniform(0.5, 1.0))
            username_element.clear()
            time.sleep(random.uniform(0.2, 0.5))
            
            # 逐个字符输入，模拟真实打字
            for char in Config.USERNAME:
                username_element.type(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.logger.info("用户名输入完成")
            time.sleep(random.uniform(0.5, 1.0))
            
            # 查找密码输入框
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[name="passwd"]',
                'input[placeholder*="密码"]'
            ]
            
            password_element = None
            for selector in password_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            password_element = element
                            self.logger.info(f"找到密码输入框: {selector}")
                            break
                    if password_element:
                        break
                except:
                    continue
            
            if not password_element:
                raise Exception("未找到密码输入框")
            
            # 模拟人类输入密码
            password_element.click()
            time.sleep(random.uniform(0.5, 1.0))
            password_element.clear()
            time.sleep(random.uniform(0.2, 0.5))
            
            # 逐个字符输入密码
            for char in Config.PASSWORD:
                password_element.type(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.logger.info("密码输入完成")
            time.sleep(random.uniform(0.5, 1.0))
            
            # 处理验证码
            captcha_handled = self._handle_captcha()
            if not captcha_handled:
                self.logger.warning("验证码处理失败或未找到验证码")
            
            # 提交表单
            return self._submit_login_form()
            
        except Exception as e:
            self.logger.error(f"填写登录表单失败: {str(e)}")
            return False
    
    def _handle_captcha(self) -> bool:
        """处理验证码"""
        try:
            import random
            import time
            
            self.logger.info("检查是否需要验证码")
            
            # 首先查找验证码输入框
            captcha_input_selectors = [
                'a[href*="login"]',
                '[class*="login"]',
                'button:has-text("登录")'
            ]
            
            login_button_found = False
            for selector in login_button_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.page.click(selector)
                        self.page.wait_for_load_state('networkidle')
                        login_button_found = True
                        break
                except:
                    continue
            
            if not login_button_found:
                self.logger.warning("未找到登录按钮，可能已在登录页面")
            
            # 等待登录表单出现
            self.page.wait_for_selector('input[name="username"], input[type="text"]', timeout=10000)
            
            # 查找用户名和密码输入框
            username_selectors = [
                'input[name="username"]',
                'input[name="user"]',
                'input[name="account"]', 
                'input[placeholder*="用户名"]',
                'input[placeholder*="账号"]'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="密码"]'
            ]
            
            # 输入用户名
            username_element = None
            for selector in username_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        username_element = self.page.locator(selector).first
                        break
                except:
                    continue
            
            if not username_element:
                raise Exception("未找到用户名输入框")
            
            username_element.clear()
            username_element.fill(Config.USERNAME)
            self.logger.info("用户名输入完成")
            
            # 输入密码
            password_element = None
            for selector in password_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        password_element = self.page.locator(selector).first
                        break
                except:
                    continue
            
            if not password_element:
                raise Exception("未找到密码输入框")
            
            password_element.clear()
            password_element.fill(Config.PASSWORD)
            self.logger.info("密码输入完成")
            
            # 处理验证码
            self.logger.info("检查是否需要验证码")
            
            # 首先查找验证码输入框
            captcha_input_selectors = [
                'input[name="captcha"]',
                'input[name="verifycode"]',
                'input[name="code"]',
                'input[name="validatecode"]',
                'input[placeholder*="验证码"]',
                'input[placeholder*="校验码"]',
                'input[placeholder*="验证"]',
                'input[title*="验证码"]',
                'input[id*="captcha"]',
                'input[id*="verify"]',
                'input[class*="captcha"]',
                'input[class*="verify"]'
            ]
            
            captcha_input = None
            for selector in captcha_input_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            captcha_input = element
                            self.logger.info(f"找到验证码输入框: {selector}")
                            break
                except:
                    continue
            
            if captcha_input:
                self.logger.info("检测到验证码输入框，开始寻找验证码图片")
                
                # 查找验证码图片
                captcha_selectors = [
                    'img[src*="captcha"]',
                    'img[src*="verifycode"]',
                    'img[src*="code"]',
                    'img[src*="verify"]',
                    'img[alt*="验证码"]',
                    'img[title*="验证码"]',
                    '[class*="captcha"] img',
                    '[class*="verify"] img',
                    '[id*="captcha"] img',
                    '[id*="verify"] img',
                    'img',  # 作为最后的尝试
                ]
                
                captcha_image_element = None
                for selector in captcha_selectors:
                    try:
                        elements = self.page.locator(selector).all()
                        for element in elements:
                            if element.is_visible():
                                # 检查图片尺寸，验证码图片通常较小
                                bbox = element.bounding_box()
                                if bbox and 50 < bbox['width'] < 300 and 20 < bbox['height'] < 100:
                                    captcha_image_element = selector
                                    self.logger.info(f"找到验证码图片: {selector}")
                                    break
                        if captcha_image_element:
                            break
                    except:
                        continue
                
                if captcha_image_element:
                    try:
                        # 识别验证码
                        self.logger.info("开始识别验证码")
                        captcha_text = captcha_solver.solve_captcha_with_retry(
                            self.page, 
                            captcha_image_element,
                            refresh_selector=None
                        )
                        
                        # 输入验证码
                        captcha_input.clear()
                        captcha_input.fill(captcha_text)
                        self.logger.info(f"验证码输入完成: {captcha_text}")
                        
                    except Exception as e:
                        self.logger.error(f"验证码识别或输入失败: {str(e)}")
                        # 即使验证码识别失败，也尝试提交，让用户看到错误信息
                else:
                    self.logger.warning("未找到验证码图片，但存在验证码输入框")
                    
                    # 调试模式下截图
                    if Config.DEBUG_MODE:
                        try:
                            screenshot_path = "data/debug_login_page.png"
                            self.page.screenshot(path=screenshot_path)
                            self.logger.info(f"已保存调试截图: {screenshot_path}")
                        except:
                            pass
                    
                    # 尝试手动输入提示
                    self.logger.info("请手动查看浏览器窗口输入验证码，程序将等待30秒")
                    
                    # 等待用户手动输入验证码
                    import time
                    time.sleep(30)
                    
            else:
                self.logger.info("未检测到验证码输入框")
            
            # 提交登录表单
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("登录")',
                'button:has-text("提交")',
                '[class*="submit"]',
                '[class*="login-btn"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        submit_button = self.page.locator(selector).first
                        break
                except:
                    continue
            
            if not submit_button:
                # 尝试按回车键提交
                password_element.press('Enter')
            else:
                submit_button.click()
            
            self.logger.info("登录表单已提交")
            
            # 等待登录结果
            self.page.wait_for_load_state('networkidle')
            time.sleep(3)  # 额外等待时间
            
            # 检查登录是否成功
            if self.check_login_status():
                self.logger.info("登录成功！")
                return True
            else:
                # 检查是否有错误信息
                error_selectors = [
                    'text=用户名或密码错误',
                    'text=验证码错误',
                    'text=登录失败',
                    '[class*="error"]',
                    '[class*="fail"]'
                ]
                
                error_msg = "登录失败"
                for selector in error_selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            error_msg = self.page.locator(selector).first.inner_text()
                            break
                    except:
                        continue
                
                self.logger.error(f"登录失败: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"登录过程中发生错误: {str(e)}")
            return False
    
    def logout(self):
        """登出"""
        try:
            if not self.is_logged_in:
                return True
                
            logout_selectors = [
                'text=退出登录',
                'text=登出',
                'a[href*="logout"]',
                '[class*="logout"]'
            ]
            
            for selector in logout_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.page.click(selector)
                        self.page.wait_for_load_state('networkidle')
                        self.is_logged_in = False
                        self.logger.info("登出成功")
                        return True
                except:
                    continue
                    
            self.logger.warning("未找到登出按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"登出失败: {str(e)}")
            return False
    
    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.browser:
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
            self.logger.info("浏览器已关闭")
        except Exception as e:
            self.logger.error(f"关闭浏览器时发生错误: {str(e)}")

# 全局登录管理器实例
login_manager = LoginManager()