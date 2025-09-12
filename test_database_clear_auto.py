#!/usr/bin/env python3
"""
自动测试数据库清空功能（无交互）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import db

def test_database_clear_auto():
    """自动测试数据库清空功能（无用户交互）"""
    
    print("数据库清空功能自动测试")
    print("=" * 50)
    
    # 1. 显示当前数据库信息
    print("\n1. 清空前数据库状态:")
    db_info_before = db.get_database_info()
    
    if 'error' in db_info_before:
        print(f"❌ 获取数据库信息失败: {db_info_before['error']}")
        return False
    
    print(f"  数据库路径: {db_info_before['database_path']}")
    print(f"  数据库大小: {db_info_before['database_size_mb']} MB")
    print(f"  课程数量: {db_info_before['courses_count']}")
    print(f"  学习记录数量: {db_info_before['learning_logs_count']}")
    
    # 2. 显示学习统计
    if db_info_before['courses_count'] > 0:
        stats_before = db.get_learning_statistics()
        print(f"\n2. 清空前学习统计:")
        print(f"  总课程数: {stats_before['total_courses']}")
        print(f"  已完成课程: {stats_before['completed_courses']}")
        print(f"  完成率: {stats_before['completion_rate']:.1f}%")
        print(f"  平均进度: {stats_before['average_progress']:.1f}%")
        
        for course_type, type_stats in stats_before['course_type_stats'].items():
            type_name = "必修课" if course_type == 'required' else "选修课"
            print(f"  {type_name}: {type_stats['count']}门 (已完成: {type_stats['completed']}门)")
    else:
        print("\n2. 数据库已为空")
        return True
        
    # 3. 执行清空操作
    print(f"\n3. 执行数据库清空操作...")
    print(f"   即将清空 {db_info_before['courses_count']} 门课程和 {db_info_before['learning_logs_count']} 条学习记录")
    
    success = db.clear_all_data()
    
    if success:
        print("✅ 数据库清空操作执行成功")
    else:
        print("❌ 数据库清空操作执行失败")
        return False
    
    # 4. 验证清空结果
    print("\n4. 验证清空结果:")
    db_info_after = db.get_database_info()
    
    if 'error' in db_info_after:
        print(f"❌ 获取清空后信息失败: {db_info_after['error']}")
        return False
        
    print(f"  课程数量: {db_info_after['courses_count']} (预期: 0)")
    print(f"  学习记录数量: {db_info_after['learning_logs_count']} (预期: 0)")
    
    # 5. 验证结果
    if db_info_after['courses_count'] == 0 and db_info_after['learning_logs_count'] == 0:
        print("✅ 数据库清空验证成功！")
        
        # 显示清空的统计
        courses_cleared = db_info_before['courses_count']
        logs_cleared = db_info_before['learning_logs_count']
        print(f"\n5. 清空统计:")
        print(f"  清空课程: {courses_cleared} 门")
        print(f"  清空学习记录: {logs_cleared} 条")
        
        return True
    else:
        print("❌ 数据库清空验证失败！")
        print(f"   课程残留: {db_info_after['courses_count']} 门")
        print(f"   学习记录残留: {db_info_after['learning_logs_count']} 条")
        return False

def test_database_functions_after_clear():
    """测试清空后的数据库功能"""
    
    print("\n" + "=" * 50)
    print("测试清空后数据库基本功能")
    print("=" * 50)
    
    try:
        # 1. 测试添加新课程
        print("\n1. 测试添加新课程...")
        
        course_id1 = db.add_or_update_course(
            course_name="清空后测试课程1",
            course_type="required", 
            video_url="https://example.com/video1",
            user_course_id="clear_test_001",
            progress=30.0
        )
        
        course_id2 = db.add_or_update_course(
            course_name="清空后测试课程2", 
            course_type="elective",
            video_url="https://example.com/video2",
            user_course_id="clear_test_002", 
            progress=60.0
        )
        
        print(f"✅ 成功添加2门测试课程，ID: {course_id1}, {course_id2}")
        
        # 2. 验证数据库状态
        print("\n2. 验证数据库状态...")
        db_info = db.get_database_info()
        print(f"  当前课程数量: {db_info['courses_count']}")
        
        if db_info['courses_count'] == 2:
            print("✅ 数据库功能正常，可以正常添加课程")
        else:
            print("❌ 数据库功能异常")
            return False
        
        # 3. 测试学习记录
        print("\n3. 测试学习记录功能...")
        db.add_learning_log(
            course_id=course_id1,
            duration_minutes=15.5,
            progress_before=0.0,
            progress_after=30.0,
            status='completed',
            notes='清空后功能测试'
        )
        
        db_info_with_log = db.get_database_info()
        if db_info_with_log['learning_logs_count'] == 1:
            print("✅ 学习记录功能正常")
        else:
            print("❌ 学习记录功能异常")
            return False
        
        # 4. 测试统计功能
        print("\n4. 测试统计功能...")
        stats = db.get_learning_statistics()
        print(f"  统计结果: 总课程 {stats['total_courses']}, 平均进度 {stats['average_progress']:.1f}%")
        
        if stats['total_courses'] == 2:
            print("✅ 统计功能正常")
        else:
            print("❌ 统计功能异常")
            return False
        
        print("\n✅ 数据库清空后所有功能测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库功能测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    try:
        # 测试数据库清空功能
        print("开始数据库清空功能测试...")
        
        if not test_database_clear_auto():
            print("\n❌ 数据库清空功能测试失败")
            return 1
        
        # 测试清空后的数据库功能
        if not test_database_functions_after_clear():
            print("\n❌ 数据库功能恢复测试失败")
            return 1
        
        print("\n" + "=" * 60)
        print("🎉 数据库清空功能完整测试成功！")
        print("   - 数据库清空功能正常工作")
        print("   - 清空后数据库功能正常")
        print("   - 可以安全地在生产环境中使用")
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