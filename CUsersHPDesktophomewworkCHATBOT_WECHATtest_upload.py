"""测试文件上传"""
import os
from simple_gradio_client import SimpleGradioClient

client = SimpleGradioClient("http://localhost:9872")

# 测试文件
test_file = "D:/GPT_SoVITS/raw/unicorn/unicorn_login_04.wav"

print(f"原始文件大小: {os.path.getsize(test_file)} bytes")

try:
    # 上传文件
    file_data = client.upload_file(test_file)
    print(f"上传成功!")
    print(f"返回数据: {file_data}")

    # 检查上传后的文件
    uploaded_path = file_data.get("path")
    if uploaded_path and os.path.exists(uploaded_path):
        uploaded_size = os.path.getsize(uploaded_path)
        print(f"上传后文件大小: {uploaded_size} bytes")
        if uploaded_size == 0:
            print("警告: 上传的文件是空的!")
    else:
        print(f"上传路径不存在: {uploaded_path}")

except Exception as e:
    print(f"上传失败: {e}")
    import traceback
    traceback.print_exc()
