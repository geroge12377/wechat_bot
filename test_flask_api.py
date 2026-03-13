"""
快速测试 Flask API
"""
import requests
import json

API_URL = "http://localhost:5000"

def test_health():
    """测试健康检查"""
    print("=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_chat():
    """测试对话接口"""
    print("\n" + "=" * 60)
    print("测试 2: 对话接口")
    print("=" * 60)

    test_messages = [
        "哥哥回来啦",
        "今天天气真好呀"
    ]

    for msg in test_messages:
        print(f"\n发送消息: {msg}")
        try:
            response = requests.post(
                f"{API_URL}/chat",
                json={"message": msg, "user_id": "test_user"},
                timeout=60
            )
            print(f"状态码: {response.status_code}")

            result = response.json()
            print(f"成功: {result.get('success')}")
            print(f"文字回复: {result.get('text')}")
            print(f"音频文件: {result.get('audio_filename')}")
            print(f"音频URL: {result.get('audio_url')}")

        except Exception as e:
            print(f"❌ 失败: {e}")

def main():
    print("\n=== Unicorn Flask API Test ===\n")

    # 测试健康检查
    if not test_health():
        print("\nFlask service not running. Please start it first:")
        print("   python wechat_bot_integrated.py server")
        return

    # 测试对话
    test_chat()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
