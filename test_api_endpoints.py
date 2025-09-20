#!/usr/bin/env python3
"""
测试课程管理的API端点
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from final_working_api_client import FinalWorkingAPIClient

async def test_course_api_endpoints():
    """测试课程API端点"""
    print("🧪 测试课程管理API端点")
    print("=" * 60)

    # 1. 初始化API客户端
    print("📋 1. 初始化API客户端...")
    client = FinalWorkingAPIClient()
    await client.initialize()

    # 2. 登录
    print("📋 2. 执行登录...")
    username = "640302198607120020"
    password = "My2062660"

    login_success = await client.login(username, password)
    if not login_success:
        print("❌ 登录失败，无法测试API端点")
        await client.close()
        return

    print("✅ 登录成功")

    # 3. 测试原有的选中课程API
    print("\n📋 3. 测试原有的选中课程API...")
    try:
        selected_courses = await client.get_selected_courses()
        print(f"   选中课程数量: {len(selected_courses)}")
        if selected_courses:
            print(f"   示例课程: {selected_courses[0].get('course_name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 选中课程API错误: {e}")

    # 4. 测试必修课程API
    print("\n📋 4. 测试必修课程API...")
    try:
        required_courses = await client.get_required_courses()
        print(f"   必修课程数量: {len(required_courses)}")
        if required_courses:
            print(f"   示例必修课: {required_courses[0].get('course_name', 'N/A')}")
            print(f"   课程类型: {required_courses[0].get('course_type', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 必修课程API错误: {e}")

    # 5. 测试选修课程API
    print("\n📋 5. 测试选修课程API...")
    try:
        elective_courses = await client.get_elective_courses()
        print(f"   选修课程数量: {len(elective_courses)}")
        if elective_courses:
            print(f"   示例选修课: {elective_courses[0].get('course_name', 'N/A')}")
            print(f"   课程类型: {elective_courses[0].get('course_type', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 选修课程API错误: {e}")

    # 6. 测试获取所有课程API
    print("\n📋 6. 测试获取所有课程API...")
    try:
        all_courses = await client.get_all_courses()
        print(f"   总课程数量: {len(all_courses)}")

        required_count = len([c for c in all_courses if c.get('course_type') == 'required'])
        elective_count = len([c for c in all_courses if c.get('course_type') == 'elective'])

        print(f"   必修课数量: {required_count}")
        print(f"   选修课数量: {elective_count}")

        if all_courses:
            print(f"   示例课程: {all_courses[0].get('course_name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 获取所有课程API错误: {e}")

    # 7. 清理
    print("\n📋 7. 清理资源...")
    await client.close()
    print("✅ 测试完成")

    # 8. API端点总结
    print(f"\n📊 API端点总结:")
    print(f"   原选中课程: /device/userCourse_new!getUserCourse.do")
    print(f"   必修课程: /device/studyCenter!getRequiredCourses.do?id=275")
    print(f"   选修课程: /device/studyCenter!getElectiveCourses.do?active_menu=2")

if __name__ == "__main__":
    asyncio.run(test_course_api_endpoints())