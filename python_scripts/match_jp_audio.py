# -*- coding: utf-8 -*-
"""
匹配日文文本和音频文件
根据场景和内容，将日文文本对应到实际的音频文件
"""

import sys
import io
from pathlib import Path
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def detect_language(text):
    """检测文本语言"""
    chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    japanese_count = sum(1 for char in text if
                       ('\u3040' <= char <= '\u309f') or
                       ('\u30a0' <= char <= '\u30ff'))
    return 'JA' if japanese_count > chinese_count else 'ZH'

def main():
    print('日文文本与音频文件匹配工具')
    print('=' * 60)

    # 读取日文list
    jp_list_file = Path('python_scripts/so-vits-svc-4.1-Stable/dataset_raw/unicorn_jp/unicorn_jp.list')
    with open(jp_list_file, 'r', encoding='utf-8') as f:
        jp_lines = f.readlines()

    # 解析日文数据
    jp_data = []
    for line in jp_lines:
        parts = line.strip().split('|')
        if len(parts) == 3:
            jp_data.append({
                'path': parts[0],
                'lang': parts[1],
                'text': parts[2]
            })

    print(f'日文文本数: {len(jp_data)}')

    # 读取中文list（获取文件名映射）
    zh_list_file = Path('python_scripts/so-vits-svc-4.1-Stable/dataset_raw/unicorn/unicorn.list')
    zh_data = []
    if zh_list_file.exists():
        with open(zh_list_file, 'r', encoding='utf-8') as f:
            zh_lines = f.readlines()

        for line in zh_lines:
            parts = line.strip().split('|')
            if len(parts) == 3:
                filename = parts[0].split('/')[-1].replace('.wav', '')
                zh_data.append({
                    'filename': filename,
                    'text': parts[2]
                })

        print(f'中文文本数: {len(zh_data)}')

    # 检查音频目录
    audio_dir = Path('D:/GPT_SoVITS/raw/unicorn')
    if not audio_dir.exists():
        print(f'❌ 音频目录不存在: {audio_dir}')
        return

    # 获取所有音频文件（mp3和wav）
    audio_files = []
    for ext in ['*.mp3', '*.wav']:
        audio_files.extend(audio_dir.glob(ext))

    audio_filenames = {f.stem for f in audio_files}
    print(f'音频文件数: {len(audio_filenames)}')
    print()

    # 策略：日文和中文应该是同一批音频的不同语言版本
    # 所以文件名应该相同，只是文本内容不同

    # 方案1: 假设日文和中文的顺序对应
    print('方案1: 按顺序对应（假设日文和中文顺序一致）')
    print('-' * 60)

    matched_count = 0
    output_lines = []

    # 取较小的数量
    min_count = min(len(jp_data), len(zh_data))

    for i in range(min_count):
        jp_text = jp_data[i]['text']
        zh_filename = zh_data[i]['filename']

        # 检查文件是否存在
        if zh_filename in audio_filenames:
            matched_count += 1
            wav_path = f"dataset/44k/unicorn/{zh_filename}.wav"
            lang = detect_language(jp_text)
            output_lines.append(f"{wav_path}|{lang}|{jp_text}\n")

            if i < 5:  # 显示前5个
                print(f'✓ {zh_filename} -> {jp_text[:40]}...')

    print()
    print(f'匹配成功: {matched_count}/{min_count}')

    # 保存新的list文件
    if matched_count > 0:
        output_file = Path('python_scripts/so-vits-svc-4.1-Stable/dataset_raw/unicorn_jp/unicorn_jp_matched.list')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)

        print(f'\n✅ 已保存匹配后的list文件: {output_file}')
        print(f'总计: {len(output_lines)} 条记录')

        # 验证
        print('\n验证前5条:')
        for line in output_lines[:5]:
            parts = line.strip().split('|')
            filename = parts[0].split('/')[-1].replace('.wav', '')
            exists = filename in audio_filenames
            status = '✓' if exists else '✗'
            print(f'{status} {filename}')
    else:
        print('\n❌ 没有匹配的文件')
        print('\n可能的原因:')
        print('1. 日文wiki的语音顺序与中文不同')
        print('2. 日文wiki包含更多语音（如改造、换装等）')
        print('3. 需要手动建立映射关系')

if __name__ == '__main__':
    main()
