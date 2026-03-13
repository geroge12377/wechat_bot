# -*- coding: utf-8 -*-
"""
修正list文件中的音频格式
根据实际存在的文件（优先wav，其次mp3）来生成正确的路径
"""

import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_audio_format():
    print('修正音频文件格式')
    print('=' * 60)

    # 读取原list
    input_file = Path('python_scripts/unicorn_gpt_sovits.list')
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f'原始list: {len(lines)} 条记录')
    print()

    # 音频目录
    audio_dir = Path('D:/GPT_SoVITS/raw/unicorn')

    # 修正每一行
    fixed_lines = []
    not_found = []
    format_stats = {'wav': 0, 'mp3': 0}

    for i, line in enumerate(lines, 1):
        parts = line.strip().split('|')
        if len(parts) != 4:
            print(f'⚠️ 第{i}行格式错误，跳过')
            continue

        # 解析原路径
        old_path = parts[0]
        speaker = parts[1]
        lang = parts[2]
        text = parts[3]

        # 提取文件名（不含扩展名）
        filename_base = old_path.split('\\')[-1].replace('.wav', '').replace('.mp3', '')

        # 检查实际存在的格式（优先wav）
        wav_path = audio_dir / f'{filename_base}.wav'
        mp3_path = audio_dir / f'{filename_base}.mp3'

        actual_format = None
        actual_file = None

        if wav_path.exists():
            actual_format = 'wav'
            actual_file = wav_path
            format_stats['wav'] += 1
        elif mp3_path.exists():
            actual_format = 'mp3'
            actual_file = mp3_path
            format_stats['mp3'] += 1
        else:
            not_found.append(filename_base)
            print(f'✗ 第{i}行: {filename_base} - 文件不存在')
            continue

        # 生成新路径
        new_path = f'D:\\GPT_SoVITS\\raw\\unicorn\\{filename_base}.{actual_format}'
        new_line = f'{new_path}|{speaker}|{lang}|{text}\n'
        fixed_lines.append(new_line)

        if i <= 5:
            print(f'✓ {filename_base}.{actual_format}')

    print()
    print(f'修正完成: {len(fixed_lines)}/{len(lines)} 条记录')
    print(f'格式统计: WAV={format_stats["wav"]}, MP3={format_stats["mp3"]}')

    if not_found:
        print(f'未找到: {len(not_found)} 个文件')

    # 保存修正后的list
    output_file = Path('python_scripts/unicorn_gpt_sovits_fixed.list')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    print()
    print(f'✅ 已保存到: {output_file}')
    print()

    # 显示示例
    print('修正后的格式示例（前3条）:')
    print('-' * 60)
    for line in fixed_lines[:3]:
        parts = line.strip().split('|')
        print(f'路径: {parts[0]}')
        print(f'Speaker: {parts[1]}')
        print(f'语言: {parts[2]}')
        print(f'文本: {parts[3][:50]}...')
        print()

if __name__ == '__main__':
    fix_audio_format()
