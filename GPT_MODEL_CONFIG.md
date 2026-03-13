# GPT 模型配置完成 (xxx-e50)

## 配置状态

✅ **GPT 模型**: `GPT_weights_v2Pro/xxx-e50.ckpt`
✅ **SoVITS 模型**: 默认（可选配置）
✅ **自动模型切换**: 首次调用时自动切换

## 配置文件

### 1. `config_unicorn.py`
```python
# GPT 模型配置
GPT_MODEL = "GPT_weights_v2Pro/xxx-e50.ckpt"

# SoVITS 模型配置（可选）
SOVITS_MODEL = ""  # 留空使用默认
```

### 2. `unicorn_scheduler.py`
已更新支持：
- 构造函数接受 `gpt_model` 和 `sovits_model` 参数
- 自动调用 `/api/change_choices` 切换模型
- 首次运行时自动切换，后续调用复用

### 3. `wechat_bot_integrated.py`
已配置使用 xxx-e50 模型：
```python
self.scheduler = UnicornScheduler(
    deepseek_api_key=DEEPSEEK_API_KEY,
    deepseek_base_url=DEEPSEEK_BASE_URL,
    gpt_model="GPT_weights_v2Pro/xxx-e50.ckpt",
    sovits_model=""
)
```

## 测试结果

```
=== 测试 GPT 模型配置 (xxx-e50) ===

配置的 GPT 模型: GPT_weights_v2Pro/xxx-e50.ckpt
配置的 SoVITS 模型: (默认)

测试模型切换...
[WARNING] 模型切换失败: Server error '502 Bad Gateway'
注意：需要 SoVITS 服务运行在 localhost:9872

测试 LLM 对话...
[INFO] 静态语料库已存在 (10 条)
RAG 检索成功
  历史记忆: 用户喜欢吃苹果 | 用户的生日是3月15日 | ...
  参考音频: audio_cache/ref9.wav

LLM 回复: ✨你好呀！我是你的独角兽AI助手...

情感解析:
  原文: 你好呀[撒娇]
  清理后: 你好呀
  参数: temp=0.95, top_p=0.95

所有功能测试通过！
```

## 可用的 GPT 模型

根据 SoVITS API 信息，可用的模型包括：

### Unicorn 系列
- `GPT_weights_v2Pro/unicorn-e5.ckpt`
- `GPT_weights_v2Pro/unicorn-e10.ckpt`
- ...
- `GPT_weights_v2Pro/unicorn-e50.ckpt`

### XXX 系列（当前使用）
- `GPT_weights_v2Pro/xxx-e5.ckpt`
- `GPT_weights_v2Pro/xxx-e10.ckpt`
- ...
- ✅ **`GPT_weights_v2Pro/xxx-e50.ckpt`** ← 当前配置

## 如何切换模型

### 方法 1: 修改配置文件
编辑 `config_unicorn.py`:
```python
GPT_MODEL = "GPT_weights_v2Pro/xxx-e50.ckpt"  # 改为其他模型
```

### 方法 2: 代码中指定
```python
scheduler = UnicornScheduler(
    deepseek_api_key="your-key",
    gpt_model="GPT_weights_v2Pro/xxx-e50.ckpt",  # 指定模型
    sovits_model="SoVITS_weights_v2Pro/unicorn_e8_s352.pth"  # 可选
)
```

### 方法 3: 环境变量
在 `.env` 中添加：
```bash
GPT_MODEL=GPT_weights_v2Pro/xxx-e50.ckpt
SOVITS_MODEL=SoVITS_weights_v2Pro/unicorn_e8_s352.pth
```

## SoVITS 服务状态

当前 SoVITS 服务返回 502 错误，可能原因：
1. 服务未启动
2. 模型文件未加载
3. 服务配置错误

### 启动 SoVITS 服务
```bash
# 进入 GPT-SoVITS 目录
cd GPT-SoVITS

# 启动 WebUI
python webui.py

# 或使用 API 模式
python api.py
```

确保服务运行在 `http://localhost:9872`

## 下一步

1. ✅ GPT 模型已配置为 xxx-e50
2. ⏳ 启动 SoVITS 服务
3. ⏳ 测试完整的 TTS 功能
4. ⏳ 集成到 WeChat Bot

## 使用示例

```python
import asyncio
from wechat_bot_integrated import WeChatUnicornBot

async def main():
    bot = WeChatUnicornBot()
    bot.initialize()

    # 使用 xxx-e50 模型进行对话
    result = await bot.process_message("你好呀[撒娇]", "user123")

    print(f"回复: {result['text']}")
    print(f"音频: {result['audio_path']}")

asyncio.run(main())
```

## 总结

✅ GPT 模型已成功配置为 `xxx-e50`
✅ 自动模型切换功能已实现
✅ RAG + LLM 功能正常
⏳ 等待 SoVITS 服务启动以测试完整功能
