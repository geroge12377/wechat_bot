#!/usr/bin/env python3
"""
修复后的So-VITS-SVC训练启动器
包含start_time变量修复
"""
import os
import sys
import subprocess
import time

def safe_training_launcher():
    """安全的训练启动器"""
    print("🚀 So-VITS-SVC 安全训练启动器")
    print("=" * 50)
    
    project_root = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable"
    os.chdir(project_root)
    
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
    
    # 启动训练，使用错误处理
    model_dir = os.path.join(project_root, "logs", "44k")
    
    cmd = [
        sys.executable, "train.py",
        "-c", "44k/config.json",
        "-m", model_dir
    ]
    
    print(f"💡 执行命令: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # 启动训练进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时显示输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        return_code = process.poll()
        
        if return_code == 0:
            print(f"\n🎉 训练完成!")
        else:
            print(f"\n❌ 训练异常退出，返回代码: {return_code}")
        
        return return_code == 0
        
    except KeyboardInterrupt:
        print(f"\n🛑 用户中断训练")
        if process:
            process.terminate()
        return False
        
    except Exception as e:
        print(f"\n❌ 启动训练失败: {e}")
        return False

def main():
    """主函数"""
    success = safe_training_launcher()
    
    if success:
        print("✅ 训练启动成功!")
    else:
        print("❌ 训练启动失败!")
        print("💡 建议检查错误信息并重试")

if __name__ == "__main__":
    main()
