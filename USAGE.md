# UnicornScheduler 使用说明

## 问题解决

成功解决了 SoVITS TTS 参考音频的问题！

### 问题原因

SoVITS 的 Gradio 服务器有两个限制：
1. 不兼容 `httpx` 库（只能使用 `requests`）
2. 不允许直接访问本地文件系统，必须先上传文件

### 解决方案

创建了 `SimpleGradioClient`，它：
- 使用 `requests` 而不是 `httpx`
- 自动上传本地音频文件到 Gradio 临时目录
- 缓存已上传的文件，避免重复上传

## 使用方法

### 1. 初始化

```python
from unicorn_scheduler import UnicornScheduler

scheduler = UnicornScheduler(
    deepseek_api_key="your-api-key",
    gpt_model="GPT_weights_v2Pro/xxx-e50.ckpt"
)

# 初始化静态语料库
scheduler.rag.init_static_collection("unicorn.list")
```

### 2. 运行对话

```python
import asyncio

async def main():
    user_input = "今天天气真好呀"
    text_response, audio_bytes = await scheduler.run(user_input)
    
    print(f"回复: {text_response}")
    
    # 保存音频
    with open("output.wav", "wb") as f:
        f.write(audio_bytes)

asyncio.run(main())
```

### 3. 测试

```bash
# 测试 TTS 功能
python test_scheduler.py

# 测试完整流程（需要 DeepSeek API key）
python wechat_bot_integrated.py
```

## 文件说明

- `unicorn_scheduler.py` - 主调度器
- `simple_gradio_client.py` - 自定义 Gradio 客户端
- `unicorn_rag.py` - RAG 引擎
- `unicorn.list` - 静态语料库（8个音频文件）

## 注意事项

1. 确保 SoVITS 服务运行在 `http://localhost:9872`
2. 音频文件路径使用正斜杠：`D:/GPT_SoVITS/raw/unicorn/xxx.wav`
3. 首次使用会自动上传参考音频，后续调用会使用缓存
4. 情感标签：[撒娇][温柔][害羞][开心][担心]

## 性能优化

- `SimpleGradioClient` 在 `__init__` 中初始化，复用连接
- 已上传的文件会被缓存，避免重复上传
- 使用 `requests` 而不是 `httpx`，兼容性更好
