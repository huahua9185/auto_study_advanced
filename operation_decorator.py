#!/usr/bin/env python3
"""
页面操作装饰器 - 可以集成到现有代码中的操作跟踪器
使用方法：导入这个模块，然后用装饰器装饰现有的方法
"""

import functools
import time
from datetime import datetime
import json
import os

class OperationLogger:
    """全局操作日志记录器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OperationLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.operation_counter = 0
            self.operations_log = []
            self._initialized = True
    
    def log_operation(self, func_name, args_info, operation_type, description, result=None, error=None):
        """记录操作"""
        self.operation_counter += 1
        operation = {
            'number': self.operation_counter,
            'timestamp': datetime.now().isoformat(),
            'function': func_name,
            'type': operation_type,
            'description': description,
            'args': args_info,
            'result': 'success' if error is None else 'error',
            'error': str(error) if error else None,
            'return_value': str(result) if result is not None else None
        }
        
        self.operations_log.append(operation)
        
        # 实时打印操作信息
        print(f"\n🔢 操作编号 #{self.operation_counter}")
        print(f"   函数: {func_name}")
        print(f"   类型: {operation_type}")
        print(f"   描述: {description}")
        if args_info:
            print(f"   参数: {args_info}")
        if error:
            print(f"   ❌ 错误: {error}")
        else:
            print(f"   ✅ 成功")
        print("-" * 50)
        
        return self.operation_counter
    
    def save_log(self, filename="page_operations_log.json"):
        """保存操作日志"""
        log_path = os.path.join(os.getcwd(), filename)
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_operations': self.operation_counter,
                'timestamp': datetime.now().isoformat(),
                'operations': self.operations_log
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📄 操作日志已保存到: {log_path}")
    
    def reset_log(self):
        """重置日志"""
        self.operation_counter = 0
        self.operations_log = []

# 全局日志记录器实例
logger = OperationLogger()

def track_page_operation(operation_type="page_operation", description=None, save_args=True):
    """
    页面操作跟踪装饰器
    
    Args:
        operation_type: 操作类型 (如 'click', 'fill', 'navigate' 等)
        description: 操作描述
        save_args: 是否保存函数参数信息
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # 构建参数信息
            args_info = {}
            if save_args:
                # 保存非敏感参数
                if args:
                    args_info['args'] = [str(arg)[:100] if len(str(arg)) > 100 else str(arg) 
                                       for arg in args[1:]]  # 跳过self参数
                if kwargs:
                    args_info['kwargs'] = {k: ("***隐藏***" if "password" in k.lower() or "pwd" in k.lower() 
                                             else str(v)[:100] if len(str(v)) > 100 else str(v)) 
                                         for k, v in kwargs.items()}
            
            # 构建描述
            final_description = description or f"调用 {func.__name__}"
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录成功操作
                op_num = logger.log_operation(
                    func_name=func_name,
                    args_info=args_info,
                    operation_type=operation_type,
                    description=final_description,
                    result=result
                )
                
                return result
                
            except Exception as e:
                # 记录失败操作
                op_num = logger.log_operation(
                    func_name=func_name,
                    args_info=args_info,
                    operation_type=operation_type,
                    description=final_description,
                    error=e
                )
                
                raise e
        
        return wrapper
    return decorator

def track_click(description=None):
    """点击操作跟踪装饰器"""
    return track_page_operation("click", description)

def track_fill(description=None):
    """表单填写跟踪装饰器"""
    return track_page_operation("fill", description, save_args=False)  # 不保存表单内容

def track_navigate(description=None):
    """页面导航跟踪装饰器"""
    return track_page_operation("navigate", description)

def track_wait(description=None):
    """等待操作跟踪装饰器"""
    return track_page_operation("wait", description)

def track_evaluate(description=None):
    """JavaScript执行跟踪装饰器"""
    return track_page_operation("evaluate", description, save_args=False)  # JS代码可能很长

# 使用示例和测试函数
def create_enhanced_login_manager():
    """创建增强版的LoginManager类，添加操作跟踪"""
    
    # 首先读取原始LoginManager
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from src.login import LoginManager
    
    class TrackedLoginManager(LoginManager):
        """增强版LoginManager，添加操作跟踪"""
        
        def __init__(self):
            super().__init__()
            # 重置日志计数器
            logger.reset_log()
            print("🎯 启用操作跟踪模式")
            print("=" * 50)
        
        @track_navigate("导航到登录页面")
        def _navigate_to_login(self):
            return super()._navigate_to_login()
        
        @track_fill("填写登录表单")
        def _fill_login_form(self):
            return super()._fill_login_form()
        
        @track_fill("填写用户名")
        def _fill_username(self):
            return super()._fill_username()
        
        @track_fill("填写密码")
        def _fill_password(self):
            return super()._fill_password()
        
        @track_click("提交登录表单")
        def _submit_login_form(self):
            return super()._submit_login_form()
        
        @track_evaluate("应用稳定性修复")
        def _apply_modal_stability_fixes(self):
            return super()._apply_modal_stability_fixes()
        
        @track_wait("等待登录模态框稳定")
        def _wait_for_login_modal_stability(self, timeout_seconds=3):
            return super()._wait_for_login_modal_stability(timeout_seconds)
        
        @track_page_operation("login", "执行完整登录流程")
        def login(self):
            return super().login()
        
        def close_browser(self):
            """关闭浏览器前保存日志"""
            try:
                logger.save_log("tracked_operations.json")
            except Exception as e:
                print(f"保存日志失败: {e}")
            super().close_browser()
    
    return TrackedLoginManager

# 简单的测试函数
if __name__ == "__main__":
    print("🧪 测试操作跟踪装饰器")
    print("=" * 40)
    
    # 测试装饰器功能
    @track_click("测试点击操作")
    def test_click(element):
        print(f"模拟点击元素: {element}")
        return True
    
    @track_fill("测试填写操作")
    def test_fill(field, value):
        print(f"模拟填写 {field}: {value}")
        return True
    
    @track_navigate("测试导航操作")
    def test_navigate(url):
        print(f"模拟导航到: {url}")
        return True
    
    # 执行测试
    test_navigate("https://example.com")
    test_click(".login-button")
    test_fill("username", "test_user")
    test_fill("password", "test_password")
    
    # 保存测试日志
    logger.save_log("decorator_test.json")
    
    print(f"\n✅ 测试完成，共记录了 {logger.operation_counter} 个操作")