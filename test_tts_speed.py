"""Test TTS generation speed"""
import time
from simple_gradio_client import SimpleGradioClient, handle_file

client = SimpleGradioClient("http://localhost:9872")

test_text = "Welcome back"
ref_audio = "unicorn.list"

print(f"Starting TTS generation: {test_text}")
start = time.time()

try:
    result = client.predict(
        api_name="/get_tts_wav",
        text=test_text,
        text_lang="日文",
        ref_audio_path=handle_file(ref_audio),
        aux_ref_audio_paths=[],
        prompt_text="",
        prompt_lang="日文",
        top_k=15,
        top_p=0.85,
        temperature=0.70,
        text_split_method="不切",
        speed_factor=1.0,
        ref_text_free=False,
        sample_steps="32",
        super_sampling=False,
        fragment_interval=0.3
    )
    elapsed = time.time() - start
    print(f"Success! Time: {elapsed:.1f}s")
    if result and len(result) > 0:
        audio_data = result[0]
        if isinstance(audio_data, dict) and 'path' in audio_data:
            print(f"Audio file: {audio_data['path']}")
        else:
            print(f"Result: {audio_data}")
except Exception as e:
    elapsed = time.time() - start
    print(f"Failed! Time: {elapsed:.1f}s")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
