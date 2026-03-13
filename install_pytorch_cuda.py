#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装 CUDA 版本的 PyTorch
适用于 NVIDIA GPU (CUDA 11.8 或 12.1)
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """运行命令并显示输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✓ {description} - 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} - 失败")
        print(f"错误: {e}")
        return False

def check_current_pytorch():
    """检查当前 PyTorch 版本"""
    print("\n检查当前 PyTorch 状态...")
    try:
        import torch
        print(f"PyTorch 版本: {torch.__version__}")
        print(f"CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA 版本: {torch.version.cuda}")
            print(f"GPU 数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        return True
    except ImportError:
        print("PyTorch 未安装")
        return False

def uninstall_pytorch():
    """卸载现有的 PyTorch"""
    print("\n卸载现有 PyTorch...")
    cmd = "pip uninstall torch torchvision torchaudio -y"
    return run_command(cmd, "卸载 PyTorch")

def install_pytorch_cuda_official():
    """从 PyTorch 官方源安装 CUDA 版本"""
    print("\n尝试从 PyTorch 官方源安装 CUDA 12.1 版本...")
    cmd = "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    return run_command(cmd, "安装 PyTorch CUDA 12.1")

def install_pytorch_cuda_mirror():
    """从清华镜像安装（可能是 CPU 版本）"""
    print("\n从清华镜像安装 PyTorch...")
    cmd = "pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple"
    return run_command(cmd, "安装 PyTorch (清华镜像)")

def download_pytorch_whl():
    """提供手动下载链接"""
    print("\n" + "="*60)
    print("手动下载 PyTorch CUDA 版本")
    print("="*60)
    print("\n如果自动安装失败，可以手动下载 whl 文件：")
    print("\n1. 访问 PyTorch 官网：")
    print("   https://pytorch.org/get-started/locally/")
    print("\n2. 或直接下载 whl 文件：")
    print("   https://download.pytorch.org/whl/torch_stable.html")
    print("\n3. 选择：")
    print("   - Python 3.14")
    print("   - Windows")
    print("   - CUDA 11.8 或 12.1")
    print("\n4. 下载后安装：")
    print("   pip install torch-*.whl")
    print("   pip install torchvision-*.whl")
    print("   pip install torchaudio-*.whl")
    print("\n推荐版本：")
    print("   torch-2.0.1+cu118")
    print("   torchvision-0.15.2+cu118")
    print("   torchaudio-2.0.2+cu118")

def main():
    """主函数"""
    print("="*60)
    print("PyTorch CUDA 版本安装脚本")
    print("="*60)

    # 检查当前状态
    has_pytorch = check_current_pytorch()

    if has_pytorch:
        print("\n检测到已安装 PyTorch")
        choice = input("\n是否卸载并重新安装 CUDA 版本? (y/n): ").lower().strip()
        if choice != 'y':
            print("取消安装")
            return

        # 卸载现有版本
        if not uninstall_pytorch():
            print("\n卸载失败，请手动卸载后重试")
            return

    # 尝试安装 CUDA 版本
    print("\n开始安装 PyTorch CUDA 版本...")

    # 方法 1: PyTorch 官方源 (CUDA 12.1)
    success = install_pytorch_cuda_official()

    if not success:
        print("\n官方源安装失败，尝试其他方法...")

        # 方法 2: 清华镜像 (可能是 CPU 版本)
        print("\n注意：清华镜像可能只有 CPU 版本")
        choice = input("是否尝试清华镜像? (y/n): ").lower().strip()
        if choice == 'y':
            success = install_pytorch_cuda_mirror()

    # 验证安装
    print("\n" + "="*60)
    print("验证安装结果")
    print("="*60)

    # 重新导入检查
    if 'torch' in sys.modules:
        del sys.modules['torch']

    check_current_pytorch()

    # 如果还是失败，提供手动下载方案
    try:
        import torch
        if not torch.cuda.is_available():
            print("\n警告：安装的是 CPU 版本，没有 CUDA 支持")
            download_pytorch_whl()
    except ImportError:
        print("\n安装失败")
        download_pytorch_whl()

    print("\n" + "="*60)
    print("安装完成")
    print("="*60)

if __name__ == "__main__":
    main()
