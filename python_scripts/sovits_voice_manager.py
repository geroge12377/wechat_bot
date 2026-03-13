#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
So-VITS-SVC 语音管理器
专门处理So-VITS-SVC模型的加载和推理
"""

import os
import sys
import json
import time
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
import hashlib
import tempfile

# 添加so-vits-svc到Python路径
SOVITS_PATH = Path(__file__).parent / "so-vits-svc-4.1-Stable"
sys.path.insert(0, str(SOVITS_PATH))

try:
    from inference.infer_tool import Svc
    import utils
    from models import SynthesizerTrn
    SOVITS_AVAILABLE = True
    print("✅ So-VITS-SVC 模块加载成功")
except ImportError as e:
    print(f"❌ So-VITS-SVC 模块加载失败: {e}")
    SOVITS_AVAILABLE = False

class SoVITSManager:
    def __init__(self, model_path=None, config_path=None, device='auto'):
        """
        初始化So-VITS-SVC管理器
        
        Args:
            model_path: 模型文件路径 (.pth)
            config_path: 配置文件路径 (.json)
            device: 设备 ('cuda', 'cpu', 'auto')
        """
        self.model_path = model_path
        self.config_path = config_path
        self.svc_model = None
        self.hps = None
        self.device = self._setup_device(device)
        
        if model_path and config_path:
            self.load_model(model_path, config_path)
    
    def _setup_device(self, device):
        """设置推理设备"""
        if device == 'auto':
            return 'cuda' if torch.cuda.is_available() else 'cpu'
        return device
    
    def load_model(self, model_path, config_path, cluster_model_path=None):
        """
        加载So-VITS-SVC模型
        
        Args:
            model_path: 模型文件路径
            config_path: 配置文件路径  
            cluster_model_path: 聚类模型路径（可选）
        """
        try:
            if not SOVITS_AVAILABLE:
                raise ImportError("So-VITS-SVC未正确安装")
            
            print(f"🔄 加载模型: {Path(model_path).name}")
            
            # 创建Svc实例
            self.svc_model = Svc(
                model_path, 
                config_path,
                self.device,
                cluster_model_path=cluster_model_path
            )
            
            # 加载配置
            with open(config_path, 'r', encoding='utf-8') as f:
                self.hps = json.load(f)
            
            self.model_path = model_path
            self.config_path = config_path
            
            print(f"✅ 模型加载成功")
            print(f"   设备: {self.device}")
            print(f"   采样率: {self.hps.get('data', {}).get('sampling_rate', 44100)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.svc_model = None
            return False
    
    def inference(self, audio_path, target_sample=-1, spk_id=0, 
                  pitch_adjust=0, f0_method='dio', 
                  cluster_ratio=0.0, slice_db=-40,
                  pad_seconds=0.5, clip_seconds=0,
                  lg_num=0, lgr_num=0.75, auto_f0=False):
        """
        执行语音转换推理
        
        Args:
            audio_path: 输入音频路径
            target_sample: 目标采样率 (-1为自动)
            spk_id: 说话人ID
            pitch_adjust: 音高调整（半音）
            f0_method: F0提取方法 ('pm', 'harvest', 'dio', 'crepe')
            cluster_ratio: 聚类混合比例
            slice_db: 静音切片阈值
            pad_seconds: 填充秒数
            clip_seconds: 裁剪秒数
            lg_num: 线性梯度裁剪
            lgr_num: 线性梯度裁剪比例
            auto_f0: 自动F0提取
        
        Returns:
            output_path: 输出音频路径
        """
        if not self.svc_model:
            raise RuntimeError("模型未加载")
        
        try:
            # 生成输出文件名
            timestamp = int(time.time() * 1000)
            output_filename = f"sovits_output_{timestamp}.wav"
            output_path = Path(tempfile.gettempdir()) / output_filename
            
            # 执行推理
            kwarg = {
                "raw_audio_path": str(audio_path),
                "spk": spk_id,
                "tran": pitch_adjust,
                "slice_db": slice_db,
                "cluster_ratio": cluster_ratio,
                "auto_predict_f0": auto_f0,
                "noice_scale": 0.4,
                "pad_seconds": pad_seconds,
                "clip_seconds": clip_seconds,
                "lg_num": lg_num,
                "lgr_num": lgr_num,
                "f0_predictor": f0_method,
                "enhancer_adaptive_key": 0,
                "cr_threshold": 0.05,
                "k_step": 100,
                "use_spk_mix": False
            }
            
            audio = self.svc_model.slice_inference(**kwarg)
            
            # 保存音频
            sf.write(
                str(output_path),
                audio,
                self.hps['data']['sampling_rate'],
                format='wav'
            )
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ 推理失败: {e}")
            raise
    
    def text_to_speech_with_sovits(self, text, tts_model, 
                                   spk_id=0, pitch_adjust=0,
                                   emotion_params=None):
        """
        结合TTS和So-VITS-SVC生成语音
        
        Args:
            text: 输入文本
            tts_model: TTS模型实例（如Coqui TTS）
            spk_id: 说话人ID
            pitch_adjust: 音高调整
            emotion_params: 情感参数字典
            
        Returns:
            output_path: 最终音频路径
        """
        try:
            # 步骤1: 使用TTS生成初始语音
            temp_tts = Path(tempfile.gettempdir()) / f"temp_tts_{int(time.time())}.wav"
            
            # 这里假设tts_model有tts_to_file方法
            tts_model.tts_to_file(
                text=text,
                file_path=str(temp_tts),
                language="zh"
            )
            
            # 步骤2: 使用So-VITS-SVC转换语音
            if emotion_params:
                # 根据情感调整参数
                pitch_adjust += emotion_params.get('pitch_shift', 0)
            
            output_path = self.inference(
                temp_tts,
                spk_id=spk_id,
                pitch_adjust=pitch_adjust,
                f0_method='dio',
                slice_db=-40
            )
            
            # 清理临时文件
            if temp_tts.exists():
                temp_tts.unlink()
            
            return output_path
            
        except Exception as e:
            print(f"❌ TTS+SoVITS失败: {e}")
            raise
    
    def get_model_info(self):
        """获取模型信息"""
        if not self.svc_model:
            return None
        
        info = {
            "model_path": str(self.model_path),
            "config_path": str(self.config_path),
            "device": self.device,
            "loaded": True,
            "sampling_rate": self.hps.get('data', {}).get('sampling_rate', 44100),
            "n_speakers": self.hps.get('data', {}).get('n_speakers', 1)
        }
        
        # 获取说话人信息
        if 'spk' in self.hps:
            info['speakers'] = self.hps['spk']
        
        return info


class VoiceConversionManager:
    """语音转换管理器 - 整合多种TTS和VC方案"""
    
    def __init__(self):
        self.sovits_manager = None
        self.tts_model = None
        self.cache_dir = Path("./audio_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # 尝试初始化各种模型
        self._init_models()
    
    def _init_models(self):
        """初始化可用的模型"""
        # 初始化So-VITS-SVC
        if SOVITS_AVAILABLE:
            self.sovits_manager = SoVITSManager(device='auto')
        
        # 初始化备用TTS
        try:
            from TTS.api import TTS
            self.tts_model = TTS(model_name="tts_models/zh-CN/baker/tacotron2-DDC-GST")
            print("✅ Coqui TTS初始化成功")
        except:
            print("⚠️ Coqui TTS不可用")
    
    def load_sovits_model(self, model_path, config_path):
        """加载So-VITS-SVC模型"""
        if not self.sovits_manager:
            self.sovits_manager = SoVITSManager()
        
        return self.sovits_manager.load_model(model_path, config_path)
    
    def convert_voice(self, text, use_sovits=True, spk_id=0, emotion="normal"):
        """
        转换语音（支持多种方案）
        
        Args:
            text: 输入文本
            use_sovits: 是否使用So-VITS-SVC
            spk_id: 说话人ID
            emotion: 情感状态
            
        Returns:
            audio_path: 音频文件路径
        """
        # 生成缓存键
        cache_key = hashlib.md5(f"{text}_{spk_id}_{emotion}".encode()).hexdigest()[:8]
        cache_file = self.cache_dir / f"voice_{cache_key}.wav"
        
        # 检查缓存
        if cache_file.exists():
            print(f"📂 使用缓存: {cache_file.name}")
            return str(cache_file)
        
        # 情感参数
        emotion_params = {
            "normal": {"pitch_shift": 0, "speed": 1.0},
            "happy": {"pitch_shift": 2, "speed": 1.05},
            "sad": {"pitch_shift": -2, "speed": 0.95},
            "shy": {"pitch_shift": 1, "speed": 0.95},
            "excited": {"pitch_shift": 3, "speed": 1.1}
        }
        
        params = emotion_params.get(emotion, emotion_params["normal"])
        
        try:
            if use_sovits and self.sovits_manager and self.sovits_manager.svc_model:
                # 使用So-VITS-SVC
                output_path = self.sovits_manager.text_to_speech_with_sovits(
                    text, 
                    self.tts_model,
                    spk_id=spk_id,
                    pitch_adjust=params["pitch_shift"],
                    emotion_params=params
                )
                
                # 移动到缓存目录
                import shutil
                shutil.move(output_path, str(cache_file))
                
            elif self.tts_model:
                # 使用Coqui TTS
                self.tts_model.tts_to_file(
                    text=text,
                    file_path=str(cache_file),
                    language="zh"
                )
            else:
                print("❌ 没有可用的语音合成方案")
                return None
            
            return str(cache_file)
            
        except Exception as e:
            print(f"❌ 语音生成失败: {e}")
            return None


# 测试函数
def test_sovits():
    """测试So-VITS-SVC功能"""
    manager = SoVITSManager()
    
    # 测试模型路径
    model_path = "./voice_models/G_latest.pth"
    config_path = "./voice_models/config.json"
    
    if Path(model_path).exists() and Path(config_path).exists():
        if manager.load_model(model_path, config_path):
            print("✅ 模型加载测试通过")
            
            # 测试推理
            test_audio = "./test_input.wav"
            if Path(test_audio).exists():
                output = manager.inference(test_audio, spk_id=0)
                print(f"✅ 推理测试通过: {output}")
    else:
        print("⚠️ 未找到测试模型文件")


if __name__ == "__main__":
    print("So-VITS-SVC 语音管理器")
    print("=" * 60)
    test_sovits()