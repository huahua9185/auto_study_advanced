#!/usr/bin/env python3
"""
快速启动 - 一键运行API版本学习系统
"""

import sys
import subprocess
import importlib.util

def check_and_install_deps():
    """检查并安装API版本依赖"""
    deps = {
        'aiohttp': 'aiohttp>=3.8.0',
        'ddddocr': 'ddddocr==1.0.6',
        'Crypto': 'pycryptodome>=3.15.0',
        'PIL': 'pillow>=10.0.0'
    }

    missing = []
    for module, package in deps.items():
        try:
            importlib.util.find_spec(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"🔧 正在安装依赖: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            print("✅ 依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败，请手动安装:")
            print(f"pip install {' '.join(missing)}")
            return False
    return True

def main():
    """主函数"""
    print("🚀 智能自动学习系统 - 快速启动")
    print("=" * 50)

    # 检查并安装依赖
    if not check_and_install_deps():
        return

    print("\n🎓 启动完整SCORM学习系统...")
    print("提示: 按 Ctrl+C 可以停止学习")
    print("=" * 50)

    try:
        # 运行主学习系统
        subprocess.run([sys.executable, 'scorm_based_learning.py'])
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except FileNotFoundError:
        print("❌ 找不到 scorm_based_learning.py 文件")
        print("请确保在正确的目录中运行此脚本")
    except Exception as e:
        print(f"❌ 运行错误: {e}")

if __name__ == "__main__":
    main()