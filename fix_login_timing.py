#!/usr/bin/env python3
"""
修复登录时序问题的建议代码
"""

def _submit_login_form_and_wait_improved(self) -> bool:
    """改进版：提交登录表单并等待响应"""
    try:
        # 原有的提交逻辑...
        
        # ✅ 改进1：增加初始等待时间
        time.sleep(3)  # 从2秒增加到3秒
        
        # ✅ 改进2：多次检查，而不是一次性检查
        max_checks = 5
        for check_attempt in range(max_checks):
            try:
                self._smart_wait_for_page_load('networkidle', 8000)
                
                # 检查URL是否发生变化（成功的重要标志）
                current_url = self.page.url
                if "/login" not in current_url.lower() and "requireAuth" not in current_url:
                    self.logger.info(f"检测到URL跳转，登录可能成功: {current_url}")
                    time.sleep(2)  # 再等2秒确保页面完全加载
                    break
                    
                time.sleep(1)  # 每次检查间隔1秒
            except:
                if check_attempt == max_checks - 1:
                    self.logger.warning("等待页面加载超时，但继续检查登录结果")
                
        # ✅ 改进3：最终确保等待
        time.sleep(2)  # 额外等待确保状态完全稳定
        
        return True
        
    except Exception as e:
        self.logger.error(f"提交登录表单失败: {str(e)}")
        return False

def _check_detailed_login_result_improved(self) -> str:
    """改进版：详细检查登录结果"""
    try:
        # ✅ 改进4：先等待一下确保页面状态稳定
        time.sleep(1)
        
        # 原有的验证码错误检查...
        # 原有的认证错误检查...
        
        # ✅ 改进5：更准确的URL检查
        current_url = self.page.url
        self.logger.info(f"检查登录结果时的URL: {current_url}")
        
        # 如果URL明确表示登录成功
        success_url_indicators = [
            'study_center', 'my_study', 'personal', 'dashboard', 
            'course', 'learning', 'index.html#/', 'main'
        ]
        
        url_indicates_success = any(indicator in current_url.lower() 
                                   for indicator in success_url_indicators)
        
        if url_indicates_success:
            self.logger.info(f"URL表明登录成功: {current_url}")
            
            # ✅ 改进6：双重确认 - 等待更长时间再检查用户元素
            time.sleep(2)
            
            # 检查用户信息元素...
            user_info_selectors = [
                '.user-info', '.username', 'button:has-text("退出")',
                '[class*="user"]', '[class*="logout"]', 'text=退出登录'
            ]
            
            for selector in user_info_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            self.logger.info(f"检测到用户信息元素，确认登录成功: {selector}")
                            return "success"
                except:
                    continue
            
            # 即使没找到用户元素，URL变化也可能表示成功
            self.logger.info("URL跳转成功，判定为登录成功")
            return "success"
        
        # ✅ 改进7：检查是否还在登录页面
        if "/login" in current_url.lower() or "requireAuth" in current_url:
            self.logger.info("仍在登录页面，可能登录失败")
            # 继续检查具体错误...
        
        return "unknown"  # 不确定的状态
        
    except Exception as e:
        self.logger.error(f"检查登录结果时出错: {str(e)}")
        return "error"

print("建议的修复方案:")
print("1. 增加等待时间：2秒 -> 3秒")
print("2. 多次检查页面状态，而不是一次性检查")
print("3. 优先检查URL变化作为成功标志")
print("4. 双重确认：先检查URL，再检查用户元素")
print("5. 增加日志输出，便于调试")
print("6. 处理页面跳转的竞态条件")