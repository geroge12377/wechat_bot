"""
测试通过 Gradio 上传端点上传参考音频
"""

import requests
import os

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = r"D:\GPT_SoVITS\raw\unicorn\unicorn_battle_25.wav"

def upload_file():
    """上传文件到 Gradio"""
    print(f"上传音频文件: {REF_AUDIO}\n")

    try:
        with open(REF_AUDIO, 'rb') as f:
            files = {'files': (os.path.basename(REF_AUDIO), f, 'audio/wav')}
            response = requests.post(
                f"{SOVITS_URL}/upload",
                files=files,
                timeout=30
            )

        print(f"上传状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"上传结果: {result}")
            return result
        else:
            print(f"上传失败: {response.text}")
            return None

    except Exception as e:
        print(f"上传异常: {e}")
        return None

def test_with_uploaded_file(uploaded_path):
    """使用上传后的文件路径测试"""
    print(f"\n使用上传的文件路径: {uploaded_path}\n")

    payload = {
        "data": [
            "你好呀，今天天气真好",
            "中文",
            uploaded_path,
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
        print(f"推理状态码: {response.status_code}")

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

                    with open("test_uploaded.wav", "wb") as f:
                        f.write(audio_bytes)
                    print("已保存到 test_uploaded.wav")

            return True
        else:
            print(f"[ERROR] TTS 推理失败")
            print(f"响应: {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] 测试异常: {e}")
        return False

if __name__ == "__main__":
    # 先上传文件
    uploaded = upload_file()

    if uploaded:
        # 使用上传后的路径测试
        if isinstance(uploaded, list) and len(uploaded) > 0:
            uploaded_path = uploaded[0]
            test_with_uploaded_file(uploaded_path)
        else:
            print("无法获取上传后的文件路径")
    else:
        print("\n文件上传失败，尝试直接使用本地路径")
        test_with_uploaded_file(REF_AUDIO)
