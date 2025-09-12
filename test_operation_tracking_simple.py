#!/usr/bin/env python3
"""
简化的操作跟踪测试脚本
专门用于测试页面操作编号功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from operation_tracker import OperationTracker
from config.config import Config
import time

def test_simple_operations():
    """简化的操作跟踪测试"""
    print("🎯 简化的页面操作跟踪测试")
    print("=" * 60)
    print("💡 每个操作都会分配编号，帮助您定位页面跳动")
    print("-" * 60)
    
    tracker = OperationTracker()
    
    try:
        # 1. 初始化浏览器
        print("\n🚀 第1步: 初始化浏览器")
        if not tracker.login_manager.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        print("✅ 浏览器初始化成功")
        
        # 2. 导航到登录页面
        print("\n📍 第2步: 导航到页面")
        login_url = Config.BASE_URL.rstrip('#/')
        if not tracker.tracked_navigate(login_url, "导航到主页面"):
            print("❌ 导航失败")
            return False
        
        print("\n⏳ 等待3秒，观察页面初始状态...")
        time.sleep(3)
        
        # 3. 查找登录相关元素（不点击，只检查）
        print("\n🔍 第3步: 查找页面元素")
        login_selectors = [
            '.login-btn',
            'button:has-text("登录")',
            'button:has-text("登陆")',
            '[class*="login"]'
        ]
        
        for i, selector in enumerate(login_selectors):
            print(f"\n🔍 检查选择器 {i+1}: {selector}")
            element = tracker.tracked_wait_for_selector(selector, f"查找选择器 {i+1}", timeout=2000)
            if element:
                print(f"   ✅ 找到元素: {selector}")
                break
            else:
                print(f"   ❌ 未找到元素: {selector}")
            time.sleep(1)
        
        # 4. 执行一些JavaScript操作
        print("\n🔧 第4步: 执行页面检查脚本")
        
        # 检查页面基本信息
        page_info_script = """
        const info = {
            title: document.title,
            url: window.location.href,
            readyState: document.readyState,
            elementCount: document.querySelectorAll('*').length
        };
        console.log('页面信息:', info);
        return info;
        """
        
        info = tracker.tracked_evaluate(page_info_script, "获取页面基本信息")
        if info:
            print(f"   页面标题: {info.get('title', 'N/A')}")
            print(f"   页面URL: {info.get('url', 'N/A')}")
            print(f"   元素数量: {info.get('elementCount', 'N/A')}")
        
        time.sleep(2)
        
        # 5. 模拟一些可能引起跳动的操作
        print("\n⚠️ 第5步: 执行可能引起跳动的操作")
        
        # 滚动页面
        scroll_script = "window.scrollTo(0, 100);"
        tracker.tracked_evaluate(scroll_script, "页面向下滚动100px")
        time.sleep(1)
        
        # 修改样式
        style_script = """
        const style = document.createElement('style');
        style.textContent = 'body { margin: 0 !important; }';
        document.head.appendChild(style);
        """
        tracker.tracked_evaluate(style_script, "应用页面样式修改")
        time.sleep(1)
        
        # 检查模态框
        modal_script = "document.querySelectorAll('.el-dialog, .modal, [role=\"dialog\"]').length"
        modal_count = tracker.tracked_evaluate(modal_script, "检查页面模态框数量")
        print(f"   页面模态框数量: {modal_count}")
        
        time.sleep(2)
        
        # 6. 尝试触发登录框（如果存在）
        print("\n🎯 第6步: 尝试触发登录相关操作")
        
        trigger_selectors = [
            'button:has-text("登录")',
            'button:has-text("登陆")', 
            '.login-btn',
            '[class*="login"]'
        ]
        
        triggered = False
        for selector in trigger_selectors:
            try:
                result = tracker.tracked_click(selector, f"尝试点击: {selector}")
                if result:
                    print(f"   ✅ 成功点击: {selector}")
                    triggered = True
                    break
            except:
                print(f"   ❌ 点击失败: {selector}")
            time.sleep(1)
        
        if triggered:
            print("\n⏳ 登录操作触发后，等待5秒观察页面变化...")
            time.sleep(5)
            
            # 再次检查模态框
            modal_count2 = tracker.tracked_evaluate(modal_script, "再次检查模态框数量")
            print(f"   触发后模态框数量: {modal_count2}")
        
        # 7. 保存操作日志
        tracker.save_operations_log("simple_operation_test.json")
        
        print(f"\n✅ 测试完成！")
        print(f"   总操作数: {tracker.operation_counter}")
        print(f"   📄 详细日志: simple_operation_test.json")
        print(f"\n💡 使用说明:")
        print(f"   - 如果看到页面跳动，请记录跳动发生在哪个操作编号之后")
        print(f"   - 查看JSON日志文件找到对应操作的详细信息")
        print(f"   - 重点关注JavaScript执行(evaluate)和点击(click)操作")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存错误日志
        tracker.save_operations_log("simple_operation_error.json")
        return False
    
    finally:
        try:
            input("\n🔚 按回车键关闭浏览器...")
            tracker.login_manager.close_browser()
        except:
            pass

if __name__ == "__main__":
    test_simple_operations()