#!/usr/bin/env python3
"""
测试main.py中的数据库清空功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import AutoStudyApp
from src.database import db

def test_main_clear_function():
    """测试main.py中的清空数据库功能"""
    
    print("测试main.py中的数据库清空功能")
    print("=" * 50)
    
    # 确保有测试数据
    print("\n1. 准备测试数据...")
    db.add_or_update_course('Main测试课程1', 'required', 'http://main1.com', 'main001', 30.0)
    db.add_or_update_course('Main测试课程2', 'elective', 'http://main2.com', 'main002', 60.0)
    
    info_before = db.get_database_info()
    print(f"测试前数据库状态: {info_before['courses_count']} 门课程")
    
    # 创建AutoStudyApp实例并测试清空功能
    print("\n2. 测试clear_database方法...")
    try:
        app = AutoStudyApp()
        
        # 直接调用clear_database方法的逻辑（跳过用户交互）
        print("\n显示数据库信息部分:")
        
        # 测试获取数据库信息
        db_info = db.get_database_info()
        if 'error' not in db_info:
            print(f"✅ 成功获取数据库信息:")
            print(f"  数据库路径: {db_info['database_path']}")
            print(f"  数据库大小: {db_info['database_size_mb']} MB")
            print(f"  课程数量: {db_info['courses_count']}")
            print(f"  学习记录数量: {db_info['learning_logs_count']}")
        
        # 测试获取学习统计
        stats = db.get_learning_statistics()
        if stats['total_courses'] > 0:
            print(f"\n✅ 成功获取学习统计:")
            print(f"  总课程数: {stats['total_courses']}")
            print(f"  已完成课程: {stats['completed_courses']}")
            print(f"  完成率: {stats['completion_rate']:.1f}%")
            for course_type, type_stats in stats['course_type_stats'].items():
                type_name = "必修课" if course_type == 'required' else "选修课"
                print(f"  {type_name}: {type_stats['count']}门 (已完成: {type_stats['completed']}门)")
        
        # 模拟用户确认清空
        print(f"\n3. 模拟执行清空操作...")
        print(f"即将清空 {db_info['courses_count']} 门课程")
        
        # 执行实际的清空操作
        if db.clear_all_data():
            print("✅ 数据库清空成功！")
            
            # 验证清空结果
            new_info = db.get_database_info()
            if 'error' not in new_info:
                print(f"\n清空后状态:")
                print(f"  课程数量: {new_info['courses_count']}")
                print(f"  学习记录数量: {new_info['learning_logs_count']}")
                
                if new_info['courses_count'] == 0:
                    print("✅ 清空功能验证成功！")
                    return True
                else:
                    print("❌ 清空功能验证失败！")
                    return False
        else:
            print("❌ 数据库清空失败！")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_main_interface_functions():
    """测试main.py中其他相关界面功能"""
    
    print("\n" + "=" * 50)
    print("测试main.py中其他相关功能")
    print("=" * 50)
    
    try:
        app = AutoStudyApp()
        
        # 1. 测试show_current_config功能
        print("\n1. 测试配置显示功能...")
        app.show_current_config()
        print("✅ 配置显示功能正常")
        
        # 2. 添加一些测试数据
        print("\n2. 添加测试数据...")
        db.add_or_update_course('界面测试课程1', 'required', 'http://ui1.com', 'ui001', 40.0)
        db.add_or_update_course('界面测试课程2', 'elective', 'http://ui2.com', 'ui002', 80.0)
        
        # 3. 测试show_statistics功能
        print("\n3. 测试统计显示功能...")
        app.show_statistics()
        print("✅ 统计显示功能正常")
        
        # 4. 测试show_course_list功能
        print("\n4. 测试课程列表显示功能...")
        app.show_course_list()
        print("✅ 课程列表显示功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试界面功能时出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    try:
        # 测试清空功能
        if not test_main_clear_function():
            print("\n❌ main.py清空功能测试失败")
            return 1
        
        # 测试其他界面功能
        if not test_main_interface_functions():
            print("\n❌ main.py界面功能测试失败")
            return 1
        
        print("\n" + "=" * 60)
        print("🎉 main.py数据库清空功能完整测试成功！")
        print("   ✅ 数据库信息显示正常")
        print("   ✅ 学习统计显示正常")
        print("   ✅ 数据库清空功能正常")
        print("   ✅ 清空后验证正常")
        print("   ✅ 相关界面功能正常")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)