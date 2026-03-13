# -*- coding: utf-8 -*-
"""
将爬取的文字数据转换为So-VITS-SVC的list文件格式
"""

import sys
import io
from pathlib import Path

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def convert_to_list(input_file, output_file, dataset_path="dataset/44k/unicorn", language="ZH"):
    """
    转换文本数据为list格式

    Args:
        input_file: 输入的text_data.txt文件路径
        output_file: 输出的list文件路径
        dataset_path: 数据集路径前缀
        language: 语言代码（ZH=中文）
    """
    print(f"转换文本数据为list格式...")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    converted_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 解析格式：filename|text
        parts = line.split('|', 1)
        if len(parts) != 2:
            print(f"⚠️ 跳过格式错误的行: {line}")
            continue

        filename, text = parts

        # 生成list格式：path/filename.wav|LANG|text
        list_line = f"{dataset_path}/{filename}.wav|{language}|{text}\n"
        converted_lines.append(list_line)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(converted_lines)

    print(f"✅ 转换完成！共 {len(converted_lines)} 条记录")
    return len(converted_lines)

def main():
    # 默认路径
    base_dir = Path("./so-vits-svc-4.1-Stable")
    input_file = base_dir / "dataset_raw/unicorn/text_data.txt"
    output_file = base_dir / "filelists/unicorn_new.list"

    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        print(f"❌ 输入文件不存在: {input_file}")
        return

    # 转换
    count = convert_to_list(input_file, output_file)

    print(f"\n生成的list文件: {output_file}")
    print(f"总共 {count} 条语音记录")

    # 显示前5行示例
    print("\n前5行示例:")
    print("=" * 80)
    with open(output_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            print(line.rstrip())
    print("=" * 80)

if __name__ == "__main__":
    main()
