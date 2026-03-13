# -*- coding: utf-8 -*-
"""
独角兽日文语音解析器 - 本地HTML版本
使用方法：
1. 手动访问 https://azurlane.koumakan.jp/wiki/Unicorn/Quotes
2. 保存完整网页为 unicorn_quotes.html
3. 运行此脚本解析
"""

import sys
import io
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class LocalHTMLParser:
    def __init__(self):
        self.base_dir = Path("./so-vits-svc-4.1-Stable")
        self.dataset_dir = self.base_dir / "dataset_raw" / "unicorn_jp"
        self.voice_data = []

        # 创建目录
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

    def detect_language(self, text):
        """检测文本语言"""
        chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        japanese_count = sum(1 for char in text if
                           ('\u3040' <= char <= '\u309f') or  # 平假名
                           ('\u30a0' <= char <= '\u30ff'))    # 片假名

        if japanese_count > chinese_count:
            return "JA"
        else:
            return "ZH"

    def parse_koumakan_html(self, html_file):
        """解析koumakan wiki的HTML文件"""
        print(f"读取文件: {html_file}")

        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')
        voice_data = []

        print("解析语音表格...")

        # 查找所有表格
        tables = soup.find_all('table', class_='wikitable')
        print(f"找到 {len(tables)} 个表格")

        for table_idx, table in enumerate(tables):
            print(f"\n解析表格 {table_idx + 1}...")
            rows = table.find_all('tr')

            for row_idx, row in enumerate(rows):
                cols = row.find_all(['td', 'th'])

                if len(cols) >= 2:
                    # 提取所有列的文本
                    texts = [col.get_text(strip=True) for col in cols]

                    # 查找音频链接
                    audio_tag = row.find('audio')
                    audio_url = ""
                    if audio_tag:
                        source = audio_tag.find('source')
                        if source and source.get('src'):
                            audio_url = source.get('src')

                    # 尝试识别场景和文本
                    # 通常第一列是场景，后面的列是不同语言的文本
                    if len(texts) >= 2:
                        scene = texts[0]

                        # 遍历所有文本列，找出日文
                        for text in texts[1:]:
                            if text and len(text) > 0:
                                lang = self.detect_language(text)

                                # 只保存日文文本
                                if lang == "JA":
                                    voice_data.append({
                                        'scene': scene,
                                        'text': text,
                                        'url': audio_url,
                                        'row': row_idx
                                    })
                                    print(f"  ✓ [{scene}] {text[:30]}...")

        return voice_data

    def save_voice_data(self, speaker_name="unicorn"):
        """保存语音数据"""
        if not self.voice_data:
            print("❌ 没有数据可保存")
            return 0

        print(f"\n📝 保存 {len(self.voice_data)} 条语音数据...")

        # 保存JSON格式
        json_data = []
        for i, voice in enumerate(self.voice_data):
            filename = f"unicorn_jp_{i+1:03d}"
            lang = self.detect_language(voice['text'])
            json_data.append({
                'filename': filename,
                'text': voice['text'],
                'scene': voice['scene'],
                'url': voice['url'],
                'language': lang
            })

        json_file = self.dataset_dir / "text_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON格式: {json_file}")

        # 保存TXT格式
        txt_file = self.dataset_dir / "text_data.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for item in json_data:
                f.write(f"{item['filename']}|{item['text']}\n")
        print(f"✅ TXT格式: {txt_file}")

        # 保存List格式
        list_file = self.dataset_dir / f"{speaker_name}_jp.list"
        with open(list_file, 'w', encoding='utf-8') as f:
            for item in json_data:
                wav_path = f"dataset/44k/{speaker_name}/{item['filename']}.wav"
                f.write(f"{wav_path}|{item['language']}|{item['text']}\n")
        print(f"✅ List格式: {list_file}")

        # 统计语言
        lang_stats = {}
        for item in json_data:
            lang = item['language']
            lang_stats[lang] = lang_stats.get(lang, 0) + 1

        print(f"\n语言统计:")
        for lang, count in lang_stats.items():
            lang_name = "日文" if lang == "JA" else "中文"
            print(f"  {lang_name}({lang}): {count} 条")

        return len(json_data)

def main():
    print("独角兽日文语音解析器 - 本地HTML版本")
    print("=" * 60)

    parser = LocalHTMLParser()

    # 查找HTML文件
    possible_files = [
        "unicorn_quotes.html",
        "Unicorn_Quotes.html",
        "unicorn.html",
    ]

    html_file = None
    for filename in possible_files:
        if Path(filename).exists():
            html_file = filename
            break

    if not html_file:
        print("\n请提供HTML文件路径:")
        print("1. 访问 https://azurlane.koumakan.jp/wiki/Unicorn/Quotes")
        print("2. 右键 -> 保存为 -> 保存完整网页")
        print("3. 将文件命名为 unicorn_quotes.html 并放在当前目录")
        print("\n或者直接输入HTML文件路径:")

        user_input = input("> ").strip()
        if user_input:
            html_file = user_input
        else:
            print("❌ 未提供文件")
            return

    if not Path(html_file).exists():
        print(f"❌ 文件不存在: {html_file}")
        return

    # 解析HTML
    parser.voice_data = parser.parse_koumakan_html(html_file)

    if parser.voice_data:
        count = parser.save_voice_data()
        print(f"\n✅ 成功保存 {count} 条日文语音数据")
        print(f"📁 输出目录: {parser.dataset_dir}")
    else:
        print("\n❌ 未找到日文语音数据")
        print("提示: 请确保HTML文件包含完整的页面内容")

if __name__ == "__main__":
    main()
