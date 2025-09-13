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
        从页面元素中获取验证码图片并识别（多重尝试版本）
        
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
            
            # 预处理图片 - 返回多个版本
            processed_images = self.preprocess_captcha_image(screenshot)
            
            # 对每个处理版本进行识别
            results = []
            raw_results = []
            
            for i, processed_image in enumerate(processed_images):
                try:
                    # 使用ddddocr识别
                    raw_result = self.ocr.classification(processed_image)
                    raw_results.append(raw_result)
                    
                    # 后处理修正识别结果
                    result = self._post_process_result(raw_result.strip())
                    
                    if self._is_valid_captcha(result):
                        results.append(result)
                        self.logger.debug(f"方法{i+1}识别结果: {raw_result} -> {result}")
                    else:
                        self.logger.debug(f"方法{i+1}识别结果无效: {raw_result} -> {result}")
                        
                except Exception as e:
                    self.logger.debug(f"方法{i+1}识别失败: {str(e)}")
                    continue
            
            # 投票选择最佳结果
            if results:
                final_result = self._vote_best_result(results)
                self.logger.info(f"验证码识别结果 (投票): {raw_results} -> {final_result}")
                return final_result
            
            # 如果所有方法都失败，尝试返回最长的有效结果
            if raw_results:
                for raw in raw_results:
                    processed = self._post_process_result(raw.strip())
                    if len(processed) >= 3:  # 至少3位数字
                        self.logger.warning(f"使用备选结果: {raw} -> {processed}")
                        return processed[:4]  # 截取前4位
            
            raise Exception("所有识别方法都失败")

        except Exception as e:
            self.logger.error(f"验证码识别失败: {str(e)}")
            raise

    def solve_captcha_from_bytes(self, image_bytes: bytes) -> str:
        """
        从图片字节数据中识别验证码

        Args:
            image_bytes: 图片的字节数据

        Returns:
            str: 识别的验证码文本
        """
        try:
            # 预处理图片 - 返回多个版本
            processed_images = self.preprocess_captcha_image(image_bytes)

            # 对每个处理版本进行识别
            results = []
            raw_results = []

            for i, processed_image in enumerate(processed_images):
                try:
                    # 使用ddddocr识别
                    raw_result = self.ocr.classification(processed_image)
                    raw_results.append(raw_result)

                    # 后处理修正识别结果
                    result = self._post_process_result(raw_result.strip())

                    if self._is_valid_captcha(result):
                        results.append(result)
                        self.logger.debug(f"方法{i+1}识别结果: {raw_result} -> {result}")
                    else:
                        self.logger.debug(f"方法{i+1}识别结果无效: {raw_result} -> {result}")

                except Exception as e:
                    self.logger.debug(f"方法{i+1}识别失败: {str(e)}")
                    continue

            # 投票选择最佳结果
            if results:
                final_result = self._vote_best_result(results)
                self.logger.info(f"验证码识别结果 (投票): {raw_results} -> {final_result}")
                return final_result

            # 如果所有方法都失败，尝试返回最长的有效结果
            if raw_results:
                for raw in raw_results:
                    processed = self._post_process_result(raw.strip())
                    if len(processed) >= 3:  # 至少3位数字
                        self.logger.warning(f"使用备选结果: {raw} -> {processed}")
                        return processed[:4]  # 截取前4位

            raise Exception("所有识别方法都失败")

        except Exception as e:
            self.logger.error(f"从字节数据识别验证码失败: {str(e)}")
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
        增强版后处理OCR识别结果，专门优化4位数字验证码
        
        Args:
            raw_result: 原始识别结果
            
        Returns:
            str: 修正后的结果
        """
        if not raw_result:
            return raw_result
            
        # 保守的字符映射表，避免冲突，只映射最确定的误识别
        char_mapping = {
            # 数字0的明确误识别（小写o、大写O、大写Q等）
            'o': '0', 'O': '0', 'Q': '0',
            # 数字1的明确误识别（小写l、大写I等）
            'l': '1', 'I': '1', '|': '1',
            # 数字2的明确误识别
            'z': '2', 'Z': '2',
            # 数字5的明确误识别
            'S': '5', 's': '5',
            # 其他明确的映射保持最小化以避免错误转换
        }
        
        # 保留数字和字母
        clean_result = ''.join(c for c in raw_result if c.isalnum() or c in '()[]{}|!@#$%^&*-_=+/\\<>?')
        
        # 分步骤处理
        step1_result = clean_result
        
        # 应用字符映射
        step2_result = ''.join(char_mapping.get(char, char) for char in step1_result)
        
        # 只保留数字
        step3_result = ''.join(c for c in step2_result if c.isdigit())
        
        # 智能补全逻辑
        if len(step3_result) == 0:
            # 如果完全没有数字，尝试更激进的转换
            aggressive_result = self._aggressive_char_conversion(raw_result)
            if aggressive_result:
                step3_result = aggressive_result
            else:
                return ''  # 返回空字符串表示无法识别
                
        elif len(step3_result) < 4:
            # 长度不足时的处理策略
            if len(step3_result) == 3:
                # 3位数字，尝试在前面补0或在后面补常见数字
                # 基于样本分析，大多数情况是丢失了最后一位
                self.logger.debug(f"3位结果，尝试智能补全: {step3_result}")
                return step3_result  # 暂时返回3位，让上层判断
            elif len(step3_result) == 2:
                # 2位数字，返回空让重试
                self.logger.debug(f"2位结果，返回空触发重试: {step3_result}")
                return ''
            else:
                # 1位或其他情况
                return ''
                
        elif len(step3_result) > 4:
            # 如果多了数字，智能选择最可能的4位
            if len(step3_result) == 5:
                # 5位数字，可能是重复了某一位
                # 找到重复的数字并移除
                char_count = Counter(step3_result)
                for char, count in char_count.items():
                    if count > 1:
                        # 移除多余的重复字符
                        step3_result = step3_result.replace(char, char, count-1)
                        break
                        
            # 如果还是太长，取前4位
            if len(step3_result) > 4:
                step3_result = step3_result[:4]
                self.logger.debug(f"截取前4位: {raw_result} -> {step3_result}")
        
        return step3_result
    
    def _aggressive_char_conversion(self, raw_result: str) -> str:
        """
        激进的字符转换，当标准方法无法提取到数字时使用
        """
        # 对每个字符尝试转换为最相似的数字
        result = []
        for char in raw_result:
            if char.isdigit():
                result.append(char)
            elif char.lower() in 'oaqd':
                result.append('0')
            elif char.lower() in 'iljt':
                result.append('1')
            elif char.lower() in 'zr':
                result.append('2')
            elif char.lower() in 'ebm':
                result.append('3')
            elif char.lower() in 'ahy':
                result.append('4')
            elif char.lower() in 'sg':
                result.append('5')
            elif char.lower() in 'gc':
                result.append('6')
            elif char.lower() in 'tf':
                result.append('7')
            elif char.lower() in 'b&':
                result.append('8')
            elif char.lower() in 'gqp':
                result.append('9')
                
        final_result = ''.join(result)
        return final_result[:4] if len(final_result) >= 4 else final_result
    
    def _vote_best_result(self, results: list) -> str:
        """
        投票选择最佳识别结果
        
        Args:
            results: 多个识别结果列表
            
        Returns:
            str: 最佳识别结果
        """
        if not results:
            return ''
            
        if len(results) == 1:
            return results[0]
        
        # 统计每个结果的出现次数
        result_count = Counter(results)
        
        # 优先选择出现次数最多的结果
        most_common = result_count.most_common(1)[0]
        if most_common[1] > 1:
            return most_common[0]
        
        # 如果所有结果都只出现一次，选择长度为4的结果
        for result in results:
            if len(result) == 4:
                return result
        
        # 否则选择第一个结果
        return results[0]
    
    def preprocess_captcha_image(self, image_data: bytes) -> list:
        """
        多种方法预处理验证码图片，返回多个处理版本以提高识别成功率
        
        Args:
            image_data: 原始图片数据
            
        Returns:
            list: 多个处理后的图片数据列表
        """
        processed_images = []
        
        try:
            from PIL import ImageEnhance, ImageFilter, ImageOps
            import numpy as np
            from scipy import ndimage
            
            # 打开原始图片
            original_image = Image.open(io.BytesIO(image_data))
            
            # 方法1：标准处理 - 去噪声 + 二值化
            try:
                image1 = original_image.copy()
                
                # 放大图片 3倍以提高识别精度
                width, height = image1.size
                image1 = image1.resize((width * 3, height * 3), Image.LANCZOS)
                
                # 转换为灰度图
                if image1.mode != 'L':
                    image1 = image1.convert('L')
                
                # 高斯滤波去噪
                image1 = image1.filter(ImageFilter.GaussianBlur(radius=0.5))
                
                # 转换为numpy数组
                img_array = np.array(image1)
                
                # 使用OTSU阈值进行二值化
                from skimage.filters import threshold_otsu
                threshold = threshold_otsu(img_array)
                binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
                
                # 形态学操作去除噪点
                from scipy.ndimage import binary_opening, binary_closing
                binary_array = binary_opening(binary_array, structure=np.ones((2,2))).astype(np.uint8) * 255
                binary_array = binary_closing(binary_array, structure=np.ones((2,2))).astype(np.uint8) * 255
                
                image1 = Image.fromarray(binary_array)
                
                # 保存处理后的图片
                output1 = io.BytesIO()
                image1.save(output1, format='PNG')
                processed_images.append(output1.getvalue())
                
            except ImportError:
                # 如果sklearn不可用，使用简化版本
                image1 = original_image.copy()
                width, height = image1.size
                image1 = image1.resize((width * 3, height * 3), Image.LANCZOS)
                
                if image1.mode != 'L':
                    image1 = image1.convert('L')
                
                img_array = np.array(image1)
                threshold = np.mean(img_array) - 10  # 更严格的阈值
                binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
                image1 = Image.fromarray(binary_array)
                
                output1 = io.BytesIO()
                image1.save(output1, format='PNG')
                processed_images.append(output1.getvalue())
            
            # 方法2：增强对比度处理
            try:
                image2 = original_image.copy()
                
                # 放大图片
                width, height = image2.size
                image2 = image2.resize((width * 3, height * 3), Image.LANCZOS)
                
                # 转换为灰度图
                if image2.mode != 'L':
                    image2 = image2.convert('L')
                
                # 直方图均衡化
                image2 = ImageOps.equalize(image2)
                
                # 强化对比度
                enhancer = ImageEnhance.Contrast(image2)
                image2 = enhancer.enhance(2.0)
                
                # 锐化
                enhancer = ImageEnhance.Sharpness(image2)
                image2 = enhancer.enhance(2.0)
                
                # 再次二值化
                img_array = np.array(image2)
                threshold = np.mean(img_array)
                binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
                image2 = Image.fromarray(binary_array)
                
                # 中值滤波去除孤立噪点
                image2 = image2.filter(ImageFilter.MedianFilter(size=3))
                
                output2 = io.BytesIO()
                image2.save(output2, format='PNG')
                processed_images.append(output2.getvalue())
                
            except Exception as e2:
                self.logger.debug(f"方法2处理失败: {e2}")
            
            # 方法3：保守处理 - 仅放大和轻微处理
            try:
                image3 = original_image.copy()
                
                # 适度放大
                width, height = image3.size
                image3 = image3.resize((width * 2, height * 2), Image.LANCZOS)
                
                # 转为灰度
                if image3.mode != 'L':
                    image3 = image3.convert('L')
                
                # 轻微增强对比度
                enhancer = ImageEnhance.Contrast(image3)
                image3 = enhancer.enhance(1.3)
                
                output3 = io.BytesIO()
                image3.save(output3, format='PNG')
                processed_images.append(output3.getvalue())
                
            except Exception as e3:
                self.logger.debug(f"方法3处理失败: {e3}")
            
            # 如果所有方法都失败，至少返回放大的原图
            if not processed_images:
                simple_image = original_image.copy()
                width, height = simple_image.size
                simple_image = simple_image.resize((width * 2, height * 2), Image.LANCZOS)
                
                output_simple = io.BytesIO()
                simple_image.save(output_simple, format='PNG')
                processed_images.append(output_simple.getvalue())
            
            self.logger.debug(f"生成了 {len(processed_images)} 种预处理图片")
            return processed_images
            
        except Exception as e:
            self.logger.warning(f"图片预处理失败: {str(e)}")
            return [image_data]  # 返回原图

# 全局验证码识别器实例
captcha_solver = CaptchaSolver()