#!/usr/bin/env python3
"""
测试修复后的视频URL访问
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager

def test_video_url_access():
    """测试视频URL访问"""
    print("测试修复后的视频URL访问")
    print("=" * 50)
    
    try:
        # 初始化浏览器
        print("1. 初始化浏览器...")
        if not login_manager.init_browser():
            print("❌ 浏览器初始化失败")
            return False
        
        page = login_manager.page
        
        # 登录
        print("2. 登录...")
        if not login_manager.login():
            print("❌ 登录失败")
            return False
        
        # 测试几个修复后的URL
        test_urls = [
            # 必修课格式 - 修复后应该使用video_page格式
            "https://edu.nxgbjy.org.cn/nxxzxy/index.html#/video_page?name=%E4%B8%AD%E5%9B%BD%E7%89%B9%E8%89%B2%E7%A4%BE%E4%BC%9A%E4%B8%BB%E4%B9%89%E7%90%86%E8%AE%BA%E4%BD%93%E7%B3%BB%E6%96%87%E7%8C%AE%E5%AF%BC%E8%AF%BB%EF%BC%88%E4%B8%8A%EF%BC%89&user_course_id=temp_664f0d3f",
            # 选修课格式
            "https://edu.nxgbjy.org.cn/nxxzxy/index.html#/elective_course_play?name=2025%E5%B9%B4%E3%80%8A%E6%94%BF%E5%BA%9C%E5%B7%A5%E4%BD%9C%E6%8A%A5%E5%91%8A%E3%80%8B%E5%AD%A6%E4%B9%A0%E8%A7%A3%E8%AF%BB%EF%BC%88%E4%B8%8A%EF%BC%89"
        ]
        
        for i, test_url in enumerate(test_urls, 1):
            print(f"\n3.{i} 测试URL访问:")
            url_type = "必修课" if "video_page" in test_url else "选修课"
            print(f"   类型: {url_type}")
            print(f"   URL: {test_url}")
            
            try:
                # 访问URL
                page.goto(test_url, wait_until='networkidle', timeout=15000)
                time.sleep(3)
                
                # 检查页面标题
                title = page.title()
                print(f"   页面标题: {title}")
                
                # 检查URL状态
                current_url = page.url
                print(f"   当前URL: {current_url}")
                
                # 检查是否跳转到了登录页
                if "login" in current_url or "登录" in title:
                    print("   ⚠️  页面跳转到了登录页面，可能需要重新登录")
                    continue
                
                # 检查页面内容
                page_text = page.evaluate('document.body.innerText')
                
                if "404" in page_text or "页面未找到" in page_text:
                    print("   ❌ 页面显示404错误")
                elif "视频" in page_text or "播放" in page_text or "学习" in page_text:
                    print("   ✅ 页面加载成功，包含学习内容")
                elif "课程" in page_text:
                    print("   ✅ 页面加载成功，显示课程页面")
                else:
                    print(f"   ⚠️  页面内容不确定，前100字符: {page_text[:100]}")
                
                # 检查是否有视频相关元素
                video_elements = page.locator('video').count()
                iframe_elements = page.locator('iframe').count()
                
                if video_elements > 0:
                    print(f"   ✅ 发现 {video_elements} 个视频元素")
                elif iframe_elements > 0:
                    print(f"   ✅ 发现 {iframe_elements} 个iframe元素（可能包含视频）")
                else:
                    print("   ⚠️  未发现明显的视频元素")
                
            except Exception as e:
                print(f"   ❌ URL访问失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False
        
    finally:
        if login_manager:
            login_manager.close_browser()

if __name__ == "__main__":
    test_video_url_access()