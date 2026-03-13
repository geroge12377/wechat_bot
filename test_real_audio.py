"""
测试使用实际音频文件的 TTS 推理
"""

import requests
import json

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = "D:\\GPT_SoVITS\\raw\\unicorn\\unicorn_battle_25.wav"

def test_with_real_audio():
    """使用实际音频文件测试"""
    print(f"测试音频文件: {REF_AUDIO}\n")

    # 方法 1: 使用文件路径（字符串）
    print("方法 1: 直接使用文件路径字符串")
    payload1 = {
        "data": [
            "你好呀",  # text
            "中文",    # text_lang
            REF_AUDIO,  # ref_audio_path (直接字符串)
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
            json=payload1,
            timeout=60
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("[OK] 方法 1 成功！")
            result = response.json()
            print(f"返回数据: {type(result)}")
            if 'data' in result:
                print(f"数据长度: {len(result['data'])}")
                if len(result['data']) > 0:
                    print(f"第一个元素类型: {type(result['data'][0])}")
            return True
        else:
            print(f"[ERROR] 方法 1 失败")
            print(f"响应: {response.text[:500]}")
    except Exception as e:
        print(f"[ERROR] 方法 1 异常: {e}")

    print("\n" + "="*60 + "\n")

    # 方法 2: 使用 FileData 格式
    print("方法 2: 使用 FileData 格式")
    payload2 = {
        "data": [
            "你好呀",
            "中文",
            {"path": REF_AUDIO},  # FileData 格式
            [],
            "",
            "中文",
            5,
            0.95,
            0.95,
            "不切",
            20,
            1.0,
            False,
            True,
            0.3,
            -1,
            True,
            True,
            1.35,
            "128",
            False
        ]
    }

    try:
        response = requests.post(
            f"{SOVITS_URL}/api/inference",
            json=payload2,
            timeout=60
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("[OK] 方法 2 成功！")
            result = response.json()
            print(f"返回数据: {type(result)}")
            if 'data' in result:
                print(f"数据长度: {len(result['data'])}")
            return True
        else:
            print(f"[ERROR] 方法 2 失败")
            print(f"响应: {response.text[:500]}")
    except Exception as e:
        print(f"[ERROR] 方法 2 异常: {e}")

    return False

if __name__ == "__main__":
    test_with_real_audio()
