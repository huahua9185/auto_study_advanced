#!/usr/bin/env python3
"""
快速API监控脚本 - 缩短时间以快速获取结果
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from playwright.async_api import async_playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quick_api_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuickAPIMonitor:
    """快速API监控器"""

    def __init__(self):
        self.captured_requests = []

    async def start_monitoring(self):
        """启动监控"""
        logger.info("🚀 启动快速API监控...")
        logger.info("📝 操作说明:")
        logger.info("   1. 浏览器将自动打开")
        logger.info("   2. 您有30秒时间手动登录并导航到视频页面")
        logger.info("   3. 30秒后自动开始API监控(1分钟)")

        async with async_playwright() as p:
            browser = await p.firefox.launch(
                headless=False,
                slow_mo=100
            )

            try:
                context = await browser.new_context(
                    viewport={'width': 1440, 'height': 900},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0'
                )
                page = await context.new_page()

                # 设置API监听
                await self._setup_api_monitoring(page)

                # 打开登录页面
                await page.goto("https://edu.nxgbjy.org.cn/nxxzxy/index.html")
                await page.wait_for_load_state('networkidle')

                # 给用户30秒时间登录和导航
                await self._countdown_for_user_setup(30)

                # 开始监控
                await self._start_monitoring(page)

                # 分析结果
                await self._analyze_results()

                logger.info("📊 监控完成！结果已显示。")

            except Exception as e:
                logger.error(f"监控过程中出错: {e}")
            finally:
                await browser.close()

    async def _setup_api_monitoring(self, page):
        """设置API监听"""
        logger.info("📡 设置API监听...")

        async def handle_request(request):
            url = request.url
            method = request.method

            # 监控相关请求
            if any(pattern in url.lower() for pattern in [
                '/device/', 'scorm', 'video', 'play', 'seek', 'progress',
                'study', 'learn', 'session', 'time', 'manifest', 'course',
                '.do'
            ]):
                request_data = {
                    'timestamp': datetime.now().isoformat(),
                    'method': method,
                    'url': url,
                    'headers': dict(request.headers),
                    'post_data': None
                }

                if method in ['POST', 'PUT', 'PATCH']:
                    try:
                        post_data = request.post_data
                        if post_data:
                            request_data['post_data'] = post_data
                    except:
                        request_data['post_data'] = 'Unable to capture'

                self.captured_requests.append(request_data)

                # 实时显示重要API
                if any(keyword in url.lower() for keyword in ['seek', 'progress', 'session', 'scorm']):
                    logger.info(f"🎯 学习API: {method} {url}")
                    if request_data.get('post_data'):
                        logger.info(f"   📋 数据: {request_data['post_data']}")

        page.on('request', handle_request)

    async def _countdown_for_user_setup(self, seconds):
        """倒计时等待用户设置"""
        logger.info(f"\n⏰ 开始{seconds}秒倒计时，请完成登录和页面导航...")
        logger.info("💡 推荐操作:")
        logger.info("   1. 登录系统 (用户名: 640302198607120020)")
        logger.info("   2. 导航到: https://edu.nxgbjy.org.cn/nxxzxy/index.html#/video_page?id=11375&user_course_id=1991474&name=学习中心")
        logger.info("   3. 确保页面完全加载")

        for i in range(seconds, 0, -10):
            logger.info(f"⏱️ 倒计时: {i} 秒...")
            await asyncio.sleep(10)

        logger.info("✅ 倒计时结束，开始API监控！")

    async def _start_monitoring(self, page):
        """开始监控"""
        logger.info("\n🎯 开始API监控 (1分钟)...")
        logger.info("🔄 建议在页面上进行以下操作:")
        logger.info("   - 播放视频")
        logger.info("   - 快进/后退")
        logger.info("   - 暂停/播放")
        logger.info("   - 拖拽进度条")

        start_time = time.time()
        monitoring_duration = 60  # 1分钟
        report_interval = 15  # 每15秒报告一次

        last_count = 0

        while time.time() - start_time < monitoring_duration:
            elapsed = int(time.time() - start_time)
            remaining = monitoring_duration - elapsed

            current_count = len(self.captured_requests)
            new_apis = current_count - last_count

            logger.info(f"📊 监控进度: {elapsed}/{monitoring_duration}秒 - 累计API: {current_count} (新增: {new_apis})")

            # 显示最近的学习API
            if new_apis > 0:
                recent_learning = [
                    req for req in self.captured_requests[last_count:]
                    if any(k in req['url'].lower() for k in ['seek', 'progress', 'session', 'scorm'])
                ]
                if recent_learning:
                    logger.info(f"🎯 新发现学习API: {len(recent_learning)} 个")

            last_count = current_count
            await asyncio.sleep(report_interval)

        logger.info("✅ API监控完成！")

    async def _analyze_results(self):
        """分析结果"""
        logger.info("\n" + "="*60)
        logger.info("🔬 分析监控结果...")

        if not self.captured_requests:
            logger.warning("⚠️ 未捕获到任何API调用")
            return

        # 分类
        learning_apis = []
        device_apis = []
        other_apis = []

        for req in self.captured_requests:
            url_lower = req['url'].lower()
            if any(k in url_lower for k in ['seek', 'progress', 'session', 'scorm', 'manifest']):
                learning_apis.append(req)
            elif '/device/' in url_lower:
                device_apis.append(req)
            else:
                other_apis.append(req)

        logger.info(f"📊 API统计:")
        logger.info(f"   🎯 学习API: {len(learning_apis)} 个")
        logger.info(f"   📱 设备API: {len(device_apis)} 个")
        logger.info(f"   📋 其他API: {len(other_apis)} 个")
        logger.info(f"   📊 总计: {len(self.captured_requests)} 个")

        # 详细分析学习API
        if learning_apis:
            logger.info(f"\n🎯 学习API详情:")
            learning_urls = {}
            for api in learning_apis:
                url = api['url']
                if url not in learning_urls:
                    learning_urls[url] = []
                learning_urls[url].append(api)

            for i, (url, apis) in enumerate(learning_urls.items(), 1):
                logger.info(f"\n--- API {i} (调用{len(apis)}次) ---")
                logger.info(f"URL: {url}")
                logger.info(f"方法: {apis[0]['method']}")

                if apis[0].get('post_data'):
                    logger.info(f"POST数据: {apis[0]['post_data']}")

        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = {
            'timestamp': datetime.now().isoformat(),
            'total_apis': len(self.captured_requests),
            'learning_apis': learning_apis,
            'device_apis': device_apis,
            'other_apis': other_apis
        }

        filename = f"quick_monitor_result_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 结果已保存: {filename}")

        # 关键发现
        if learning_apis:
            logger.info(f"\n🔑 关键发现:")
            unique_urls = set(api['url'] for api in learning_apis)
            for url in unique_urls:
                method = next(api['method'] for api in learning_apis if api['url'] == url)
                count = len([api for api in learning_apis if api['url'] == url])
                logger.info(f"✨ {method} {url} ({count}次)")
        else:
            logger.warning("⚠️ 未发现学习进度API")

        logger.info("="*60)

async def main():
    monitor = QuickAPIMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())