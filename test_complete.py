"""
完整测试：LLM + TTS
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from unicorn_scheduler import UnicornScheduler

load_dotenv()

async def main():
    print("="*60)
    print("开始完整测试：LLM + TTS")
    print("="*60)

    # 初始化调度器
    scheduler = UnicornScheduler(
        deepseek_api_key=os.getenv("AI_API_KEY"),
        deepseek_base_url=os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    )

    # 初始化静态语料库
    scheduler.rag.init_static_collection("unicorn.list")

    # 测试用例
    test_input = "哥哥回来啦"

    print(f"\n用户输入: {test_input}")
    print("-"*60)

    try:
        # 运行完整流程
        text_response, audio_bytes = await scheduler.run(test_input)

        print(f"\n【成功】")
        print(f"回复文本: {text_response}")
        print(f"音频大小: {len(audio_bytes)} bytes")

        # 保存音频
        audio_file = Path("test_complete_output.wav")
        with open(audio_file, "wb") as f:
            f.write(audio_bytes)

        print(f"音频已保存: {audio_file.absolute()}")
        print("\n✓ 测试通过！")

    except Exception as e:
        print(f"\n【失败】")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
