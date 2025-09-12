#!/usr/bin/env python3
"""
修复登录界面跳动问题的解决方案
根据login_modal_analysis.json的分析结果
"""

def inject_stability_fixes(page):
    """注入CSS和JavaScript来修复页面跳动问题"""
    
    stability_script = """
    // 1. 修复模态框层级冲突
    function fixModalLayering() {
        const modals = document.querySelectorAll('[class*="dialog"], [class*="modal"]');
        modals.forEach((modal, index) => {
            if (modal.classList.contains('v-modal')) {
                modal.style.zIndex = '2000';
            } else if (modal.classList.contains('el-dialog__wrapper')) {
                modal.style.zIndex = '2001';
            }
        });
    }

    // 2. 禁用输入框过渡动画（减少重绘）
    function disableInputTransitions() {
        const style = document.createElement('style');
        style.textContent = `
            .el-input__inner {
                transition: none !important;
            }
            .el-input__prefix {
                transition: none !important;
            }
            .el-input__icon {
                transition: none !important;
            }
            /* 禁用所有登录框内的动画 */
            .el-dialog * {
                transition: none !important;
                animation: none !important;
            }
        `;
        document.head.appendChild(style);
    }

    // 3. 修复验证码加载导致的布局跳动
    function fixCaptchaLayout() {
        const captchaContainer = document.querySelector('img[src*="code"], img[src*="auth"]');
        if (captchaContainer) {
            // 预设固定尺寸避免加载时跳动
            captchaContainer.style.width = '110px';
            captchaContainer.style.height = '40px';
            captchaContainer.style.display = 'block';
        }
    }

    // 4. 强制模态框位置稳定
    function stabilizeModalPosition() {
        const dialog = document.querySelector('.el-dialog.el-dialog--center');
        if (dialog) {
            dialog.style.position = 'fixed';
            dialog.style.top = '50%';
            dialog.style.left = '50%';
            dialog.style.transform = 'translate(-50%, -50%)';
            dialog.style.margin = '0';
        }
    }

    // 5. 监控并阻止布局抖动
    function preventLayoutThrashing() {
        let isStabilizing = false;
        
        const observer = new MutationObserver((mutations) => {
            if (isStabilizing) return;
            
            let needsStabilization = false;
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' || 
                    (mutation.type === 'attributes' && 
                     ['style', 'class'].includes(mutation.attributeName))) {
                    needsStabilization = true;
                }
            });
            
            if (needsStabilization) {
                isStabilizing = true;
                requestAnimationFrame(() => {
                    fixModalLayering();
                    stabilizeModalPosition();
                    fixCaptchaLayout();
                    
                    setTimeout(() => {
                        isStabilizing = false;
                    }, 100);
                });
            }
        });

        // 监控登录框内的变化
        const loginModal = document.querySelector('.el-dialog');
        if (loginModal) {
            observer.observe(loginModal, {
                childList: true,
                attributes: true,
                subtree: true
            });
        }
    }

    // 执行所有修复
    fixModalLayering();
    disableInputTransitions();
    fixCaptchaLayout();
    stabilizeModalPosition();
    preventLayoutThrashing();

    console.log('✅ 页面跳动修复已应用');
    """
    
    try:
        page.evaluate(stability_script)
        return True
    except Exception as e:
        print(f"❌ 注入修复脚本失败: {e}")
        return False

def apply_login_stability_fix(login_instance):
    """在登录过程中应用稳定性修复"""
    
    try:
        # 等待登录框出现
        login_instance.page.wait_for_selector('.el-dialog', timeout=5000)
        
        # 应用修复
        success = inject_stability_fixes(login_instance.page)
        
        if success:
            # 额外等待确保修复生效
            login_instance.page.wait_for_timeout(500)
            print("✅ 登录界面跳动修复已应用")
        
        return success
        
    except Exception as e:
        print(f"❌ 应用登录稳定性修复失败: {e}")
        return False

# 测试修复效果的独立脚本
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from playwright.sync_api import sync_playwright
    from config.config import Config
    import time
    
    def test_stability_fix():
        """测试修复效果"""
        print("🧪 测试登录界面跳动修复效果...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=1000)
            page = browser.new_page()
            
            try:
                # 访问网站
                page.goto(Config.BASE_URL.rstrip('#/'))
                page.wait_for_load_state('networkidle')
                
                # 点击登录按钮
                page.click('text=登录')
                page.wait_for_selector('.el-dialog', timeout=5000)
                
                print("⏱️ 登录框已出现，开始监测跳动...")
                
                # 应用修复
                success = inject_stability_fixes(page)
                
                if success:
                    print("✅ 修复已应用，观察10秒...")
                    
                    # 监控10秒，观察是否还有跳动
                    for i in range(10):
                        time.sleep(1)
                        print(f"   监控进度: {i+1}/10 秒")
                    
                    print("✅ 监控完成，请检查界面是否稳定")
                else:
                    print("❌ 修复应用失败")
                
                # 保持页面打开一段时间供观察
                input("按Enter键关闭浏览器...")
                
            except Exception as e:
                print(f"❌ 测试过程出错: {e}")
            
            finally:
                browser.close()
    
    test_stability_fix()