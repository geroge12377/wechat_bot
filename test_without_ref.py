"""
测试不使用参考音频的 TTS（验证模型是否已加载）
"""

import requests

SOVITS_URL = "http://localhost:9872"

def test_without_ref_audio():
    """不使用参考音频测试"""
    print("测试不使用参考音频的 TTS 推理...\n")

    payload = {
        "data": [
            "你好呀",  # text
            "中文",    # text_lang
            None,      # ref_audio_path (不使用参考音频)
            [],        # aux_ref_audio_paths
            "",        # prompt_text
            "中文",    # prompt_lang
            5,         # top_k
            0.95,      # top_p
            0.95,      # temperature
            "不切",    # text_split_method
            20,        # batch_size
            1.0,       # speed_factor
            False,     # ref_text_free
            True,      # split_bucket
            0.3,       # fragment_interval
            -1,        # seed
            True,      # keep_random
            True,      # parallel_infer
            1.35,      # repetition_penalty
            "128",     # sample_steps
            False      # super_sampling
        ]
    }

    try:
        response = requests.post(
            f"{SOVITS_URL}/api/inference",
            json=payload,
            timeout=60
        )
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print("[OK] TTS 推理成功！模型已加载。")
            result = response.json()
            print(f"返回数据: {result}")

            if 'data' in result and len(result['data']) > 0:
                audio_data = result['data'][0]
                print(f"\n音频数据类型: {type(audio_data)}")

                # 如果是文件路径
                if isinstance(audio_data, str):
                    print(f"音频文件路径: {audio_data}")

                    # 尝试读取文件
                    try:
                        with open(audio_data, 'rb') as f:
                            audio_bytes = f.read()
                        print(f"音频大小: {len(audio_bytes)} bytes")

                        # 保存到本地
                        with open("test_no_ref.wav", "wb") as f:
                            f.write(audio_bytes)
                        print("已保存到 test_no_ref.wav")
                    except Exception as e:
                        print(f"读取音频文件失败: {e}")

            return True
        else:
            print(f"[ERROR] TTS 推理失败: {response.status_code}")
            print(f"响应: {response.text}")
            print("\n可能原因：")
            print("1. GPT 和 SoVITS 模型未通过 WebUI 加载")
            print("2. 请打开 http://localhost:9872 并手动加载模型")
            return False

    except Exception as e:
        print(f"[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_without_ref_audio()
