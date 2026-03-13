"""
测试使用参考音频的 TTS
"""

import requests
import os

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = r"D:\GPT_SoVITS\raw\unicorn\unicorn_battle_25.wav"

def test_with_ref_audio():
    """使用参考音频测试"""
    print(f"测试音频文件: {REF_AUDIO}")
    print(f"文件是否存在: {os.path.exists(REF_AUDIO)}\n")

    payload = {
        "data": [
            "你好呀，今天天气真好",  # text
            "中文",                  # text_lang
            REF_AUDIO,               # ref_audio_path
            [],                      # aux_ref_audio_paths
            "",                      # prompt_text
            "中文",                  # prompt_lang
            5,                       # top_k
            0.95,                    # top_p
            0.95,                    # temperature
            "凑四句一切",            # text_split_method
            1,                       # batch_size
            1.0,                     # speed_factor
            True,                    # ref_text_free
            True,                    # split_bucket
            0.3,                     # fragment_interval
            -1,                      # seed
            True,                    # keep_random
            True,                    # parallel_infer
            1.35,                    # repetition_penalty
            "128",                   # sample_steps
            False                    # super_sampling
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
            print("[OK] TTS 推理成功！")
            result = response.json()

            if 'data' in result and len(result['data']) > 0:
                audio_data = result['data'][0]
                print(f"音频数据类型: {type(audio_data)}")

                # 如果是字典格式
                if isinstance(audio_data, dict) and 'path' in audio_data:
                    audio_file_path = audio_data['path']
                    print(f"音频文件路径: {audio_file_path}")

                    # 读取音频文件
                    with open(audio_file_path, 'rb') as f:
                        audio_bytes = f.read()
                    print(f"音频大小: {len(audio_bytes)} bytes")

                    # 保存到本地
                    with open("test_with_ref.wav", "wb") as f:
                        f.write(audio_bytes)
                    print("已保存到 test_with_ref.wav")

            return True
        else:
            print(f"[ERROR] TTS 推理失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_ref_audio()
