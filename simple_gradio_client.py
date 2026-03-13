"""
使用 requests 模拟 gradio_client 的简单包装器
因为 SoVITS 服务器不兼容 httpx
"""

import requests
import os
from pathlib import Path
from typing import Dict, List, Any


class SimpleGradioClient:
    """
    简单的 Gradio 客户端，使用 requests 而不是 httpx
    专门为 SoVITS 设计
    """

    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self._uploaded_files = {}  # 缓存已上传的文件

    def upload_file(self, filepath: str) -> Dict:
        """
        上传文件到 Gradio 服务器
        返回 FileData 格式
        """
        # 检查是否已上传
        if filepath in self._uploaded_files:
            return self._uploaded_files[filepath]

        path = Path(filepath)
        if not path.exists():
            raise ValueError(f"File {filepath} does not exist")

        # 上传文件
        with open(filepath, 'rb') as f:
            files = {'files': (path.name, f, 'audio/wav')}
            response = requests.post(
                f"{self.url}/upload",
                files=files,
                timeout=30
            )
            response.raise_for_status()

        # 解析返回的路径
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            uploaded_path = result[0]

            # 构造 FileData 格式
            file_data = {
                "path": uploaded_path,
                "meta": {"_type": "gradio.FileData"},
                "orig_name": path.name
            }

            # 缓存
            self._uploaded_files[filepath] = file_data
            return file_data
        else:
            raise ValueError(f"Upload failed: {result}")

    def predict(self, api_name: str, **kwargs) -> List[Any]:
        """
        调用 Gradio API
        """
        # 处理 ref_audio_path - 如果是字符串，先上传
        ref_audio_path = kwargs.get("ref_audio_path")
        if isinstance(ref_audio_path, str):
            ref_audio_path = self.upload_file(ref_audio_path)
        elif isinstance(ref_audio_path, dict) and 'path' in ref_audio_path:
            # 如果是 FileData 格式但路径是本地文件，需要上传
            local_path = ref_audio_path['path']
            if os.path.exists(local_path):
                ref_audio_path = self.upload_file(local_path)

        # 处理辅助参考音频
        aux_refs = kwargs.get("aux_ref_audio_paths", [])
        if aux_refs:
            processed_aux = []
            for ref in aux_refs:
                if isinstance(ref, str) and os.path.exists(ref):
                    processed_aux.append(self.upload_file(ref))
                else:
                    processed_aux.append(ref)
            aux_refs = processed_aux

        # 根据 API 端点构造不同的 payload
        if api_name == "/get_tts_wav":
            # /get_tts_wav 的参数顺序
            data = [
                ref_audio_path,                                    # ref_wav_path
                kwargs.get("prompt_text", ""),                     # prompt_text
                kwargs.get("prompt_lang", "日文"),                 # prompt_language
                kwargs.get("text", ""),                            # text
                kwargs.get("text_lang", "日文"),                   # text_language
                kwargs.get("text_split_method", "凑四句一切"),      # how_to_cut
                kwargs.get("top_k", 15),                           # top_k
                kwargs.get("top_p", 1.0),                          # top_p
                kwargs.get("temperature", 1.0),                    # temperature
                kwargs.get("ref_text_free", False),                # ref_free
                kwargs.get("speed_factor", 1.0),                   # speed
                False,                                             # if_freeze
                aux_refs if aux_refs else None,                   # inp_refs
                str(kwargs.get("sample_steps", "8")),              # sample_steps (字符串)
                kwargs.get("super_sampling", False),               # if_sr
                kwargs.get("fragment_interval", 0.3),              # pause_second
            ]
        else:
            # 旧的参数顺序（兼容）
            data = [
                kwargs.get("text", ""),
                kwargs.get("text_lang", "日文"),
                ref_audio_path,
                aux_refs,
                kwargs.get("prompt_text", ""),
                kwargs.get("prompt_lang", "日文"),
                kwargs.get("top_k", 5),
                kwargs.get("top_p", 1.0),
                kwargs.get("temperature", 1.0),
                kwargs.get("text_split_method", "凑四句一切"),
                kwargs.get("batch_size", 1),
                kwargs.get("speed_factor", 1.0),
                kwargs.get("ref_text_free", False),
                kwargs.get("split_bucket", False),
                kwargs.get("fragment_interval", 0.3),
                kwargs.get("seed", -1),
                kwargs.get("keep_random", True),
                kwargs.get("parallel_infer", False),
                kwargs.get("repetition_penalty", 1.35),
                kwargs.get("sample_steps", "128"),
                kwargs.get("super_sampling", False),
            ]

        payload = {"data": data}

        # 发送请求
        response = requests.post(
            f"{self.url}/api{api_name}",
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        # 解析响应
        result = response.json()

        if 'data' in result:
            return result['data']
        else:
            raise ValueError(f"Unexpected response format: {result}")


# 兼容函数
def handle_file(filepath: str) -> str:
    """
    返回文件路径（将在 predict 中自动上传）
    """
    return filepath
