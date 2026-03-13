"""
模拟 handle_file() 的返回格式测试
"""

import requests
import os
from pathlib import Path

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = r"D:\GPT_SoVITS\raw\unicorn\unicorn_battle_25.wav"

def test_handle_file_format():
    """模拟 handle_file() 格式"""
    print(f"测试音频文件: {REF_AUDIO}")
    print(f"文件是否存在: {os.path.exists(REF_AUDIO)}\n")

    # 模拟 handle_file() 的返回
    ref_audio_data = {
        "path": REF_AUDIO,
        "meta": {"_type": "gradio.FileData"},
        "orig_name": Path(REF_AUDIO).name
    }

    print(f"参考音频数据: {ref_audio_data}\n")

    payload = {
        "data": [
            "你好呀，今天天气真好",
            "中文",
            ref_audio_data,  # 使用 handle_file 格式
            [],
            "",
            "中文",
            5,
            0.95,
            0.95,
            "凑四句一切",
            1,
            1.0,
            True,
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
            json=payload,
            timeout=60
        )
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print("[OK] TTS 推理成功！")
            result = response.json()

            if 'data' in result and len(result['data']) > 0:
                audio_data = result['data'][0]
                if isinstance(audio_data, dict) and 'path' in audio_data:
                    audio_file_path = audio_data['path']
                    print(f"音频文件路径: {audio_file_path}")

                    with open(audio_file_path, 'rb') as f:
                        audio_bytes = f.read()
                    print(f"音频大小: {len(audio_bytes)} bytes")

                    with open("test_success.wav", "wb") as f:
                        f.write(audio_bytes)
                    print("已保存到 test_success.wav")

            return True
        else:
            print(f"[ERROR] TTS 推理失败: {response.status_code}")
            print(f"响应: {response.text}")

            print("\n请确认:")
            print("1. 是否在 WebUI 中手动加载了 GPT 和 SoVITS 模型？")
            print("2. 是否在 WebUI 中上传参考音频并成功生成过一次音频？")
            print("3. 如果没有，请在 WebUI 中测试一次，确保模型完全初始化")

            return False

    except Exception as e:
        print(f"[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_handle_file_format()
