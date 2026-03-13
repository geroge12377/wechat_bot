#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RVC 训练数据检查脚本
检查 WAV 文件的质量、采样率、时长等信息
"""

import os
import wave
import glob
from pathlib import Path

def check_wav_file(wav_path):
    """检查单个 WAV 文件的信息"""
    try:
        with wave.open(wav_path, 'rb') as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            framerate = wav.getframerate()
            frames = wav.getnframes()
            duration = frames / float(framerate)

            return {
                'path': wav_path,
                'channels': channels,
                'sample_width': sample_width,
                'sample_rate': framerate,
                'duration': duration,
                'valid': True
            }
    except Exception as e:
        return {
            'path': wav_path,
            'error': str(e),
            'valid': False
        }

def main():
    # 训练数据目录
    data_dir = Path("./so-vits-svc-4.1-Stable/dataset/44k/unicorn/")

    if not data_dir.exists():
        print(f"[ERROR] 数据目录不存在: {data_dir}")
        return

    # 查找所有 WAV 文件
    wav_files = list(data_dir.glob("*.wav"))

    if not wav_files:
        print(f"[ERROR] 在 {data_dir} 中没有找到 WAV 文件")
        return

    print(f"[检查] 找到 {len(wav_files)} 个 WAV 文件\n")
    print("=" * 80)

    # 统计信息
    total_duration = 0
    valid_files = 0
    invalid_files = []
    sample_rates = {}

    # 检查每个文件
    for wav_file in wav_files:
        info = check_wav_file(str(wav_file))

        if info['valid']:
            valid_files += 1
            total_duration += info['duration']

            # 统计采样率
            sr = info['sample_rate']
            sample_rates[sr] = sample_rates.get(sr, 0) + 1

            # 显示文件信息（只显示前 10 个）
            if valid_files <= 10:
                print(f"[OK] {wav_file.name}")
                print(f"   采样率: {info['sample_rate']} Hz")
                print(f"   声道数: {info['channels']}")
                print(f"   时长: {info['duration']:.2f} 秒")
                print()
        else:
            invalid_files.append(info)
            print(f"[ERROR] {wav_file.name}")
            print(f"   错误: {info['error']}")
            print()

    if valid_files > 10:
        print(f"... 还有 {valid_files - 10} 个文件未显示\n")

    # 显示统计信息
    print("=" * 80)
    print("\n[统计信息]:")
    print(f"[OK] 有效文件: {valid_files}")
    print(f"[ERROR] 无效文件: {len(invalid_files)}")
    print(f"[时长] 总时长: {total_duration / 60:.2f} 分钟 ({total_duration:.2f} 秒)")
    print(f"[平均] 平均时长: {total_duration / valid_files:.2f} 秒/文件")

    print("\n[采样率分布]:")
    for sr, count in sorted(sample_rates.items()):
        print(f"   {sr} Hz: {count} 个文件")

    # 给出建议
    print("\n[建议]:")

    if total_duration < 600:  # 少于 10 分钟
        print("   [警告] 训练数据时长较短（少于 10 分钟），建议增加更多数据")
    elif total_duration < 1800:  # 10-30 分钟
        print("   [OK] 训练数据时长适中（10-30 分钟），可以开始训练")
    else:
        print("   [OK] 训练数据时长充足（超过 30 分钟），效果应该不错")

    # 检查采样率一致性
    if len(sample_rates) > 1:
        print("   [警告] 检测到多种采样率，建议统一采样率以获得更好效果")
        print("   [提示] 可以在 RVC 预处理时自动重采样")
    else:
        sr = list(sample_rates.keys())[0]
        if sr == 44100:
            print("   [OK] 采样率统一为 44.1kHz，适合训练")
        elif sr == 48000:
            print("   [OK] 采样率统一为 48kHz，适合训练")
        else:
            print(f"   [警告] 采样率为 {sr} Hz，建议重采样到 44.1kHz 或 48kHz")

    # RVC 训练建议
    print("\n[RVC 训练参数建议]:")
    print(f"   实验名称: unicorn")
    print(f"   目标采样率: 40k 或 48k")
    print(f"   训练轮数: 200-500 epoch")

    if total_duration < 600:
        print(f"   批次大小: 4-8")
    elif total_duration < 1800:
        print(f"   批次大小: 8-12")
    else:
        print(f"   批次大小: 12-16")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
