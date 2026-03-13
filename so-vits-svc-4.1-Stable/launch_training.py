#!/usr/bin/env python3
"""
增强版训练启动脚本
"""
import os
import sys
import subprocess

def main():
    # 确保在项目根目录
    project_root = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable"
    os.chdir(project_root)
    
    print("🚀 启动 So-VITS-SVC 训练")
    print(f"📁 工作目录: {project_root}")
    
    # 检查关键文件
    required_files = [
        "train.py",
        "44k/config.json",
        "filelists/train.txt",
        "filelists/val.txt"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少文件: {file}")
            return False
    
    print("✅ 所有必要文件已找到")
    
    # 启动训练
    model_dir = os.path.join(project_root, "logs", "44k")
    
    cmd = [
        sys.executable, "train.py",
        "-c", "44k/config.json",
        "-m", model_dir
    ]
    
    print(f"💡 执行命令: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

if __name__ == "__main__":
    main()
