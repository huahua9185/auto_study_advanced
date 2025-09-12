#!/usr/bin/env python3
"""
自动化学习程序启动脚本
"""

import os
import sys
from pathlib import Path

# 确保在正确的目录中运行
project_root = Path(__file__).parent
os.chdir(project_root)

# 检查虚拟环境
if not os.path.exists('venv'):
    print("错误: 未找到虚拟环境！")
    print("请先运行以下命令创建虚拟环境:")
    print("python3 -m venv venv")
    print("source venv/bin/activate")  
    print("pip install -r requirements.txt")
    print("playwright install firefox")
    sys.exit(1)

# 添加项目路径
sys.path.insert(0, str(project_root))

try:
    from src.main import main
    main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有依赖:")
    print("source venv/bin/activate")
    print("pip install -r requirements.txt")
    print("playwright install firefox")
    sys.exit(1)
except Exception as e:
    print(f"程序运行错误: {e}")
    sys.exit(1)