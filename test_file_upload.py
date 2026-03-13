"""
测试使用文件上传方式的参考音频
"""

import requests
import os

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = r"D:\GPT_SoVITS\raw\unicorn\unicorn_battle_25.wav"

def test_with_file_upload():
    """使用文件上传方式测试"""
    print(f"测试音频文件: {REF_AUDIO}")
    print(f"文件是否存在: {os.path.exists(REF_AUDIO)}\n")

    # 方法 1: 使用 multipart/form-data 上传文件
    print("方法 1: 使用 multipart/form-data")
    try:
        with open(REF_AUDIO, 'rb') as f:
            files = {
                'ref_audio_path': f
            }
            data = {
                'text': '你好呀，今天天气真好',
                'text_lang': '中文',
                'prompt_text': '',
                'prompt_lang': '中文',
                'top_k': 5,
                'top_p': 0.95,
                'temperature': 0.95,
                'text_split_method': '凑四句一切',
                'batch_size': 1,
                'speed_factor': 1.0,
                'ref_text_free': True,
                'split_bucket': True,
                'fragment_interval': 0.3,
                'seed': -1,
                'keep_random': True,
                'parallel_infer': True,
                'repetition_penalty': 1.35,
                'sample_steps': '128',
                'super_sampling': False
            }

            response = requests.post(
                f"{SOVITS_URL}/api/inference",
                files=files,
                data=data,
                timeout=60
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:500]}")

    except Exception as e:
        print(f"[ERROR] 方法 1 失败: {e}")

    print("\n" + "="*60 + "\n")

    # 方法 2: 先上传文件，再使用返回的路径
    print("方法 2: 先上传文件")
    try:
        # 检查是否有上传端点
        response = requests.get(f"{SOVITS_URL}/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"可用端点: {list(info.get('named_endpoints', {}).keys())}")

    except Exception as e:
        print(f"[ERROR] 方法 2 失败: {e}")

if __name__ == "__main__":
    test_with_file_upload()
