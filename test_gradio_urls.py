"""
测试不同的 gradio_client 连接方式
"""

from gradio_client import Client, handle_file
import sys

REF_AUDIO = "D:/GPT_SoVITS/raw/unicorn/unicorn_battle_25.wav"

# 尝试不同的 URL 格式
urls = [
    "http://localhost:9872",
    "http://localhost:9872/",
    "http://127.0.0.1:9872",
    "http://127.0.0.1:9872/",
]

for url in urls:
    print(f"\n尝试连接: {url}")
    print("=" * 60)
    try:
        client = Client(url, verbose=False)
        print(f"[OK] 连接成功！")

        # 尝试调用推理
        print("调用推理 API...")
        result = client.predict(
            text="你好呀",
            text_lang="中文",
            ref_audio_path=handle_file(REF_AUDIO),
            aux_ref_audio_paths=[],
            prompt_text="",
            prompt_lang="中文",
            ref_text_free=True,
            top_k=5,
            top_p=0.95,
            temperature=0.95,
            text_split_method="凑四句一切",
            batch_size=1,
            speed_factor=1.0,
            split_bucket=True,
            fragment_interval=0.3,
            seed=-1,
            keep_random=True,
            parallel_infer=True,
            repetition_penalty=1.35,
            sample_steps="128",
            super_sampling=False,
            api_name="/inference"
        )

        print(f"[OK] 推理成功！")
        print(f"音频文件: {result[0]}")

        # 读取并保存音频
        with open(result[0], 'rb') as f:
            audio_bytes = f.read()
        print(f"音频大小: {len(audio_bytes)} bytes")

        with open("test_gradio_success.wav", "wb") as f:
            f.write(audio_bytes)
        print("已保存到 test_gradio_success.wav")

        sys.exit(0)  # 成功后退出

    except ValueError as e:
        if "Could not fetch config" in str(e):
            print(f"[FAIL] 无法获取配置: {e}")
        else:
            print(f"[FAIL] ValueError: {e}")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")

print("\n所有连接方式都失败了")
