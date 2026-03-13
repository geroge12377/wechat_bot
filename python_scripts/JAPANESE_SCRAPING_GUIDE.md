# 爬取日文语音台词 - 使用指南

## 问题说明

由于目标网站有反爬虫保护（Anubis），直接用脚本爬取会被拦截。因此需要手动保存网页后再解析。

## 方法一：手动保存网页（推荐）

### 步骤：

1. **访问网页**
   - 英文Wiki（含日文原文）: https://azurlane.koumakan.jp/wiki/Unicorn/Quotes
   - 日文Wiki: https://azurlane.wikiru.jp/?ユニコーン

2. **保存完整网页**
   - 在浏览器中按 `Ctrl+S` 或右键 -> "另存为"
   - 选择 "网页，完整" 或 "Web Page, Complete"
   - 保存为 `unicorn_quotes.html`
   - 放在 `python_scripts` 目录下

3. **运行解析脚本**
   ```bash
   cd python_scripts
   python parse_local_html.py
   ```

## 方法二：使用浏览器开发者工具

### 步骤：

1. **打开开发者工具**
   - 访问 https://azurlane.koumakan.jp/wiki/Unicorn/Quotes
   - 按 `F12` 打开开发者工具
   - 切换到 "Elements" 或 "元素" 标签

2. **复制HTML**
   - 右键点击 `<html>` 标签
   - 选择 "Copy" -> "Copy outerHTML"
   - 粘贴到文本编辑器
   - 保存为 `unicorn_quotes.html`

3. **运行解析脚本**
   ```bash
   python parse_local_html.py
   ```

## 方法三：使用Selenium（自动化）

如果需要自动化，可以安装Selenium：

```bash
pip install selenium webdriver-manager
```

然后使用带浏览器的爬虫（开发中）。

## 预期输出

解析成功后会生成：

```
so-vits-svc-4.1-Stable/dataset_raw/unicorn_jp/
├── text_data.json          # JSON格式（含完整信息）
├── text_data.txt           # 简化格式
└── unicorn_jp.list         # So-VITS-SVC标准格式
```

### unicorn_jp.list 格式示例：
```
dataset/44k/unicorn/unicorn_jp_001.wav|JA|お兄ちゃん、ユニコーンです
dataset/44k/unicorn/unicorn_jp_002.wav|JA|ユニコーンと優ちゃん、頑張ります
```

## 网站推荐

### 1. Azur Lane English Wiki (推荐)
- URL: https://azurlane.koumakan.jp/wiki/Unicorn/Quotes
- 优点：包含日文原文、中文翻译、英文翻译
- 格式：表格清晰，易于解析
- 音频：有音频文件链接

### 2. Azur Lane Japanese Wiki
- URL: https://azurlane.wikiru.jp/?ユニコーン
- 优点：纯日文，数据最全
- 缺点：格式可能不统一

## 故障排除

### 问题1：未找到日文数据
- 确保保存的是完整网页（不是单个HTML文件）
- 检查HTML文件是否包含表格内容
- 尝试在浏览器中完全加载页面后再保存

### 问题2：语言检测错误
- 脚本会自动检测日文（平假名、片假名）
- 如果检测为ZH但实际是日文，可能是汉字过多
- 可以手动修改生成的list文件中的语言代码

### 问题3：编码问题
- 确保HTML文件保存为UTF-8编码
- Windows用户可能需要在记事本中"另存为"并选择UTF-8编码

## 快速测试

如果你已经有HTML文件，可以快速测试：

```bash
# 直接指定文件路径
python parse_local_html.py
# 然后输入文件路径，例如：
# > C:\Users\HP\Downloads\unicorn_quotes.html
```

## 下一步

解析完成后：
1. 检查生成的 `unicorn_jp.list` 文件
2. 确认语言代码是否正确（应该是JA）
3. 下载对应的日文语音文件
4. 用于So-VITS-SVC训练
