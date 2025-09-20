#!/usr/bin/env python3
"""
测试数据库迁移功能
"""

import asyncio
import sys
import sqlite3
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from console_learning_system.core.config_manager import ConfigManager
from console_learning_system.core.login_manager import LoginManager
from console_learning_system.core.course_manager import CourseManager

def check_database_schema(db_file):
    """检查数据库架构"""
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(courses)")
            columns = cursor.fetchall()

            print("数据库架构:")
            print("-" * 50)
            for col in columns:
                print(f"  {col[1]:<20} {col[2]:<15} (NOT NULL: {bool(col[3])}, DEFAULT: {col[4]})")

            return [col[1] for col in columns]
    except Exception as e:
        print(f"检查数据库架构失败: {e}")
        return []

async def test_database_migration():
    """测试数据库迁移"""
    print("🧪 测试数据库迁移功能")
    print("=" * 60)

    # 1. 检查迁移前的数据库架构
    print("📋 1. 迁移前数据库架构...")
    data_dir = Path("console_learning_system/data")
    db_file = data_dir / "courses.db"

    if db_file.exists():
        old_columns = check_database_schema(db_file)
        print(f"   发现 {len(old_columns)} 个现有字段")
    else:
        print("   数据库文件不存在，将创建新的")
        old_columns = []

    # 2. 初始化课程管理器（会触发数据库迁移）
    print("\n📋 2. 初始化课程管理器并执行迁移...")
    config_manager = ConfigManager()
    login_manager = LoginManager(config_manager)
    course_manager = CourseManager(config_manager, login_manager)

    await course_manager.initialize()

    # 3. 检查迁移后的数据库架构
    print("\n📋 3. 迁移后数据库架构...")
    new_columns = check_database_schema(db_file)
    print(f"   现在有 {len(new_columns)} 个字段")

    # 4. 比较迁移前后的差异
    print("\n📋 4. 迁移结果分析...")
    if old_columns:
        added_columns = set(new_columns) - set(old_columns)
        if added_columns:
            print(f"   ✅ 新增字段: {', '.join(sorted(added_columns))}")
        else:
            print("   ℹ️ 没有新增字段（数据库已是最新）")
    else:
        print(f"   ✅ 创建了新数据库，包含 {len(new_columns)} 个字段")

    # 5. 验证字段完整性
    print("\n📋 5. 验证字段完整性...")
    required_fields = [
        'course_name', 'course_type', 'progress', 'video_url', 'user_course_id',
        'course_id', 'description', 'duration', 'last_study_time',
        'is_completed', 'is_started', 'created_at', 'updated_at',
        'credit', 'period', 'lecturer', 'status', 'select_date',
        'complete_date', 'study_times', 'process'
    ]

    missing_fields = set(required_fields) - set(new_columns)
    if missing_fields:
        print(f"   ❌ 缺少字段: {', '.join(sorted(missing_fields))}")
    else:
        print("   ✅ 所有必需字段都存在")

    # 6. 测试数据保存和加载
    print("\n📋 6. 测试数据保存和加载...")
    try:
        # 创建测试课程数据
        test_course_data = {
            'course_name': '测试课程',
            'course_type': 'required',
            'progress': 50.0,
            'video_url': 'https://example.com/video',
            'user_course_id': '12345',
            'course_id': '67890',
            'description': '这是一个测试课程',
            'duration': 120,
            'last_study_time': '2025-01-01 12:00:00',
            'credit': 2.0,
            'period': 32.0,
            'lecturer': '张教授',
            'status': 'learning',
            'select_date': '2025-01-01',
            'complete_date': '',
            'study_times': 5,
            'process': 50.0
        }

        from console_learning_system.core.course_manager import Course
        test_course = Course(test_course_data)

        # 临时添加测试课程
        original_courses = course_manager.courses.copy()
        course_manager.courses = [test_course]

        # 保存到数据库
        course_manager._save_to_database()
        print("   ✅ 测试数据保存成功")

        # 从数据库加载
        loaded_courses = course_manager._load_from_database()
        if loaded_courses and len(loaded_courses) == 1:
            loaded_course = loaded_courses[0]
            print("   ✅ 测试数据加载成功")

            # 验证字段值
            print(f"      课程名称: {loaded_course.course_name}")
            print(f"      学分: {loaded_course.credit}")
            print(f"      讲师: {loaded_course.lecturer}")
            print(f"      学习次数: {loaded_course.study_times}")
        else:
            print("   ❌ 测试数据加载失败")

        # 恢复原始数据
        course_manager.courses = original_courses
        course_manager._save_to_database()

    except Exception as e:
        print(f"   ❌ 数据保存加载测试失败: {e}")

    print("\n🎉 数据库迁移测试完成!")

if __name__ == "__main__":
    asyncio.run(test_database_migration())