# 独角兽语音爬虫 - 使用说明

## 功能特性

✅ 自动爬取独角兽语音文本数据
✅ 自动检测语言（中文ZH/日文JA）
✅ 生成So-VITS-SVC标准list文件格式
✅ 支持多种输出格式（TXT/JSON/CSV/LIST）

## 生成的文件

### 1. text_data.txt
简化格式，每行一条：
```
unicorn_anniversary_01|碧蓝航线五周年快乐
```

### 2. text_data.json
JSON格式，包含完整信息：
```json
{
  "filename": "unicorn_anniversary_01",
  "text": "碧蓝航线五周年快乐",
  "scene": "五周年登录",
  "skin": "基础",
  "type": "anniversary",
  "language": "ZH"
}
```

### 3. text_data.csv
CSV表格格式，可用Excel打开：
```
文件名,文本内容,场景,皮肤,类型,语言
"unicorn_anniversary_01","碧蓝航线五周年快乐","五周年登录","基础","anniversary","ZH"
```

### 4. unicorn.list ⭐
**So-VITS-SVC标准格式，可直接使用：**
```
dataset/44k/unicorn/unicorn_anniversary_01.wav|ZH|碧蓝航线五周年快乐
```

格式说明：
- `dataset/44k/unicorn/` - 数据集路径（对应实际文件位置）
- `unicorn_anniversary_01.wav` - 音频文件名
- `ZH` - 语言代码（自动检测：ZH=中文，JA=日文）
- `碧蓝航线五周年快乐` - 文本内容

## 使用方法

### 仅生成文字数据和list文件
```bash
python python_scripts/unicorn_scraper_cli.py --text-only
```

### 下载音频文件
```bash
python python_scripts/unicorn_scraper_cli.py --download
```

### 转换音频为WAV格式
```bash
python python_scripts/unicorn_scraper_cli.py --convert
```

### 执行所有操作
```bash
python python_scripts/unicorn_scraper_cli.py --all
```

## 语言检测规则

爬虫会自动检测每条文本的语言：
- 统计中文字符数量（Unicode范围：\u4e00-\u9fff）
- 统计日文平假名和片假名数量（\u3040-\u309f, \u30a0-\u30ff）
- 如果日文字符更多，标记为JA
- 否则标记为ZH

## 数据统计

当前爬取结果：
- 总计：63 条语音文本
- 中文(ZH)：63 条
- 日文(JA)：0 条

包含皮肤：
- 基础形态
- 小小的星之歌姬
- 春之礼
- 憧憬的约会日
- 梦想的纯白誓约
- 天使的My Night
- 清凉阅读时光
- 天使的护理时间
- Champion of Unicorn

## 文件位置

```
python_scripts/
├── unicorn_scraper.py          # 核心爬虫类
├── unicorn_scraper_cli.py      # CLI命令行工具
└── so-vits-svc-4.1-Stable/
    └── dataset_raw/
        └── unicorn/
            ├── text_data.txt       # 简化格式
            ├── text_data.json      # JSON格式
            ├── text_data.csv       # CSV格式
            ├── unicorn.list        # ⭐ So-VITS-SVC标准格式
            └── README.md           # 数据集说明
```

## 注意事项

1. **路径对应**：list文件中的路径 `dataset/44k/unicorn/` 对应实际的音频文件位置
2. **语言代码**：自动检测，中文为ZH，日文为JA
3. **Speaker名称**：默认为 `unicorn`，可在代码中修改
4. **文件格式**：生成的list文件可直接用于So-VITS-SVC训练

## 下一步

1. 下载对应的音频文件（使用 `--download` 参数）
2. 转换音频为WAV格式（使用 `--convert` 参数）
3. 将生成的 `unicorn.list` 文件用于So-VITS-SVC训练
