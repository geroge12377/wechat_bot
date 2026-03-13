"""
测试不同的参考音频文件
"""

from simple_gradio_client import SimpleGradioClient, handle_file

SOVITS_URL = "http://localhost:9872"

# 尝试不同的音频文件
audio_files = [
    "D:/GPT_SoVITS/raw/unicorn/unicorn_couple_2_31.wav",  # 295K
    "D:/GPT_SoVITS/raw/unicorn/unicorn_cheerleader_desc_62.wav",  # 373K
    "D:/GPT_SoVITS/raw/unicorn/unicorn_battle_25.wav",  # 414K
]

def test_audio_file(audio_path):
    """测试单个音频文件"""
    print(f"\n测试音频: {audio_path}")
    print("=" * 60)

    try:
        client = SimpleGradioClient(SOVITS_URL)

        result = client.predict(
            api_name="/inference",
            text="你好呀",
            text_lang="中文",
            ref_audio_path=handle_file(audio_path),
            aux_ref_audio_paths=[],
            prompt_text="",
            prompt_lang="中文",
            top_k=5,
            top_p=0.95,
            temperature=0.95,
            text_split_method="凑四句一切",
            batch_size=1,
            speed_factor=1.0,
            ref_text_free=True,
            split_bucket=True,
            fragment_interval=0.3,
            seed=-1,
            keep_random=True,
            parallel_infer=True,
            repetition_penalty=1.35,
            sample_steps="128",
            super_sampling=False
        )

        print(f"[OK] 成功！")

        if result and len(result) > 0:
            audio_data = result[0]
            if isinstance(audio_data, dict) and 'path' in audio_data:
                audio_file_path = audio_data['path']
                with open(audio_file_path, 'rb') as f:
                    audio_bytes = f.read()
                print(f"音频大小: {len(audio_bytes)} bytes")
                return True

        return False

    except Exception as e:
        print(f"[FAIL] {e}")
        return False

def main():
    print("测试不同的参考音频文件")
    print("=" * 60)

    for audio_file in audio_files:
        if test_audio_file(audio_file):
            print(f"\n成功！使用的音频文件: {audio_file}")
            break
    else:
        print("\n所有音频文件都失败了")
        print("\n请确认:")
        print("1. 是否在 WebUI 中手动上传了参考音频？")
        print("2. 是否在 WebUI 中成功生成过一次音频？")
        print("3. 检查 SoVITS 运行终端是否有错误日志")

if __name__ == "__main__":
    main()
