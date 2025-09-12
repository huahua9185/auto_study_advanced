#!/usr/bin/env python3
"""
测试：点击按钮获取真实的视频URL
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager
from config.config import Config

def test_real_video_urls():
    """测试获取真实的视频URL"""
    print("测试获取真实的视频URL")
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
        print("\n3. 测试必修课真实URL...")
        page.goto(Config.REQUIRED_COURSES_URL, wait_until='networkidle')
        time.sleep(3)
        
        # 找到第一个继续学习按钮
        buttons = page.locator('button:has-text("继续学习")').all()
        if buttons:
            print(f"找到 {len(buttons)} 个继续学习按钮")
            
            # 点击第一个按钮
            print("\n点击第一个按钮...")
            buttons[0].click()
            time.sleep(5)  # 等待页面跳转
            
            # 获取跳转后的URL
            current_url = page.url
            print(f"跳转后的URL: {current_url}")
            
            # 解析URL参数
            if '#/' in current_url:
                hash_part = current_url.split('#/')[1]
                print(f"Hash部分: {hash_part}")
                
                if '?' in hash_part:
                    path, params_str = hash_part.split('?', 1)
                    print(f"路径: {path}")
                    print("参数:")
                    
                    params = {}
                    for param in params_str.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key] = value
                            print(f"  {key}: {value}")
                    
                    # 检查关键参数
                    if 'id' in params:
                        print(f"✅ 找到课程ID: {params['id']}")
                    else:
                        print("❌ 缺少课程ID参数")
                    
                    if 'user_course_id' in params:
                        print(f"✅ 找到user_course_id: {params['user_course_id']}")
                    else:
                        print("❌ 缺少user_course_id参数")
            
            # 返回课程列表
            page.goto(Config.REQUIRED_COURSES_URL, wait_until='networkidle')
            time.sleep(2)
        
        # 测试选修课
        print("\n4. 测试选修课真实URL...")
        page.goto(Config.ELECTIVE_COURSES_URL, wait_until='networkidle')
        time.sleep(3)
        
        # 找到播放元素
        play_elements = page.locator('td:has-text("播放")').all()
        if play_elements:
            print(f"找到 {len(play_elements)} 个播放元素")
            
            # 点击第一个
            print("\n点击第一个播放元素...")
            play_elements[0].click()
            time.sleep(5)
            
            # 获取跳转后的URL
            current_url = page.url
            print(f"跳转后的URL: {current_url}")
            
            # 解析URL
            if '#/' in current_url:
                hash_part = current_url.split('#/')[1]
                print(f"Hash部分: {hash_part}")
                
                if '?' in hash_part:
                    path, params_str = hash_part.split('?', 1)
                    print(f"路径: {path}")
                    print("参数:")
                    
                    params = {}
                    for param in params_str.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key] = value
                            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if login_manager:
            login_manager.close_browser()

if __name__ == "__main__":
    test_real_video_urls()