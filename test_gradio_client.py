"""
使用 gradio_client 测试 SoVITS TTS
"""

from gradio_client import Client, handle_file
import os

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = r"D:\GPT_SoVITS\raw\unicorn\unicorn_anniversary_01.wav"

def test_with_gradio_client():
    """使用 gradio_client 测试"""
    print(f"测试音频文件: {REF_AUDIO}")
    print(f"文件是否存在: {os.path.exists(REF_AUDIO)}\n")

    try:
        print("连接到 SoVITS...")
        client = Client(SOVITS_URL, verbose=False)

        print("调用 /inference API...")
        result = client.predict(
            text="你好呀",
            text_lang="中文",
            ref_audio_path=handle_file(REF_AUDIO),
            aux_ref_audio_paths=[],
            prompt_text="",
            prompt_lang="中文",
            top_k=5,
            top_p=0.95,
            temperature=0.95,
            text_split_method="凑四句一切",
            batch_size=1,
            speed_factor=1.0,
            ref_text_free=True,
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
        print(f"返回结果类型: {type(result)}")
        print(f"返回结果: {result}")

        # 检查返回的音频文件
        if result and len(result) > 0:
            audio_file_path = result[0]
            print(f"\n生成的音频文件: {audio_file_path}")

            # 读取音频文件
            with open(audio_file_path, 'rb') as f:
                audio_bytes = f.read()

            print(f"音频大小: {len(audio_bytes)} bytes")

            # 保存到本地
            with open("test_output.wav", "wb") as f:
                f.write(audio_bytes)
            print("已保存到 test_output.wav")

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
    test_with_gradio_client()
