#!/usr/bin/env python3
"""
多模态反诈智能助手 - 前端启动脚本
启动Streamlit多页面应用
"""

import sys
import os
import subprocess

def main():
    """启动前端应用"""
    print("🚀 启动多模态反诈智能助手前端...")
    print(f"工作目录: {os.getcwd()}")

    # 检查是否在正确的目录
    if not os.path.exists("app.py"):
        print("❌ 错误: 请在frontend目录中运行此脚本")
        print("💡 提示: 请确保当前目录包含app.py文件")
        sys.exit(1)

    # 启动Streamlit应用
    print("🌐 启动Streamlit多页面应用...")
    print("📱 访问地址: http://localhost:8501")
    print("🔐 默认页面: 登录界面 (pages/01_Login.py)")
    print("💡 提示: 按Ctrl+C停止应用")

    try:
        # 使用当前Python环境中的streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--theme.base", "light",
            "--browser.serverAddress", "localhost",
            "--browser.serverPort", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()