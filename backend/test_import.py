#!/usr/bin/env python3
"""
测试导入问题
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"当前目录: {current_dir}")
print(f"Python路径: {sys.path}")

try:
    # 尝试导入app模块
    import app
    print("✓ app模块导入成功")
    
    # 尝试导入main
    from app.main import app as fastapi_app
    print("✓ app.main导入成功")
    
    # 尝试导入admin模块
    from app.api import admin
    print("✓ app.api.admin导入成功")
    
    print("\n所有导入成功！")
    
except Exception as e:
    print(f"\n导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()