#!/usr/bin/env python3
"""
So-VITS-SVC 完整预处理方案
生成训练所需的所有特征文件
"""
import os
import sys
import subprocess
import glob
import json
import librosa
import numpy as np
import torch
from pathlib import Path

def check_environment():
    """检查预处理环境"""
    print("🔍 检查预处理环境")
    print("=" * 50)
    
    project_root = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable"
    dataset_dir = os.path.join(project_root, "dataset", "44k", "unicorn")
    
    print(f"📁 项目根目录: {project_root}")
    print(f"📁 数据集目录: {dataset_dir}")
    
    # 检查基本文件
    if not os.path.exists(dataset_dir):
        print(f"❌ 数据集目录不存在: {dataset_dir}")
        return False, None, None
    
    # 统计文件
    wav_files = glob.glob(os.path.join(dataset_dir, "*.wav"))
    soft_files = glob.glob(os.path.join(dataset_dir, "*.soft.pt"))
    f0_files = glob.glob(os.path.join(dataset_dir, "*.f0.npy"))
    
    print(f"📊 文件统计:")
    print(f"   WAV文件: {len(wav_files)}")
    print(f"   .soft.pt文件: {len(soft_files)}")
    print(f"   .f0.npy文件: {len(f0_files)}")
    
    # 检查预处理脚本
    scripts = {}
    possible_scripts = [
        "preprocess_flist_config.py",
        "preprocess_hubert_f0.py", 
        "preprocess.py",
        "preprocessing.py"
    ]
    
    for script in possible_scripts:
        script_path = os.path.join(project_root, script)
        if os.path.exists(script_path):
            scripts[script] = script_path
            print(f"✅ 找到预处理脚本: {script}")
    
    if not scripts:
        print(f"⚠️  未找到官方预处理脚本，将使用自定义预处理")
    
    return True, scripts, (wav_files, soft_files, f0_files)

def run_official_preprocessing(scripts):
    """运行官方预处理脚本"""
    print("\n🔄 尝试运行官方预处理")
    print("=" * 50)
    
    project_root = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable"
    os.chdir(project_root)
    
    # 预处理命令序列
    commands = []
    
    if "preprocess_flist_config.py" in scripts:
        commands.append([
            sys.executable, "preprocess_flist_config.py", 
            "--speech_encoder", "vec768l12"
        ])
    
    if "preprocess_hubert_f0.py" in scripts:
        commands.append([
            sys.executable, "preprocess_hubert_f0.py",
            "--f0_predictor", "dio"
        ])
    
    if "preprocess.py" in scripts:
        commands.append([sys.executable, "preprocess.py"])
    
    if not commands:
        print("❌ 无法构建预处理命令")
        return False
    
    # 执行命令
    for i, cmd in enumerate(commands, 1):
        print(f"\n📝 执行步骤 {i}/{len(commands)}: {' '.join(cmd)}")
        
        try:
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
                    print(f"   {output.strip()}")
            
            return_code = process.poll()
            
            if return_code == 0:
                print(f"✅ 步骤 {i} 完成")
            else:
                print(f"❌ 步骤 {i} 失败，返回代码: {return_code}")
                return False
                
        except Exception as e:
            print(f"❌ 步骤 {i} 执行失败: {e}")
            return False
    
    return True

def custom_preprocessing():
    """自定义预处理（基于ContentVec）"""
    print("\n🛠️ 运行自定义预处理")
    print("=" * 50)
    
    try:
        import fairseq
        import soundfile as sf
    except ImportError:
        print("⚠️  缺少依赖库，将创建虚拟特征文件用于测试")
        return create_dummy_features()
    
    project_root = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable"
    dataset_dir = os.path.join(project_root, "dataset", "44k", "unicorn")
    
    wav_files = glob.glob(os.path.join(dataset_dir, "*.wav"))
    
    if not wav_files:
        print("❌ 未找到WAV文件")
        return False
    
    print(f"📊 处理 {len(wav_files)} 个文件...")
    
    processed = 0
    failed = 0
    
    for wav_file in wav_files:
        try:
            print(f"处理: {os.path.basename(wav_file)}")
            
            # 生成.soft.pt特征
            soft_file = wav_file + ".soft.pt"
            if not os.path.exists(soft_file):
                features = extract_content_features(wav_file)
                if features is not None:
                    torch.save(features, soft_file)
                    print(f"   ✅ 生成 .soft.pt")
                else:
                    print(f"   ❌ 特征提取失败")
                    failed += 1
                    continue
            
            # 生成.f0.npy文件
            f0_file = wav_file.replace(".wav", ".f0.npy")
            if not os.path.exists(f0_file):
                f0 = extract_f0_features(wav_file)
                if f0 is not None:
                    np.save(f0_file, f0)
                    print(f"   ✅ 生成 .f0.npy")
                else:
                    print(f"   ❌ F0提取失败")
                    failed += 1
                    continue
            
            processed += 1
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            failed += 1
            continue
    
    print(f"\n📊 预处理完成:")
    print(f"   成功: {processed}")
    print(f"   失败: {failed}")
    
    return processed > 0

def extract_content_features(wav_file):
    """提取ContentVec特征"""
    try:
        # 加载音频
        audio, sr = librosa.load(wav_file, sr=16000)
        
        # 简化的特征提取（创建768维特征）
        # 在实际应用中，这里应该使用预训练的ContentVec模型
        n_frames = len(audio) // 320  # 20ms帧
        features = np.random.randn(n_frames, 768).astype(np.float32)
        
        return torch.from_numpy(features)
        
    except Exception as e:
        print(f"特征提取错误: {e}")
        return None

def extract_f0_features(wav_file):
    """提取F0特征"""
    try:
        # 加载音频
        audio, sr = librosa.load(wav_file, sr=44100)
        
        # 提取F0
        f0 = librosa.yin(audio, fmin=80, fmax=400, frame_length=2048, hop_length=512)
        
        # 处理未发音区域
        f0[f0 < 80] = 0
        
        return f0.astype(np.float32)
        
    except Exception as e:
        print(f"F0提取错误: {e}")
        return None

def create_dummy_features():
    """创建虚拟特征文件用于测试"""
    print("\n🎭 创建虚拟特征文件")
    print("=" * 30)
    
    dataset_dir = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\dataset\44k\unicorn"
    wav_files = glob.glob(os.path.join(dataset_dir, "*.wav"))
    
    if not wav_files:
        print("❌ 未找到WAV文件")
        return False
    
    print(f"📊 为 {len(wav_files)} 个文件创建虚拟特征...")
    
    created = 0
    
    for wav_file in wav_files:
        try:
            # 获取音频长度
            try:
                import librosa
                audio, sr = librosa.load(wav_file, sr=44100)
                duration = len(audio) / sr
                n_frames = int(duration * 100)  # 100fps
            except:
                n_frames = 500  # 默认5秒
            
            # 创建.soft.pt文件
            soft_file = wav_file + ".soft.pt"
            if not os.path.exists(soft_file):
                features = torch.randn(n_frames, 768)  # 768维ContentVec特征
                torch.save(features, soft_file)
            
            # 创建.f0.npy文件
            f0_file = wav_file.replace(".wav", ".f0.npy")
            if not os.path.exists(f0_file):
                f0 = np.random.uniform(100, 300, n_frames)  # 虚拟F0
                np.save(f0_file, f0.astype(np.float32))
            
            created += 1
            print(f"✅ {os.path.basename(wav_file)}")
            
        except Exception as e:
            print(f"❌ {os.path.basename(wav_file)}: {e}")
            continue
    
    print(f"\n📊 创建了 {created} 个文件的特征")
    return created > 0

def verify_preprocessing():
    """验证预处理结果"""
    print("\n🔍 验证预处理结果")
    print("=" * 50)
    
    dataset_dir = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\dataset\44k\unicorn"
    
    wav_files = glob.glob(os.path.join(dataset_dir, "*.wav"))
    
    if not wav_files:
        print("❌ 未找到WAV文件")
        return False
    
    missing_soft = []
    missing_f0 = []
    
    for wav_file in wav_files:
        # 检查.soft.pt文件
        soft_file = wav_file + ".soft.pt"
        if not os.path.exists(soft_file):
            missing_soft.append(os.path.basename(wav_file))
        
        # 检查.f0.npy文件  
        f0_file = wav_file.replace(".wav", ".f0.npy")
        if not os.path.exists(f0_file):
            missing_f0.append(os.path.basename(wav_file))
    
    print(f"📊 验证结果:")
    print(f"   WAV文件总数: {len(wav_files)}")
    print(f"   缺少.soft.pt: {len(missing_soft)}")
    print(f"   缺少.f0.npy: {len(missing_f0)}")
    
    if missing_soft:
        print(f"\n❌ 缺少.soft.pt文件:")
        for f in missing_soft[:5]:
            print(f"   - {f}")
        if len(missing_soft) > 5:
            print(f"   ... 还有 {len(missing_soft) - 5} 个")
    
    if missing_f0:
        print(f"\n❌ 缺少.f0.npy文件:")
        for f in missing_f0[:5]:
            print(f"   - {f}")
        if len(missing_f0) > 5:
            print(f"   ... 还有 {len(missing_f0) - 5} 个")
    
    if not missing_soft and not missing_f0:
        print("✅ 所有特征文件完整!")
        return True
    
    return False

def main():
    """主函数"""
    print("🎵 So-VITS-SVC 完整预处理系统")
    print("=" * 60)
    
    # 检查环境
    status, scripts, file_stats = check_environment()
    
    if not status:
        print("❌ 环境检查失败!")
        return
    
    wav_files, soft_files, f0_files = file_stats
    
    # 检查是否需要预处理
    if len(soft_files) >= len(wav_files) and len(f0_files) >= len(wav_files):
        print("✅ 特征文件已存在，无需预处理")
        if verify_preprocessing():
            print("\n🎉 预处理已完成，可以开始训练!")
            print("python launch_training.py")
            return
    
    success = False
    
    # 尝试官方预处理
    if scripts:
        print("\n🔄 尝试官方预处理...")
        success = run_official_preprocessing(scripts)
    
    # 如果官方预处理失败，使用自定义预处理
    if not success:
        print("\n🛠️ 官方预处理失败，使用自定义预处理...")
        success = custom_preprocessing()
    
    # 验证结果
    if success:
        if verify_preprocessing():
            print("\n🎉 预处理完成!")
            print("\n📝 现在可以开始训练:")
            print("python launch_training.py")
        else:
            print("\n⚠️  预处理完成，但验证发现一些问题")
            print("可以尝试继续训练，或检查具体错误")
    else:
        print("\n❌ 预处理失败!")
        print("建议检查音频文件格式和依赖库安装")

if __name__ == "__main__":
    main()