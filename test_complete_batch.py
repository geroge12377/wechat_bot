"""
完整测试结果保存
"""
import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from unicorn_scheduler import UnicornScheduler

load_dotenv()

async def main():
    scheduler = UnicornScheduler(
        deepseek_api_key=os.getenv("AI_API_KEY"),
        deepseek_base_url=os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    )

    scheduler.rag.init_static_collection("unicorn.list")

    test_cases = [
        "哥哥回来啦",
        "今天天气真好呀",
        "独角兽真可爱"
    ]

    results = []

    for i, test_input in enumerate(test_cases):
        print(f"\nTest {i+1}/{len(test_cases)}: {test_input}")

        try:
            text_response, audio_bytes = await scheduler.run(test_input)

            # 保存音频
            audio_file = Path(f"test_output_{i+1}.wav")
            with open(audio_file, "wb") as f:
                f.write(audio_bytes)

            result = {
                "input": test_input,
                "output": text_response,
                "audio_size": len(audio_bytes),
                "audio_file": str(audio_file),
                "status": "success"
            }

            print(f"  Output: {text_response}")
            print(f"  Audio: {len(audio_bytes)} bytes -> {audio_file}")

        except Exception as e:
            result = {
                "input": test_input,
                "error": str(e),
                "status": "failed"
            }
            print(f"  Error: {e}")

        results.append(result)

    # 保存结果
    with open("complete_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print("Test Summary:")
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"  Success: {success_count}/{len(results)}")
    print(f"  Results saved to: complete_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
