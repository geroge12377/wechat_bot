"""
测试独角兽人设集成
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from unicorn_scheduler import UnicornScheduler

# 加载环境变量
load_dotenv()

async def main():
    # 初始化调度器
    scheduler = UnicornScheduler(
        deepseek_api_key=os.getenv("AI_API_KEY"),
        deepseek_base_url=os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    )

    # 初始化静态语料库（首次运行）
    scheduler.rag.init_static_collection("unicorn.list")

    # 测试对话
    test_inputs = [
        "哥哥回来啦",
        "今天天气真好呀",
        "独角兽真可爱"
    ]

    for user_input in test_inputs:
        print(f"\n{'='*50}")
        print(f"用户: {user_input}")
        print(f"{'='*50}")

        try:
            text_response, audio_bytes = await scheduler.run(user_input)

            print(f"独角兽: {text_response}")
            print(f"音频大小: {len(audio_bytes)} bytes")

            # 保存音频文件
            audio_file = Path(f"test_audio_{hash(user_input) % 10000}.wav")
            with open(audio_file, "wb") as f:
                f.write(audio_bytes)
            print(f"音频已保存: {audio_file}")

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
