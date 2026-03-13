"""
测试 GPT 模型配置 (xxx-e50)
"""

import asyncio
from unicorn_scheduler import UnicornScheduler
from dotenv import load_dotenv
import os

load_dotenv()

async def test_model_config():
    """测试模型配置"""
    print("=== 测试 GPT 模型配置 (xxx-e50) ===\n")

    # 初始化调度器，指定 GPT 模型
    scheduler = UnicornScheduler(
        deepseek_api_key=os.getenv("AI_API_KEY"),
        deepseek_base_url=os.getenv("AI_BASE_URL"),
        gpt_model="GPT_weights_v2Pro/xxx-e50.ckpt",
        sovits_model=""  # 留空使用默认
    )

    print(f"配置的 GPT 模型: {scheduler.gpt_model}")
    print(f"配置的 SoVITS 模型: {scheduler.sovits_model or '(默认)'}")
    print()

    # 测试模型切换
    print("测试模型切换...")
    try:
        await scheduler._change_models()
        print("模型切换成功！\n")
    except Exception as e:
        print(f"模型切换失败: {e}\n")
        print("注意：需要 SoVITS 服务运行在 localhost:9872\n")

    # 测试简单对话（不含 TTS）
    print("测试 LLM 对话...")
    try:
        # 初始化 RAG
        scheduler.rag.init_static_collection("unicorn.list")

        # 测试检索
        history, ref_audio = await scheduler.rag.query_memory("你好")
        print(f"RAG 检索成功")
        print(f"  历史记忆: {history[:50]}...")
        print(f"  参考音频: {ref_audio}")

        # 测试 LLM 调用
        llm_response = await scheduler._call_deepseek("你好呀", history)
        print(f"\nLLM 回复: {llm_response[:100]}...")

        # 测试情感解析
        clean_text, emotion_params = scheduler._parse_emotion_tag("你好呀[撒娇]")
        print(f"\n情感解析:")
        print(f"  原文: 你好呀[撒娇]")
        print(f"  清理后: {clean_text}")
        print(f"  参数: temp={emotion_params['temp']}, top_p={emotion_params['top_p']}")

        print("\n所有功能测试通过！")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_model_config())
