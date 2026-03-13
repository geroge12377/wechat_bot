"""
最终诊断：对比有无参考音频的情况
"""

import requests

SOVITS_URL = "http://localhost:9872"
REF_AUDIO = "D:/GPT_SoVITS/raw/unicorn/unicorn_battle_25.wav"

def test_without_ref():
    """不使用参考音频"""
    print("测试 1: 不使用参考音频")
    print("=" * 60)

    payload = {
        "data": [
            "你好呀",
            "中文",
            None,  # 不使用参考音频
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
            print("[OK] 成功！")
            return True
        else:
            print(f"[FAIL] 失败: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"[ERROR] 异常: {e}")
        return False


def test_with_ref_string():
    """使用字符串路径"""
    print("\n测试 2: 使用字符串路径作为参考音频")
    print("=" * 60)

    payload = {
        "data": [
            "你好呀",
            "中文",
            REF_AUDIO,  # 字符串路径
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
            print("[OK] 成功！")
            return True
        else:
            print(f"[FAIL] 失败: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"[ERROR] 异常: {e}")
        return False


def test_with_ref_filedata():
    """使用 FileData 格式"""
    print("\n测试 3: 使用 FileData 格式作为参考音频")
    print("=" * 60)

    ref_audio_data = {
        "path": REF_AUDIO,
        "meta": {"_type": "gradio.FileData"},
        "orig_name": "unicorn_battle_25.wav"
    }

    payload = {
        "data": [
            "你好呀",
            "中文",
            ref_audio_data,  # FileData 格式
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
            print("[OK] 成功！")
            return True
        else:
            print(f"[FAIL] 失败: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"[ERROR] 异常: {e}")
        return False


def main():
    print("SoVITS 参考音频诊断")
    print("=" * 60)
    print(f"参考音频: {REF_AUDIO}\n")

    result1 = test_without_ref()
    result2 = test_with_ref_string()
    result3 = test_with_ref_filedata()

    print("\n" + "=" * 60)
    print("诊断结果:")
    print(f"  不使用参考音频: {'✓ 成功' if result1 else '✗ 失败'}")
    print(f"  字符串路径: {'✓ 成功' if result2 else '✗ 失败'}")
    print(f"  FileData 格式: {'✓ 成功' if result3 else '✗ 失败'}")

    if result1 and not result2 and not result3:
        print("\n结论: 模型未完全初始化，需要在 WebUI 中手动加载并测试")
        print("请执行以下步骤:")
        print("1. 打开 http://localhost:9872")
        print("2. 确认 GPT 和 SoVITS 模型已选择")
        print("3. 上传参考音频并成功生成一次")
        print("4. 重新运行此脚本")

if __name__ == "__main__":
    main()
