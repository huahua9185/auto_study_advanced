#!/usr/bin/env python3
"""
测试最终的真实API端点
"""

import asyncio
from final_working_api_client import FinalWorkingAPIClient

async def test_final_apis():
    """测试最终的真实API端点"""
    print("🧪 测试最终的真实API端点")
    print("=" * 60)

    async with FinalWorkingAPIClient() as client:
        # 登录
        print("📋 1. 执行登录...")
        success = await client.login("640302198607120020", "My2062660")
        if not success:
            print("❌ 登录失败")
            return
        print("✅ 登录成功")

        # 测试必修课API
        print("\n📋 2. 测试必修课API...")
        required_courses = await client.get_required_courses()
        print(f"   必修课数量: {len(required_courses)}")
        if required_courses:
            course = required_courses[0]
            print(f"   示例课程: {course.get('course_name', 'N/A')}")
            print(f"   课程ID: {course.get('id', 'N/A')}")
            print(f"   用户课程ID: {course.get('user_course_id', 'N/A')}")
            print(f"   学分: {course.get('credit', 'N/A')}")

        # 测试选修课API
        print("\n📋 3. 测试选修课API...")
        elective_courses = await client.get_elective_courses()
        print(f"   选修课数量: {len(elective_courses)}")
        if elective_courses:
            course = elective_courses[0]
            print(f"   示例课程: {course.get('course_name', 'N/A')}")
            print(f"   课程ID: {course.get('id', 'N/A')}")
            print(f"   用户课程ID: {course.get('user_course_id', 'N/A')}")
            print(f"   进度: {course.get('progress', 'N/A')}%")
            print(f"   状态: {course.get('status', 'N/A')}")

        # 测试获取所有课程
        print("\n📋 4. 测试获取所有课程...")
        all_courses = await client.get_all_courses()
        print(f"   总课程数量: {len(all_courses)}")

        required_count = len([c for c in all_courses if c.get('course_type') == 'required'])
        elective_count = len([c for c in all_courses if c.get('course_type') == 'elective'])

        print(f"   必修课: {required_count}")
        print(f"   选修课: {elective_count}")

        # 显示课程分布
        print("\n📊 课程状态统计:")
        completed_courses = [c for c in all_courses if c.get('status') == 'completed' or c.get('progress', 0) >= 100]
        learning_courses = [c for c in all_courses if c.get('status') == 'learning' or (0 < c.get('progress', 0) < 100)]
        not_started_courses = [c for c in all_courses if c.get('status') == 'not_started' or c.get('progress', 0) == 0]

        print(f"   已完成: {len(completed_courses)}")
        print(f"   学习中: {len(learning_courses)}")
        print(f"   未开始: {len(not_started_courses)}")

    print("\n🎉 API测试完成!")

if __name__ == "__main__":
    asyncio.run(test_final_apis())