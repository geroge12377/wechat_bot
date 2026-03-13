# -*- coding: utf-8 -*-
"""
独角兽日文语音爬虫
支持从多个wiki源爬取日文台词
"""

import sys
import io
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import time

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class JapaneseVoiceScraper:
    def __init__(self):
        self.base_dir = Path("./so-vits-svc-4.1-Stable")
        self.dataset_dir = self.base_dir / "dataset_raw" / "unicorn_jp"
        self.voice_data = []

        # 创建目录
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        }

    def fetch_page(self, url):
        """获取页面内容"""
        try:
            print(f"正在获取页面: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"❌ 获取页面失败: {e}")
            return None

    def parse_koumakan_quotes(self, html):
        """解析 azurlane.koumakan.jp 的语音页面"""
        soup = BeautifulSoup(html, 'html.parser')
        voice_data = []

        print("解析 Koumakan Wiki 格式...")

        # 查找语音表格
        tables = soup.find_all('table', class_='wikitable')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows[1:]:  # 跳过表头
                cols = row.find_all('td')

                if len(cols) >= 3:
                    # 通常格式: 场景 | 日文 | 中文/英文
                    scene = cols[0].get_text(strip=True)
                    japanese_text = cols[1].get_text(strip=True)

                    # 查找音频链接
                    audio_tag = cols[1].find('audio') or cols[0].find('audio')
                    audio_url = ""
                    if audio_tag:
                        source = audio_tag.find('source')
                        if source and source.get('src'):
                            audio_url = source.get('src')

                    if japanese_text and japanese_text not in ['', '-', '—']:
                        voice_data.append({
                            'scene': scene,
                            'text': japanese_text,
                            'url': audio_url,
                            'source': 'koumakan'
                        })

        return voice_data

    def parse_wikiru_page(self, html):
        """解析 azurlane.wikiru.jp 的页面"""
        soup = BeautifulSoup(html, 'html.parser')
        voice_data = []

        print("解析 Wikiru 格式...")

        # 查找包含语音的区域
        # wikiru通常使用特定的div或table结构
        voice_sections = soup.find_all(['table', 'div'], class_=lambda x: x and ('voice' in str(x).lower() or 'quote' in str(x).lower()))

        for section in voice_sections:
            rows = section.find_all('tr')

            for row in rows:
                cols = row.find_all(['td', 'th'])

                if len(cols) >= 2:
                    scene = cols[0].get_text(strip=True)
                    text = cols[1].get_text(strip=True)

                    # 查找音频
                    audio_tag = row.find('audio')
                    audio_url = ""
                    if audio_tag:
                        source = audio_tag.find('source')
                        if source and source.get('src'):
                            audio_url = source.get('src')

                    if text and len(text) > 0:
                        voice_data.append({
                            'scene': scene,
                            'text': text,
                            'url': audio_url,
                            'source': 'wikiru'
                        })

        return voice_data

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
                'source': voice['source'],
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

    def scrape_from_url(self, url):
        """从指定URL爬取"""
        html = self.fetch_page(url)
        if not html:
            return False

        # 根据URL判断使用哪个解析器
        if 'koumakan.jp' in url:
            self.voice_data = self.parse_koumakan_quotes(html)
        elif 'wikiru.jp' in url:
            self.voice_data = self.parse_wikiru_page(html)
        else:
            print("⚠️ 未知的wiki格式，尝试通用解析...")
            # 尝试两种解析方式
            data1 = self.parse_koumakan_quotes(html)
            data2 = self.parse_wikiru_page(html)
            self.voice_data = data1 if len(data1) > len(data2) else data2

        print(f"✅ 找到 {len(self.voice_data)} 条语音数据")

        # 如果没找到数据，保存HTML用于调试
        if not self.voice_data:
            debug_file = self.dataset_dir / "debug_page.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"⚠️ 未找到语音数据，已保存页面到 {debug_file} 用于调试")
            return False

        return True

def main():
    print("独角兽日文语音爬虫")
    print("=" * 60)

    scraper = JapaneseVoiceScraper()

    # 可选的URL列表
    urls = [
        "https://azurlane.koumakan.jp/wiki/Unicorn/Quotes",
        "https://azurlane.wikiru.jp/?ユニコーン",
    ]

    print("\n可用的数据源:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")

    print("\n请选择数据源 (1-2)，或输入自定义URL:")
    choice = input("> ").strip()

    if choice.startswith('http'):
        target_url = choice
    elif choice.isdigit() and 1 <= int(choice) <= len(urls):
        target_url = urls[int(choice) - 1]
    else:
        print("❌ 无效的选择")
        return

    print(f"\n开始爬取: {target_url}")

    if scraper.scrape_from_url(target_url):
        count = scraper.save_voice_data()
        print(f"\n✅ 成功保存 {count} 条日文语音数据")
        print(f"📁 输出目录: {scraper.dataset_dir}")
    else:
        print("\n❌ 爬取失败")

if __name__ == "__main__":
    main()
