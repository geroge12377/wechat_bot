#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
So-VITS-SVC 依赖安装脚本
"""

import subprocess
import sys
import platform

def install_dependencies():
    """安装So-VITS-SVC所需的依赖"""
    
    print("开始安装 So-VITS-SVC 依赖...")
    
    # 基础依赖
    base_deps = [
        "torch==2.0.1",
        "torchaudio==2.0.2",
        "torchvision==0.15.2",
        "numpy==1.23.5",
        "scipy==1.10.1",
        "librosa==0.9.2",
        "soundfile==0.12.1",
        "tqdm",
        "tensorboard",
        "matplotlib",
        "Cython",
        "pydub",
        "faiss-cpu",
        "gradio",
        "Markdown",
        "Pillow>=9.1.1",
        "resampy==0.4.2",
        "scikit-learn",
        "tensorboardX",
        "pyworld==0.3.2",
        "praat-parselmouth"
    ]
    
    # 根据系统选择PyTorch版本
    if platform.system() == "Windows":
        # Windows CUDA 11.8
        torch_cmd = [
            sys.executable, '-m', 'pip', 'install',
            'torch==2.0.1+cu118', 'torchvision==0.15.2+cu118', 'torchaudio==2.0.2',
            '--index-url', 'https://download.pytorch.org/whl/cu118'
        ]
    else:
        # Linux/Mac
        torch_cmd = [
            sys.executable, '-m', 'pip', 'install',
            'torch==2.0.1', 'torchvision==0.15.2', 'torchaudio==2.0.2'
        ]
    
    try:
        # 升级pip
        print("升级pip...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # 安装PyTorch
        print("安装PyTorch...")
        subprocess.check_call(torch_cmd)
        
        # 安装其他依赖
        print("安装其他依赖...")
        for dep in base_deps:
            if not dep.startswith("torch"):  # 跳过torch相关，已经安装
                print(f"安装 {dep}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
        
        print("✅ 所有依赖安装完成！")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def check_installation():
    """检查安装是否成功"""
    try:
        import torch
        import librosa
        import soundfile
        import pyworld
        
        print("\n检查安装状态:")
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"✅ CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ CUDA版本: {torch.version.cuda}")
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        print("✅ 其他依赖正常")
        
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("So-VITS-SVC 依赖安装程序")
    print("=" * 60)
    
    if install_dependencies():
        print("\n正在检查安装...")
        check_installation()
    
    input("\n按回车键退出...")