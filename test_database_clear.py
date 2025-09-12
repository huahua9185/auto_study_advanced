#!/usr/bin/env python3
"""
测试数据库清空功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import db

def test_database_clear():
    """测试数据库清空功能"""
    
    print("数据库清空功能测试")
    print("=" * 50)
    
    # 1. 显示当前数据库信息
    print("\n1. 当前数据库信息:")
    db_info = db.get_database_info()
    
    if 'error' in db_info:
        print(f"获取数据库信息失败: {db_info['error']}")
        return False
    
    print(f"  数据库路径: {db_info['database_path']}")
    print(f"  数据库大小: {db_info['database_size_mb']} MB")
    print(f"  课程数量: {db_info['courses_count']}")
    print(f"  学习记录数量: {db_info['learning_logs_count']}")
    
    # 2. 显示学习统计
    if db_info['courses_count'] > 0:
        print("\n2. 学习统计信息:")
        stats = db.get_learning_statistics()
        print(f"  总课程数: {stats['total_courses']}")
        print(f"  已完成课程: {stats['completed_courses']}")
        print(f"  完成率: {stats['completion_rate']:.1f}%")
        print(f"  平均进度: {stats['average_progress']:.1f}%")
        
        for course_type, type_stats in stats['course_type_stats'].items():
            type_name = "必修课" if course_type == 'required' else "选修课"
            print(f"  {type_name}: {type_stats['count']}门 (已完成: {type_stats['completed']}门, 平均进度: {type_stats['avg_progress']:.1f}%)")
    else:
        print("\n2. 当前数据库为空")
    
    # 3. 询问是否进行清空测试
    if db_info['courses_count'] > 0:
        confirm = input(f"\n是否要测试数据库清空功能？这将删除 {db_info['courses_count']} 门课程的所有数据 (y/n): ")
        if confirm.lower() not in ['y', 'yes', '是']:
            print("取消测试。")
            return True
        
        # 4. 执行清空操作
        print("\n3. 执行数据库清空...")
        success = db.clear_all_data()
        
        if success:
            print("✅ 数据库清空成功！")
        else:
            print("❌ 数据库清空失败！")
            return False
        
        # 5. 验证清空结果
        print("\n4. 验证清空结果:")
        new_info = db.get_database_info()
        
        if 'error' in new_info:
            print(f"获取清空后信息失败: {new_info['error']}")
            return False
            
        print(f"  课程数量: {new_info['courses_count']} (预期: 0)")
        print(f"  学习记录数量: {new_info['learning_logs_count']} (预期: 0)")
        
        # 检查清空是否成功
        if new_info['courses_count'] == 0 and new_info['learning_logs_count'] == 0:
            print("✅ 数据库清空验证成功！")
            return True
        else:
            print("❌ 数据库清空验证失败！")
            return False
    else:
        print("\n3. 数据库已为空，无需清空")
        return True

def test_database_functions():
    """测试数据库其他功能"""
    
    print("\n" + "=" * 50)
    print("测试数据库基本功能")
    print("=" * 50)
    
    # 1. 测试添加课程
    print("\n1. 测试添加测试课程...")
    
    course_id1 = db.add_or_update_course(
        course_name="测试必修课程",
        course_type="required", 
        video_url="https://example.com/video1",
        user_course_id="test001",
        progress=50.0
    )
    
    course_id2 = db.add_or_update_course(
        course_name="测试选修课程", 
        course_type="elective",
        video_url="https://example.com/video2",
        user_course_id="test002", 
        progress=80.0
    )
    
    print(f"添加了2门测试课程，ID: {course_id1}, {course_id2}")
    
    # 2. 测试获取课程
    print("\n2. 测试获取课程...")
    all_courses = db.get_all_courses()
    print(f"数据库中共有 {len(all_courses)} 门课程")
    
    for course in all_courses:
        print(f"  - {course['course_name']} ({course['course_type']}) - 进度: {course['progress']}%")
    
    # 3. 测试学习统计
    print("\n3. 测试学习统计...")
    stats = db.get_learning_statistics()
    print(f"统计信息: 总课程 {stats['total_courses']}, 完成率 {stats['completion_rate']:.1f}%")
    
    # 4. 测试数据库信息
    print("\n4. 测试数据库信息...")
    db_info = db.get_database_info()
    print(f"数据库信息: 课程 {db_info['courses_count']} 门, 大小 {db_info['database_size_mb']} MB")
    
    return True

def main():
    """主函数"""
    try:
        # 先测试数据库清空功能
        if not test_database_clear():
            print("\n❌ 数据库清空功能测试失败")
            return 1
        
        # 再测试数据库基本功能
        if not test_database_functions():
            print("\n❌ 数据库基本功能测试失败")
            return 1
        
        print("\n✅ 所有数据库功能测试成功！")
        return 0
        
    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n测试完成，退出码: {exit_code}")
    sys.exit(exit_code)