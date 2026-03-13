#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音训练配置文件
Voice Training Configuration
"""

import json
from pathlib import Path

# 基础配置
BASE_CONFIG = {
    "training": {
        "model_name": "unicorn_voice",
        "model_type": "xtts_v2",
        "epochs": 100,
        "batch_size": 8,
        "learning_rate": 0.0001,
        "use_gpu": True,
        "mixed_precision": True,
        "data_augmentation": True,
        "sample_rate": 22050,
        "n_mels": 80,
        "hop_length": 256,
        "win_length": 1024,
        "save_every": 10,
        "validate_every": 5,
        "early_stopping_patience": 20
    },
    "vits": {
        "model_name": "unicorn_vits",
        "n_speakers": 1,
        "sampling_rate": 22050,
        "filter_length": 1024,
        "hop_length": 256,
        "win_length": 1024,
        "n_mel_channels": 80,
        "mel_fmin": 0.0,
        "mel_fmax": None,
        "epochs": 10000,
        "batch_size": 16,
        "learning_rate": 0.0002,
        "adam_betas": [0.8, 0.99],
        "eps": 1e-9,
        "lr_decay": 0.999875,
        "segment_size": 8192,
        "c_mel": 45,
        "c_kl": 1.0
    },
    "audio": {
        "supported_formats": [".wav", ".mp3", ".flac", ".m4a", ".ogg"],
        "max_duration": 10,  # 秒
        "min_duration": 0.5,  # 秒
        "target_sample_rate": 22050,
        "normalize": True,
        "trim_silence": True,
        "silence_threshold": 20  # dB
    },
    "text": {
        "max_length": 1000,
        "cleaners": ["chinese_cleaners"],
        "supported_languages": ["zh", "en"]
    }
}

def get_config(name=None):
    """获取配置"""
    if name:
        return BASE_CONFIG.get(name, {})
    return BASE_CONFIG

def save_config_to_file(name, path=None):
    """保存配置到文件"""
    try:
        config = get_config(name)
        if not config:
            return False
        
        if not path:
            path = Path(__file__).parent / f"{name}_config.json"
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

def load_config_from_file(path):
    """从文件加载配置"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置失败: {e}")
        return None

def validate_config():
    """验证配置"""
    errors = []
    
    # 验证训练配置
    training_config = get_config("training")
    if training_config.get("batch_size", 0) <= 0:
        errors.append("批次大小必须大于0")
    
    if training_config.get("learning_rate", 0) <= 0:
        errors.append("学习率必须大于0")
    
    # 验证音频配置
    audio_config = get_config("audio")
    if audio_config.get("max_duration", 0) <= audio_config.get("min_duration", 0):
        errors.append("最大时长必须大于最小时长")
    
    return errors

# 预设配置
PRESET_CONFIGS = {
    "fast": {
        "epochs": 50,
        "batch_size": 16,
        "learning_rate": 0.001,
        "description": "快速训练，适合测试"
    },
    "balanced": {
        "epochs": 100,
        "batch_size": 8,
        "learning_rate": 0.0001,
        "description": "平衡配置，推荐使用"
    },
    "quality": {
        "epochs": 200,
        "batch_size": 4,
        "learning_rate": 0.00005,
        "description": "高质量训练，耗时较长"
    }
}