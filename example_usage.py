"""
Unicorn Scheduler 使用示例

运行前准备：
1. 确保 SoVITS 服务运行在 http://localhost:9872
2. 准备 unicorn.list 文件（格式：path|speaker|lang|text）
3. 配置 DeepSeek API Key
"""

import asyncio
from unicorn_scheduler import UnicornScheduler


async def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===\n")

    # 1. 初始化调度器
    scheduler = UnicornScheduler(
        deepseek_api_key="sk-your-api-key-here"  # 替换为真实的 API Key
    )

    # 2. 初始化静态语料库（仅首次运行需要）
    try:
        scheduler.rag.init_static_collection("unicorn.list")
    except FileNotFoundError:
        print("[WARNING] unicorn.list 文件不存在，跳过语料库初始化")
        print("请创建 unicorn.list 文件，格式：path|speaker|lang|text")
        return

    # 3. 运行对话
    user_input = "今天天气真好呀[开心]"
    print(f"用户输入: {user_input}")

    try:
        text_response, audio_bytes = await scheduler.run(user_input)
        print(f"回复文本: {text_response}")
        print(f"音频大小: {len(audio_bytes)} bytes")

        # 保存音频
        with open("output.wav", "wb") as f:
            f.write(audio_bytes)
        print("音频已保存: output.wav")

    except Exception as e:
        print(f"[ERROR] {e}")


async def example_emotion_tags():
    """情感标签示例"""
    print("\n=== 情感标签示例 ===\n")

    scheduler = UnicornScheduler(deepseek_api_key="dummy")

    # 测试不同情感标签
    test_cases = [
        "你好呀[撒娇]",
        "[温柔]晚安",
        "我有点担心[担心]",
        "[开心]太棒了",
        "有点不好意思[害羞]",
        "没有标签的普通文本"
    ]

    for text in test_cases:
        clean_text, emotion_params = scheduler._parse_emotion_tag(text)
        print(f"输入: {text}")
        print(f"  -> 清理后: {clean_text}")
        print(f"  -> Temperature: {emotion_params['temp']}, Top_P: {emotion_params['top_p']}")
        print(f"  -> 检索关键词: {emotion_params['search_kw']}\n")


async def example_rag_query():
    """RAG 检索示例"""
    print("\n=== RAG 检索示例 ===\n")

    from unicorn_rag import UnicornRAG

    rag = UnicornRAG()

    # 保存一些长时记忆
    print("保存长时记忆...")
    rag.save_long_term_memory("用户喜欢吃苹果")
    rag.save_long_term_memory("用户的生日是3月15日")
    rag.save_long_term_memory("用户最近在学习Python编程")

    # 查询记忆
    print("\n查询记忆...")
    queries = ["用户喜欢吃什么", "用户的生日", "用户在学什么"]

    for query in queries:
        history, ref_audio = await rag.query_memory(query)
        print(f"查询: {query}")
        print(f"  -> 相关记忆: {history}\n")


if __name__ == "__main__":
    print("Unicorn Scheduler 使用示例\n")
    print("=" * 50)

    # 运行情感标签示例（不需要 API Key）
    asyncio.run(example_emotion_tags())

    # 运行 RAG 检索示例（不需要 API Key）
    asyncio.run(example_rag_query())

    # 运行完整示例（需要 API Key 和 SoVITS 服务）
    print("\n" + "=" * 50)
    print("\n如需运行完整示例，请：")
    print("1. 配置 DeepSeek API Key")
    print("2. 启动 SoVITS 服务 (http://localhost:9872)")
    print("3. 准备 unicorn.list 文件")
    print("4. 取消下面的注释并运行：")
    print("   # asyncio.run(example_basic_usage())")
