"""
测试使用 Gradio FileData 格式的参考音频
"""

import requests
import os

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = r"D:\GPT_SoVITS\raw\unicorn\unicorn_battle_25.wav"

def test_filedata_format():
    """使用 FileData 格式测试"""
    print(f"测试音频文件: {REF_AUDIO}")
    print(f"文件是否存在: {os.path.exists(REF_AUDIO)}\n")

    # 尝试使用 Gradio FileData 格式
    filedata = {
        "path": REF_AUDIO,
        "url": None,
        "size": None,
        "orig_name": os.path.basename(REF_AUDIO),
        "mime_type": "audio/wav",
        "is_stream": False,
        "meta": {"_type": "gradio.FileData"}
    }

    payload = {
        "data": [
            "你好呀，今天天气真好",
            "中文",
            filedata,  # 使用 FileData 格式
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

                    with open("test_filedata.wav", "wb") as f:
                        f.write(audio_bytes)
                    print("已保存到 test_filedata.wav")

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
    test_filedata_format()
