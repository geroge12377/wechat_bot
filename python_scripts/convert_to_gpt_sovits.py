# -*- coding: utf-8 -*-
"""
转换list格式为GPT-SoVITS格式
格式: 音频路径|speaker|语言|文本
"""

import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def convert_to_gpt_sovits_format():
    print('转换为GPT-SoVITS格式')
    print('=' * 60)

    # 读取匹配后的list
    input_file = Path('python_scripts/so-vits-svc-4.1-Stable/dataset_raw/unicorn_jp/unicorn_jp_matched.list')

    if not input_file.exists():
        print(f'❌ 输入文件不存在: {input_file}')
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f'读取文件: {input_file}')
    print(f'原始格式行数: {len(lines)}')
    print()

    # 转换格式
    output_lines = []
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) == 3:
            # 原格式: dataset/44k/unicorn/unicorn_xxx.wav|JA|文本
            old_path = parts[0]
            lang = parts[1]
            text = parts[2]

            # 提取文件名
            filename = old_path.split('/')[-1]  # unicorn_xxx.wav

            # 新格式: D:\GPT_SoVITS\raw\unicorn\unicorn_xxx.wav|unicorn|JA|文本
            new_path = f'D:\\GPT_SoVITS\\raw\\unicorn\\{filename}'
            new_line = f'{new_path}|unicorn|{lang}|{text}\n'
            output_lines.append(new_line)

    print('转换格式示例（前3条）:')
    print('-' * 60)
    for line in output_lines[:3]:
        parts = line.strip().split('|')
        print(f'路径: {parts[0]}')
        print(f'Speaker: {parts[1]}')
        print(f'语言: {parts[2]}')
        print(f'文本: {parts[3][:50]}...')
        print()

    # 保存到本地目录（因为GPT-SoVITS目录可能被保护）
    local_output = Path('python_scripts/unicorn_gpt_sovits.list')
    target_file = Path('D:/GPT_SoVITS/output/asr_opt/unicorn.list')

    # 保存到本地
    with open(local_output, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f'✅ 已保存到本地: {local_output}')
    print(f'总计: {len(output_lines)} 条记录')
    print()

    # 尝试复制到目标位置
    print('尝试复制到GPT-SoVITS目录...')
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # 尝试直接写入
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)

        print(f'✅ 成功覆盖: {target_file}')
    except Exception as e:
        print(f'⚠️ 无法直接写入: {e}')
        print()
        print('请手动操作:')
        print(f'1. 关闭占用 {target_file} 的程序')
        print(f'2. 复制 {local_output.absolute()}')
        print(f'3. 粘贴到 {target_file}')
        print('   (覆盖原文件)')

    print()

    # 验证文件
    print('验证音频文件存在性（前5个）:')
    print('-' * 60)
    for line in output_lines[:5]:
        parts = line.strip().split('|')
        audio_path = Path(parts[0])
        exists = audio_path.exists()
        status = '✓' if exists else '✗'
        print(f'{status} {audio_path.name}')

    print()
    print('🎉 转换完成！')
    print(f'格式: 音频路径|speaker|语言|文本')
    print(f'可用于GPT-SoVITS训练')

if __name__ == '__main__':
    convert_to_gpt_sovits_format()
