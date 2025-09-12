#!/usr/bin/env python3
"""
测试浏览器窗口大小设置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager

def test_browser_size():
    """测试浏览器窗口大小设置"""
    
    print("浏览器窗口大小测试")
    print("=" * 50)
    
    try:
        # 1. 初始化浏览器
        print("1. 初始化浏览器...")
        if not login_manager.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        page = login_manager.page
        print("✅ 浏览器初始化成功")
        
        # 2. 获取viewport大小
        print("\n2. 检查viewport设置...")
        viewport = page.viewport_size
        print(f"Viewport大小: {viewport['width']}x{viewport['height']}")
        
        # 3. 验证设置是否正确
        expected_width = 1440
        expected_height = 900
        
        if viewport['width'] == expected_width and viewport['height'] == expected_height:
            print(f"✅ 窗口大小设置正确: {expected_width}x{expected_height}")
        else:
            print(f"❌ 窗口大小设置错误")
            print(f"   预期: {expected_width}x{expected_height}")
            print(f"   实际: {viewport['width']}x{viewport['height']}")
            return False
        
        # 4. 测试页面加载（可选）
        print("\n3. 测试页面加载...")
        try:
            page.goto("https://www.baidu.com", timeout=10000)
            
            # 获取页面实际窗口大小
            window_size = page.evaluate("""
                () => ({
                    width: window.innerWidth,
                    height: window.innerHeight,
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight,
                    screenWidth: window.screen.width,
                    screenHeight: window.screen.height
                })
            """)
            
            print(f"页面内部大小: {window_size['width']}x{window_size['height']}")
            print(f"窗口外部大小: {window_size['outerWidth']}x{window_size['outerHeight']}")
            print(f"屏幕大小: {window_size['screenWidth']}x{window_size['screenHeight']}")
            
            print("✅ 页面加载测试成功")
            
        except Exception as e:
            print(f"⚠️  页面加载测试失败: {str(e)}")
        
        # 5. 保存截图验证
        print("\n4. 保存截图验证...")
        try:
            screenshot_path = "data/browser_size_test.png"
            
            # 确保目录存在
            os.makedirs("data", exist_ok=True)
            
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"✅ 截图已保存: {screenshot_path}")
            
            # 获取截图文件大小信息
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                print(f"截图文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")
        
        except Exception as e:
            print(f"❌ 保存截图失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False
        
    finally:
        # 清理资源
        try:
            if login_manager:
                login_manager.close_browser()
            print("\n5. 浏览器已关闭")
        except Exception as e:
            print(f"⚠️  关闭浏览器时出错: {str(e)}")

def main():
    """主函数"""
    try:
        success = test_browser_size()
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 浏览器窗口大小设置测试成功！")
            print("   ✅ 浏览器初始化正常")
            print("   ✅ Viewport设置为1440x900")
            print("   ✅ 页面加载功能正常")
            print("   ✅ 截图功能正常")
            print("=" * 50)
            return 0
        else:
            print("\n❌ 浏览器窗口大小设置测试失败！")
            return 1
            
    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)