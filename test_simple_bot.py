"""
WeChat Bot 测试版（不依赖 SoVITS）
仅测试 RAG + LLM 功能
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from unicorn_rag import UnicornRAG
import httpx

# 加载环境变量
load_dotenv()

# 配置
DEEPSEEK_API_KEY = os.getenv("AI_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("AI_BASE_URL")

# 情感标签映射
EMOTION_MAP = {
    "[撒娇]": {"temp": 0.95, "top_p": 0.95},
    "[温柔]": {"temp": 0.85, "top_p": 0.80},
    "[害羞]": {"temp": 0.75, "top_p": 0.85},
    "[开心]": {"temp": 0.92, "top_p": 0.90},
    "[担心]": {"temp": 0.80, "top_p": 0.85},
    "default": {"temp": 0.90, "top_p": 0.90},
}


class SimpleChatBot:
    """简化版聊天机器人（不含 TTS）"""

    def __init__(self):
        self.rag = UnicornRAG()
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL

    def initialize(self):
        """初始化语料库"""
        try:
            self.rag.init_static_collection("unicorn.list")
            print("[INFO] 语料库初始化完成")
        except Exception as e:
            print(f"[WARNING] 语料库初始化失败: {e}")

    def parse_emotion(self, text: str):
        """解析情感标签"""
        for tag, params in EMOTION_MAP.items():
            if tag in text:
                clean_text = text.replace(tag, "").strip()
                return clean_text, tag.strip("[]"), params
        return text, "default", EMOTION_MAP["default"]

    async def chat(self, user_input: str) -> dict:
        """处理聊天消息"""
        try:
            # 1. 解析情感
            clean_input, emotion, emotion_params = self.parse_emotion(user_input)

            # 2. RAG 检索
            history, ref_audio = await self.rag.query_memory(clean_input)

            # 3. 调用 LLM
            api_url = self.base_url
            if api_url.endswith('/v1'):
                api_url = f"{api_url}/chat/completions"
            else:
                api_url = f"{api_url}/v1/chat/completions"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gemini-3.1-flash-lite-preview",
                        "messages": [
                            {"role": "system", "content": f"你是独角兽AI助手，性格可爱活泼。历史记忆：{history}"},
                            {"role": "user", "content": clean_input}
                        ],
                        "temperature": emotion_params["temp"]
                    }
                )
                response.raise_for_status()
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]

            # 4. 保存记忆
            self.rag.save_long_term_memory(f"用户：{clean_input} | 回复：{llm_response}")

            return {
                "success": True,
                "text": llm_response,
                "emotion": emotion,
                "temperature": emotion_params["temp"],
                "top_p": emotion_params["top_p"],
                "ref_audio": ref_audio
            }

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """测试"""
    print("=== 简化版聊天机器人测试 ===\n")

    bot = SimpleChatBot()
    bot.initialize()

    test_messages = [
        "你好呀[撒娇]",
        "今天天气真好[开心]",
        "我有点担心明天的考试[担心]",
        "你叫什么名字？"
    ]

    for msg in test_messages:
        print(f"\n{'='*50}")
        print(f"用户: {msg}")

        result = await bot.chat(msg)

        if result["success"]:
            # 移除 emoji 等特殊字符
            import re
            clean_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？、：；""''（）【】《》\.,!?\-]', '', result['text'])
            print(f"回复: {clean_text}")
            print(f"情感: {result['emotion']}")
            print(f"参数: temp={result['temperature']}, top_p={result['top_p']}")
            print(f"参考音频: {result['ref_audio']}")
        else:
            print(f"错误: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
