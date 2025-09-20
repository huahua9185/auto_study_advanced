#!/bin/bash
"""
虚拟环境激活脚本
使用方法: source activate_venv.sh
"""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🚀 激活虚拟环境..."
source venv/bin/activate

# 显示当前Python环境
echo "✅ 虚拟环境已激活"
echo "Python路径: $(which python)"
echo "Python版本: $(python --version)"

# 检查API版本依赖
echo "🔍 检查依赖..."
python -c "
try:
    import aiohttp, ddddocr
    from Crypto.Cipher import DES
    print('✅ API版本依赖完整')
except ImportError as e:
    print(f'⚠️ 依赖缺失: {e}')
    print('运行以下命令安装:')
    print('pip install aiohttp ddddocr pycryptodome pillow')
"

echo ""
echo "🎯 现在可以运行以下命令:"
echo "  python scorm_based_learning.py    # 完整学习系统"
echo "  python final_working_api_client.py # 基础API测试"
echo "  python start.py                   # 统一启动脚本"
echo ""