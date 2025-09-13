#!/usr/bin/env python3
"""
增强版验证码识别器 - 专门优化登录验证码识别率
基于分析结果的改进版本
"""

import ddddocr
import base64
import io
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import logging
import numpy as np
from collections import Counter
import warnings
import os
import re

# 抑制警告
os.environ['ORT_DISABLE_ALL_WARNING'] = '1'
warnings.filterwarnings('ignore', category=UserWarning, module='onnxruntime')

try:
    from src.pillow_fix import *
except:
    pass

class EnhancedCaptchaSolver:
    def __init__(self):
        """初始化增强版验证码识别器"""
        try:
            # 创建多个OCR实例以提高准确率
            self.ocr_instances = []
            for i in range(3):  # 使用3个实例
                try:
                    ocr = ddddocr.DdddOcr(show_ad=False)
                    self.ocr_instances.append(ocr)
                except TypeError:
                    ocr = ddddocr.DdddOcr()
                    self.ocr_instances.append(ocr)
        except Exception as e:
            print(f"OCR初始化失败: {e}")
            # 至少保证有一个实例
            try:
                self.ocr_instances = [ddddocr.DdddOcr(show_ad=False)]
            except:
                self.ocr_instances = [ddddocr.DdddOcr()]

        self.logger = logging.getLogger(__name__)

        # 字符修正字典（基于常见识别错误）
        self.char_corrections = {
            'o': '0', 'O': '0', 'l': '1', 'I': '1',
            'S': '5', 's': '5', 'G': '6', 'g': '9',
            'q': '9', 'Q': '0', 'Z': '2', 'z': '2'
        }

    def enhance_image(self, image_data: bytes) -> list:
        """增强图像处理，返回多个处理版本"""
        processed_images = []

        try:
            # 打开原始图片
            original_image = Image.open(io.BytesIO(image_data))

            # 确保是RGB模式
            if original_image.mode != 'RGB':
                original_image = original_image.convert('RGB')

            # 方法1: 原始图片
            img1 = io.BytesIO()
            original_image.save(img1, format='PNG')
            processed_images.append(img1.getvalue())

            # 方法2: 灰度化 + 对比度增强
            gray_image = original_image.convert('L')
            enhancer = ImageEnhance.Contrast(gray_image)
            enhanced = enhancer.enhance(2.0)  # 增强对比度
            img2 = io.BytesIO()
            enhanced.save(img2, format='PNG')
            processed_images.append(img2.getvalue())

            # 方法3: 二值化处理
            threshold = 128
            binary_image = gray_image.point(lambda x: 255 if x > threshold else 0, mode='1')
            img3 = io.BytesIO()
            binary_image.save(img3, format='PNG')
            processed_images.append(img3.getvalue())

            # 方法4: 锐化处理
            sharpened = original_image.filter(ImageFilter.SHARPEN)
            img4 = io.BytesIO()
            sharpened.save(img4, format='PNG')
            processed_images.append(img4.getvalue())

            # 方法5: 降噪处理
            denoised = original_image.filter(ImageFilter.MedianFilter(size=3))
            img5 = io.BytesIO()
            denoised.save(img5, format='PNG')
            processed_images.append(img5.getvalue())

        except Exception as e:
            self.logger.error(f"图像处理异常: {e}")
            # 至少返回原图
            processed_images = [image_data]

        return processed_images

    def correct_characters(self, text: str) -> str:
        """字符修正"""
        if not text:
            return text

        corrected = ""
        for char in text:
            corrected += self.char_corrections.get(char, char)

        return corrected

    def validate_result(self, result: str) -> bool:
        """验证识别结果是否合理"""
        if not result:
            return False

        # 长度检查
        if len(result) < 3 or len(result) > 6:
            return False

        # 字符检查 - 应该主要是数字
        digit_count = sum(1 for c in result if c.isdigit())
        if digit_count / len(result) < 0.7:  # 至少70%是数字
            return False

        return True

    def solve_captcha_enhanced(self, image_data: bytes, max_attempts: int = 5) -> str:
        """增强版验证码识别"""
        try:
            all_results = []

            # 多次尝试识别
            for attempt in range(max_attempts):
                # 获取增强的图像
                enhanced_images = self.enhance_image(image_data)

                # 对每个处理版本使用多个OCR实例
                for img_data in enhanced_images:
                    for ocr in self.ocr_instances:
                        try:
                            raw_result = ocr.classification(img_data)
                            if raw_result:
                                # 字符修正
                                corrected = self.correct_characters(raw_result.strip())

                                # 只保留数字
                                digits_only = ''.join(c for c in corrected if c.isdigit())

                                if self.validate_result(digits_only):
                                    all_results.append(digits_only)
                        except Exception as e:
                            continue

                # 如果已经有足够的结果，可以提前结束
                if len(all_results) >= 10:
                    break

                time.sleep(0.1)  # 短暂延迟

            if not all_results:
                return None

            # 投票选择最佳结果
            result_counter = Counter(all_results)

            # 优先选择4位数字的结果
            four_digit_results = [r for r in all_results if len(r) == 4]
            if four_digit_results:
                four_digit_counter = Counter(four_digit_results)
                most_common = four_digit_counter.most_common(1)[0]
                if most_common[1] >= 2:  # 至少出现2次
                    return most_common[0]

            # 如果没有4位数字，选择最常见的
            most_common = result_counter.most_common(1)[0]
            if most_common[1] >= 2:  # 至少出现2次
                return most_common[0]

            # 如果都只出现1次，选择第一个4位数字结果
            for result in all_results:
                if len(result) == 4:
                    return result

            # 最后选择任意一个有效结果
            return all_results[0] if all_results else None

        except Exception as e:
            self.logger.error(f"增强识别异常: {e}")
            return None

    def solve_captcha_from_bytes(self, image_data: bytes) -> str:
        """兼容原版接口的增强识别"""
        return self.solve_captcha_enhanced(image_data)
