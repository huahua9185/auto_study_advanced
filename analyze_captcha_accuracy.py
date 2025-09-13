#!/usr/bin/env python3
"""
验证码识别准确率分析工具
分析当前验证码识别的问题并提供优化建议
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import time
import logging
from PIL import Image
import io
from src.captcha_solver import CaptchaSolver
from src.pure_api_learner import PureAPILearner

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

def collect_captcha_samples(num_samples: int = 20):
    """收集验证码样本进行分析"""
    print(f"🔍 收集 {num_samples} 个验证码样本...")

    samples = []
    session = requests.Session()
    captcha_url = "https://edu.nxgbjy.org.cn/device/login!get_auth_code.do"

    for i in range(num_samples):
        try:
            print(f"获取样本 {i+1}/{num_samples}...")

            response = session.get(captcha_url)
            if response.status_code == 200:
                # 保存验证码图片
                filename = f"captcha_sample_{i+1:03d}.png"
                with open(filename, 'wb') as f:
                    f.write(response.content)

                samples.append({
                    'filename': filename,
                    'image_data': response.content,
                    'size': len(response.content)
                })

                print(f"  已保存: {filename} ({len(response.content)} bytes)")
            else:
                print(f"  获取失败: HTTP {response.status_code}")

            time.sleep(0.5)  # 避免过于频繁的请求

        except Exception as e:
            print(f"  样本 {i+1} 异常: {e}")

    print(f"✅ 成功收集 {len(samples)} 个验证码样本")
    return samples

def analyze_captcha_samples(samples):
    """分析验证码样本的特征"""
    print("\n📊 分析验证码样本特征...")

    solver = CaptchaSolver()
    results = []

    for i, sample in enumerate(samples, 1):
        try:
            print(f"分析样本 {i}/{len(samples)}: {sample['filename']}")

            # 打开图片分析
            image = Image.open(io.BytesIO(sample['image_data']))
            width, height = image.size
            mode = image.mode

            print(f"  图片尺寸: {width}x{height}, 模式: {mode}")

            # 使用原版高识别率方法
            raw_results = []
            processed_results = []

            # 多次识别获取稳定性
            for attempt in range(3):
                try:
                    raw_result = solver.ocr.classification(sample['image_data'])
                    raw_results.append(raw_result)

                    # 使用原版的solve_captcha_from_bytes方法
                    processed_result = solver.solve_captcha_from_bytes(sample['image_data'])
                    processed_results.append(processed_result)

                except Exception as e:
                    print(f"    识别异常: {e}")

            # 分析一致性
            raw_consistency = len(set(raw_results)) / len(raw_results) if raw_results else 0
            processed_consistency = len(set(processed_results)) / len(processed_results) if processed_results else 0

            result = {
                'filename': sample['filename'],
                'size': sample['size'],
                'dimensions': (width, height),
                'mode': mode,
                'raw_results': raw_results,
                'processed_results': processed_results,
                'raw_consistency': raw_consistency,
                'processed_consistency': processed_consistency
            }

            results.append(result)

            print(f"  原始识别: {raw_results}")
            print(f"  处理后识别: {processed_results}")
            print(f"  原始一致性: {raw_consistency:.2f}, 处理后一致性: {processed_consistency:.2f}")

        except Exception as e:
            print(f"  分析异常: {e}")

    return results

def analyze_recognition_patterns(results):
    """分析识别模式和问题"""
    print("\n🔍 分析识别模式...")

    # 统计字符识别准确率
    all_raw_results = []
    all_processed_results = []

    for result in results:
        all_raw_results.extend(result['raw_results'])
        all_processed_results.extend(result['processed_results'])

    print(f"总识别次数: {len(all_raw_results)}")

    # 分析字符长度分布
    length_distribution = {}
    for result in all_processed_results:
        if result:
            length = len(result)
            length_distribution[length] = length_distribution.get(length, 0) + 1

    print("字符长度分布:")
    for length, count in sorted(length_distribution.items()):
        print(f"  {length}位: {count} 次 ({count/len(all_processed_results)*100:.1f}%)")

    # 分析常见字符
    all_chars = ''.join(all_processed_results)
    char_freq = {}
    for char in all_chars:
        if char.isdigit():
            char_freq[char] = char_freq.get(char, 0) + 1

    print("数字字符频率:")
    for char, freq in sorted(char_freq.items()):
        print(f"  {char}: {freq} 次")

    # 识别一致性统计
    high_consistency = sum(1 for r in results if r['processed_consistency'] >= 0.7)
    print(f"\n一致性分析:")
    print(f"  高一致性(>=70%): {high_consistency}/{len(results)} ({high_consistency/len(results)*100:.1f}%)")

    return {
        'length_distribution': length_distribution,
        'char_frequency': char_freq,
        'high_consistency_rate': high_consistency / len(results) if results else 0
    }

def suggest_improvements(analysis_results):
    """基于分析结果提供改进建议"""
    print("\n💡 识别率改进建议:")

    # 基于长度分布的建议
    length_dist = analysis_results['length_distribution']
    if 4 in length_dist and length_dist[4] / sum(length_dist.values()) > 0.8:
        print("✅ 验证码主要是4位数字，当前识别策略合适")
    else:
        print("⚠️ 验证码长度不稳定，需要改进长度处理逻辑")

    # 基于一致性的建议
    if analysis_results['high_consistency_rate'] < 0.6:
        print("⚠️ 识别一致性较低，建议:")
        print("   1. 增加图像预处理步骤")
        print("   2. 使用更多识别模型投票")
        print("   3. 改进字符后处理逻辑")
    else:
        print("✅ 识别一致性良好")

    return [
        "使用更强的图像预处理",
        "增加多模型投票机制",
        "改进字符过滤和修正",
        "增加识别重试机制",
        "优化ddddocr参数"
    ]

def create_enhanced_captcha_solver():
    """创建增强版验证码识别器"""
    print("\n🔧 创建增强版验证码识别器...")

    enhanced_solver_code = '''#!/usr/bin/env python3
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
'''

    # 保存增强版识别器
    with open('src/enhanced_captcha_solver.py', 'w', encoding='utf-8') as f:
        f.write(enhanced_solver_code)

    print("✅ 增强版验证码识别器已创建: src/enhanced_captcha_solver.py")

if __name__ == "__main__":
    print("🧪 验证码识别准确率分析")
    print("=" * 60)

    try:
        # 1. 收集样本
        samples = collect_captcha_samples(10)  # 收集10个样本进行快速分析

        if not samples:
            print("❌ 无法收集验证码样本")
            exit(1)

        # 2. 分析样本
        results = analyze_captcha_samples(samples)

        # 3. 分析模式
        analysis = analyze_recognition_patterns(results)

        # 4. 提供建议
        suggestions = suggest_improvements(analysis)

        # 5. 创建增强版识别器
        create_enhanced_captcha_solver()

        print("\n✅ 验证码分析完成！")
        print("📁 生成的文件:")
        print("  - 验证码样本: captcha_sample_*.png")
        print("  - 增强识别器: src/enhanced_captcha_solver.py")

    except Exception as e:
        print(f"❌ 分析异常: {e}")
        import traceback
        traceback.print_exc()