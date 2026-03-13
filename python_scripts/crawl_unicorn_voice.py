#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独角兽语音爬虫
从萌娘百科爬取独角兽的语音文件
"""

import requests
from bs4 import BeautifulSoup
import os
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

# 配置
MOEGIRL_URL = "https://zh.moegirl.org.cn/碧蓝航线:独角兽"
OUTPUT_DIR = Path(__file__).parent.parent / "so-vits-svc-4.1-Stable" / "dataset_raw" / "unicorn_new"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_page(url):
    """获取页面内容"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"获取页面失败: {e}")
        return None

def parse_voice_data(html):
    """解析语音数据"""
    soup = BeautifulSoup(html, 'html.parser')
    voice_data = []

    # 查找所有语音相关的表格或区块
    # 萌娘百科通常使用特定的class或id来标记语音区域
    voice_sections = soup.find_all(['table', 'div'], class_=lambda x: x and ('voice' in x.lower() or 'audio' in x.lower()))

    for section in voice_sections:
        # 查找音频标签
        audio_tags = section.find_all('audio')
        for audio in audio_tags:
            source = audio.find('source')
            if source and source.get('src'):
                audio_url = source.get('src')

                # 获取对应的文本（通常在附近的td或span中）
                parent = audio.find_parent(['td', 'div', 'span'])
                text = ""
                category = ""

                if parent:
                    # 尝试获取台词文本
                    text_elem = parent.find_next_sibling(['td', 'div'])
                    if text_elem:
                        text = text_elem.get_text(strip=True)

                    # 尝试获取分类（通常在前面的th或标题中）
                    category_elem = parent.find_previous(['th', 'h3', 'h4'])
                    if category_elem:
                        category = category_elem.get_text(strip=True)

                voice_data.append({
                    'url': audio_url,
                    'text': text,
                    'category': category
                })

    return voice_data

def download_audio(url, output_path):
    """下载音频文件"""
    try:
        # 处理相对URL
        if not url.startswith('http'):
            url = urljoin(MOEGIRL_URL, url)

        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True
    except Exception as e:
        print(f"下载失败 {url}: {e}")
        return False

def main():
    """主函数"""
    print("开始爬取独角兽语音数据...")
    print(f"目标URL: {MOEGIRL_URL}")

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 获取页面
    print("\n1. 获取页面内容...")
    html = fetch_page(MOEGIRL_URL)
    if not html:
        print("✗ 获取页面失败")
        return

    print("✓ 页面获取成功")

    # 解析语音数据
    print("\n2. 解析语音数据...")
    voice_data = parse_voice_data(html)
    print(f"✓ 找到 {len(voice_data)} 条语音")

    if not voice_data:
        print("⚠ 未找到语音数据，可能需要调整解析逻辑")
        # 保存HTML用于调试
        debug_path = OUTPUT_DIR / "debug_page.html"
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"已保存页面到 {debug_path} 用于调试")
        return

    # 下载语音文件
    print("\n3. 下载语音文件...")
    metadata = []

    for i, item in enumerate(voice_data, 1):
        print(f"\n[{i}/{len(voice_data)}] {item['category']}")
        print(f"  文本: {item['text'][:50]}...")

        # 生成文件名
        filename = f"unicorn_{i:03d}.mp3"
        output_path = OUTPUT_DIR / filename

        # 下载
        if download_audio(item['url'], output_path):
            print(f"  ✓ 下载成功: {filename}")
            metadata.append({
                'filename': filename,
                'url': item['url'],
                'text': item['text'],
                'category': item['category']
            })
        else:
            print(f"  ✗ 下载失败")

        # 延迟，避免请求过快
        time.sleep(1)

    # 保存元数据
    print("\n4. 保存元数据...")
    metadata_path = OUTPUT_DIR / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✓ 元数据已保存到 {metadata_path}")

    # 保存文字数据
    print("\n5. 保存文字数据...")

    # 保存为纯文本格式
    text_file = OUTPUT_DIR / "text_data.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        for item in metadata:
            f.write(f"{item['filename']}|{item['text']}\n")
    print(f"✓ 文本格式已保存到 {text_file}")

    # 保存为CSV格式
    csv_file = OUTPUT_DIR / "text_data.csv"
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write("文件名,文本内容,分类\n")
        for item in metadata:
            text = item['text'].replace('"', '""')
            category = item['category'].replace('"', '""')
            f.write(f'"{item["filename"]}","{text}","{category}"\n')
    print(f"✓ CSV格式已保存到 {csv_file}")

    # 生成统计报告
    print("\n" + "="*50)
    print("爬取完成！")
    print(f"成功下载: {len(metadata)} 条语音")
    print(f"文字数据: {len(metadata)} 条")
    print(f"输出目录: {OUTPUT_DIR}")
    print("="*50)

    # 按分类统计
    categories = {}
    for item in metadata:
        cat = item['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\n分类统计:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} 条")

if __name__ == "__main__":
    main()
