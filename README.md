# Unicorn Scheduler - 情感化 TTS 调度系统

基于 ChromaDB RAG + DeepSeek + GPT-SoVITS 的智能语音合成调度器，支持情感标签路由和长时记忆。

## 架构特点

### 1. ChromaDB RAG 引擎
- **静态 collection**：索引 `unicorn.list` 的 126 条语料（格式：`path|speaker|lang|text`）
- **动态 collection**：长时记忆，语义脱水后存储
- **检索策略**：返回最相关 3 条历史记忆 + 对应 ref audio 路径

### 2. 情感标签路由
支持的情感标签及对应 TTS 参数：

| 标签 | Temperature | Top_P | 检索关键词 |
|------|-------------|-------|-----------|
| `[撒娇]` | 0.95 | 0.95 | 撒娇 依赖 |
| `[温柔]` | 0.85 | 0.80 | 温柔 治愈 |
| `[害羞]` | 0.75 | 0.85 | 害羞 怯生生 |
| `[开心]` | 0.92 | 0.90 | 开心 欢快 |
| `[担心]` | 0.80 | 0.85 | 担心 焦虑 |
| 默认 | 0.90 | 0.90 | 平常 |

### 3. TTS 固定参数（不可修改）
```python
speed = 1.0
repeat_penalty = 1.35
sample_steps = 128
```

### 4. 异步调度流程
```
用户输入 → RAG 检索（并发）→ DeepSeek 生成 → 标签解析 → 情感匹配 ref audio → SoVITS 推理 → 返回音频
```

## 环境要求

- Python 3.8+
- 4GB+ 内存（腾讯云轻量服务器可用）
- SoVITS 服务运行在 `http://localhost:9872`

## 安装依赖

```bash
pip install chromadb httpx
```

## 使用方法

### 1. 准备语料文件

创建 `unicorn.list` 文件，格式：
```
audio/ref1.wav|speaker1|zh|你好呀，今天天气真好
audio/ref2.wav|speaker1|zh|我有点害羞呢
audio/ref3.wav|speaker1|zh|好开心啊
...
```

### 2. 初始化并运行

```python
import asyncio
from unicorn_scheduler import UnicornScheduler

async def main():
    # 初始化调度器
    scheduler = UnicornScheduler(
        deepseek_api_key="sk-your-deepseek-api-key"
    )

    # 首次运行：初始化静态语料库
    scheduler.rag.init_static_collection("unicorn.list")

    # 运行对话
    user_input = "今天天气真好呀[开心]"
    text_response, audio_bytes = await scheduler.run(user_input)

    print(f"回复: {text_response}")

    # 保存音频
    with open("output.wav", "wb") as f:
        f.write(audio_bytes)

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. 测试

```bash
python test_scheduler.py
```

## API 接口说明

### UnicornScheduler.run(user_input: str)

**参数：**
- `user_input`: 用户输入文本，可包含情感标签（如 `"你好呀[撒娇]"`）

**返回：**
- `text_response`: 清理后的回复文本（去除标签）
- `audio_bytes`: 合成的音频字节流（WAV 格式）

**流程：**
1. 并发执行 RAG 检索（历史记忆 + 默认参考音频）
2. 调用 DeepSeek API 生成回复
3. 解析情感标签 → 映射 TTS 参数
4. 根据情感关键词检索匹配的 ref audio
5. 调用 SoVITS HTTP 推理
6. 保存对话到长时记忆

## SoVITS API 格式

本项目使用 Gradio API 格式调用 SoVITS：

```python
POST http://localhost:9872/api/inference
Content-Type: application/json

{
  "data": [
    "待合成文本",
    "中文",                          # text_lang
    {"path": "ref_audio.wav"},      # ref_audio_path
    [],                             # aux_ref_audio_paths
    "",                             # prompt_text
    "中文",                         # prompt_lang
    5,                              # top_k
    0.95,                           # top_p
    0.95,                           # temperature
    "不切",                         # text_split_method
    20,                             # batch_size
    1.0,                            # speed_factor
    false,                          # ref_text_free
    true,                           # split_bucket
    0.3,                            # fragment_interval
    -1,                             # seed
    true,                           # keep_random
    true,                           # parallel_infer
    1.35,                           # repetition_penalty
    "128",                          # sample_steps
    false                           # super_sampling
  ]
}
```

## 内存优化

- 使用 `chromadb.PersistentClient` 而非独立进程
- 异步非阻塞 HTTP 调用（httpx）
- 不加载 WebUI，仅调用 HTTP 接口
- 适合 4GB 内存的腾讯云轻量服务器

## 文件结构

```
.
├── unicorn_rag.py          # RAG 引擎（ChromaDB）
├── unicorn_scheduler.py    # 主调度器
├── test_scheduler.py       # 测试脚本
├── unicorn.list            # 静态语料库（126条）
├── unicorn_memory/         # ChromaDB 持久化目录
└── README.md               # 本文档
```

## 注意事项

1. **DeepSeek API Key**：需要在初始化时提供有效的 API Key
2. **SoVITS 服务**：确保 SoVITS 服务运行在 `localhost:9872`
3. **语料路径**：`unicorn.list` 中的音频路径需要是 SoVITS 可访问的绝对路径或相对路径
4. **首次运行**：首次运行会初始化 ChromaDB，需要一定时间

## 故障排查

### 1. SoVITS 连接失败
```bash
# 检查 SoVITS 服务是否运行
curl http://localhost:9872/info
```

### 2. ChromaDB 初始化失败
```bash
# 删除旧的数据库重新初始化
rm -rf unicorn_memory/
```

### 3. DeepSeek API 调用失败
- 检查 API Key 是否有效
- 检查网络连接
- 查看 API 配额是否用尽

## License

MIT
