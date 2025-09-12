"""
Pillow 兼容性修复
解决 ddddocr 在新版 Pillow 中的兼容性问题
"""

try:
    from PIL import Image
    
    # 检查是否存在 ANTIALIAS 属性
    if not hasattr(Image, 'ANTIALIAS'):
        # 在新版 Pillow 中，ANTIALIAS 已被重命名为 LANCZOS
        Image.ANTIALIAS = Image.LANCZOS
        print("已修复 Pillow 兼容性: Image.ANTIALIAS -> Image.LANCZOS")
        
except ImportError:
    print("PIL/Pillow 未安装")
except Exception as e:
    print(f"Pillow 兼容性修复失败: {e}")