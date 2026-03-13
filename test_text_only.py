"""测试纯文本 LLM 链路"""
import requests
import json
import socket

# 网络诊断
print("=== 网络诊断 ===")
print(f"localhost 解析为: {socket.gethostbyname('localhost')}")

# 测试连接
url = "http://localhost:5000/chat"
print(f"\n=== 测试请求 ===")
print(f"目标 URL: {url}")

# 先测试 health 接口
try:
    health_response = requests.get("http://localhost:5000/health", timeout=5)
    print(f"Health 检查: {health_response.status_code} - {health_response.json()}")
except Exception as e:
    print(f"Health 检查失败: {e}")
    exit(1)

# 测试 chat 接口
data = {"message": "你好呀", "user_id": "test123"}
print(f"请求数据: {data}")

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
except requests.exceptions.Timeout:
    print("超时（30秒）")
except Exception as e:
    print(f"错误: {e}")
