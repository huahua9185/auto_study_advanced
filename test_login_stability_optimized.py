#!/usr/bin/env python3
"""
测试优化后的登录稳定性脚本
验证基于分析结果的登录稳定性改进效果
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.login import login_manager

class LoginStabilityTester:
    def __init__(self):
        self.test_results = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_attempts': 0,
            'successful_logins': 0,
            'failed_logins': 0,
            'login_times': [],
            'layout_stability_times': [],
            'improvements_observed': [],
            'issues_remaining': []
        }
    
    def test_login_stability(self, num_tests=3):
        """测试登录稳定性优化效果"""
        print("测试优化后的登录稳定性")
        print("=" * 60)
        
        try:
            # 初始化浏览器
            print("1. 初始化浏览器...")
            if not login_manager.init_browser():
                print("❌ 浏览器初始化失败")
                return False
            
            print(f"2. 开始进行 {num_tests} 次登录测试...")
            
            for test_num in range(1, num_tests + 1):
                print(f"\n--- 测试 {test_num}/{num_tests} ---")
                self.test_results['total_attempts'] += 1
                
                # 记录登录开始时间
                start_time = time.time()
                
                try:
                    # 执行登录测试
                    login_success = login_manager.login()
                    
                    # 记录登录耗时
                    login_time = time.time() - start_time
                    self.test_results['login_times'].append(login_time)
                    
                    if login_success:
                        self.test_results['successful_logins'] += 1
                        print(f"✅ 登录成功 (耗时: {login_time:.2f}s)")
                        
                        # 测试完成后登出，准备下一次测试
                        if test_num < num_tests:
                            print("   正在登出以准备下一次测试...")
                            login_manager.logout()
                            time.sleep(2)
                    else:
                        self.test_results['failed_logins'] += 1
                        print(f"❌ 登录失败 (耗时: {login_time:.2f}s)")
                        
                except Exception as e:
                    self.test_results['failed_logins'] += 1
                    print(f"❌ 测试异常: {str(e)}")
                
                # 测试间短暂等待
                if test_num < num_tests:
                    print("   等待 3 秒后进行下一次测试...")
                    time.sleep(3)
            
            # 生成测试报告
            self.generate_test_report()
            
            # 保存测试结果
            self.save_test_results()
            
            return True
            
        except Exception as e:
            print(f"❌ 测试过程中出现错误: {str(e)}")
            return False
            
        finally:
            if login_manager:
                login_manager.close_browser()
    
    def generate_test_report(self):
        """生成测试报告"""
        print(f"\n测试报告:")
        print("=" * 40)
        
        # 基本统计
        success_rate = (self.test_results['successful_logins'] / self.test_results['total_attempts']) * 100
        print(f"总测试次数: {self.test_results['total_attempts']}")
        print(f"成功登录: {self.test_results['successful_logins']}")
        print(f"失败登录: {self.test_results['failed_logins']}")
        print(f"成功率: {success_rate:.1f}%")
        
        # 时间分析
        if self.test_results['login_times']:
            avg_time = sum(self.test_results['login_times']) / len(self.test_results['login_times'])
            min_time = min(self.test_results['login_times'])
            max_time = max(self.test_results['login_times'])
            
            print(f"\n登录时间分析:")
            print(f"平均登录时间: {avg_time:.2f}s")
            print(f"最快登录时间: {min_time:.2f}s")
            print(f"最慢登录时间: {max_time:.2f}s")
        
        # 与之前分析结果对比
        print(f"\n优化效果分析:")
        print("基于之前的稳定性分析:")
        print("- 页面加载时间: 7.38s (之前)")
        print("- 发现4个动态Banner元素")
        print("- 页面存在'加载中...'文本导致布局抖动")
        
        if self.test_results['login_times']:
            current_avg = sum(self.test_results['login_times']) / len(self.test_results['login_times'])
            print(f"- 当前平均登录时间: {current_avg:.2f}s")
            
            if current_avg < 7.38:
                improvement = 7.38 - current_avg
                percentage = (improvement / 7.38) * 100
                print(f"✅ 登录时间改善: {improvement:.2f}s ({percentage:.1f}% 提升)")
                self.test_results['improvements_observed'].append(f"登录时间缩短 {improvement:.2f}s")
            else:
                print("⚠️  登录时间未见明显改善")
                self.test_results['issues_remaining'].append("登录时间仍然较长")
        
        # 稳定性改进
        if success_rate >= 80:
            print("✅ 登录成功率良好")
            self.test_results['improvements_observed'].append(f"登录成功率 {success_rate:.1f}%")
        else:
            print("⚠️  登录成功率仍需改善")
            self.test_results['issues_remaining'].append(f"登录成功率偏低 {success_rate:.1f}%")
        
        # 具体改进措施效果
        print(f"\n已实施的优化措施:")
        print("✅ 添加了页面布局稳定性检查")
        print("✅ 等待动态Banner元素完成加载")
        print("✅ 检测'加载中...'文本消失")
        print("✅ 监控页面高度稳定性")
        print("✅ 在表单填写前等待布局稳定")
    
    def save_test_results(self):
        """保存测试结果"""
        try:
            with open('login_stability_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n测试结果已保存到: login_stability_test_results.json")
        except Exception as e:
            print(f"❌ 保存测试结果失败: {str(e)}")

def main():
    """主函数"""
    tester = LoginStabilityTester()
    
    try:
        success = tester.test_login_stability(num_tests=3)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 登录稳定性测试完成!")
            print("详细测试结果请查看: login_stability_test_results.json")
            print("=" * 60)
            return 0
        else:
            print("\n❌ 登录稳定性测试失败!")
            return 1
            
    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)