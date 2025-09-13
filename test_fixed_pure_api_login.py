#!/usr/bin/env python3
"""
测试修复后的纯API登录系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pure_api_learner import PureAPILearner
import logging

# 设置详细日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

def test_pure_api_login():
    """测试纯API登录"""
    print("🚀 测试修复后的纯API登录系统...")
    print("=" * 80)

    try:
        # 创建纯API学习器
        learner = PureAPILearner(
            username="640302198607120020",
            password="My2062660"
        )

        # 测试密码加密
        print("🔒 测试密码加密...")
        encrypted = learner._encrypt_password("My2062660")
        print(f"  原始密码: My2062660")
        print(f"  加密结果: {encrypted}")
        print(f"  预期结果: mVQa+elBFeEJd4M1m5eRJw==")

        if encrypted == "mVQa+elBFeEJd4M1m5eRJw==":
            print("  ✅ 密码加密匹配浏览器结果！")
        else:
            print("  ❌ 密码加密不匹配")
            return False

        print("-" * 60)

        # 测试登录
        print("🔑 测试登录流程...")
        login_result = learner.login()

        if login_result:
            print("✅ 纯API登录成功！")
            print(f"👤 用户信息: {learner.user_info}")
            print(f"🍪 会话状态: 已建立")
            return True
        else:
            print("❌ 纯API登录失败")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_course_operations():
    """测试课程操作（如果登录成功）"""
    print("\n" + "=" * 80)
    print("🎓 测试课程操作...")

    try:
        learner = PureAPILearner(
            username="640302198607120020",
            password="My2062660"
        )

        # 登录
        if not learner.login():
            print("❌ 登录失败，无法测试课程操作")
            return False

        print("✅ 登录成功，开始测试课程操作")

        # 获取选修课程
        print("\n📚 获取选修课程列表...")
        elective_courses = learner.get_elective_courses()
        print(f"  找到 {len(elective_courses)} 门选修课程")

        for course in elective_courses[:3]:  # 只显示前3门
            print(f"  - {course.course_name} (进度: {course.progress}%)")

        # 获取必修课程
        print("\n📖 获取必修课程列表...")
        required_courses = learner.get_required_courses()
        print(f"  找到 {len(required_courses)} 门必修课程")

        for course in required_courses[:3]:  # 只显示前3门
            print(f"  - {course.course_name} (进度: {course.progress}%)")

        return True

    except Exception as e:
        print(f"❌ 课程操作异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始测试修复后的纯API系统")

    # 测试登录
    login_success = test_pure_api_login()

    if login_success:
        # 测试课程操作
        course_success = test_course_operations()

        if course_success:
            print("\n🎉 所有测试通过！纯API系统完全可用！")
        else:
            print("\n⚠️ 登录成功但课程操作有问题")
    else:
        print("\n❌ 登录测试失败，需要进一步调试")

    print("\n" + "=" * 80)