#!/usr/bin/env python3
"""
验证登录界面跳动修复效果的简化测试脚本
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from config.config import Config
import time

def verify_login_stability_fix():
    """验证登录稳定性修复效果"""
    print("🧪 验证登录界面跳动修复效果")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        try:
            # 1. 访问网站
            print("1. 访问网站...")
            page.goto(Config.BASE_URL.rstrip('#/'))
            page.wait_for_load_state('networkidle')
            
            # 2. 点击登录按钮触发模态框
            print("2. 触发登录模态框...")
            page.click('text=登录')
            page.wait_for_selector('.el-dialog', timeout=5000)
            print("   ✅ 登录框已出现")
            
            # 3. 应用我们的修复方案
            print("3. 应用稳定性修复...")
            fix_result = page.evaluate('''
                () => {
                    // 应用CSS修复
                    const style = document.createElement('style');
                    style.textContent = `
                        .el-dialog * {
                            transition: none !important;
                            animation: none !important;
                        }
                        .el-input__inner {
                            transition: none !important;
                        }
                        .el-input__prefix {
                            transition: none !important;
                        }
                        .el-input__icon {
                            transition: none !important;
                        }
                        .el-dialog.el-dialog--center {
                            position: fixed !important;
                            top: 50% !important;
                            left: 50% !important;
                            transform: translate(-50%, -50%) !important;
                            margin: 0 !important;
                        }
                        img[src*="code"], img[src*="auth"] {
                            width: 110px !important;
                            height: 40px !important;
                            display: block !important;
                        }
                    `;
                    style.id = 'stability-fix';
                    document.head.appendChild(style);
                    
                    // 修复模态框层级
                    const modals = document.querySelectorAll('[class*="dialog"], [class*="modal"]');
                    let modalCount = 0;
                    modals.forEach((modal) => {
                        if (modal.classList.contains('v-modal')) {
                            modal.style.zIndex = '2000';
                        } else if (modal.classList.contains('el-dialog__wrapper')) {
                            modal.style.zIndex = '2001';
                        }
                        modalCount++;
                    });
                    
                    // 强制稳定主对话框
                    const dialog = document.querySelector('.el-dialog.el-dialog--center');
                    if (dialog) {
                        dialog.style.position = 'fixed';
                        dialog.style.top = '50%';
                        dialog.style.left = '50%';
                        dialog.style.transform = 'translate(-50%, -50%)';
                        dialog.style.margin = '0';
                    }
                    
                    return {
                        styleApplied: true,
                        modalCount: modalCount,
                        dialogFixed: !!dialog
                    };
                }
            ''')
            
            if fix_result['styleApplied']:
                print(f"   ✅ CSS修复已应用")
                print(f"   📊 检测到 {fix_result['modalCount']} 个模态框元素")
                print(f"   🎯 主对话框定位: {'已固定' if fix_result['dialogFixed'] else '未找到'}")
            
            # 4. 检查修复效果
            print("4. 检查修复效果...")
            
            # 检查输入框动画是否禁用
            input_check = page.evaluate('''
                () => {
                    const inputs = document.querySelectorAll('.el-input__inner');
                    let disabledCount = 0;
                    inputs.forEach(input => {
                        const style = window.getComputedStyle(input);
                        if (style.transition === 'none') {
                            disabledCount++;
                        }
                    });
                    return {
                        total: inputs.length,
                        disabled: disabledCount
                    };
                }
            ''')
            
            print(f"   📝 输入框动画禁用: {input_check['disabled']}/{input_check['total']}")
            
            # 检查验证码固定尺寸
            captcha_check = page.evaluate('''
                () => {
                    const captcha = document.querySelector('img[src*="code"], img[src*="auth"]');
                    if (captcha) {
                        const style = window.getComputedStyle(captcha);
                        return {
                            found: true,
                            width: style.width,
                            height: style.height
                        };
                    }
                    return {found: false};
                }
            ''')
            
            if captcha_check['found']:
                print(f"   🖼️ 验证码尺寸: {captcha_check['width']} x {captcha_check['height']}")
            else:
                print("   ℹ️ 未检测到验证码图片")
            
            # 5. 稳定性观察
            print("5. 稳定性观察 (10秒)...")
            print("   请观察登录框是否还有跳动...")
            
            for i in range(10):
                time.sleep(1)
                
                # 检查模态框位置稳定性
                position = page.evaluate('''
                    () => {
                        const dialog = document.querySelector('.el-dialog.el-dialog--center');
                        if (dialog) {
                            const rect = dialog.getBoundingClientRect();
                            return {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y)
                            };
                        }
                        return null;
                    }
                ''')
                
                print(f"   第{i+1}秒: 位置 {position}")
            
            print("\n✅ 修复效果验证完成!")
            print("如果位置数值保持稳定，说明跳动问题已解决")
            
            # 保持页面打开供观察
            input("\n按Enter键关闭浏览器...")
            
        except Exception as e:
            print(f"❌ 测试过程出错: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            browser.close()

if __name__ == "__main__":
    verify_login_stability_fix()