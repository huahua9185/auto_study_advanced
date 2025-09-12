from playwright.sync_api import Browser, Page, sync_playwright
import logging
import time
import random
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
            
            # Firefox 浏览器启动参数
            launch_options = {
                'headless': Config.HEADLESS,
                'slow_mo': 100,  # 减少操作延迟，原来1000ms太慢了
                'args': [
                    '--disable-web-security',
                    '--disable-extensions',
                    '--no-first-run'
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
            
            # 设置viewport，使用配置文件中的窗口大小
            self.page.set_viewport_size({"width": Config.VIEWPORT_WIDTH, "height": Config.VIEWPORT_HEIGHT})
            
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
            
            # 方法1：检查Cookie中是否有登录信息
            cookies = self.page.context.cookies()
            has_session = any('JSESSIONID' in cookie.get('name', '') or 
                            'token' in cookie.get('name', '').lower() or
                            'session' in cookie.get('name', '').lower()
                            for cookie in cookies)
            
            # 方法2：检查页面是否有错误提示（这表示登录失败）
            error_indicators = [
                'text=校验码错误',
                'text=验证码错误',
                'text=用户名或密码错误',
                'text=登录失败',
                '.el-message--error',
                '.el-notification--error'
            ]
            
            has_error = False
            for indicator in error_indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        if self.page.locator(indicator).first.is_visible():
                            has_error = True
                            self.logger.debug(f"检测到错误提示: {indicator}")
                            break
                except:
                    continue
            
            # 如果有错误提示，说明登录失败
            if has_error:
                self.is_logged_in = False
                return False
            
            # 方法3：检查登录表单是否还存在
            login_form_exists = False
            login_form_indicators = [
                'input[placeholder="用户名"]',
                'input[placeholder="密码"]',
                'input[placeholder="验证码"]',
                'button:has-text("登录")',
                'button.el-button.el-button--primary:has-text("登录")'
            ]
            
            visible_form_elements = 0
            for indicator in login_form_indicators:
                try:
                    elements = self.page.locator(indicator).all()
                    for element in elements:
                        if element.is_visible():
                            visible_form_elements += 1
                            break
                except:
                    continue
            
            # 如果登录表单元素超过3个还可见，说明还在登录页
            if visible_form_elements >= 3:
                login_form_exists = True
                self.logger.debug(f"检测到{visible_form_elements}个登录表单元素仍可见")
            
            # 方法4：尝试访问需要登录的页面
            # 如果没有错误且登录表单不可见，尝试访问个人中心
            if not has_error and not login_form_exists:
                try:
                    # 尝试点击个人中心或学习中心
                    nav_links = [
                        'text=我的学习',
                        'text=个人中心',
                        'text=学习中心'
                    ]
                    
                    for link in nav_links:
                        if self.page.locator(link).count() > 0:
                            # 尝试点击
                            self.page.locator(link).first.click()
                            self._smart_wait_for_page_load('networkidle', 5000)
                            
                            # 检查URL是否变化
                            new_url = self.page.url
                            if 'my_study' in new_url or 'study_center' in new_url or 'personal' in new_url:
                                self.is_logged_in = True
                                self.logger.info(f"登录成功，已进入: {link}")
                                return True
                            break
                except:
                    pass
            
            # 综合判断
            if not has_error and not login_form_exists and has_session:
                self.is_logged_in = True
                self.logger.info("登录成功（无错误、无登录表单、有Session）")
                return True
            
            # 尝试访问需要登录的页面来确认状态
            try:
                self.page.goto(Config.REQUIRED_COURSES_URL)
                self.page.wait_for_load_state('networkidle', timeout=10000)
                
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
    
    def login(self, max_retries: int = 3, max_captcha_retries: int = 3) -> bool:
        """
        稳定版本的登录方法 - 基于测试脚本的成功经验
        减少复杂的重试和页面重载，避免跳动
        """
        for main_attempt in range(max_retries):
            try:
                self.logger.info(f"开始登录流程 (尝试 {main_attempt + 1}/{max_retries})")
                
                # 简化的页面导航
                if not self._navigate_to_login_stable():
                    continue
                
                # 简化的登录尝试 - 基于测试脚本的方法
                for captcha_attempt in range(max_captcha_retries):
                    try:
                        self.logger.info(f"登录尝试 {captcha_attempt + 1}/{max_captcha_retries}")
                        
                        # 应用稳定性修复（已经禁用跳动操作）
                        self._apply_modal_stability_fixes()
                        
                        # 等待模态框稳定（已经禁用跳动操作）
                        self._wait_for_login_modal_stability(timeout_seconds=1)
                        
                        # 使用测试脚本中的稳定填写方法
                        if not self._fill_login_form_stable():
                            self.logger.warning("填写表单失败，重试")
                            continue
                        
                        # 使用测试脚本中的稳定提交方法
                        if not self._submit_login_form_stable():
                            continue
                        
                        # 简化的结果检查
                        login_result = self._check_login_result_simple()
                        
                        if login_result == "success":
                            self.logger.info("登录成功！")
                            return True
                        elif login_result == "captcha_error":
                            self.logger.warning(f"验证码错误 ({captcha_attempt + 1}/{max_captcha_retries})")
                            if captcha_attempt < max_captcha_retries - 1:
                                time.sleep(1)  # 短暂等待，避免页面操作冲突
                                continue
                        elif login_result == "auth_error":
                            self.logger.error("用户名或密码错误")
                            return False
                        else:
                            self.logger.warning(f"登录状态未知: {login_result}")
                            if captcha_attempt < max_captcha_retries - 1:
                                time.sleep(1)
                                continue
                        
                    except Exception as e:
                        self.logger.error(f"登录尝试 {captcha_attempt + 1} 异常: {str(e)}")
                        if captcha_attempt < max_captcha_retries - 1:
                            time.sleep(1)
                            continue
                
                # 主要重试之间的简化处理（避免页面重载引起的跳动）
                if main_attempt < max_retries - 1:
                    self.logger.warning("当前尝试失败，重新尝试...")
                    time.sleep(2)  # 短暂等待，让页面状态稳定
                    
            except Exception as e:
                self.logger.error(f"主要尝试 {main_attempt + 1} 异常: {str(e)}")
                if main_attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        
        self.logger.error("所有登录尝试都失败了")
        return False
    
    def _navigate_to_login(self) -> bool:
        """导航到登录页面"""
        try:
            self.logger.info("导航到登录页面")
            
            # 访问主页
            self.page.goto(Config.BASE_URL)
            # 简化等待：只等待DOM内容加载，不等待网络空闲
            try:
                self.page.wait_for_load_state('domcontentloaded', timeout=8000)
                time.sleep(2)  # Vue.js 渲染等待 - 参考仓库关键设计
                
                # 等待登录页面基本加载完成
                time.sleep(1)
                
            except:
                self.logger.debug("等待DOM加载超时，继续执行")
            
            # 查找并点击登录按钮 - 使用测试脚本中验证的简化版本
            login_button_selectors = [
                'text=登录', 
                'button:has-text("登录")'
            ]
            
            login_button_found = False
            for selector in login_button_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        login_button_found = True
                        self.logger.info(f"点击登录按钮成功: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"尝试登录按钮选择器失败 {selector}: {str(e)}")
                    continue
            
            if not login_button_found:
                self.logger.warning("未找到登录按钮")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"导航到登录页面失败: {str(e)}")
            return False
    
    def _fill_login_form(self) -> bool:
        """填写登录表单 - 按顺序填写用户名→密码→验证码"""
        try:
            # 按顺序填写表单字段，参考仓库的严格顺序
            if not self._fill_username():
                return False
            time.sleep(0.5)  # 字段间短暂等待
            
            if not self._fill_password():
                return False
            time.sleep(0.5)
            
            if not self._fill_captcha():
                return False
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"填写登录表单失败: {str(e)}")
            return False
    
    def _fill_captcha(self) -> bool:
        """填写验证码"""
        try:
            # 查找验证码输入框
            captcha_input_selectors = [
                'input[placeholder="验证码"].el-input__inner',
                'input[placeholder="验证码"]',
                'input[name="captcha"]',
                'input[name="verifycode"]',
                'input[placeholder*="验证码"]'
            ]
            
            captcha_input = None
            for selector in captcha_input_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        captcha_input = element
                        self.logger.debug(f"找到验证码输入框: {selector}")
                        break
                except:
                    continue
            
            if not captcha_input:
                self.logger.info("未检测到验证码输入框，跳过验证码")
                return True
            
            # 查找验证码图片
            captcha_image_selectors = [
                'img[src*="/device/login!get_auth_code.do"]',
                'img[src*="auth_code"]',
                'img[src*="captcha"]',
                'img[alt*="验证码"]'
            ]
            
            captcha_image = None
            for selector in captcha_image_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        captcha_image = element
                        self.logger.debug(f"找到验证码图片: {selector}")
                        break
                except:
                    continue
            
            if not captcha_image:
                self.logger.warning("未找到验证码图片")
                return False
            
            # 识别验证码
            from src.captcha_solver import captcha_solver
            captcha_text = captcha_solver.solve_captcha_from_element(self.page, captcha_image)
            
            if not captcha_text or len(captcha_text) != 4 or not captcha_text.isdigit():
                self.logger.warning(f"验证码识别失败或格式不正确: {captcha_text}")
                return False
            
            # 填写验证码
            captcha_input.click()
            captcha_input.fill("")  # 清空
            captcha_input.fill(captcha_text)
            
            # 验证填写结果
            filled_value = captcha_input.input_value()
            if filled_value == captcha_text:
                self.logger.info(f"验证码填写成功: {captcha_text}")
                return True
            else:
                self.logger.warning(f"验证码填写验证失败: 期望'{captcha_text}', 实际'{filled_value}'")
                return False
                
        except Exception as e:
            self.logger.error(f"填写验证码失败: {str(e)}")
            return False
    
    def _submit_login_form_and_wait(self) -> bool:
        """提交登录表单并等待响应"""
        try:
            # 查找提交按钮
            submit_selectors = [
                'button.el-button.el-button--primary:has-text("登录")',
                'button:has-text("登录")',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible() and element.is_enabled():
                        submit_button = element
                        break
                except:
                    continue
            
            # 提交表单
            if submit_button:
                submit_button.click()
                self.logger.info("点击登录按钮")
            else:
                # 备用方案：按回车键
                self.logger.info("未找到登录按钮，使用回车键提交")
                self.page.keyboard.press('Enter')
            
            # 等待服务器处理 - 参考仓库的关键等待
            time.sleep(2)  # 给服务器验证时间
            
            # 等待页面状态变化
            try:
                self._smart_wait_for_page_load('networkidle', 10000)
            except:
                pass  # 页面可能有动态内容，忽略超时
            
            time.sleep(1)  # 额外等待确保状态稳定
            
            return True
            
        except Exception as e:
            self.logger.error(f"提交登录表单失败: {str(e)}")
            return False
    
    def _check_detailed_login_result(self) -> str:
        """
        详细检查登录结果 - 参考仓库的多维度状态验证
        """
        try:
            # 检查是否有验证码错误 - 参考仓库的15+种选择器
            captcha_error_selectors = [
                'text=校验码错误',
                'text=验证码错误',
                'text=验证码不正确',
                '.el-message:has-text("验证码")',
                '.el-message--error:has-text("验证码")',
                '.el-message--error:has-text("校验码")',
                '.el-notification--error:has-text("验证码")',
                '.error-message:has-text("验证码")',
                '[class*="error"]:has-text("验证码")',
                '[class*="message"]:has-text("验证码")',
                'div:has-text("验证码错误")',
                'div:has-text("校验码错误")',
                'span:has-text("验证码错误")',
                'p:has-text("验证码错误")'
            ]
            
            for selector in captcha_error_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            self.logger.info(f"检测到验证码错误: {selector}")
                            return "captcha_error"
                except:
                    continue
            
            # 检查是否有用户名或密码错误
            auth_error_selectors = [
                'text=用户名或密码错误',
                'text=账号或密码错误', 
                'text=登录失败',
                '.el-message--error:has-text("用户")',
                '.el-message--error:has-text("密码")',
                '.el-message--error:has-text("账号")',
                '.el-message--error:has-text("登录失败")',
                'div:has-text("用户名或密码错误")',
                'div:has-text("账号或密码错误")'
            ]
            
            for selector in auth_error_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            self.logger.info(f"检测到认证错误: {selector}")
                            return "auth_error"
                except:
                    continue
            
            # 检查URL变化 - 参考仓库的关键检查
            current_url = self.page.url
            self.logger.debug(f"当前URL: {current_url}")
            
            # 检查是否跳转到了非登录页面（成功）
            if "requireAuth" not in current_url and "/login" not in current_url.lower():
                # 进一步确认用户信息元素
                user_info_selectors = [
                    '.user-info', 
                    '.username', 
                    'button:has-text("退出")',
                    '[class*="user"]',
                    '[class*="logout"]',
                    'text=退出登录'
                ]
                
                for selector in user_info_selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            element = self.page.locator(selector).first
                            if element.is_visible():
                                self.logger.info("检测到用户信息元素，登录成功")
                                return "success"
                    except:
                        continue
                
                # URL变化但没有用户信息元素，仍认为成功
                self.logger.info("URL已跳转，登录可能成功")
                return "success"
            
            # 检查表单状态 - 参考仓库的表单状态检测
            try:
                username_input = self.page.locator('input[placeholder="用户名"]').first
                captcha_input = self.page.locator('input[placeholder*="验证码"]').first
                
                username_value = ""
                captcha_value = ""
                
                if username_input.count() > 0:
                    username_value = username_input.input_value()
                if captcha_input.count() > 0:
                    captcha_value = captcha_input.input_value()
                
                self.logger.debug(f"表单状态 - 用户名: '{username_value}', 验证码: '{captcha_value}'")
                
                # 如果用户名还在但验证码被清空，通常是验证码错误
                if username_value and not captcha_value:
                    self.logger.info("表单状态显示验证码错误（验证码被清空）")
                    return "captcha_error"
                # 如果所有字段都被清空，可能是其他错误
                elif not username_value and not captcha_value:
                    self.logger.info("表单状态显示其他错误（所有字段被清空）")
                    return "other_error"
                    
            except Exception as e:
                self.logger.debug(f"检查表单状态失败: {str(e)}")
            
            # 默认情况
            self.logger.debug("未检测到明确的登录结果，返回unknown")
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"检查登录结果失败: {str(e)}")
            return "unknown"
    
    def _refresh_captcha_and_clear_form(self) -> None:
        """刷新验证码并清空表单 - 防跳动版本，跳过所有点击操作"""
        try:
            self.logger.info("刷新验证码并清空表单 (防跳动版本)")
            
            # 跳过所有会导致页面跳动的点击操作
            # 因为验证码刷新点击会导致页面重排和跳动
            self.logger.debug("跳过验证码图片点击刷新操作，避免页面跳动")
            
            # 仅清空验证码输入框，不进行点击刷新操作
            try:
                captcha_input = self.page.locator('input[placeholder*="验证码"]').first
                if captcha_input.count() > 0 and captcha_input.is_visible():
                    # 使用更温和的方式清空，避免不必要的点击
                    captcha_input.fill("")
                    self.logger.debug("清空验证码输入框")
            except Exception as e:
                self.logger.debug(f"清空验证码输入框失败: {str(e)}")
            
            # 由于跳过了刷新操作，提示用户可能需要手动处理验证码
            self.logger.info("已跳过验证码刷新操作以避免页面跳动，如需刷新验证码请手动操作")
                
        except Exception as e:
            self.logger.error(f"处理验证码表单失败: {str(e)}")
    
    def _try_login(self) -> bool:
        """单次登录尝试"""
        try:
            # 快速启动，减少等待时间
            time.sleep(0.3)
            
            # 访问主页，寻找登录入口
            self.page.goto(Config.BASE_URL)
            self._smart_wait_for_page_load('networkidle', 5000)
            
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
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            # 快速点击
                            element.click()
                            self._smart_wait_for_page_load('networkidle', 5000)
                            login_button_found = True
                            self.logger.info(f"点击登录按钮: {selector}")
                            break
                    if login_button_found:
                        break
                except:
                    continue
            
            if not login_button_found:
                self.logger.warning("未找到登录按钮，可能已在登录页面")
            
            # 快速等待登录表单出现
            time.sleep(0.2)
            
            # 查找并填写登录表单
            return self._fill_login_form()
            
        except Exception as e:
            self.logger.error(f"登录尝试失败: {str(e)}")
            return False
    
    def _fill_login_form(self) -> bool:
        """填写登录表单"""
        try:
            # 等待登录表单出现
            self.page.wait_for_selector('input[name="username"], input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]', timeout=10000)
            
            # 填写用户名
            if not self._fill_username():
                return False
            self._adaptive_wait(1, "用户名输入后")
            
            # 填写密码
            if not self._fill_password():
                return False
            self._adaptive_wait(1, "密码输入后")
            
            # 处理验证码
            self._smart_handle_captcha()
            self._adaptive_wait(1, "验证码输入后")
            
            # 提交表单
            return self._submit_login_form()
            
        except Exception as e:
            self.logger.error(f"填写登录表单失败: {str(e)}")
            return False
    
    def _smart_fill_input(self, input_type: str, selectors: list, value: str, 
                         timeout: int = 10, wait_after: float = 1.0) -> bool:
        """
        智能填写输入框
        
        Args:
            input_type: 输入框类型（用于日志）
            selectors: 选择器列表，按优先级排序
            value: 要填写的值
            timeout: 超时时间（秒）
            wait_after: 填写后等待时间（秒）
            
        Returns:
            bool: 填写成功返回True，失败返回False
        """
        try:
            self.logger.info(f"开始填写{input_type}")
            
            for attempt, selector in enumerate(selectors, 1):
                try:
                    self.logger.debug(f"尝试选择器 {attempt}/{len(selectors)}: {selector}")
                    
                    # 等待元素出现
                    element = self.page.wait_for_selector(selector, timeout=timeout * 1000)
                    if not element:
                        self.logger.debug(f"选择器未匹配到元素: {selector}")
                        continue
                    
                    # 检查元素是否可见和可用
                    if not element.is_visible():
                        self.logger.debug(f"元素不可见: {selector}")
                        continue
                        
                    if not element.is_enabled():
                        self.logger.debug(f"元素不可用: {selector}")
                        continue
                    
                    # 跳过滚动操作避免页面跳动
                    # element.scroll_into_view_if_needed()  # 注释掉可能导致页面跳动的滚动操作
                    # self.page.wait_for_timeout(200)  # 注释掉相关等待
                    
                    # 清空现有内容（使用更温和的方式）
                    element.click()  # 先点击获取焦点
                    element.fill("")  # 清空
                    
                    # 填写新内容
                    element.fill(value)
                    
                    # 验证填写是否成功
                    filled_value = element.input_value()
                    if filled_value == value:
                        self.logger.info(f"{input_type}填写成功，使用选择器: {selector}")
                        
                        # 跳过事件触发操作避免页面跳动
                        # element.dispatch_event('change')  # 注释掉可能导致页面重排的事件
                        # element.dispatch_event('input')   # 注释掉可能导致页面重排的事件  
                        # element.dispatch_event('blur')    # 注释掉可能导致页面重排的事件
                        
                        # 使用自适应等待
                        if wait_after > 0:
                            self._adaptive_wait(wait_after, f"{input_type}填写后")
                        
                        return True
                    else:
                        self.logger.warning(f"{input_type}填写验证失败: 期望'{value}', 实际'{filled_value}'")
                        
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 填写失败: {str(e)}")
                    continue
            
            self.logger.error(f"{input_type}填写失败：所有选择器都无法工作")
            return False
            
        except Exception as e:
            self.logger.error(f"{input_type}填写过程出错: {str(e)}")
            return False
    
    def _find_element_by_selectors(self, element_type: str, selectors: list, timeout: int = 10):
        """
        通过选择器列表查找元素
        
        Args:
            element_type: 元素类型（用于日志）
            selectors: 选择器列表
            timeout: 超时时间（秒）
            
        Returns:
            找到的元素对象，失败返回None
        """
        try:
            for attempt, selector in enumerate(selectors, 1):
                try:
                    self.logger.debug(f"查找{element_type} - 尝试选择器 {attempt}/{len(selectors)}: {selector}")
                    
                    # 等待元素出现
                    element = self.page.wait_for_selector(selector, timeout=timeout * 1000)
                    if not element:
                        continue
                    
                    # 检查元素是否可见
                    if element.is_visible():
                        self.logger.info(f"找到{element_type}，使用选择器: {selector}")
                        return element
                    else:
                        self.logger.debug(f"元素不可见: {selector}")
                        
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 查找失败: {str(e)}")
                    continue
            
            self.logger.warning(f"未找到{element_type}：所有选择器都无法匹配")
            return None
            
        except Exception as e:
            self.logger.error(f"查找{element_type}过程出错: {str(e)}")
            return None
    
    def _find_captcha_image(self, selectors: list, timeout: int = 10):
        """
        查找验证码图片元素
        
        Args:
            selectors: 选择器列表
            timeout: 超时时间（秒）
            
        Returns:
            包含元素信息的字典，失败返回None
        """
        try:
            for attempt, selector in enumerate(selectors, 1):
                try:
                    self.logger.debug(f"查找验证码图片 - 尝试选择器 {attempt}/{len(selectors)}: {selector}")
                    
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            # 检查图片尺寸
                            bbox = element.bounding_box()
                            if bbox and 50 < bbox['width'] < 300 and 20 < bbox['height'] < 100:
                                self.logger.info(f"找到验证码图片: {selector}, 尺寸: {bbox['width']}x{bbox['height']}")
                                return {
                                    "element": element,
                                    "selector": selector,
                                    "width": bbox['width'],
                                    "height": bbox['height']
                                }
                        
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 查找失败: {str(e)}")
                    continue
            
            self.logger.warning("未找到验证码图片：所有选择器都无法匹配")
            return None
            
        except Exception as e:
            self.logger.error(f"查找验证码图片过程出错: {str(e)}")
            return None
    
    def _analyze_login_failure(self) -> dict:
        """
        分析登录失败的原因
        
        Returns:
            包含失败原因分析的字典
        """
        try:
            failure_info = {
                'type': 'unknown',
                'message': '未知错误',
                'retry_strategy': 'normal',
                'retry_delay': 5
            }
            
            # 检查是否有验证码错误
            captcha_error_selectors = [
                'text=校验码错误',
                'text=验证码错误',
                'text=验证码不正确',
                '.el-message--error:has-text("验证码")',
                '.el-message--error:has-text("校验码")',
                '.error-message:has-text("验证码")'
            ]
            
            for selector in captcha_error_selectors:
                if self.page.locator(selector).count() > 0:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        failure_info.update({
                            'type': 'captcha_error',
                            'message': '验证码错误',
                            'retry_strategy': 'refresh_captcha',
                            'retry_delay': 2
                        })
                        self.logger.info("检测到验证码错误")
                        return failure_info
            
            # 检查是否有用户名密码错误
            auth_error_selectors = [
                'text=用户名或密码错误',
                'text=账号或密码错误', 
                'text=登录失败',
                '.el-message--error:has-text("用户")',
                '.el-message--error:has-text("密码")',
                '.el-message--error:has-text("账号")'
            ]
            
            for selector in auth_error_selectors:
                if self.page.locator(selector).count() > 0:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        failure_info.update({
                            'type': 'auth_error',
                            'message': '用户名或密码错误',
                            'retry_strategy': 'check_credentials',
                            'retry_delay': 10
                        })
                        self.logger.info("检测到用户名或密码错误")
                        return failure_info
            
            # 检查是否有网络或服务器错误
            network_error_selectors = [
                'text=网络错误',
                'text=服务器错误',
                'text=连接超时',
                '.el-message--error:has-text("网络")',
                '.el-message--error:has-text("超时")',
                '.el-message--error:has-text("服务器")'
            ]
            
            for selector in network_error_selectors:
                if self.page.locator(selector).count() > 0:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        failure_info.update({
                            'type': 'network_error',
                            'message': '网络或服务器错误',
                            'retry_strategy': 'retry_with_delay',
                            'retry_delay': 15
                        })
                        self.logger.info("检测到网络或服务器错误")
                        return failure_info
            
            # 检查页面加载状态
            current_url = self.page.url
            if 'login' in current_url.lower():
                failure_info.update({
                    'type': 'form_error',
                    'message': '表单提交失败或页面未跳转',
                    'retry_strategy': 'reload_page',
                    'retry_delay': 3
                })
                self.logger.info("检测到表单提交失败")
            
            return failure_info
            
        except Exception as e:
            self.logger.error(f"分析登录失败原因时出错: {str(e)}")
            return {
                'type': 'unknown',
                'message': '分析失败原因时出错',
                'retry_strategy': 'normal',
                'retry_delay': 5
            }
    
    def _handle_captcha_error_retry(self, delay: int):
        """处理验证码错误的重试策略"""
        self.logger.info(f"验证码错误重试策略: 等待{delay}秒后继续")
        time.sleep(delay)
        # 不需要刷新页面，只需等待
    
    def _handle_auth_error_retry(self, delay: int):
        """处理认证错误的重试策略"""
        self.logger.warning(f"认证错误重试策略: 等待{delay}秒后重新加载页面")
        self.page.goto(Config.BASE_URL)
        self._smart_wait_for_page_load('networkidle', 5000)
        time.sleep(delay)
    
    def _handle_network_error_retry(self, delay: int):
        """处理网络错误的重试策略"""
        self.logger.info(f"网络错误重试策略: 等待{delay}秒后重新连接")
        try:
            # 关闭当前页面
            if self.page and not self.page.is_closed():
                self.page.close()
            
            # 创建新页面并重新配置
            self.page = self.browser.new_page()
            
            # 重新设置页面超时
            self.page.set_default_timeout(Config.PAGE_LOAD_TIMEOUT)
            
            # 重新设置HTTP headers
            self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # 重新设置viewport
            self.page.set_viewport_size({"width": 1366, "height": 768})
            
        except Exception as e:
            self.logger.error(f"重新创建页面失败: {str(e)}")
        
        time.sleep(delay)
    
    def _handle_form_error_retry(self, delay: int):
        """处理表单错误的重试策略"""
        self.logger.info(f"表单错误重试策略: 等待{delay}秒后重新加载页面")
        self.page.goto(Config.BASE_URL)
        self._smart_wait_for_page_load('networkidle', 5000)
        time.sleep(delay)
    
    def _handle_default_retry(self, delay: int):
        """默认重试策略"""
        self.logger.info(f"默认重试策略: 等待{delay}秒后重新加载页面")
        self.page.goto(Config.BASE_URL)
        self._smart_wait_for_page_load('networkidle', 5000)
        time.sleep(delay)
    
    def _smart_wait_for_page_load(self, expected_state: str = 'networkidle', 
                                 base_timeout: int = 5000, max_attempts: int = 3) -> bool:
        """
        智能等待页面加载
        
        Args:
            expected_state: 期望的页面状态
            base_timeout: 基础超时时间（毫秒）
            max_attempts: 最大尝试次数
            
        Returns:
            bool: 是否成功等待到期望状态
        """
        try:
            for attempt in range(max_attempts):
                try:
                    # 动态调整超时时间
                    timeout = base_timeout * (attempt + 1)
                    self.logger.debug(f"等待页面加载 - 尝试 {attempt + 1}/{max_attempts}, 超时: {timeout}ms")
                    
                    # 等待页面状态
                    self.page.wait_for_load_state(expected_state, timeout=timeout)
                    
                    # 额外检查页面是否真正就绪
                    if self._check_page_ready():
                        self.logger.debug("页面加载完成且就绪")
                        return True
                    else:
                        self.logger.debug("页面加载完成但未就绪，继续等待")
                        
                except Exception as e:
                    self.logger.debug(f"等待页面加载失败 (尝试 {attempt + 1}): {str(e)}")
                    if attempt < max_attempts - 1:
                        # 短暂等待后重试
                        time.sleep(1)
                        continue
            
            self.logger.warning("页面加载等待超时")
            return False
            
        except Exception as e:
            self.logger.error(f"智能等待页面加载失败: {str(e)}")
            return False
    
    def _check_page_ready(self) -> bool:
        """
        检查页面是否真正就绪
        
        Returns:
            bool: 页面是否就绪
        """
        try:
            # 检查是否有loading指示器
            # 注意：移除了'text=加载中'，因为页面上可能有固定的"加载中"文字
            loading_selectors = [
                '.el-loading-mask',
                '.el-loading-parent--relative',
                '.el-loading-spinner',
                '[class*="el-loading"]'
            ]
            
            for selector in loading_selectors:
                if self.page.locator(selector).count() > 0:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        self.logger.debug(f"检测到加载指示器: {selector}")
                        return False
            
            # 检查页面是否有基本的可交互元素
            basic_selectors = [
                'input',
                'button',
                'a',
                'form'
            ]
            
            has_interactive_elements = False
            for selector in basic_selectors:
                if self.page.locator(selector).count() > 0:
                    has_interactive_elements = True
                    break
            
            if not has_interactive_elements:
                self.logger.debug("页面缺少基本交互元素")
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"检查页面就绪状态失败: {str(e)}")
            return True  # 出错时假设页面就绪
    
    def _adaptive_wait(self, base_delay: float, context: str = "操作") -> None:
        """
        自适应等待策略
        
        Args:
            base_delay: 基础延迟时间（秒）
            context: 操作上下文（用于日志）
        """
        try:
            # 检查网络状况并调整等待时间
            adjusted_delay = base_delay
            
            # 检查页面加载状态
            if not self._check_page_ready():
                adjusted_delay *= 1.5  # 页面未就绪时增加等待时间
                self.logger.debug(f"{context}: 页面未就绪，延长等待时间至 {adjusted_delay:.1f}秒")
            
            # 检查是否有错误或警告信息
            error_selectors = [
                '.el-message--error',
                '.el-message--warning',
                '[class*="error"]'
            ]
            
            has_messages = False
            for selector in error_selectors:
                if self.page.locator(selector).count() > 0:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        has_messages = True
                        break
            
            if has_messages:
                adjusted_delay *= 0.8  # 有错误消息时稍微减少等待时间
                self.logger.debug(f"{context}: 检测到消息提示，调整等待时间至 {adjusted_delay:.1f}秒")
            
            self.logger.debug(f"{context}: 等待 {adjusted_delay:.1f}秒")
            time.sleep(adjusted_delay)
            
        except Exception as e:
            self.logger.debug(f"自适应等待失败: {str(e)}, 使用基础延迟 {base_delay}秒")
            time.sleep(base_delay)
    
    def _fill_username(self) -> bool:
        """填写用户名 - 使用测试脚本中验证的简化版本"""
        selectors = ['input[placeholder*="用户名"]']
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.count() > 0 and element.is_visible():
                    element.click()
                    element.fill(Config.USERNAME)
                    self.logger.info(f"用户名填写成功，使用选择器: {selector}")
                    return True
            except Exception as e:
                self.logger.debug(f"用户名选择器 {selector} 填写失败: {str(e)}")
                continue
        
        self.logger.error("用户名填写失败：未找到用户名输入框")
        return False
    
    def _fill_password(self) -> bool:
        """填写密码 - 使用测试脚本中验证的简化版本"""
        selectors = ['input[type="password"]']
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.count() > 0 and element.is_visible():
                    element.click()
                    element.fill(Config.PASSWORD)
                    self.logger.info(f"密码填写成功，使用选择器: {selector}")
                    return True
            except Exception as e:
                self.logger.debug(f"密码选择器 {selector} 填写失败: {str(e)}")
                continue
        
        self.logger.error("密码填写失败：未找到密码输入框")
        return False
    
    def _smart_handle_captcha(self) -> bool:
        """智能处理验证码"""
        try:
            self.logger.info("开始智能验证码处理")
            
            # 定义验证码输入框选择器（按优先级排序）
            captcha_input_selectors = [
                'input[placeholder="验证码"].el-input__inner',  # 精确匹配调试发现的选择器
                'input[placeholder="验证码"]',
                'input[name="captcha"]',
                'input[name="verifycode"]',
                'input[name="code"]',
                'input[name="validatecode"]',
                'input[placeholder*="校验码"]',
                'input[placeholder*="验证"]',
                'input[title*="验证码"]',
                'input[id*="captcha"]',
                'input[id*="verify"]',
                'input[class*="captcha"]',
                'input[class*="verify"]'
            ]
            
            # 检查是否有验证码输入框
            captcha_input_element = self._find_element_by_selectors(
                "验证码输入框", captcha_input_selectors
            )
            
            if not captcha_input_element:
                self.logger.info("未检测到验证码输入框")
                return True
            
            # 查找验证码图片
            captcha_image_selectors = [
                'img[src*="/device/login!get_auth_code.do"]',  # 精确匹配调试发现的验证码URL
                'img[src*="captcha"]',
                'img[src*="verifycode"]',
                'img[src*="code"]',
                'img[src*="verify"]',
                'img[alt*="验证码"]',
                'img[title*="验证码"]',
                '[class*="captcha"] img',
                '[class*="verify"] img',
                '[id*="captcha"] img',
                '[id*="verify"] img'
            ]
            
            # 查找验证码图片元素
            captcha_image_element = self._find_captcha_image(captcha_image_selectors)
            
            if captcha_image_element:
                try:
                    # 识别验证码
                    self.logger.info("开始识别4位数字验证码")
                    captcha_text = captcha_solver.solve_captcha_with_retry(
                        self.page, 
                        captcha_image_element["selector"],
                        refresh_selector=captcha_image_element["selector"]  # 可以点击图片刷新
                    )
                    
                    # 验证结果是否为4位数字
                    if len(captcha_text) != 4 or not captcha_text.isdigit():
                        self.logger.warning(f"验证码格式不正确: {captcha_text}，应为4位数字")
                        # 尝试重新识别一次
                        captcha_text = captcha_solver.solve_captcha_from_element(self.page, captcha_image_element["selector"])
                        captcha_text = captcha_solver._post_process_result(captcha_text)
                        
                        if len(captcha_text) != 4 or not captcha_text.isdigit():
                            self.logger.error(f"验证码仍然不符合规则: {captcha_text}")
                            return False
                    
                    # 使用智能填写方法输入验证码
                    success = self._smart_fill_input(
                        input_type="验证码",
                        selectors=[
                            'input[placeholder="验证码"].el-input__inner',  # 精确匹配调试发现的选择器
                            'input[placeholder="验证码"]'
                        ],
                        value=captcha_text,
                        wait_after=1.0
                    )
                    
                    if success:
                        self.logger.info(f"验证码输入完成: {captcha_text}")
                        return True
                    else:
                        self.logger.error("验证码输入失败")
                        return False
                    
                except Exception as e:
                    self.logger.error(f"验证码识别或输入失败: {str(e)}")
                    return False
            else:
                self.logger.warning("检测到验证码输入框但未找到验证码图片")
                
                # 调试模式下截图
                if hasattr(Config, 'DEBUG_MODE') and Config.DEBUG_MODE:
                    try:
                        screenshot_path = "data/debug_captcha_page.png"
                        self.page.screenshot(path=screenshot_path)
                        self.logger.info(f"已保存调试截图: {screenshot_path}")
                    except:
                        pass
                
                # 减少手动输入等待时间
                self.logger.info("请手动输入验证码，程序将等待10秒")
                time.sleep(10)
                return True
                
        except Exception as e:
            self.logger.error(f"处理验证码失败: {str(e)}")
            return False
    
    def _submit_login_form(self) -> bool:
        """智能提交登录表单"""
        try:
            submit_selectors = [
                'button.el-button.el-button--primary:has-text("登录")',  # 精确匹配调试发现的登录按钮
                'button:has-text("登录")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("提交")',
                'button:has-text("确定")',
                '[class*="submit"]',
                '[class*="login-btn"]',
                '[id*="submit"]',
                '[id*="login"]'
            ]
            
            # 使用智能查找方法
            submit_button = self._find_element_by_selectors("提交按钮", submit_selectors)
            
            # 提交表单
            if submit_button:
                # 滚动到按钮可见区域
                submit_button.scroll_into_view_if_needed()
                self.page.wait_for_timeout(200)
                
                # 确保按钮可用
                if submit_button.is_enabled():
                    submit_button.click()
                    self.logger.info("登录表单已提交（通过点击按钮）")
                else:
                    self.logger.warning("提交按钮不可用，尝试按回车键")
                    self.page.keyboard.press('Enter')
                    self.logger.info("登录表单已提交（通过回车键）")
            else:
                # 尝试按回车键提交
                self.logger.info("未找到提交按钮，尝试按回车键")
                self.page.keyboard.press('Enter')
                self.logger.info("登录表单已提交（通过回车键）")
            
            # 快速等待登录结果
            self._smart_wait_for_page_load('networkidle', 5000)
            time.sleep(0.5)  # 进一步减少等待时间
            
            # 检查登录是否成功
            if self.check_login_status():
                self.logger.info("登录成功！")
                return True
            else:
                # 先检查是否还在加载中
                loading_indicators = [
                    '.el-loading-mask',
                    '.el-loading-parent--relative',
                    '.el-loading-spinner',
                    '[class*="el-loading"]'
                ]
                
                for indicator in loading_indicators:
                    try:
                        if self.page.locator(indicator).count() > 0:
                            self.logger.info("页面仍在加载中，等待...")
                            time.sleep(2)
                            # 再次检查登录状态
                            if self.check_login_status():
                                self.logger.info("登录成功！")
                                return True
                            break
                    except:
                        continue
                
                # 检查是否有错误信息
                error_selectors = [
                    'text=用户名或密码错误',
                    'text=验证码错误',
                    'text=登录失败',
                    '[class*="error"]',
                    '[class*="fail"]',
                    'text=验证码不允许为空'
                ]
                
                error_msg = "登录失败"
                for selector in error_selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            error_element = self.page.locator(selector).first
                            if error_element.is_visible():
                                error_msg = error_element.inner_text()
                                break
                    except:
                        continue
                
                self.logger.error(f"登录失败: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"提交登录表单失败: {str(e)}")
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
                        self._smart_wait_for_page_load('networkidle', 5000)
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
    
    def _wait_for_login_modal_stability(self, timeout_seconds=3):
        """
        等待登录模态框稳定 - 完全禁用版本，避免任何导致跳动的DOM操作
        """
        try:
            self.logger.info("等待登录模态框稳定（无跳动版本）...")
            
            # 检查页面是否可用
            if not self.page:
                self.logger.error("页面对象为空，无法执行稳定性检查")
                return False
            
            # 仅进行基本的等待，不执行任何DOM修改操作
            # 因为所有的DOM操作（修改样式、位置等）都会导致页面重排和跳动
            time.sleep(1)  # 基本等待，让模态框自然完成加载
            
            # 仅检查模态框是否存在，不进行任何修改
            try:
                modal_exists = self.page.evaluate('() => document.querySelector(".el-dialog") !== null')
                if modal_exists:
                    self.logger.debug("模态框检测完成")
                else:
                    self.logger.debug("未检测到模态框")
            except Exception as e:
                self.logger.debug(f"模态框检测异常: {e}")
            
            # 跳过所有会导致跳动的DOM操作：
            # - 不修改zIndex
            # - 不强制设置对话框位置
            # - 不禁用输入框动画
            # - 不预设验证码尺寸
            # - 不进行最终稳定性检查
            
            self.logger.debug("跳过所有DOM操作，避免页面跳动")
            return True
            
        except Exception as e:
            self.logger.error(f"等待模态框稳定时发生异常: {e}")
            return False
    
    def _apply_modal_stability_fixes(self):
        """应用基于分析结果的模态框稳定性修复 - 完全禁用版本，避免任何DOM操作"""
        try:
            # 完全跳过此方法，不执行任何DOM操作
            # 因为创建和添加style元素本身会导致页面重排
            self.logger.debug("跳过CSS稳定性修复，避免DOM操作引起的页面跳动")
            return True  # 返回True表示"成功"（实际是跳过）
        except Exception as e:
            self.logger.debug(f"应用模态框稳定性修复失败: {e}")
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

    # ============ 稳定版本的登录方法 - 基于测试脚本的成功经验 ============
    
    def _navigate_to_login_stable(self) -> bool:
        """稳定版本的导航到登录页面 - 基于测试脚本"""
        try:
            self.logger.info("导航到登录页面（稳定版本）")
            
            # 访问主页
            self.page.goto(Config.BASE_URL.rstrip('#/'))
            time.sleep(2)  # 基本等待
            
            # 点击登录按钮
            login_selectors = ['text=登录', 'button:has-text("登录")']
            for selector in login_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        self.logger.info(f"点击登录按钮成功: {selector}")
                        time.sleep(1.5)  # 等待登录框出现
                        return True
                except:
                    continue
            
            self.logger.warning("未找到登录按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"导航到登录页面失败: {str(e)}")
            return False
    
    def _fill_login_form_stable(self) -> bool:
        """稳定版本的填写登录表单 - 基于测试脚本"""
        try:
            # 填写用户名
            username_selectors = ['input[placeholder*="用户名"]']
            username_filled = False
            for selector in username_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        element.fill(Config.USERNAME)
                        username_filled = True
                        break
                except:
                    continue
            
            if not username_filled:
                self.logger.warning("未能填写用户名")
                return False
            
            time.sleep(0.5)
            
            # 填写密码
            password_selectors = ['input[type="password"]']
            password_filled = False
            for selector in password_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        element.fill(Config.PASSWORD)
                        password_filled = True
                        break
                except:
                    continue
            
            if not password_filled:
                self.logger.warning("未能填写密码")
                return False
            
            time.sleep(0.5)
            
            # 处理验证码（如果存在）
            self._handle_captcha_stable()
            
            return True
            
        except Exception as e:
            self.logger.error(f"填写登录表单失败: {str(e)}")
            return False
    
    def _handle_captcha_stable(self) -> bool:
        """稳定版本的验证码处理 - 基于测试脚本"""
        try:
            captcha_input = self.page.locator('input[placeholder*="验证码"]').first
            if captcha_input.count() > 0 and captcha_input.is_visible():
                # 尝试识别验证码
                captcha_image_selector = 'img[src*="/device/login!get_auth_code.do"]'
                captcha_image = self.page.locator(captcha_image_selector).first
                if captcha_image.count() > 0 and captcha_image.is_visible():
                    from src.captcha_solver import captcha_solver
                    # 传递选择器字符串而不是Locator对象
                    captcha_text = captcha_solver.solve_captcha_from_element(self.page, captcha_image_selector)
                    
                    if captcha_text and len(captcha_text) == 4 and captcha_text.isdigit():
                        captcha_input.click()
                        captcha_input.fill(captcha_text)
                        self.logger.info(f"验证码填写: {captcha_text}")
                        return True
                    else:
                        self.logger.warning(f"验证码识别失败: {captcha_text}")
                        # 使用测试验证码作为备用
                        captcha_input.click()
                        captcha_input.fill("1234")
                        self.logger.info("使用测试验证码: 1234")
                        return True
                else:
                    self.logger.debug("未找到验证码图片")
                    return True
            else:
                self.logger.debug("未找到验证码输入框")
                return True
                
        except Exception as e:
            self.logger.error(f"处理验证码失败: {str(e)}")
            return False
    
    def _submit_login_form_stable(self) -> bool:
        """稳定版本的提交登录表单 - 基于测试脚本"""
        try:
            # 查找提交按钮
            submit_selectors = [
                'button:has-text("登录")',
                'input[type="submit"]',
                'button[type="submit"]',
                '.el-button--primary:has-text("登录")',
                '[class*="submit"]:has-text("登录")',
                '.login-btn'
            ]
            
            for selector in submit_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        self.logger.info(f"提交按钮点击成功，选择器: {selector}")
                        time.sleep(2)  # 等待页面响应
                        return True
                except:
                    continue
            
            # 备用方案：按回车键
            self.logger.info("未找到提交按钮，使用回车键提交")
            self.page.keyboard.press('Enter')
            time.sleep(2)
            return True
                    
        except Exception as e:
            self.logger.error(f"提交登录表单失败: {str(e)}")
            return False
    
    def _check_login_result_simple(self) -> str:
        """简化版本的登录结果检查 - 基于测试脚本"""
        try:
            # 检查常见的错误消息
            error_selectors = [
                '.el-message--error',
                '.error-message',
                '[class*="error"]',
                '.el-form-item__error'
            ]
            
            for selector in error_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            error_text = element.text_content()
                            if error_text:
                                if "验证码" in error_text or "校验码" in error_text:
                                    return "captcha_error"
                                elif "用户名" in error_text or "密码" in error_text:
                                    return "auth_error"
                                else:
                                    return f"error: {error_text}"
                except:
                    continue
            
            # 检查是否成功跳转
            current_url = self.page.url
            success_indicators = ["#/home", "#/dashboard", "#/main", "#/user"]
            
            for indicator in success_indicators:
                if indicator in current_url:
                    return "success"
            
            # 检查是否登录框还在
            modal_exists = self.page.locator('.el-dialog').count() > 0
            if not modal_exists:
                # 登录框消失但未明确成功跳转，可能是成功
                return "success"
            
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"检查登录结果失败: {str(e)}")
            return "error"

# 全局登录管理器实例
login_manager = LoginManager()