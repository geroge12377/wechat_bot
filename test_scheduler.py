"""
测试完整的 UnicornScheduler 流程
"""

import asyncio
from unicorn_scheduler import UnicornScheduler

async def test_scheduler():
    print("初始化 UnicornScheduler...")

    # 使用测试 API key（如果没有真实的，可以跳过 DeepSeek 测试）
    scheduler = UnicornScheduler(
        deepseek_api_key="test-key"  # 替换为真实的 API key
    )

    # 初始化静态语料库
    print("初始化静态语料库...")
    scheduler.rag.init_static_collection("unicorn.list")

    print("\n测试 TTS 功能（不调用 LLM）...")

    # 直接测试 TTS
    test_text = "你好呀，今天天气真好"
    ref_audio = "D:/GPT_SoVITS/raw/unicorn/unicorn_battle_25.wav"

    try:
        audio_bytes = await scheduler._call_sovits_tts(
            text=test_text,
            ref_audio_path=ref_audio,
            temperature=0.95,
            top_p=0.95
        )

        print(f"[OK] TTS 成功！")
        print(f"音频大小: {len(audio_bytes)} bytes")

        # 保存音频
        with open("test_scheduler_output.wav", "wb") as f:
            f.write(audio_bytes)
        print("已保存到 test_scheduler_output.wav")

        return True

    except Exception as e:
        print(f"[ERROR] TTS 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_scheduler())
