# Unicorn Scheduler 配置文件

# SoVITS 服务地址
SOVITS_URL = "http://localhost:9872"

# GPT 模型配置
GPT_MODEL = "GPT_weights_v2Pro/xxx-e50.ckpt"

# SoVITS 模型配置（可选，留空使用默认）
SOVITS_MODEL = ""  # 例如: "SoVITS_weights_v2Pro/unicorn_e8_s352.pth"

# TTS 固定参数（不可修改）
TTS_FIXED_PARAMS = {
    "speed": 1.0,              # speed_factor
    "repeat_penalty": 1.35,    # repetition_penalty
    "sample_steps": 128        # sample_steps
}

# 情感标签映射
EMOTION_MAP = {
    "[撒娇]": {"temp": 0.95, "top_p": 0.95, "search_kw": "撒娇 依赖"},
    "[温柔]": {"temp": 0.85, "top_p": 0.80, "search_kw": "温柔 治愈"},
    "[害羞]": {"temp": 0.75, "top_p": 0.85, "search_kw": "害羞 怯生生"},
    "[开心]": {"temp": 0.92, "top_p": 0.90, "search_kw": "开心 欢快"},
    "[担心]": {"temp": 0.80, "top_p": 0.85, "search_kw": "担心 焦虑"},
    "default": {"temp": 0.90, "top_p": 0.90, "search_kw": "平常"},
}

# DeepSeek API 配置（从 .env 读取，这里是备用）
DEEPSEEK_API_KEY = ""
DEEPSEEK_BASE_URL = "https://api.vectorengine.ai/v1"
