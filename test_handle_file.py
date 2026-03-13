"""
使用 gradio_client 的 handle_file 测试
"""

from gradio_client import Client, handle_file

SOVITS_URL = "http://localhost:9872/"
REF_AUDIO = "D:/GPT_SoVITS/raw/unicorn/unicorn_battle_25.wav"

def test_with_handle_file():
    """使用 handle_file 测试"""
    print(f"测试音频文件: {REF_AUDIO}\n")

    try:
        print("连接到 SoVITS...")
        client = Client(SOVITS_URL)
        print("连接成功！\n")

        print("调用推理 API...")
        result = client.predict(
            text="你好呀，今天天气真好",
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

        print("[OK] 推理成功！")
        print(f"返回结果: {result}")

        if result and len(result) > 0:
            audio_file_path = result[0]
            print(f"\n音频文件路径: {audio_file_path}")

            # 读取音频文件
            with open(audio_file_path, 'rb') as f:
                audio_bytes = f.read()
            print(f"音频大小: {len(audio_bytes)} bytes")

            # 保存到本地
            with open("test_handle_file.wav", "wb") as f:
                f.write(audio_bytes)
            print("已保存到 test_handle_file.wav")

            return True
        else:
            print("[ERROR] 返回结果为空")
            return False

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_handle_file()
