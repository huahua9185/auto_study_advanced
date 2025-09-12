import ddddocr
import base64
import io
from PIL import Image
from playwright.sync_api import Page
import logging
from config.config import Config
import numpy as np
from collections import Counter
import warnings
import os

# 抑制 ONNX Runtime 警告
os.environ['ORT_DISABLE_ALL_WARNING'] = '1'
warnings.filterwarnings('ignore', category=UserWarning, module='onnxruntime')

# 应用 Pillow 兼容性修复
try:
    from src.pillow_fix import *
except:
    pass

class CaptchaSolver:
    def __init__(self):
        """初始化验证码识别器"""
        try:
            # 尝试使用新版本API
            self.ocr = ddddocr.DdddOcr(show_ad=False)
        except TypeError:
            # 如果show_ad参数不支持，使用旧版本API
            self.ocr = ddddocr.DdddOcr()
        self.logger = logging.getLogger(__name__)
        
    def solve_captcha_from_element(self, page: Page, captcha_selector: str) -> str:
        """
        从页面元素中获取验证码图片并识别
        
        Args:
            page: Playwright页面对象
            captcha_selector: 验证码图片元素的选择器
            
        Returns:
            str: 识别的验证码文本
        """
        try:
            # 等待验证码元素出现
            captcha_element = page.wait_for_selector(captcha_selector, timeout=Config.ELEMENT_WAIT_TIMEOUT)
            
            if not captcha_element:
                raise Exception("验证码元素未找到")
            
            # 获取验证码图片
            screenshot = captcha_element.screenshot()
            
            # 预处理图片以提高识别准确率
            processed_image = self.preprocess_captcha_image(screenshot)
            
            # 使用ddddocr识别
            raw_result = self.ocr.classification(processed_image)
            
            # 后处理修正识别结果
            result = self._post_process_result(raw_result.strip())
            
            self.logger.info(f"验证码识别结果: {raw_result} -> {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"验证码识别失败: {str(e)}")
            raise
    
    def solve_captcha_from_base64(self, base64_image: str) -> str:
        """
        从base64图片数据识别验证码
        
        Args:
            base64_image: base64编码的图片数据
            
        Returns:
            str: 识别的验证码文本
        """
        try:
            # 解码base64图片
            image_data = base64.b64decode(base64_image)
            
            # 使用ddddocr识别
            result = self.ocr.classification(image_data)
            
            self.logger.info(f"验证码识别结果: {result}")
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"验证码识别失败: {str(e)}")
            raise
    
    def solve_captcha_with_retry(self, page: Page, captcha_selector: str, 
                               refresh_selector: str = None, max_retries: int = None) -> str:
        """
        带重试机制的验证码识别
        
        Args:
            page: Playwright页面对象
            captcha_selector: 验证码图片元素的选择器
            refresh_selector: 刷新验证码按钮的选择器（可选）
            max_retries: 最大重试次数
            
        Returns:
            str: 识别的验证码文本
        """
        if max_retries is None:
            max_retries = Config.CAPTCHA_MAX_RETRIES
            
        best_result = None
        best_confidence = 0
            
        for attempt in range(max_retries):
            try:
                self.logger.info(f"验证码识别尝试 {attempt + 1}/{max_retries}")
                
                # 跳过验证码刷新操作避免页面跳动
                # if attempt > 0 and refresh_selector:
                #     self.logger.info("刷新验证码") 
                #     page.click(refresh_selector)  # 注释掉导致页面跳动的点击操作
                #     page.wait_for_timeout(2000)  # 注释掉相关等待
                if attempt > 0:
                    self.logger.info("跳过验证码刷新操作以避免页面跳动，继续使用当前验证码重试识别")
                
                # 单次快速识别，提高时效性
                result = self.solve_captcha_from_element(page, captcha_selector)
                if self._is_valid_captcha(result):
                    self.logger.info(f"识别结果: {result}")
                    return result
                else:
                    # 如果第一次识别失败，尝试第二次
                    result = self.solve_captcha_from_element(page, captcha_selector)
                    if self._is_valid_captcha(result):
                        self.logger.info(f"第二次识别结果: {result}")
                        return result
                
            except Exception as e:
                self.logger.warning(f"第 {attempt + 1} 次识别失败: {str(e)}")
                if attempt == max_retries - 1 and best_result:
                    self.logger.info(f"使用最佳结果: {best_result}")
                    return best_result
                continue
        
        if best_result:
            return best_result
        raise Exception("验证码识别失败")
    
    def _is_valid_captcha(self, captcha_text: str) -> bool:
        """
        验证识别结果的有效性（专门4位数字）
        
        Args:
            captcha_text: 识别的验证码文本
            
        Returns:
            bool: 是否有效
        """
        if not captcha_text:
            return False
            
        # 移除空格和特殊字符
        captcha_text = captcha_text.strip()
        
        # 严格检查长度：必须是4位
        if len(captcha_text) != 4:
            return False
            
        # 严格检查是否全部为数字
        if not captcha_text.isdigit():
            return False
                
        return True
    
    def _post_process_result(self, raw_result: str) -> str:
        """
        后处理OCR识别结果，专门优吖4位数字验证码
        
        Args:
            raw_result: 原始识别结果
            
        Returns:
            str: 修正后的结果
        """
        if not raw_result:
            return raw_result
            
        # 精细调优的字符映射表，专门4位数字验证码
        char_mapping = {
            # 数字0的所有可能误识别
            'o': '0', 'O': '0', 'D': '0', 'Q': '0', 'a': '0', 'A': '0', 'U': '0', 'u': '0',
            # 数字1的所有可能误识别
            'l': '1', 'I': '1', 'i': '1', '|': '1', '!': '1', 't': '1', 'T': '1', 'j': '1',
            # 数字2的所有可能误识别
            'z': '2', 'Z': '2', 'R': '2', 'r': '2',
            # 数字3的所有可能误识别
            'E': '3', 'B': '3', 'm': '3', 'M': '3',
            # 数字4的所有可能误识别
            'A': '4', 'h': '4', 'y': '4', 'Y': '4', 'H': '4',
            # 数字5的所有可能误识别
            'S': '5', 's': '5', 'G': '5', 'g': '5',
            # 数字6的所有可能误识别  
            'G': '6', 'b': '6', 'C': '6', 'c': '6', 'e': '6',
            # 数字7的所有可能误识别
            'T': '7', '/': '7', '\\': '7', 'L': '7', 'F': '7', 'f': '7',
            # 数字8的所有可能误识别
            'B': '8', '&': '8', '@': '8',
            # 数字9的所有可能误识别
            'g': '9', 'q': '9', 'P': '9', 'p': '9', 'd': '9',
        }
        
        # 移除非数字字符
        clean_result = ''.join(c for c in raw_result if c.isalnum())
        
        # 应用字符映射
        corrected_result = ''.join(char_mapping.get(char, char) for char in clean_result)
        
        # 只保留数字
        corrected_result = ''.join(c for c in corrected_result if c.isdigit())
        
        # 如果结果不是4位，尝试补正
        if len(corrected_result) == 0:
            # 完全无数字，返回原始结果让上层重试
            return raw_result
        elif len(corrected_result) < 4:
            # 如果缺少数字，返回空让上层重试
            self.logger.warning(f"识别结果长度不足: {corrected_result} ({len(corrected_result)}位)")
            return ''
        elif len(corrected_result) > 4:
            # 如果多了数字，取前4位
            self.logger.warning(f"识别结果过长，截取前4位: {corrected_result} -> {corrected_result[:4]}")
            corrected_result = corrected_result[:4]
        
        return corrected_result
    
    def preprocess_captcha_image(self, image_data: bytes) -> bytes:
        """
        预处理验证码图片以提高识别准确率
        
        Args:
            image_data: 原始图片数据
            
        Returns:
            bytes: 处理后的图片数据
        """
        try:
            from PIL import ImageEnhance, ImageFilter, ImageOps
            import numpy as np
            
            # 打开图片
            image = Image.open(io.BytesIO(image_data))
            
            # 放大图片以提高识别精度 - 改为2倍以避免过度模糊
            width, height = image.size
            image = image.resize((width * 2, height * 2), Image.LANCZOS)
            
            # 转换为灰度图
            if image.mode != 'L':
                image = image.convert('L')
            
            # 先进行自适应直方图均衡化
            image = ImageOps.equalize(image)
            
            # 转换为numpy数组进行高级处理
            img_array = np.array(image)
            
            # 二值化处理 - 使用自适应阈值
            threshold = np.mean(img_array)
            binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
            
            # 转换回 PIL 图片
            image = Image.fromarray(binary_array)
            
            # 形态学处理 - 去除小的噪点
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # 轻微锐化
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # 最终对比度调整
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # 保存处理后的图片
            output = io.BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            self.logger.warning(f"图片预处理失败: {str(e)}")
            return image_data  # 返回原图

# 全局验证码识别器实例
captcha_solver = CaptchaSolver()