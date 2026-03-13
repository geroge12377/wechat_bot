"""
测试不同的参考音频路径格式
"""

import requests

SOVITS_URL = "http://localhost:9872"

# 尝试不同的路径格式
test_paths = [
    None,  # 不使用参考音频（应该成功）
    r"D:\GPT_SoVITS\raw\unicorn\unicorn_battle_25.wav",  # 绝对路径（Windows）
    "D:/GPT_SoVITS/raw/unicorn/unicorn_battle_25.wav",   # 绝对路径（Unix风格）
    "raw/unicorn/unicorn_battle_25.wav",                  # 相对路径
    "unicorn_battle_25.wav",                              # 文件名
]

def test_path(ref_audio_path):
    """测试单个路径"""
    payload = {
        "data": [
            "你好",
            "中文",
            ref_audio_path,
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
            json=payload,
            timeout=60
        )
        return response.status_code, response.text[:100]
    except Exception as e:
        return None, str(e)

def main():
    print("测试不同的参考音频路径格式\n")
    print("="*60)

    for i, path in enumerate(test_paths, 1):
        print(f"\n测试 {i}: {path}")
        status, response = test_path(path)
        if status == 200:
            print(f"  [OK] 成功！状态码: {status}")
        else:
            print(f"  [FAIL] 失败。状态码: {status}")
            if response:
                print(f"  响应: {response}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
