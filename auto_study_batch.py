#!/usr/bin/env python3
"""
非交互式自动学习脚本
适用于后台运行，自动执行学习流程
"""

import sys
import os
import logging
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import Config
from src.login import login_manager
from src.enhanced_course_parser import EnhancedCourseParser
from src.auto_study import AutoStudyManager
from src.database import db

class BatchAutoStudy:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.login_manager = login_manager
        self.course_parser = None
        self.auto_study_manager = None
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/batch_auto_study.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 确保日志目录存在
        log_dir = Path('data')
        log_dir.mkdir(exist_ok=True)
    
    def run_batch_study(self):
        """运行批量自动学习流程"""
        try:
            self.logger.info("开始批量自动学习流程")
            
            # 初始化和登录
            if not self.initialize():
                return False
            
            # 获取并更新课程信息
            if not self.update_courses():
                return False
            
            # 开始自动学习
            return self.start_auto_study()
            
        except Exception as e:
            self.logger.error(f"批量学习失败: {str(e)}")
            return False
        finally:
            self.cleanup()
    
    def initialize(self):
        """初始化程序"""
        try:
            self.logger.info("初始化批量自动学习程序")
            
            # 初始化浏览器
            if not self.login_manager.page:
                if not self.login_manager.init_browser():
                    self.logger.error("浏览器初始化失败")
                    return False
            
            # 检查登录状态
            if not self.login_manager.check_login_status():
                self.logger.info("当前未登录，正在执行登录...")
                if not self.login_manager.login():
                    self.logger.error("登录失败")
                    return False
                self.logger.info("登录成功！")
            else:
                self.logger.info("已处于登录状态")
            
            return True
            
        except Exception as e:
            self.logger.error(f"程序初始化失败: {str(e)}")
            return False
    
    def update_courses(self):
        """获取并更新课程信息"""
        try:
            self.logger.info("开始获取课程信息...")
            
            if not self.course_parser:
                self.course_parser = EnhancedCourseParser(self.login_manager.page)
            
            # 解析所有课程
            courses_data = self.course_parser.parse_all_courses()
            
            if not courses_data or (not courses_data.get('required') and not courses_data.get('elective')):
                self.logger.warning("未获取到课程数据")
                return False
            
            # 统计课程数量
            required_count = len(courses_data.get('required', []))
            elective_count = len(courses_data.get('elective', []))
            total_count = required_count + elective_count
            
            self.logger.info(f"成功获取课程信息 - 必修课: {required_count}门, 选修课: {elective_count}门, 共计: {total_count}门")
            
            # 自动保存课程信息到数据库
            self.logger.info("自动保存课程信息到数据库...")
            if self.course_parser.save_courses_to_database(courses_data):
                self.logger.info("课程信息保存成功")
                return True
            else:
                self.logger.error("课程信息保存失败")
                return False
                
        except Exception as e:
            self.logger.error(f"更新课程信息失败: {str(e)}")
            return False
    
    def start_auto_study(self):
        """开始自动学习"""
        try:
            self.logger.info("开始自动学习流程")
            
            # 检查是否有未完成的课程
            incomplete_courses = db.get_incomplete_courses()
            if not incomplete_courses:
                self.logger.info("没有未完成的课程，学习任务已全部完成！")
                return True
            
            self.logger.info(f"发现 {len(incomplete_courses)} 门未完成的课程，开始学习")
            
            # 创建自动学习管理器
            if not self.auto_study_manager:
                self.auto_study_manager = AutoStudyManager(self.login_manager.page)
            
            # 开始自动学习
            success = self.auto_study_manager.start_auto_study()
            
            if success:
                self.logger.info("自动学习流程完成")
                
                # 显示最终统计
                self.show_final_statistics()
                return True
            else:
                self.logger.warning("自动学习流程未能正常完成")
                return False
                
        except Exception as e:
            self.logger.error(f"自动学习失败: {str(e)}")
            return False
    
    def show_final_statistics(self):
        """显示最终学习统计"""
        try:
            self.logger.info("="*50)
            self.logger.info("最终学习统计")
            self.logger.info("="*50)
            
            stats = db.get_learning_statistics()
            
            self.logger.info(f"总课程数量: {stats['total_courses']}")
            self.logger.info(f"已完成课程: {stats['completed_courses']}")
            self.logger.info(f"完成率: {stats['completion_rate']:.1f}%")
            self.logger.info(f"平均进度: {stats['average_progress']:.1f}%")
            
            self.logger.info("分类统计:")
            for course_type, type_stats in stats['course_type_stats'].items():
                type_name = "必修课" if course_type == 'required' else "选修课"
                self.logger.info(f"  {type_name}: {type_stats['completed']}/{type_stats['count']} (平均进度: {type_stats['avg_progress']:.1f}%)")
            
            self.logger.info("="*50)
            
        except Exception as e:
            self.logger.warning(f"显示统计信息时出错: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理资源...")
            if self.login_manager:
                self.login_manager.close_browser()
            self.logger.info("资源清理完成")
        except Exception as e:
            self.logger.warning(f"清理资源时出错: {str(e)}")

def main():
    """主函数"""
    batch_study = BatchAutoStudy()
    
    try:
        success = batch_study.run_batch_study()
        
        if success:
            print("\n✅ 批量自动学习成功完成!")
            return 0
        else:
            print("\n❌ 批量自动学习失败!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断程序执行")
        batch_study.cleanup()
        return 2
    except Exception as e:
        print(f"\n💥 程序执行异常: {str(e)}")
        batch_study.cleanup()
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)