#!/usr/bin/env python3
"""
反诈智能助手后端启动脚本
"""

import uvicorn
import sys
import os

# 让系统能找到 app 文件夹
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
