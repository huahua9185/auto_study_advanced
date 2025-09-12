#!/usr/bin/env python3
"""
自动化学习程序主入口
基于Playwright的网页自动化学习系统
"""

import sys
import os
import logging
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import Config
from src.login import login_manager
from src.enhanced_course_parser import EnhancedCourseParser
from src.auto_study import AutoStudyManager
from src.database import db

class AutoStudyApp:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.login_manager = login_manager
        self.course_parser = None
        self.auto_study_manager = None
        self.running = True
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/auto_study.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 确保日志目录存在
        log_dir = Path('data')
        log_dir.mkdir(exist_ok=True)
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("       自动化学习系统")
        print("="*50)
        print("1. 获取（更新）课程信息")
        print("2. 开始自动学习") 
        print("3. 查看课程列表")
        print("4. 查看学习统计")
        print("5. 设置选项")
        print("0. 退出程序")
        print("="*50)
    
    def show_course_list(self):
        """显示课程列表"""
        try:
            courses = db.get_all_courses()
            
            if not courses:
                print("\n暂无课程数据，请先获取课程信息。")
                return
            
            print(f"\n课程列表（共 {len(courses)} 门课程）:")
            print("-" * 80)
            print(f"{'序号':<4} {'课程类型':<8} {'课程名称':<30} {'学习进度':<10} {'完成状态':<8}")
            print("-" * 80)
            
            for i, course in enumerate(courses, 1):
                course_type = "必修课" if course['course_type'] == 'required' else "选修课"
                progress = f"{course['progress']:.1f}%"
                status = "已完成" if course['is_completed'] else "未完成"
                course_name = course['course_name'][:25] + "..." if len(course['course_name']) > 25 else course['course_name']
                
                print(f"{i:<4} {course_type:<8} {course_name:<30} {progress:<10} {status:<8}")
            
        except Exception as e:
            self.logger.error(f"显示课程列表失败: {str(e)}")
            print(f"显示课程列表时发生错误: {str(e)}")
    
    def show_statistics(self):
        """显示学习统计"""
        try:
            stats = db.get_learning_statistics()
            
            print("\n学习统计信息:")
            print("-" * 40)
            print(f"总课程数量: {stats['total_courses']}")
            print(f"已完成课程: {stats['completed_courses']}")
            print(f"完成率: {stats['completion_rate']:.1f}%")
            print(f"平均进度: {stats['average_progress']:.1f}%")
            
            print("\n分类统计:")
            for course_type, type_stats in stats['course_type_stats'].items():
                type_name = "必修课" if course_type == 'required' else "选修课"
                print(f"  {type_name}:")
                print(f"    总数: {type_stats['count']}")
                print(f"    已完成: {type_stats['completed']}")
                print(f"    平均进度: {type_stats['avg_progress']:.1f}%")
            
        except Exception as e:
            self.logger.error(f"显示统计信息失败: {str(e)}")
            print(f"显示统计信息时发生错误: {str(e)}")
    
    def update_courses(self):
        """获取并更新课程信息"""
        try:
            print("\n正在获取课程信息...")
            
            if not self.course_parser:
                self.course_parser = EnhancedCourseParser(self.login_manager.page)
            
            # 解析所有课程
            courses_data = self.course_parser.parse_all_courses()
            
            if not courses_data['required'] and not courses_data['elective']:
                print("未能获取到课程信息，请检查网络连接或登录状态。")
                return
            
            # 显示解析结果
            required_count = len(courses_data['required'])
            elective_count = len(courses_data['elective'])
            
            print(f"\n成功解析到课程信息:")
            print(f"  必修课: {required_count} 门")
            print(f"  选修课: {elective_count} 门")
            
            # 询问用户确认
            confirm = input("\n是否保存这些课程信息到数据库？(y/n): ").strip().lower()
            
            if confirm in ['y', 'yes', '是']:
                # 保存到数据库
                if self.course_parser.save_courses_to_database(courses_data):
                    print("课程信息已成功保存到数据库！")
                else:
                    print("保存课程信息时发生错误。")
            else:
                print("取消保存课程信息。")
                
        except Exception as e:
            self.logger.error(f"更新课程信息失败: {str(e)}")
            print(f"获取课程信息时发生错误: {str(e)}")
    
    def start_auto_learning(self):
        """开始自动学习"""
        try:
            # 检查是否有未完成的课程
            incomplete_courses = db.get_incomplete_courses()
            
            if not incomplete_courses:
                print("\n没有未完成的课程，所有课程都已学习完毕！")
                return
            
            print(f"\n找到 {len(incomplete_courses)} 门未完成的课程")
            
            # 显示将要学习的课程
            print("即将学习的课程:")
            for i, course in enumerate(incomplete_courses[:5], 1):  # 只显示前5门
                course_type = "必修课" if course['course_type'] == 'required' else "选修课"
                print(f"  {i}. [{course_type}] {course['course_name']} - 进度: {course['progress']:.1f}%")
            
            if len(incomplete_courses) > 5:
                print(f"  ... 还有 {len(incomplete_courses) - 5} 门课程")
            
            # 询问用户确认
            confirm = input("\n是否开始自动学习？(y/n): ").strip().lower()
            
            if confirm not in ['y', 'yes', '是']:
                print("取消自动学习。")
                return
            
            print("\n开始自动学习...")
            print("提示: 按 Ctrl+C 可以停止学习")
            
            # 初始化自动学习管理器
            if not self.auto_study_manager:
                self.auto_study_manager = AutoStudyManager(self.login_manager.page)
            
            # 开始自动学习
            success = self.auto_study_manager.start_auto_study()
            
            if success:
                print("\n自动学习任务完成！")
            else:
                print("\n自动学习过程中出现错误。")
                
        except KeyboardInterrupt:
            print("\n\n用户中断学习...")
            if self.auto_study_manager:
                self.auto_study_manager.stop_study()
            print("学习已停止。")
            
        except Exception as e:
            self.logger.error(f"自动学习失败: {str(e)}")
            print(f"自动学习时发生错误: {str(e)}")
    
    def show_settings(self):
        """显示设置选项"""
        while True:
            print("\n" + "="*30)
            print("       设置选项")
            print("="*30)
            print("1. 查看当前配置")
            print("2. 测试登录")
            print("3. 清空数据库")
            print("0. 返回主菜单")
            print("="*30)
            
            choice = input("请选择操作: ").strip()
            
            if choice == '1':
                self.show_current_config()
            elif choice == '2':
                self.test_login()
            elif choice == '3':
                self.clear_database()
            elif choice == '0':
                break
            else:
                print("无效选择，请重新输入。")
    
    def show_current_config(self):
        """显示当前配置"""
        print(f"\n当前配置:")
        print(f"  目标网站: {Config.BASE_URL}")
        print(f"  用户名: {Config.USERNAME}")
        print(f"  密码: {'*' * len(Config.PASSWORD)}")
        print(f"  浏览器: {Config.BROWSER_TYPE}")
        print(f"  无头模式: {Config.HEADLESS}")
        print(f"  窗口大小: {Config.VIEWPORT_WIDTH}x{Config.VIEWPORT_HEIGHT}")
        print(f"  数据库路径: {Config.DATABASE_PATH}")
    
    def test_login(self):
        """测试登录功能"""
        try:
            print("\n正在测试登录...")
            
            if self.login_manager.check_login_status():
                print("当前已处于登录状态。")
            else:
                print("当前未登录，尝试登录...")
                if self.login_manager.login():
                    print("登录测试成功！")
                else:
                    print("登录测试失败。")
                    
        except Exception as e:
            self.logger.error(f"登录测试失败: {str(e)}")
            print(f"登录测试时发生错误: {str(e)}")
    
    def clear_database(self):
        """清空数据库"""
        try:
            # 先显示当前数据库信息
            db_info = db.get_database_info()
            if 'error' not in db_info:
                print(f"\n当前数据库信息:")
                print(f"  数据库路径: {db_info['database_path']}")
                print(f"  数据库大小: {db_info['database_size_mb']} MB")
                print(f"  课程数量: {db_info['courses_count']}")
                print(f"  学习记录数量: {db_info['learning_logs_count']}")
            
            # 获取学习统计信息
            stats = db.get_learning_statistics()
            if stats['total_courses'] > 0:
                print(f"\n即将清空的数据:")
                print(f"  总课程数: {stats['total_courses']}")
                print(f"  已完成课程: {stats['completed_courses']}")
                print(f"  完成率: {stats['completion_rate']:.1f}%")
                for course_type, type_stats in stats['course_type_stats'].items():
                    type_name = "必修课" if course_type == 'required' else "选修课"
                    print(f"  {type_name}: {type_stats['count']}门 (已完成: {type_stats['completed']}门)")
            
            confirm = input("\n警告: 此操作将永久删除所有课程数据和学习记录，无法恢复！\n确定要继续吗？(输入'清空'确认): ")
            
            if confirm == '清空':
                print("\n正在清空数据库...")
                
                if db.clear_all_data():
                    print("✅ 数据库清空成功！")
                    
                    # 验证清空结果
                    new_info = db.get_database_info()
                    if 'error' not in new_info:
                        print(f"\n清空后状态:")
                        print(f"  课程数量: {new_info['courses_count']}")
                        print(f"  学习记录数量: {new_info['learning_logs_count']}")
                else:
                    print("❌ 数据库清空失败！")
                    
            else:
                print("已取消操作。")
                
        except Exception as e:
            self.logger.error(f"清空数据库操作失败: {str(e)}")
            print(f"清空数据库时发生错误: {str(e)}")
    
    def initialize(self):
        """初始化应用程序"""
        try:
            self.logger.info("初始化自动化学习程序")
            
            print("正在初始化程序...")
            
            # 初始化浏览器
            if not self.login_manager.init_browser():
                print("浏览器初始化失败，程序无法继续运行。")
                return False
            
            print("浏览器初始化完成")
            
            # 检查登录状态
            print("正在检查登录状态...")
            
            if not self.login_manager.check_login_status():
                print("当前未登录，正在执行登录...")
                
                login_success = self.login_manager.login()
                
                if not login_success:
                    print("登录失败，程序无法继续运行。")
                    print("请检查用户名、密码或网络连接。")
                    return False
                
                print("登录成功！")
            else:
                print("检测到已登录状态")
            
            self.logger.info("程序初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"程序初始化失败: {str(e)}")
            print(f"程序初始化时发生错误: {str(e)}")
            return False
    
    def run(self):
        """运行主程序"""
        try:
            print("欢迎使用自动化学习系统！")
            print("程序启动中...")
            
            # 初始化程序
            if not self.initialize():
                print("程序初始化失败，即将退出。")
                return
            
            # 主循环
            while self.running:
                try:
                    self.show_menu()
                    choice = input("\n请选择操作 (0-5): ").strip()
                    
                    if choice == '0':
                        print("正在退出程序...")
                        self.running = False
                        
                    elif choice == '1':
                        self.update_courses()
                        
                    elif choice == '2':
                        self.start_auto_learning()
                        
                    elif choice == '3':
                        self.show_course_list()
                        
                    elif choice == '4':
                        self.show_statistics()
                        
                    elif choice == '5':
                        self.show_settings()
                        
                    else:
                        print("无效选择，请重新输入。")
                        
                    # 暂停一下，让用户能看到结果
                    if self.running and choice != '0':
                        input("\n按回车键继续...")
                        
                except KeyboardInterrupt:
                    print("\n\n检测到用户中断...")
                    confirm = input("确定要退出程序吗？(y/n): ").strip().lower()
                    if confirm in ['y', 'yes', '是']:
                        self.running = False
                    else:
                        print("继续运行程序...")
                        
                except Exception as e:
                    self.logger.error(f"主循环中发生错误: {str(e)}")
                    print(f"操作过程中发生错误: {str(e)}")
                    input("按回车键继续...")
                    
        except Exception as e:
            self.logger.error(f"程序运行失败: {str(e)}")
            print(f"程序运行时发生严重错误: {str(e)}")
            
        finally:
            # 清理资源
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理资源...")
            
            # 关闭浏览器
            if self.login_manager:
                self.login_manager.close_browser()
                
            print("程序已安全退出。再见！")
            
        except Exception as e:
            self.logger.error(f"清理资源时发生错误: {str(e)}")
            print(f"清理资源时发生错误: {str(e)}")

def main():
    """主函数"""
    try:
        app = AutoStudyApp()
        app.run()
        
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()