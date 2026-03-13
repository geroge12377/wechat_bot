#!/usr/bin/env python3
"""
so-vits-svc训练启动脚本
"""

import os
import subprocess
import sys

def start_training():
    """启动训练"""
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 当前目录和检查点目录
    current_dir = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\44k"
    checkpoint_dir = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\logs\44k"
    
    print("🚀 启动so-vits-svc训练")
    print("=" * 50)
    print(f"📁 当前目录: {current_dir}")
    print(f"📁 检查点目录: {checkpoint_dir}")
    
    # 验证文件
    g_file = os.path.join(checkpoint_dir, "G_25.pth")
    d_file = os.path.join(checkpoint_dir, "D_25.pth")
    
    if not os.path.exists(g_file):
        print(f"❌ G检查点不存在: {g_file}")
        return False
        
    if not os.path.exists(d_file):
        print(f"❌ D检查点不存在: {d_file}")
        return False
    
    print("✅ 检查点文件验证通过")
    
    # 切换到44k目录
    os.chdir(current_dir)
    
    # 启动训练
    cmd = [sys.executable, "../train.py", "-c", "config.json", "-m", checkpoint_dir]
    
    print(f"🔄 执行命令: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 训练失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 用户中断训练")
        return False

if __name__ == "__main__":
    start_training()
