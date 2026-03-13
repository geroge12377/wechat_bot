"""
SoVITS 服务诊断工具
检查服务状态、模型加载情况
"""

import requests
import json

SOVITS_URL = "http://localhost:9872"

def check_service():
    """检查服务是否运行"""
    try:
        response = requests.get(f"{SOVITS_URL}/", timeout=5)
        print("[OK] SoVITS 服务正在运行")
        return True
    except Exception as e:
        print(f"[ERROR] SoVITS 服务未运行: {e}")
        return False

def check_api_info():
    """检查 API 信息"""
    try:
        response = requests.get(f"{SOVITS_URL}/info", timeout=5)
        if response.status_code == 200:
            print("[OK] API 信息可访问")
            data = response.json()

            # 检查可用的端点
            endpoints = data.get('named_endpoints', {})
            print(f"\n可用的 API 端点: {len(endpoints)} 个")
            for name in endpoints.keys():
                print(f"  - {name}")

            return True
        else:
            print(f"[WARNING] API 信息返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] 无法获取 API 信息: {e}")
        return False

def test_change_choices():
    """测试模型切换"""
    print("\n测试模型切换...")
    try:
        payload = {
            "data": [
                "",  # SoVITS 模型（空=默认）
                "GPT_weights_v2Pro/xxx-e50.ckpt"  # GPT 模型
            ]
        }

        response = requests.post(
            f"{SOVITS_URL}/api/change_choices",
            json=payload,
            timeout=30
        )

        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:200]}")

        if response.status_code == 200:
            print("[OK] 模型切换成功")
            return True
        else:
            print(f"[ERROR] 模型切换失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] 模型切换异常: {e}")
        return False

def test_simple_inference():
    """测试简单的 TTS 推理"""
    print("\n测试 TTS 推理...")
    try:
        # 使用最简单的参数
        payload = {
            "data": [
                "你好",  # text
                "中文",  # text_lang
                None,    # ref_audio_path (可能需要实际文件)
                [],      # aux_ref_audio_paths
                "",      # prompt_text
                "中文",  # prompt_lang
                5,       # top_k
                1.0,     # top_p
                1.0,     # temperature
                "不切",  # text_split_method
                20,      # batch_size
                1.0,     # speed_factor
                False,   # ref_text_free
                True,    # split_bucket
                0.3,     # fragment_interval
                -1,      # seed
                True,    # keep_random
                True,    # parallel_infer
                1.35,    # repetition_penalty
                "128",   # sample_steps
                False    # super_sampling
            ]
        }

        response = requests.post(
            f"{SOVITS_URL}/api/inference",
            json=payload,
            timeout=60
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print("[OK] TTS 推理成功")
            result = response.json()
            print(f"返回数据类型: {type(result)}")
            if 'data' in result:
                print(f"返回数据长度: {len(result['data'])}")
            return True
        else:
            print(f"[ERROR] TTS 推理失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"[ERROR] TTS 推理异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("SoVITS 服务诊断")
    print("=" * 60)

    # 1. 检查服务
    if not check_service():
        print("\n请先启动 SoVITS 服务！")
        print("运行: python webui.py 或 python api.py")
        return

    # 2. 检查 API
    if not check_api_info():
        print("\n[WARNING] API 信息不可用，服务可能未完全启动")

    # 3. 测试模型切换
    test_change_choices()

    # 4. 测试推理
    test_simple_inference()

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
