# -*- coding: utf-8 -*-
"""
独角兽语音数据爬取器 - CLI版本
支持命令行参数，无需交互式输入
"""

import sys
import io
import argparse
from unicorn_scraper import UnicornVoiceScraper

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='独角兽语音数据爬取器')
    parser.add_argument('--download', action='store_true', help='下载语音文件')
    parser.add_argument('--convert', action='store_true', help='转换为WAV格式')
    parser.add_argument('--text-only', action='store_true', help='仅保存文字数据')
    parser.add_argument('--all', action='store_true', help='执行所有操作')

    args = parser.parse_args()

    print("独角兽语音数据爬取器 - CLI版本")
    print("=" * 60)

    scraper = UnicornVoiceScraper()
    scraper.extract_voice_data_from_html("")

    print(f"准备目录: {scraper.dataset_dir}")

    # 仅保存文字数据
    if args.text_only:
        print("\n仅保存文字数据模式...")
        text_count = scraper.save_text_data()
        print(f"✅ 已保存 {text_count} 条文字数据")
        scraper.create_dataset_info()
        return

    # 下载语音文件
    if args.download or args.all:
        print("\n开始下载语音文件...")
        success_count = scraper.download_voice_files()

        if success_count > 0:
            print(f"\n🎉 成功下载 {success_count} 个语音文件!")

            # 保存文字数据
            text_count = scraper.save_text_data()
            print(f"✅ 已保存 {text_count} 条文字数据")

            # 创建数据集信息
            scraper.create_dataset_info()

    # 转换格式
    if args.convert or args.all:
        print("\n开始转换音频格式...")
        scraper.convert_to_wav()
        scraper.prepare_for_training()

    print("\n" + "=" * 60)
    print("操作完成!")
    print("\n使用说明:")
    print("  --text-only  : 仅保存文字数据")
    print("  --download   : 下载语音文件")
    print("  --convert    : 转换为WAV格式")
    print("  --all        : 执行所有操作")

if __name__ == "__main__":
    main()
