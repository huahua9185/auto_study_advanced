#!/usr/bin/env python3
"""
优化的登录管理器 - 减少验证码过期问题
专门针对验证码时效性优化的登录流程
"""

import time
import logging
from typing import Optional, Tuple
from datetime import datetime
import threading

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pure_api_learner import PureAPILearner, APISession, UserInfo


class OptimizedLoginManager:
    """优化的登录管理器"""

    def __init__(self, username: str, password: str):
        """
        初始化优化登录管理器

        Args:
            username: 用户名
            password: 密码
        """
        self.username = username
        self.password = password

        # 创建API会话
        self.api_session = APISession()

        # 用户信息
        self.user_info: Optional[UserInfo] = None
        self.is_logged_in = False

        # 登录优化配置
        self.max_login_attempts = 5  # 增加重试次数
        self.captcha_timeout = 8.0   # 验证码使用时间限制(秒)
        self.fast_retry_delay = 0.5  # 快速重试延迟

        # 日志
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("OptimizedLoginManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _encrypt_password(self, password: str, key: str = "CCR!@#$%") -> str:
        """DES密码加密 - Base64版本"""
        try:
            from Crypto.Cipher import DES
            from Crypto.Util.Padding import pad
            import base64

            # 确保密钥是8字节
            if len(key) > 8:
                key = key[:8]
            elif len(key) < 8:
                key = key.ljust(8, '\0')

            key_bytes = key.encode('utf-8')
            cipher = DES.new(key_bytes, DES.MODE_ECB)
            password_bytes = password.encode('utf-8')
            padded_password = pad(password_bytes, DES.block_size)
            encrypted = cipher.encrypt(padded_password)
            base64_result = base64.b64encode(encrypted).decode('utf-8')

            return base64_result
        except Exception as e:
            self.logger.error(f"密码加密失败: {e}")
            return password

    def _get_captcha_fast(self) -> Tuple[Optional[str], float]:
        """
        快速获取验证码

        Returns:
            Tuple[验证码文本, 获取耗时]
        """
        start_time = time.time()

        try:
            # 获取验证码图片
            captcha_url = f"{self.api_session.base_url}/device/login!get_auth_code.do"

            headers = {
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': f'{self.api_session.base_url}/nxxzxy/index.html'
            }

            response = self.api_session.session.get(captcha_url, headers=headers, timeout=3)

            if response.status_code != 200:
                self.logger.error(f"获取验证码失败: HTTP {response.status_code}")
                return None, time.time() - start_time

            # 使用原版高识别率方法
            from src.captcha_solver import CaptchaSolver
            solver = CaptchaSolver()

            captcha_text = solver.solve_captcha_from_bytes(response.content)

            elapsed = time.time() - start_time

            if captcha_text:
                self.logger.info(f"验证码识别成功: {captcha_text} (耗时: {elapsed:.2f}s)")
                return captcha_text, elapsed
            else:
                self.logger.warning(f"验证码识别失败 (耗时: {elapsed:.2f}s)")
                return None, elapsed

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"获取验证码异常: {e} (耗时: {elapsed:.2f}s)")
            return None, elapsed

    def _login_attempt_fast(self, captcha_code: str) -> Optional[dict]:
        """
        快速登录尝试

        Args:
            captcha_code: 验证码

        Returns:
            登录响应JSON或None
        """
        try:
            # 加密密码
            encrypted_password = self._encrypt_password(self.password)

            # 准备登录数据
            login_data = {
                'username': self.username,
                'password': encrypted_password,
                'verify_code': captcha_code,
                'terminal': '1'
            }

            # 发送登录请求
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.api_session.base_url}/nxxzxy/index.html'
            }

            response = self.api_session.session.post(
                f"{self.api_session.base_url}/device/login.do",
                data=login_data,
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                    return result
                except:
                    self.logger.error(f"登录响应不是JSON格式: {response.text}")
                    return None
            else:
                self.logger.error(f"登录请求失败: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"登录尝试异常: {e}")
            return None

    def optimized_login(self) -> bool:
        """
        优化的登录流程 - 最小化验证码过期风险

        Returns:
            bool: 登录是否成功
        """
        self.logger.info(f"🚀 开始优化登录流程 (最大尝试次数: {self.max_login_attempts})")

        for attempt in range(1, self.max_login_attempts + 1):
            self.logger.info(f"登录尝试 {attempt}/{self.max_login_attempts}")

            try:
                # 步骤1: 快速获取验证码
                captcha_code, captcha_time = self._get_captcha_fast()

                if not captcha_code:
                    self.logger.warning(f"验证码获取失败，{self.fast_retry_delay}s后重试")
                    time.sleep(self.fast_retry_delay)
                    continue

                # 步骤2: 检查验证码获取时间
                if captcha_time > self.captcha_timeout:
                    self.logger.warning(f"验证码获取耗时过长 ({captcha_time:.2f}s > {self.captcha_timeout}s)，可能已过期")

                # 步骤3: 立即尝试登录（最小化延迟）
                login_start = time.time()
                result = self._login_attempt_fast(captcha_code)
                login_time = time.time() - login_start

                self.logger.info(f"登录请求耗时: {login_time:.2f}s，总耗时: {captcha_time + login_time:.2f}s")

                if not result:
                    self.logger.warning(f"登录请求失败，{self.fast_retry_delay}s后重试")
                    time.sleep(self.fast_retry_delay)
                    continue

                # 步骤4: 分析登录结果
                status = result.get('status')
                message = result.get('message', 'no message')

                if status == 1:
                    # 登录成功
                    self.logger.info("✅ 登录成功!")

                    # 保存用户信息
                    user_data = result.get('user', {})
                    self.user_info = UserInfo(
                        user_id=result.get('user_id'),
                        username=self.username,
                        realname=user_data.get('realname', ''),
                        org_name=user_data.get('org_name', ''),
                        uuid=user_data.get('uuid', ''),
                        avatar=user_data.get('avatar', '')
                    )

                    self.is_logged_in = True
                    return True

                elif status == 0:
                    # 登录失败
                    if "校验码错误" in message:
                        self.logger.warning(f"验证码错误，立即重试 (总时间: {captcha_time + login_time:.2f}s)")
                        # 验证码错误时不延迟，立即重试
                        continue
                    else:
                        self.logger.error(f"登录失败: {message}")
                        return False
                else:
                    self.logger.warning(f"未知状态码: {status}, 消息: {message}")
                    time.sleep(self.fast_retry_delay)
                    continue

            except Exception as e:
                self.logger.error(f"登录异常: {e}")
                time.sleep(self.fast_retry_delay)
                continue

        self.logger.error(f"❌ 登录失败，已达到最大重试次数 ({self.max_login_attempts})")
        return False

    def login(self) -> bool:
        """兼容接口 - 调用优化登录"""
        return self.optimized_login()

    def get_user_info(self) -> Optional[UserInfo]:
        """获取用户信息"""
        return self.user_info

    def is_login_valid(self) -> bool:
        """检查登录是否有效"""
        return self.is_logged_in and self.user_info is not None


class FastLoginTester:
    """快速登录测试器"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def test_optimized_login(self, test_count: int = 5) -> dict:
        """
        测试优化登录的成功率

        Args:
            test_count: 测试次数

        Returns:
            测试结果统计
        """
        print(f"🧪 测试优化登录 (测试次数: {test_count})")

        results = {
            'total_tests': test_count,
            'successful_logins': 0,
            'failed_logins': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'fastest_time': float('inf'),
            'slowest_time': 0.0,
            'details': []
        }

        for i in range(1, test_count + 1):
            print(f"\n--- 测试 {i}/{test_count} ---")

            manager = OptimizedLoginManager(self.username, self.password)

            start_time = time.time()
            success = manager.login()
            end_time = time.time()

            elapsed = end_time - start_time
            results['total_time'] += elapsed

            if success:
                results['successful_logins'] += 1
                results['fastest_time'] = min(results['fastest_time'], elapsed)
                print(f"✅ 登录成功 (耗时: {elapsed:.2f}s)")
            else:
                results['failed_logins'] += 1
                print(f"❌ 登录失败 (耗时: {elapsed:.2f}s)")

            results['slowest_time'] = max(results['slowest_time'], elapsed)

            results['details'].append({
                'test_number': i,
                'success': success,
                'time': elapsed,
                'user_info': manager.get_user_info()
            })

            # 测试间隔
            time.sleep(1)

        # 计算统计
        results['average_time'] = results['total_time'] / test_count
        results['success_rate'] = (results['successful_logins'] / test_count) * 100

        if results['fastest_time'] == float('inf'):
            results['fastest_time'] = 0.0

        print(f"\n📊 测试结果总结:")
        print(f"  成功次数: {results['successful_logins']}/{test_count}")
        print(f"  成功率: {results['success_rate']:.1f}%")
        print(f"  平均耗时: {results['average_time']:.2f}s")
        print(f"  最快: {results['fastest_time']:.2f}s")
        print(f"  最慢: {results['slowest_time']:.2f}s")

        return results


if __name__ == "__main__":
    print("🚀 优化登录管理器测试")

    # 创建测试器
    tester = FastLoginTester("640302198607120020", "My2062660")

    # 运行测试
    results = tester.test_optimized_login(test_count=3)

    if results['success_rate'] > 60:  # 60%以上成功率算优化成功
        print("\n🎉 登录优化效果良好！")
    else:
        print("\n⚠️ 登录优化效果有限，需要进一步调整")