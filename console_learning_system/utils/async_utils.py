#!/usr/bin/env python3
"""
异步工具模块
提供在同步环境中运行异步代码的工具
"""

import asyncio
import threading
from typing import Coroutine, Any


def run_async_in_sync(coro: Coroutine) -> Any:
    """
    在同步环境中运行异步代码
    解决asyncio.run()在已有事件循环中的冲突问题
    """
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_running_loop()
        # 如果已有事件循环，在新线程中运行
        return _run_in_new_thread(coro)
    except RuntimeError:
        # 如果没有事件循环，直接运行
        return asyncio.run(coro)


def _run_in_new_thread(coro: Coroutine) -> Any:
    """在新线程中运行异步代码"""
    result = None
    exception = None

    def thread_target():
        nonlocal result, exception
        try:
            result = asyncio.run(coro)
        except Exception as e:
            exception = e

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self):
        self.running_tasks = set()
        self.cancelled = False

    async def run_task(self, coro: Coroutine):
        """运行异步任务"""
        task = asyncio.create_task(coro)
        self.running_tasks.add(task)

        try:
            result = await task
            return result
        except asyncio.CancelledError:
            print("任务被取消")
            return None
        finally:
            self.running_tasks.discard(task)

    def cancel_all_tasks(self):
        """取消所有运行中的任务"""
        self.cancelled = True
        for task in self.running_tasks:
            task.cancel()

    def is_cancelled(self):
        """检查是否被取消"""
        return self.cancelled