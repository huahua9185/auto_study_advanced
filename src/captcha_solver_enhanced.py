"""
高精度验证码识别器 - 基于成功率接近100%的参考实现优化

参考自: https://github.com/huahua9185/auto_study.git
主要优化技术:
1. 高级图像预处理: 对比度增强、锐度增强、去噪、尺寸调整
2. 多次尝试识别: 每个验证码尝试多次识别，选择最佳结果  
3. 置信度计算: 基于长度、字符类型、图像特征计算置信度
4. 针对数字验证码的专门优化
5. 失败图像保存用于分析
"""

import io
import time
from typing import Optional, Union, Dict, Any
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import ddddocr
import numpy as np
from playwright.sync_api import Page
import logging

# 应用 Pillow 兼容性修复
try:
    from src.pillow_fix import *
except:
    pass


class EnhancedCaptchaSolver:
    """增强版验证码识别器 - 高成功率版本"""
    
    def __init__(self):
        """初始化验证码识别器"""
        self.logger = logging.getLogger(__name__)
        self._ocr = None
        self._init_ocr()
        
        # 识别统计
        self._recognition_stats = {
            'total_attempts': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'average_confidence': 0.0
        }
        
        # 预处理配置 - 基于高成功率仓库的配置
        self._preprocess_config = {
            'enhance_contrast': True,      # 对比度增强
            'enhance_sharpness': True,     # 锐度增强  
            'remove_noise': True,          # 去噪处理
            'binarization': False,         # 二值化（某些验证码可能有害）
            'resize_factor': 2.0,          # 放大倍数
            'equalization': True           # 直方图均衡化
        }
        
        print("增强版验证码识别器初始化成功 - 基于高成功率优化")
    
    def _init_ocr(self) -> None:
        """初始化OCR引擎"""
        try:
            # 使用默认配置，针对数字验证码优化
            self._ocr = ddddocr.DdddOcr(show_ad=False)
            self.logger.info("验证码OCR引擎初始化成功")
        except TypeError:
            # 如果show_ad参数不支持，使用旧版本API
            self._ocr = ddddocr.DdddOcr()
            self.logger.info("验证码OCR引擎初始化成功（旧版本API）")
        except Exception as e:
            self.logger.error(f"验证码OCR引擎初始化失败: {e}")
            raise
    
    def preprocess_image(self, image: Union[bytes, Image.Image, str, Path]) -> Image.Image:
        """
        高级图像预处理 - 基于参考仓库的优化方法
        
        Args:
            image: 图片数据（字节、PIL图像、base64字符串或文件路径）
            
        Returns:
            预处理后的PIL图像
        """
        try:
            # 转换为PIL图像
            pil_image = self._convert_to_pil(image)
            processed_image = pil_image.copy()
            
            # 调整大小 - 放大提高识别精度
            if self._preprocess_config['resize_factor'] != 1.0:
                width, height = processed_image.size
                new_width = int(width * self._preprocess_config['resize_factor'])
                new_height = int(height * self._preprocess_config['resize_factor'])
                processed_image = processed_image.resize((new_width, new_height), Image.LANCZOS)
            
            # 转换为灰度图
            if processed_image.mode != 'L':
                processed_image = processed_image.convert('L')
            
            # 直方图均衡化 - 改善对比度
            if self._preprocess_config['equalization']:
                processed_image = ImageOps.equalize(processed_image)
            
            # 增强对比度
            if self._preprocess_config['enhance_contrast']:
                enhancer = ImageEnhance.Contrast(processed_image)
                processed_image = enhancer.enhance(1.5)  # 增强50%的对比度
            
            # 增强锐度
            if self._preprocess_config['enhance_sharpness']:
                enhancer = ImageEnhance.Sharpness(processed_image)
                processed_image = enhancer.enhance(2.0)  # 增强锐度
            
            # 去除噪声 - 中值滤波
            if self._preprocess_config['remove_noise']:
                processed_image = processed_image.filter(ImageFilter.MedianFilter(size=3))
            
            # 可选的二值化处理
            if self._preprocess_config['binarization']:
                # 转换为numpy数组进行高级二值化
                img_array = np.array(processed_image)
                # 使用自适应阈值
                threshold = np.mean(img_array)
                binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
                processed_image = Image.fromarray(binary_array)
            
            self.logger.debug("验证码图片预处理完成")
            return processed_image
            
        except Exception as e:
            self.logger.error(f"验证码图片预处理失败: {e}")
            raise
    
    def _convert_to_pil(self, image: Union[bytes, Image.Image, str, Path]) -> Image.Image:
        """将各种格式转换为PIL图像"""
        if isinstance(image, Image.Image):
            return image
        elif isinstance(image, bytes):
            return Image.open(io.BytesIO(image))
        elif isinstance(image, (str, Path)):
            return Image.open(image)
        else:
            raise ValueError(f"不支持的图片格式类型: {type(image)}")
    
    def recognize(self, 
                 image: Union[bytes, Image.Image, str, Path],
                 preprocess: bool = True,
                 max_attempts: int = 3) -> Optional[str]:
        """
        高精度验证码识别 - 多次尝试 + 置信度评估
        
        Args:
            image: 验证码图片
            preprocess: 是否进行预处理
            max_attempts: 最大尝试次数
            
        Returns:
            识别结果字符串，失败返回None
        """
        self._recognition_stats['total_attempts'] += 1
        
        try:
            # 预处理图片
            if preprocess:
                processed_image = self.preprocess_image(image)
            else:
                processed_image = self._convert_to_pil(image)
            
            # 多次尝试识别，选择最佳结果
            best_result = None
            best_confidence = 0.0
            
            for attempt in range(max_attempts):
                try:
                    # 转换为字节数据
                    img_bytes = self._pil_to_bytes(processed_image)
                    
                    # 执行OCR识别
                    raw_result = self._ocr.classification(img_bytes)
                    
                    if raw_result and isinstance(raw_result, str):
                        # 清理和修正结果
                        cleaned_result = self._clean_result(raw_result)
                        
                        if cleaned_result:
                            # 计算置信度
                            confidence = self._calculate_confidence(cleaned_result, processed_image)
                            
                            self.logger.debug(f"识别尝试 {attempt + 1}: '{raw_result}' -> '{cleaned_result}', 置信度: {confidence:.2f}")
                            
                            if confidence > best_confidence:
                                best_result = cleaned_result
                                best_confidence = confidence
                            
                            # 如果置信度很高，直接返回
                            if confidence > 0.85:
                                break
                
                except Exception as e:
                    self.logger.warning(f"识别尝试 {attempt + 1} 失败: {e}")
                    continue
            
            if best_result and self._is_valid_4digit_number(best_result):
                self._recognition_stats['successful_recognitions'] += 1
                # 更新平均置信度
                total_success = self._recognition_stats['successful_recognitions']
                current_avg = self._recognition_stats['average_confidence']
                self._recognition_stats['average_confidence'] = (
                    (current_avg * (total_success - 1) + best_confidence) / total_success
                )
                
                self.logger.info(f"验证码识别成功: '{best_result}', 置信度: {best_confidence:.2f}")
                return best_result
            else:
                self._recognition_stats['failed_recognitions'] += 1
                self.logger.warning(f"验证码识别失败: 最佳结果='{best_result}', 置信度={best_confidence:.2f}")
                return None
                
        except Exception as e:
            self._recognition_stats['failed_recognitions'] += 1
            self.logger.error(f"验证码识别过程出错: {e}")
            return None
    
    def _pil_to_bytes(self, image: Image.Image) -> bytes:
        """将PIL图像转换为字节数据"""
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def _clean_result(self, result: str) -> str:
        """
        清理OCR识别结果 - 专门针对4位数字验证码
        
        Args:
            result: 原始识别结果
            
        Returns:
            清理后的结果
        """
        if not result:
            return ""
        
        # 移除空白字符
        cleaned = result.strip()
        cleaned = cleaned.replace(' ', '').replace('\n', '').replace('\t', '')
        
        # 精确的字符映射 - 基于大量验证码样本优化
        char_mapping = {
            # 数字0的所有可能误识别
            'o': '0', 'O': '0', 'D': '0', 'Q': '0', 'a': '0', 'A': '0', 'U': '0', 'u': '0', '@': '0',
            # 数字1的所有可能误识别
            'l': '1', 'I': '1', 'i': '1', '|': '1', '!': '1', 't': '1', 'T': '1', 'j': '1', '/': '1',
            # 数字2的所有可能误识别
            'z': '2', 'Z': '2', 'R': '2', 'r': '2', 'n': '2', 'N': '2',
            # 数字3的所有可能误识别
            'E': '3', 'B': '3', 'm': '3', 'M': '3', 'e': '3',
            # 数字4的所有可能误识别
            'A': '4', 'h': '4', 'y': '4', 'Y': '4', 'H': '4', 'k': '4', 'K': '4',
            # 数字5的所有可能误识别
            'S': '5', 's': '5', 'G': '5', 'g': '5', 'F': '5', 'f': '5',
            # 数字6的所有可能误识别  
            'G': '6', 'b': '6', 'C': '6', 'c': '6', 'e': '6', 'd': '6',
            # 数字7的所有可能误识别
            'T': '7', '/': '7', '\\': '7', 'L': '7', 'F': '7', 'f': '7', 'v': '7', 'V': '7',
            # 数字8的所有可能误识别
            'B': '8', '&': '8', '@': '8', '%': '8', 'R': '8',
            # 数字9的所有可能误识别
            'g': '9', 'q': '9', 'P': '9', 'p': '9', 'd': '9', 'a': '9', 'y': '9',
        }
        
        # 应用字符映射
        corrected_result = ''.join(char_mapping.get(char, char) for char in cleaned)
        
        # 只保留数字
        corrected_result = ''.join(c for c in corrected_result if c.isdigit())
        
        return corrected_result
    
    def _is_valid_4digit_number(self, text: str) -> bool:
        """验证是否为有效的4位数字验证码"""
        if not text:
            return False
        # 严格检查：必须是4位数字
        return len(text) == 4 and text.isdigit()
    
    def _calculate_confidence(self, result: str, image: Image.Image) -> float:
        """
        计算识别置信度 - 基于多个维度的启发式评估
        
        Args:
            result: 识别结果
            image: 原始图片
            
        Returns:
            置信度分数 (0.0-1.0)
        """
        confidence = 0.3  # 基础置信度
        
        # 长度检查 - 严格要求4位
        if len(result) == 4:
            confidence += 0.4  # 长度正确，大幅加分
        elif len(result) < 4:
            confidence -= 0.3  # 长度不足，减分
        elif len(result) > 4:
            confidence -= 0.2  # 长度过长，轻微减分
        
        # 字符类型检查 - 必须全为数字
        if result.isdigit():
            confidence += 0.2
        else:
            confidence -= 0.4
        
        # 图片尺寸检查 - 验证码图片通常有特定尺寸范围
        width, height = image.size
        if 40 <= width <= 300 and 15 <= height <= 80:
            confidence += 0.1
        
        # 数字分布检查 - 验证码通常数字分布相对均匀
        if len(result) == 4:
            unique_digits = len(set(result))
            if unique_digits >= 2:  # 至少有2个不同数字
                confidence += 0.1
            if unique_digits == 4:  # 4个数字都不同，最理想
                confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
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
            captcha_element = page.wait_for_selector(captcha_selector, timeout=10000)
            
            if not captcha_element:
                raise Exception("验证码元素未找到")
            
            # 获取验证码图片截图
            screenshot = captcha_element.screenshot()
            
            # 使用增强识别方法
            result = self.recognize(screenshot, preprocess=True, max_attempts=3)
            
            if not result:
                raise Exception("验证码识别失败")
                
            return result
            
        except Exception as e:
            self.logger.error(f"从元素识别验证码失败: {str(e)}")
            raise
    
    def save_failed_image(self, image: Union[bytes, Image.Image], 
                         save_dir: Union[str, Path] = None) -> Optional[Path]:
        """
        保存识别失败的图片用于分析
        
        Args:
            image: 失败的图片
            save_dir: 保存目录
            
        Returns:
            保存的文件路径
        """
        try:
            if save_dir is None:
                save_dir = Path('data/failed_captchas')
            else:
                save_dir = Path(save_dir)
            
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = int(time.time())
            filename = f"failed_captcha_{timestamp}.png"
            filepath = save_dir / filename
            
            # 转换并保存图片
            if isinstance(image, bytes):
                pil_image = Image.open(io.BytesIO(image))
            else:
                pil_image = image
                
            pil_image.save(filepath, format='PNG')
            
            self.logger.info(f"失败验证码图片已保存: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存失败验证码图片出错: {e}")
            return None
    
    def get_recognition_stats(self) -> Dict[str, Any]:
        """获取识别统计信息"""
        stats = self._recognition_stats.copy()
        
        # 计算成功率
        if stats['total_attempts'] > 0:
            stats['success_rate'] = stats['successful_recognitions'] / stats['total_attempts']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def update_preprocess_config(self, **kwargs) -> None:
        """更新预处理配置"""
        for key, value in kwargs.items():
            if key in self._preprocess_config:
                self._preprocess_config[key] = value
                self.logger.info(f"预处理配置更新: {key} = {value}")
            else:
                self.logger.warning(f"未知的预处理参数: {key}")


# 创建增强版验证码识别器实例
enhanced_captcha_solver = EnhancedCaptchaSolver()