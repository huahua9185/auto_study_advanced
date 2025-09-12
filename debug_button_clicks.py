#!/usr/bin/env python3
"""
调试按钮点击行为脚本
专门分析点击"继续学习"按钮后的页面变化和URL获取
"""

import sys
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager
from config.config import Config

def debug_button_clicks():
    """调试按钮点击行为"""
    print("开始调试按钮点击行为")
    print("=" * 60)
    
    try:
        # 初始化浏览器
        print("1. 初始化浏览器...")
        if not login_manager.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        page = login_manager.page
        
        # 登录
        print("2. 登录...")
        if not login_manager.check_login_status():
            if not login_manager.login():
                print("❌ 登录失败")
                return False
        print("✅ 登录成功")
        
        # 访问必修课页面
        print("\n3. 分析必修课按钮点击行为...")
        page.goto(Config.REQUIRED_COURSES_URL, wait_until='networkidle')
        time.sleep(3)
        
        # 设置页面导航监听
        navigation_info = []
        
        def on_navigation(request):
            navigation_info.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'timestamp': time.time()
            })
            print(f"🌐 捕获到导航请求: {request.method} {request.url}")
        
        # 监听所有请求
        page.on('request', on_navigation)
        
        # 找到第一个继续学习按钮
        buttons = page.locator('button:has-text("继续学习")').all()
        if not buttons:
            print("❌ 未找到继续学习按钮")
            return False
        
        print(f"找到 {len(buttons)} 个继续学习按钮")
        
        # 分析第一个按钮的详细信息
        button = buttons[0]
        print("\n分析第一个按钮的详细属性:")
        
        # 获取按钮的所有属性
        button_attrs = page.evaluate('''
            (element) => {
                const attrs = {};
                for (let i = 0; i < element.attributes.length; i++) {
                    const attr = element.attributes[i];
                    attrs[attr.name] = attr.value;
                }
                return {
                    tagName: element.tagName,
                    className: element.className,
                    id: element.id,
                    innerHTML: element.innerHTML,
                    outerHTML: element.outerHTML,
                    attributes: attrs,
                    onclick: element.onclick ? element.onclick.toString() : null,
                    href: element.href || null
                };
            }
        ''', button.element_handle())
        
        print("按钮详细信息:")
        print(json.dumps(button_attrs, indent=2, ensure_ascii=False))
        
        # 记录点击前的状态
        print("\n准备点击按钮...")
        initial_url = page.url
        print(f"点击前URL: {initial_url}")
        
        # 清空导航记录
        navigation_info.clear()
        
        # 点击按钮并监控变化
        print("点击按钮...")
        button.click()
        
        # 等待并监控页面变化
        for i in range(10):  # 监控10秒
            time.sleep(1)
            current_url = page.url
            
            if current_url != initial_url:
                print(f"✅ 第{i+1}秒: URL发生变化")
                print(f"   初始URL: {initial_url}")
                print(f"   当前URL: {current_url}")
                
                # 分析URL变化
                if '#/video_page?' in current_url:
                    print("✅ 成功跳转到视频页面!")
                    
                    # 解析URL参数
                    if '?' in current_url:
                        url_parts = current_url.split('?', 1)
                        if len(url_parts) > 1:
                            params_str = url_parts[1]
                            print("URL参数:")
                            for param in params_str.split('&'):
                                if '=' in param:
                                    key, value = param.split('=', 1)
                                    print(f"  {key}: {value}")
                    
                    break
                elif '#/' in current_url and current_url != initial_url:
                    print("ℹ️ 跳转到其他页面")
                    break
            else:
                print(f"⏳ 第{i+1}秒: URL未变化")
        
        final_url = page.url
        print(f"\n最终URL: {final_url}")
        
        # 显示所有捕获的导航信息
        if navigation_info:
            print("\n捕获到的所有导航请求:")
            for i, nav in enumerate(navigation_info):
                print(f"{i+1}. {nav['method']} {nav['url']}")
        else:
            print("\n⚠️ 未捕获到任何导航请求")
        
        # 检查页面内容变化
        print("\n检查页面是否有新的内容加载...")
        
        # 检查是否有视频相关元素
        video_elements = page.locator('video, iframe, [src*="video"], [src*="play"]').all()
        if video_elements:
            print(f"✅ 找到 {len(video_elements)} 个视频相关元素")
        else:
            print("❌ 未找到视频相关元素")
        
        # 检查页面标题
        title = page.title()
        print(f"页面标题: {title}")
        
        # 保存当前页面状态
        timestamp = int(time.time())
        
        # 保存HTML
        html_content = page.content()
        with open(f'debug_button_click_{timestamp}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 保存截图
        page.screenshot(path=f'debug_button_click_{timestamp}.png')
        
        print(f"\n调试信息已保存:")
        print(f"  HTML: debug_button_click_{timestamp}.html")
        print(f"  截图: debug_button_click_{timestamp}.png")
        
        return True
        
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if login_manager:
            login_manager.close_browser()

if __name__ == "__main__":
    debug_button_clicks()