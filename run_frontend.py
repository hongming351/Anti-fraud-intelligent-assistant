#!/usr/bin/env python3
"""
多模态反诈智能助手 - 前端启动入口
从项目根目录启动新的前端应用
"""

import sys
import os
import subprocess

def main():
    """启动前端应用"""
    print("🛡️ 多模态反诈智能助手 - 前端启动")
    print("=" * 50)

    # 检查前端目录是否存在
    frontend_dir = "frontend"
    if not os.path.exists(frontend_dir):
        print(f"❌ 错误: 前端目录 '{frontend_dir}' 不存在")
        print("💡 提示: 请先创建前端目录结构")
        sys.exit(1)

    # 切换到前端目录
    original_dir = os.getcwd()
    os.chdir(frontend_dir)

    try:
        # 运行前端启动脚本
        subprocess.run([sys.executable, "run.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 前端启动失败: {e}")
        sys.exit(1)
    finally:
        # 切换回原始目录
        os.chdir(original_dir)

if __name__ == "__main__":
    main()