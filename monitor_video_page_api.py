#!/usr/bin/env python3
"""
监听视频播放页面的API调用，分析视频相关信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from src.enhanced_course_parser import EnhancedCourseParser
from src.login import LoginManager
import json
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def monitor_video_page_api():
    """监听视频播放页面的API调用"""
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()

        try:
            # 登录
            login_manager = LoginManager()
            login_manager.browser = browser
            login_manager.page = page
            if not login_manager.login():
                print("登录失败，无法进行监听")
                return

            print("登录成功，开始监听视频页面API...")

            # 获取一门选修课的URL
            parser = EnhancedCourseParser(page)
            elective_courses = parser.parse_elective_courses_enhanced()

            if not elective_courses:
                print("未找到选修课程")
                return

            # 选择第一门课程
            target_course = elective_courses[0]
            course_name = target_course['course_name']
            video_url = target_course['video_url']

            print(f"\n=== 目标课程 ===")
            print(f"课程名称: {course_name}")
            print(f"视频URL: {video_url}")

            # 捕获的网络数据
            captured_requests = []
            captured_responses = []

            def handle_request(request):
                url = request.url
                method = request.method

                # 过滤有用的API请求
                if any(keyword in url.lower() for keyword in [
                    'video', 'play', 'progress', 'study', 'course', 'scorm',
                    'sco', 'duration', 'position', 'complete', 'api', 'device'
                ]):
                    print(f"\n📤 REQUEST: {method} {url}")

                    headers = dict(request.headers)
                    post_data = None
                    if method == 'POST' and request.post_data:
                        try:
                            post_data = request.post_data
                            # 尝试解析JSON
                            if headers.get('content-type', '').lower().find('json') != -1:
                                post_data = json.loads(post_data)
                        except:
                            pass

                    captured_requests.append({
                        'timestamp': time.time(),
                        'method': method,
                        'url': url,
                        'headers': headers,
                        'post_data': post_data
                    })

            def handle_response(response):
                url = response.url
                status = response.status

                # 过滤有用的API响应
                if any(keyword in url.lower() for keyword in [
                    'video', 'play', 'progress', 'study', 'course', 'scorm',
                    'sco', 'duration', 'position', 'complete', 'api', 'device'
                ]) and status == 200:
                    print(f"📥 RESPONSE: {status} {url}")

                    try:
                        headers = dict(response.headers)
                        response_data = None

                        # 尝试获取响应体
                        if 'json' in headers.get('content-type', '').lower():
                            response_data = response.json()
                            print(f"   JSON Data: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}...")
                        elif 'text' in headers.get('content-type', '').lower():
                            response_data = response.text()
                            print(f"   Text Data: {response_data[:200]}...")

                        captured_responses.append({
                            'timestamp': time.time(),
                            'status': status,
                            'url': url,
                            'headers': headers,
                            'data': response_data
                        })

                    except Exception as e:
                        print(f"   获取响应数据失败: {e}")

            # 设置网络监听
            page.on('request', handle_request)
            page.on('response', handle_response)

            # 访问视频播放页面
            print(f"\n🎬 访问视频播放页面...")
            page.goto(video_url)

            # 等待页面完全加载
            page.wait_for_load_state('networkidle')
            time.sleep(5)

            print(f"\n⏳ 等待页面加载和初始API调用...")
            time.sleep(10)

            # 尝试查找并点击播放按钮
            try:
                print(f"\n▶️ 查找播放按钮...")
                play_selectors = [
                    'button:has-text("播放")',
                    '[class*="play"]',
                    '[id*="play"]',
                    'button[title*="播放"]',
                    'button[title*="Play"]',
                    '.video-play-btn',
                    '#playButton',
                    '.play-button'
                ]

                for selector in play_selectors:
                    try:
                        play_button = page.locator(selector).first
                        if play_button.count() > 0:
                            print(f"找到播放按钮: {selector}")
                            play_button.click()
                            print("点击播放按钮成功")
                            time.sleep(5)
                            break
                    except Exception as e:
                        continue
                else:
                    print("未找到明显的播放按钮，继续监听...")

            except Exception as e:
                print(f"播放按钮点击失败: {e}")

            # 继续监听一段时间
            print(f"\n🔍 继续监听API调用 30 秒...")
            time.sleep(30)

            # 保存捕获的数据
            all_data = {
                'course_info': {
                    'name': course_name,
                    'url': video_url
                },
                'requests': captured_requests,
                'responses': captured_responses,
                'capture_time': time.time()
            }

            filename = 'video_page_api_capture.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n📊 监听完成！")
            print(f"捕获到 {len(captured_requests)} 个请求")
            print(f"捕获到 {len(captured_responses)} 个响应")
            print(f"数据已保存到: {filename}")

            # 分析关键API
            print(f"\n🔍 关键API分析:")
            video_related_apis = []
            progress_related_apis = []
            scorm_related_apis = []

            for req in captured_requests:
                url = req['url'].lower()
                if 'video' in url or 'play' in url:
                    video_related_apis.append(req)
                elif 'progress' in url or 'position' in url:
                    progress_related_apis.append(req)
                elif 'scorm' in url or 'sco' in url:
                    scorm_related_apis.append(req)

            if video_related_apis:
                print(f"📺 视频相关API ({len(video_related_apis)}个):")
                for api in video_related_apis[:3]:  # 只显示前3个
                    print(f"   {api['method']} {api['url']}")

            if progress_related_apis:
                print(f"📈 进度相关API ({len(progress_related_apis)}个):")
                for api in progress_related_apis[:3]:
                    print(f"   {api['method']} {api['url']}")

            if scorm_related_apis:
                print(f"📚 SCORM相关API ({len(scorm_related_apis)}个):")
                for api in scorm_related_apis[:3]:
                    print(f"   {api['method']} {api['url']}")

            input("\n按回车键关闭浏览器...")

        except Exception as e:
            print(f"监听失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    monitor_video_page_api()