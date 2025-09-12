#!/usr/bin/env python3
"""
批量测试验证码识别准确率
用于收集样本和优化识别算法
"""

import sys
from pathlib import Path
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from config.config import Config
from src.captcha_solver import captcha_solver
import json

def test_batch_captcha(num_samples=10):
    """批量测试验证码识别"""
    print(f"=== 批量验证码识别测试 ({num_samples}个样本) ===")
    results = []
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        try:
            # 访问主页
            print("正在访问主页...")
            page.goto(Config.BASE_URL)
            page.wait_for_load_state('networkidle')
            
            # 点击登录按钮
            print("点击登录按钮...")
            page.click('text=登录')
            page.wait_for_load_state('networkidle')
            
            for i in range(num_samples):
                print(f"\n--- 样本 {i+1}/{num_samples} ---")
                
                # 查找验证码图片
                captcha_image = page.locator('img[src*="/device/login!get_auth_code.do"]').first
                
                if captcha_image:
                    # 截图保存
                    screenshot_path = f"data/captcha_sample_{i+1}.png"
                    captcha_image.screenshot(path=screenshot_path)
                    print(f"验证码已保存: {screenshot_path}")
                    
                    # 识别验证码
                    result = captcha_solver.solve_captcha_from_element(
                        page, 
                        'img[src*="/device/login!get_auth_code.do"]'
                    )
                    
                    print(f"识别结果: {result}")
                    
                    # 记录结果
                    results.append({
                        'sample': i+1,
                        'screenshot': screenshot_path,
                        'result': result,
                        'length': len(result) if result else 0
                    })
                    
                    # 刷新验证码
                    if i < num_samples - 1:
                        print("刷新验证码...")
                        captcha_image.click()
                        time.sleep(2)
                
        except Exception as e:
            print(f"测试过程中发生错误: {str(e)}")
            
        finally:
            browser.close()
    
    # 保存测试结果
    with open('data/captcha_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 统计分析
    print("\n=== 测试结果统计 ===")
    print(f"总样本数: {len(results)}")
    
    if results:
        lengths = [r['length'] for r in results]
        print(f"识别长度分布: {set(lengths)}")
        print(f"最常见长度: {max(set(lengths), key=lengths.count)}")
        
        # 分析字符类型
        all_chars = ''.join([r['result'] for r in results if r['result']])
        digit_count = sum(c.isdigit() for c in all_chars)
        letter_count = sum(c.isalpha() for c in all_chars)
        
        print(f"数字字符占比: {digit_count}/{len(all_chars)} ({digit_count/len(all_chars)*100:.1f}%)")
        print(f"字母字符占比: {letter_count}/{len(all_chars)} ({letter_count/len(all_chars)*100:.1f}%)")

if __name__ == "__main__":
    test_batch_captcha(5)  # 测试5个样本