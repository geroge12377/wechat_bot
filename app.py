# app.py - 独角兽AI聊天机器人主程序（支持VITS语音模型）
import os
import sys
import time
import requests
import json
import random
import base64
import tempfile
import hashlib
from flask import Flask, jsonify, send_from_directory, request, send_file
from datetime import datetime
import sqlite3
import wave
import io
from pathlib import Path

# 使用相对路径
BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "static"
VOICE_MODELS_DIR = BASE_DIR / "voice_models"
AUDIO_CACHE_DIR = BASE_DIR / "audio_cache"
UPLOADS_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "unicorn_data.db"

# 创建必要的目录
for directory in [STATIC_DIR, VOICE_MODELS_DIR, AUDIO_CACHE_DIR, UPLOADS_DIR]:
    directory.mkdir(exist_ok=True)

# 语音功能相关导入
try:
    import torch
    import numpy as np
    import soundfile as sf
    from scipy.io import wavfile
    import librosa
    print("✅ 基础音频库已加载")
    AUDIO_LIBS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 基础音频库未完全安装: {e}")
    AUDIO_LIBS_AVAILABLE = False

# TTS相关导入（支持多种后端）
TTS_BACKEND = None
try:
    # 优先尝试导入VITS
    import vits
    from vits.models import SynthesizerTrn
    from vits.text import text_to_sequence
    print("✅ VITS模型库已加载")
    TTS_BACKEND = "vits"
except ImportError:
    try:
        # 备用：Coqui TTS
        from TTS.api import TTS
        print("✅ Coqui TTS已加载（备用）")
        TTS_BACKEND = "coqui"
    except ImportError:
        print("⚠️ 未找到TTS库，语音合成功能将不可用")
        TTS_BACKEND = None

# 语音识别导入
try:
    import speech_recognition as sr
    import pydub
    from pydub import AudioSegment
    print("✅ 语音识别库已加载")
    STT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 语音识别库未安装: {e}")
    STT_AVAILABLE = False

# 初始化Flask应用
app = Flask(__name__, 
    static_folder=str(STATIC_DIR), 
    static_url_path='/static'
)

# API配置 - 使用 VectorEngine (Gemini)
API_BASE_URL = "https://api.vectorengine.ai/v1/chat/completions"
API_KEY = "sk-cjeKQXbJvi1cLQ7O7a0L43nvJGZvcJnNvQve8T0urA4FdjrA"
API_MODEL = "gemini-3.1-flash-lite-preview"

# ======================
# 增强的语音管理器（支持VITS）
# ======================
class EnhancedVoiceManager:
    def __init__(self):
        self.voice_models = {}
        self.current_model = None
        self.current_backend = TTS_BACKEND
        self.is_voice_enabled = False
        
        # VITS相关配置
        self.vits_config = None
        self.vits_model = None
        
        # Coqui TTS相关
        self.coqui_tts = None
        
        # 语音识别器
        self.recognizer = None
        
        # 初始化系统
        self.init_voice_system()
    
    def init_voice_system(self):
        """初始化语音系统"""
        try:
            print("🎙️ 正在初始化语音系统...")
            
            # 扫描已有的语音模型
            self.scan_voice_models()
            
            # 初始化默认TTS
            if self.current_backend == "vits":
                self.init_vits_default()
            elif self.current_backend == "coqui":
                self.init_coqui_default()
            
            # 初始化语音识别
            if STT_AVAILABLE:
                self.init_speech_recognition()
            
            self.is_voice_enabled = True
            print("✅ 语音系统初始化完成")
            
        except Exception as e:
            print(f"❌ 语音系统初始化失败: {str(e)}")
            self.is_voice_enabled = False
    
    def scan_voice_models(self):
        """扫描本地语音模型"""
        self.voice_models = {}
        
        # 扫描VITS模型
        vits_models = list(VOICE_MODELS_DIR.glob("*.pth"))
        for model_path in vits_models:
            model_name = model_path.stem
            config_path = model_path.with_suffix(".json")
            
            if config_path.exists():
                self.voice_models[model_name] = {
                    "type": "vits",
                    "model_path": str(model_path),
                    "config_path": str(config_path),
                    "loaded": False
                }
                print(f"📦 发现VITS模型: {model_name}")
        
        # 扫描其他格式的模型
        onnx_models = list(VOICE_MODELS_DIR.glob("*.onnx"))
        for model_path in onnx_models:
            model_name = model_path.stem
            self.voice_models[model_name] = {
                "type": "onnx",
                "model_path": str(model_path),
                "loaded": False
            }
            print(f"📦 发现ONNX模型: {model_name}")
    
    def init_vits_default(self):
        """初始化默认VITS模型"""
        try:
            # 检查是否有独角兽专用模型
            unicorn_model = self.voice_models.get("unicorn_voice")
            if unicorn_model and unicorn_model["type"] == "vits":
                self.load_vits_model("unicorn_voice")
            else:
                print("ℹ️ 未找到独角兽语音模型，等待导入...")
        except Exception as e:
            print(f"⚠️ VITS初始化失败: {str(e)}")
    
    def init_coqui_default(self):
        """初始化默认Coqui TTS"""
        try:
            # 使用中文模型
            self.coqui_tts = TTS(model_name="tts_models/zh-CN/baker/tacotron2-DDC-GST")
            print("✅ Coqui TTS中文模型已加载")
        except Exception as e:
            print(f"⚠️ Coqui TTS加载失败: {str(e)}")
    
    def init_speech_recognition(self):
        """初始化语音识别"""
        try:
            self.recognizer = sr.Recognizer()
            # 调整识别参数
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            print("✅ 语音识别系统已初始化")
        except Exception as e:
            print(f"❌ 语音识别初始化失败: {str(e)}")
    
    def load_vits_model(self, model_name):
        """加载VITS模型"""
        if model_name not in self.voice_models:
            return False
        
        model_info = self.voice_models[model_name]
        if model_info["type"] != "vits":
            return False
        
        try:
            import json
            
            # 加载配置
            with open(model_info["config_path"], 'r', encoding='utf-8') as f:
                self.vits_config = json.load(f)
            
            # 创建模型
            self.vits_model = SynthesizerTrn(
                len(self.vits_config["symbols"]),
                self.vits_config["data"]["filter_length"] // 2 + 1,
                self.vits_config["train"]["segment_size"] // self.vits_config["data"]["hop_length"],
                **self.vits_config["model"]
            )
            
            # 加载权重
            checkpoint = torch.load(model_info["model_path"], map_location='cpu')
            self.vits_model.load_state_dict(checkpoint['model'])
            self.vits_model.eval()
            
            model_info["loaded"] = True
            self.current_model = model_name
            print(f"✅ VITS模型 {model_name} 加载成功")
            return True
            
        except Exception as e:
            print(f"❌ VITS模型加载失败: {str(e)}")
            return False
    
    def text_to_speech(self, text, emotion="normal", speaker_id=0):
        """文本转语音（支持多种后端）"""
        try:
            if not self.is_voice_enabled:
                return None
            
            # 清理文本
            clean_text = self.clean_text_for_tts(text)
            if not clean_text:
                return None
            
            # 生成唯一文件名
            text_hash = hashlib.md5(f"{clean_text}_{emotion}_{speaker_id}".encode()).hexdigest()[:8]
            timestamp = int(time.time() * 1000)
            output_filename = f"unicorn_{emotion}_{text_hash}_{timestamp}.wav"
            output_path = AUDIO_CACHE_DIR / output_filename
            
            # 检查缓存
            cache_pattern = f"unicorn_{emotion}_{text_hash}_*.wav"
            cached_files = list(AUDIO_CACHE_DIR.glob(cache_pattern))
            if cached_files and cached_files[0].exists():
                print(f"📂 使用缓存音频: {cached_files[0].name}")
                return str(cached_files[0])
            
            # 使用VITS生成
            if self.current_backend == "vits" and self.vits_model:
                self._generate_vits_audio(clean_text, str(output_path), speaker_id)
            # 使用Coqui TTS生成
            elif self.current_backend == "coqui" and self.coqui_tts:
                self._generate_coqui_audio(clean_text, str(output_path))
            else:
                print("❌ 没有可用的TTS后端")
                return None
            
            # 应用情感效果
            if output_path.exists():
                self.apply_emotion_effects(str(output_path), emotion)
                return str(output_path)
            
            return None
            
        except Exception as e:
            print(f"❌ TTS生成失败: {str(e)}")
            return None
    
    def _generate_vits_audio(self, text, output_path, speaker_id=0):
        """使用VITS生成音频"""
        try:
            # 文本转序列
            text_norm = text_to_sequence(text, self.vits_config["data"]["text_cleaners"])
            text_norm = torch.LongTensor(text_norm)
            text_len = torch.LongTensor([len(text_norm)])
            
            # 生成音频
            with torch.no_grad():
                x = text_norm.unsqueeze(0)
                x_len = text_len
                sid = torch.LongTensor([speaker_id])
                
                audio = self.vits_model.infer(x, x_len, sid=sid, noise_scale=0.667, 
                                            noise_scale_w=0.8, length_scale=1.0)[0][0,0]
                audio = audio.cpu().numpy()
            
            # 保存音频
            sf.write(output_path, audio, self.vits_config["data"]["sampling_rate"])
            print(f"✅ VITS音频生成成功: {Path(output_path).name}")
            
        except Exception as e:
            print(f"❌ VITS生成失败: {str(e)}")
            raise
    
    def _generate_coqui_audio(self, text, output_path):
        """使用Coqui TTS生成音频"""
        try:
            self.coqui_tts.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=None,
                language="zh"
            )
            print(f"✅ Coqui音频生成成功: {Path(output_path).name}")
        except Exception as e:
            print(f"❌ Coqui生成失败: {str(e)}")
            raise
    
    def clean_text_for_tts(self, text):
        """清理文本用于TTS"""
        import re
        
        # 移除情感标记
        text = re.sub(r'\[.*?\]', '', text)
        
        # 移除动作描述
        text = re.sub(r'[（(].*?[)）]', '', text)
        
        # 移除特殊符号
        text = text.replace('✨', '').replace('...', '。').strip()
        
        # 确保文本不为空
        if not text or len(text.strip()) < 2:
            text = "呜，独角兽不知道说什么好了"
        
        return text
    
    def apply_emotion_effects(self, audio_path, emotion):
        """应用情感效果到音频"""
        if not AUDIO_LIBS_AVAILABLE:
            return
        
        try:
            # 情感参数
            emotion_params = {
                "normal": {"pitch_shift": 0, "speed": 1.0, "reverb": 0.1},
                "shy": {"pitch_shift": 2, "speed": 0.95, "reverb": 0.15},
                "happy": {"pitch_shift": 3, "speed": 1.05, "reverb": 0.2},
                "sad": {"pitch_shift": -2, "speed": 0.9, "reverb": 0.25},
                "excited": {"pitch_shift": 4, "speed": 1.1, "reverb": 0.3}
            }
            
            params = emotion_params.get(emotion, emotion_params["normal"])
            
            # 加载音频
            y, sr = librosa.load(audio_path, sr=None)
            
            # 音高变换
            if params["pitch_shift"] != 0:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=params["pitch_shift"])
            
            # 速度变换
            if params["speed"] != 1.0:
                y = librosa.effects.time_stretch(y, rate=params["speed"])
            
            # 添加混响效果（简单实现）
            if params["reverb"] > 0:
                # 创建简单的延迟效果模拟混响
                delay_samples = int(0.02 * sr)  # 20ms延迟
                reverb = np.zeros_like(y)
                reverb[delay_samples:] = y[:-delay_samples] * params["reverb"]
                y = y + reverb
            
            # 归一化
            y = y / np.max(np.abs(y)) * 0.95
            
            # 保存处理后的音频
            sf.write(audio_path, y, sr)
            
        except Exception as e:
            print(f"⚠️ 情感效果应用失败: {str(e)}")
    
    def speech_to_text(self, audio_file_path):
        """语音转文本"""
        if not self.recognizer:
            return None
        
        try:
            # 加载音频文件
            with sr.AudioFile(audio_file_path) as source:
                # 降噪
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
            
            # 尝试多种识别引擎
            text = None
            
            # 优先使用百度API（需要配置）
            try:
                text = self.recognizer.recognize_google(audio_data, language='zh-CN')
                print(f"✅ Google识别结果: {text}")
            except:
                # 备用：离线识别
                try:
                    text = self.recognizer.recognize_sphinx(audio_data, language='zh-CN')
                    print(f"✅ Sphinx识别结果: {text}")
                except:
                    pass
            
            return text
            
        except Exception as e:
            print(f"❌ 语音识别失败: {str(e)}")
            return None
    
    def import_vits_model(self, model_file_path, config_file_path, model_name="unicorn_voice"):
        """导入VITS模型"""
        try:
            # 复制模型文件
            model_dest = VOICE_MODELS_DIR / f"{model_name}.pth"
            config_dest = VOICE_MODELS_DIR / f"{model_name}.json"
            
            import shutil
            shutil.copy2(model_file_path, model_dest)
            shutil.copy2(config_file_path, config_dest)
            
            # 重新扫描模型
            self.scan_voice_models()
            
            # 加载新模型
            if self.load_vits_model(model_name):
                self.current_backend = "vits"
                return True, f"模型 {model_name} 导入成功"
            else:
                return False, "模型导入后加载失败"
                
        except Exception as e:
            return False, f"模型导入失败: {str(e)}"
    
    def get_voice_status(self):
        """获取语音系统状态"""
        return {
            "voice_enabled": self.is_voice_enabled,
            "backend": self.current_backend,
            "current_model": self.current_model,
            "available_models": list(self.voice_models.keys()),
            "tts_available": bool(self.vits_model or self.coqui_tts),
            "stt_available": bool(self.recognizer),
            "audio_cache_size": len(list(AUDIO_CACHE_DIR.glob("*.wav")))
        }
    
    def clear_audio_cache(self, max_age_hours=24):
        """清理音频缓存"""
        try:
            current_time = time.time()
            cleared_count = 0
            
            for audio_file in AUDIO_CACHE_DIR.glob("*.wav"):
                file_age_hours = (current_time - audio_file.stat().st_mtime) / 3600
                if file_age_hours > max_age_hours:
                    audio_file.unlink()
                    cleared_count += 1
            
            print(f"🗑️ 清理了 {cleared_count} 个过期音频文件")
            return cleared_count
            
        except Exception as e:
            print(f"❌ 清理缓存失败: {str(e)}")
            return 0

# 创建语音管理器实例
voice_manager = EnhancedVoiceManager() if AUDIO_LIBS_AVAILABLE else None

# ======================
# 数据库和好感度系统（保持原有功能）
# ======================
class RelationshipManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建关系数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationship_stats (
                id INTEGER PRIMARY KEY,
                affection INTEGER DEFAULT 50,
                intimacy INTEGER DEFAULT 50,
                level INTEGER DEFAULT 1,
                total_messages INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建对话记录表（增加语音字段）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                unicorn_reply TEXT,
                emotion TEXT,
                affection_change INTEGER DEFAULT 0,
                intimacy_change INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_voice BOOLEAN DEFAULT FALSE,
                voice_file_path TEXT,
                voice_backend TEXT
            )
        ''')
        
        # 检查是否需要插入初始数据
        cursor.execute('SELECT COUNT(*) FROM relationship_stats')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO relationship_stats (affection, intimacy, level, total_messages)
                VALUES (50, 50, 1, 0)
            ''')
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """获取当前关系数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT affection, intimacy, level, total_messages FROM relationship_stats WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'affection': result[0],
                'intimacy': result[1], 
                'level': result[2],
                'total_messages': result[3]
            }
        return {'affection': 50, 'intimacy': 50, 'level': 1, 'total_messages': 0}
    
    def update_stats(self, affection_change=0, intimacy_change=0):
        """更新关系数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前数据
        current_stats = self.get_stats()
        
        # 计算新数值
        new_affection = max(0, min(100, current_stats['affection'] + affection_change))
        new_intimacy = max(0, min(100, current_stats['intimacy'] + intimacy_change))
        new_total_messages = current_stats['total_messages'] + 1
        
        # 根据好感度和亲密度计算等级
        avg_relationship = (new_affection + new_intimacy) / 2
        new_level = min(100, max(1, int(avg_relationship / 10) + 1))
        
        # 更新数据库
        cursor.execute('''
            UPDATE relationship_stats 
            SET affection = ?, intimacy = ?, level = ?, total_messages = ?, last_updated = ?
            WHERE id = 1
        ''', (new_affection, new_intimacy, new_level, new_total_messages, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return {
            'affection': new_affection,
            'intimacy': new_intimacy,
            'level': new_level,
            'total_messages': new_total_messages,
            'affection_change': affection_change,
            'intimacy_change': intimacy_change
        }
    
    def save_chat_record(self, user_message, unicorn_reply, emotion, 
                        affection_change=0, intimacy_change=0, 
                        voice_file_path=None, voice_backend=None):
        """保存聊天记录（包含语音信息）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history 
            (user_message, unicorn_reply, emotion, affection_change, intimacy_change, 
             has_voice, voice_file_path, voice_backend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_message, unicorn_reply, emotion, affection_change, intimacy_change, 
              voice_file_path is not None, voice_file_path, voice_backend))
        
        conn.commit()
        conn.close()

# 创建关系管理器实例
relationship_manager = RelationshipManager()

# [保留原有的UnicornAI类，只修改语音相关部分]
class UnicornAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.chat_history = []
        self.unicorn_voice_lines = self.load_game_voice_lines()
        self.unicorn_knowledge = self.load_unicorn_knowledge()
        self.current_emotion = "普通"
        
        # 语音相关设置
        self.voice_enabled = voice_manager.is_voice_enabled if voice_manager else False
        
        # 系统提示
        system_prompt = f"""
你必须完全成为《碧蓝航线》中的独角兽。以下是你的核心设定和游戏中的真实语音台词：

【角色核心人格】
{self.unicorn_knowledge['core_personality']}

【真实游戏语音库】
{self.format_voice_lines(self.unicorn_voice_lines)}

【行为模式】
{self.unicorn_knowledge['behavior_patterns']}

【情感响应系统】
1. 初始情感状态：普通
2. 情感状态会根据对话内容自然变化：
   - 普通：日常对话状态
   - 害羞：当哥哥做出亲密举动时
   - 兴奋：遇到开心的事情时
   - 低落：感到难过或担忧时
   - 吃醋：哥哥提到其他女孩子时

【对话规则】
1. 严格使用游戏中出现的台词和表达方式
2. 回复必须包含角色动作描述，如"(抱紧优酱)"
3. 保持纯真柔弱语气
4. 优先使用游戏中的真实台词
5. 对"哥哥"的称呼必须一致
6. 每次回复前必须标注当前情感状态（格式：[情感状态]）
7. 情感状态会影响思考动作和说话风格
"""
        self.chat_history.append({"role": "system", "content": system_prompt})
        
        # 添加游戏中的初始问候
        initial_greeting = self.select_voice_line("login")
        self.chat_history.append({"role": "assistant", "content": initial_greeting})
    
    def load_game_voice_lines(self):
        """从游戏中提取独角兽的真实语音台词"""
        return {
            "login": [
                "（听到脚步声，从门后探出半个头）哥、哥哥...你回来啦...（低头捏优酱耳朵）独角兽和优酱...等了你一下午呢...的说",
                "（抱着优酱小跑过来）哥哥！欢迎回来...优酱今天也很乖哦...",
                "（揉着眼睛从沙发上起来）啊...哥哥回来了？对、对不起...独角兽不小心睡着了..."
            ],
            "daily": [
                "（轻轻晃优酱）今天港区的风很舒服呢...哥哥要不要一起散步？优酱说想去海边...",
                "（低头玩手指）那个...哥哥...能教独角兽画画吗？优酱也想被画得可爱一点...",
                "（突然想到什么）啊！哥哥！今天有好好吃饭吗？独角兽做了小饼干...的说"
            ],
            "affection": [
                "（脸红低头）哥哥的手...好温暖...优酱说也想被摸摸头...",
                "（突然抱住手臂）今、今天可以多陪独角兽一会吗？就一会会...",
                "（把优酱举到面前）优酱说...最喜欢哥哥了...呜...（害羞地藏起脸）"
            ],
            "jealous": [
                "（抱紧优酱，声音变小）哥哥...刚才是在和其他人说话吗？优酱说...有点寂寞...的说",
                "（低头玩优酱耳朵）那个姐姐...比独角兽更可爱吗？...独角兽也会努力的...",
                "（眼含泪光）哥哥...不要不理独角兽...优酱说要乖乖的..."
            ],
            "mixed": [
                "（抱紧优酱）今天的演习...独角兽很努力了...的说！哥哥有看到吗？",
                "（轻轻戳优酱）优酱说...哥哥最近好像很忙...的说...都没时间陪我们玩了...",
                "（歪头思考）嗯...这个蛋糕的味道...优酱说比上次那家店的好吃呢..."
            ]
        }
    
    def select_voice_line(self, category=None):
        """从指定类别的游戏台词中随机选择一句"""
        if not category:
            category = random.choice(list(self.unicorn_voice_lines.keys()))
        
        return random.choice(self.unicorn_voice_lines.get(category, ["（抱紧优酱）呜...独角兽不知道说什么好了..."])) + " ✨"

    def format_voice_lines(self, lines_dict):
        """格式化游戏台词用于系统提示"""
        formatted = ""
        for category, lines in lines_dict.items():
            formatted += f"\n【{category.upper()}】\n"
            for i, line in enumerate(lines, 1):
                formatted += f"{i}. {line}\n"
        return formatted
    
    def load_unicorn_knowledge(self):
        """独角兽角色设定知识库"""
        return {
            "core_personality": (
                "纯真善良的妹妹型角色，心智年龄8-10岁。极度依赖指挥官(哥哥)，"
                "将粉色玩偶'优酱'视为最重要的伙伴。性格内向害羞，但在哥哥面前会展现柔弱又粘人的一面。"
                "有轻微占有欲，不喜欢哥哥关注其他女孩子。"
            ),
            "behavior_patterns": (
                "【日常】\n"
                "- 紧张时：捏优酱耳朵、低头脸红\n"
                "- 开心时：轻轻摇晃优酱，哼歌\n"
                "- 困惑时：歪头眨眼，优酱举到脸前\n\n"
                "【占有欲表现】\n"
                "当哥哥提到其他女性时：\n"
                "1. 抱紧优酱，声音带鼻音\n"
                "2. 小声表达不安\n"
                "3. 需要安抚\n"
            )
        }
    
    def calculate_relationship_change(self, user_input):
        """根据用户输入计算好感度和亲密度变化"""
        affection_change = 0
        intimacy_change = 0
        
        # 正面词汇增加好感度
        positive_words = ["喜欢", "爱", "可爱", "漂亮", "温柔", "乖", "棒", "厉害", "好", "赞"]
        negative_words = ["讨厌", "烦", "笨", "坏", "不好", "难看"]
        intimate_words = ["抱", "亲", "摸", "贴贴", "一起", "陪", "想你", "想念"]
        
        # 计算好感度变化
        for word in positive_words:
            if word in user_input:
                affection_change += 2
        
        for word in negative_words:
            if word in user_input:
                affection_change -= 3
        
        # 计算亲密度变化
        for word in intimate_words:
            if word in user_input:
                intimacy_change += 3
                affection_change += 1
        
        # 普通对话也会小幅增加关系
        if len(user_input) > 0 and affection_change == 0 and intimacy_change == 0:
            affection_change = 1
            intimacy_change = 1
        
        return affection_change, intimacy_change
    
    def update_emotion(self, user_input, stats):
        """根据用户输入和关系数据更新情感状态"""
        affection = stats['affection']
        intimacy = stats['intimacy']
        
        # 基础情感判断
        if "抱" in user_input or "亲" in user_input or "摸" in user_input:
            if intimacy >= 60:
                self.current_emotion = "幸福"
            else:
                self.current_emotion = "害羞"
        elif "!" in user_input or "！" in user_input or "开心" in user_input:
            self.current_emotion = "兴奋"
        elif "其他" in user_input or "别人" in user_input or "女孩" in user_input:
            self.current_emotion = "吃醋"
        elif "不" in user_input or "别" in user_input or "难过" in user_input:
            self.current_emotion = "低落"
        else:
            # 根据好感度决定默认情感
            if affection >= 80:
                self.current_emotion = "开心"
            elif affection >= 60:
                self.current_emotion = "温和"
            elif affection >= 40:
                self.current_emotion = "普通"
            else:
                self.current_emotion = "紧张"
    
    def generate_reply(self, user_input, enable_voice=False):
        """生成回复（支持语音）"""
        # 获取当前关系数据
        current_stats = relationship_manager.get_stats()
        
        # 计算关系变化
        affection_change, intimacy_change = self.calculate_relationship_change(user_input)
        
        # 更新关系数据
        updated_stats = relationship_manager.update_stats(affection_change, intimacy_change)
        
        # 更新情感状态
        self.update_emotion(user_input, updated_stats)
        
        # 生成文本回复
        ai_reply = self.generate_text_reply(user_input, updated_stats)
        
        # 生成语音回复
        voice_file_path = None
        voice_backend = None
        if enable_voice and self.voice_enabled and voice_manager:
            # 根据亲密度选择speaker_id（如果使用VITS多说话人模型）
            speaker_id = 0  # 默认说话人
            if updated_stats['intimacy'] >= 80:
                speaker_id = 1  # 更亲密的语调（如果模型支持）
            
            voice_file_path = voice_manager.text_to_speech(
                text=ai_reply,
                emotion=self.current_emotion.lower(),
                speaker_id=speaker_id
            )
            voice_backend = voice_manager.current_backend
        
        # 保存聊天记录
        relationship_manager.save_chat_record(
            user_input, ai_reply, self.current_emotion,
            affection_change, intimacy_change, voice_file_path, voice_backend
        )
        
        return ai_reply, updated_stats, voice_file_path
    
    def generate_text_reply(self, user_input, stats):
        """生成文本回复"""
        # 添加用户输入到历史
        self.chat_history.append({"role": "user", "content": user_input})
        
        # 情感状态标记
        emotion_prefix = f"[{self.current_emotion}] "
        
        try:
            # 尝试API增强回复
            api_reply = self.get_api_enhanced_reply(user_input, stats)
            if api_reply and len(api_reply) > 10:
                ai_reply = api_reply
            else:
                # 使用预设回复
                ai_reply = self.select_voice_line("mixed")
                
        except Exception as e:
            print(f"回复生成失败: {str(e)}")
            ai_reply = random.choice([
                "（突然抱紧优酱）呜...通讯好像出问题了...哥哥能检查一下吗？...的说 ✨",
                "（困惑地歪头）优酱...刚才的信号好奇怪...哥哥听到了吗？ ✨",
                "（低头戳手指）对、对不起...独角兽好像搞砸了什么... ✨"
            ])
        
        # 添加到历史记录
        self.chat_history.append({"role": "assistant", "content": ai_reply})
        
        # 确保回复包含情感状态
        if not ai_reply.startswith("["):
            ai_reply = emotion_prefix + ai_reply
        
        return ai_reply
    
    def get_api_enhanced_reply(self, user_input, stats):
        """使用API增强回复"""
        enhanced_prompt = f"""
当前关系状态：
- 好感度：{stats['affection']}/100
- 亲密度：{stats['intimacy']}/100  
- 等级：{stats['level']}
- 总对话数：{stats['total_messages']}

请根据当前关系状态调整独角兽的回应方式。好感度和亲密度越高，回应应该越亲昵和主动。
"""
        
        enhanced_messages = [
            {"role": "system", "content": self.chat_history[0]["content"] + enhanced_prompt},
            {"role": "user", "content": user_input}
        ]
        
        payload = {
            "model": API_MODEL,
            "messages": enhanced_messages,
            "temperature": 0.35,
            "max_tokens": 250,
            "top_p": 0.9,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                API_BASE_URL,
                headers=headers,
                json=payload,
                timeout=45
            )
            
            # 添加更好的错误处理
            if response.status_code != 200:
                print(f"API错误: {response.status_code} - {response.text}")
                return None
                
            # 检查响应是否为JSON
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                print(f"无效的响应类型: {content_type}")
                print(f"响应内容: {response.text[:200]}")  # 打印前200个字符
                return None
                
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            print(f"API请求异常: {str(e)}")
            
        return None

# 创建独角兽AI实例
unicorn_ai = UnicornAI(API_KEY)

# ======================
# Web路由
# ======================
@app.route('/')
def index():
    """首页路由"""
    index_file = STATIC_DIR / 'index.html'
    
    if index_file.exists():
        return send_from_directory(str(STATIC_DIR), 'index.html')
    
    # 备用：检查其他可能的位置
    alternative_paths = [
        BASE_DIR / 'index.html',
        Path.cwd() / 'static' / 'index.html',
        Path.cwd() / 'index.html'
    ]
    
    for alt_path in alternative_paths:
        if alt_path.exists():
            print(f"✅ 找到前端文件: {alt_path}")
            return send_from_directory(str(alt_path.parent), alt_path.name)
    
    return """
    <h1>前端文件未找到</h1>
    <p>请确保index.html文件位于static目录中</p>
    """, 404

@app.route('/generate_reply', methods=['POST'])
def generate_reply():
    """处理聊天请求（兼容原版+语音）"""
    try:
        data = request.json
        if not data or 'user_input' not in data:
            return jsonify({'error': '无效请求'}), 400
        
        user_input = data['user_input']
        enable_voice = data.get('enable_voice', False)
        
        reply, updated_stats, voice_file_path = unicorn_ai.generate_reply(user_input, enable_voice)
        
        # 如果有语音文件，转换为base64
        voice_data = None
        if voice_file_path and Path(voice_file_path).exists():
            try:
                with open(voice_file_path, 'rb') as f:
                    voice_data = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"语音文件读取失败: {str(e)}")
        
        return jsonify({
            'reply': reply,
            'emotion': unicorn_ai.current_emotion,
            'stats': updated_stats,
            'voice_data': voice_data,
            'voice_available': voice_data is not None,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'reply': '[普通] （抱紧优酱）呜...独角兽好像遇到了一些问题...的说 ✨',
            'emotion': '普通',
            'stats': relationship_manager.get_stats(),
            'voice_data': None,
            'voice_available': False
        }), 500

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    """语音转文本"""
    try:
        if not voice_manager:
            return jsonify({'error': '语音系统未启用'}), 500
            
        if 'audio' not in request.files:
            return jsonify({'error': '没有音频文件'}), 400
        
        audio_file = request.files['audio']
        
        # 保存临时音频文件
        temp_path = UPLOADS_DIR / f"temp_stt_{int(time.time())}.wav"
        audio_file.save(str(temp_path))
        
        # 识别语音
        text = voice_manager.speech_to_text(str(temp_path))
        
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
        
        if text:
            return jsonify({
                'status': 'success',
                'text': text
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '语音识别失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/voice_status', methods=['GET'])
def voice_status():
    """获取语音系统状态"""
    try:
        if voice_manager:
            status = voice_manager.get_voice_status()
        else:
            status = {
                "voice_enabled": False,
                "backend": None,
                "current_model": None,
                "available_models": [],
                "tts_available": False,
                "stt_available": False,
                "audio_cache_size": 0
            }
        
        return jsonify({
            'status': 'success',
            'voice_system': status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/import_voice_model', methods=['POST'])
def import_voice_model():
    """导入训练好的VITS语音模型"""
    try:
        if not voice_manager:
            return jsonify({'error': '语音系统未启用'}), 500
        
        # 检查必需文件
        if 'model_file' not in request.files or 'config_file' not in request.files:
            return jsonify({'error': '需要同时上传模型文件(.pth)和配置文件(.json)'}), 400
        
        model_file = request.files['model_file']
        config_file = request.files['config_file']
        model_name = request.form.get('model_name', 'unicorn_voice')
        
        # 保存临时文件
        temp_model = UPLOADS_DIR / f"temp_{model_file.filename}"
        temp_config = UPLOADS_DIR / f"temp_{config_file.filename}"
        
        model_file.save(str(temp_model))
        config_file.save(str(temp_config))
        
        # 导入模型
        success, message = voice_manager.import_vits_model(
            str(temp_model), 
            str(temp_config), 
            model_name
        )
        
        # 清理临时文件
        temp_model.unlink(missing_ok=True)
        temp_config.unlink(missing_ok=True)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'model_name': model_name
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/clear_audio_cache', methods=['POST'])
def clear_audio_cache():
    """清理音频缓存"""
    try:
        if not voice_manager:
            return jsonify({'error': '语音系统未启用'}), 500
        
        max_age_hours = request.json.get('max_age_hours', 24) if request.json else 24
        cleared_count = voice_manager.clear_audio_cache(max_age_hours)
        
        return jsonify({
            'status': 'success',
            'message': f'清理了 {cleared_count} 个过期音频文件',
            'cleared_count': cleared_count
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_stats', methods=['GET'])
def get_stats():
    """获取当前关系数据"""
    try:
        stats = relationship_manager.get_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test_api():
    """系统状态测试"""
    try:
        stats = relationship_manager.get_stats()
        voice_status = voice_manager.get_voice_status() if voice_manager else {"voice_enabled": False}
        
        # 检查各个目录
        directories_status = {
            'static': STATIC_DIR.exists(),
            'voice_models': VOICE_MODELS_DIR.exists(),
            'audio_cache': AUDIO_CACHE_DIR.exists(),
            'uploads': UPLOADS_DIR.exists()
        }
        
        return jsonify({
            'status': 'success',
            'message': '系统运行正常',
            'system_info': {
                'base_dir': str(BASE_DIR),
                'directories': directories_status,
                'database': '数据库连接正常',
                'relationship_system': '关系系统运行正常',
                'voice_system': voice_status,
                'current_stats': stats
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'系统错误: {str(e)}'
        }), 500

# ======================
# 添加缺失的路由
# ======================

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    """重置关系数据到初始状态"""
    try:
        # 重置数据库中的关系数据
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE relationship_stats 
            SET affection = 50, intimacy = 50, level = 1, total_messages = 0, last_updated = ?
            WHERE id = 1
        ''', (datetime.now(),))
        
        conn.commit()
        conn.close()
        
        # 获取重置后的数据
        reset_stats = relationship_manager.get_stats()
        
        return jsonify({
            'status': 'success',
            'stats': reset_stats,
            'message': '关系数据已重置'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/admin_control', methods=['POST'])
def admin_control():
    """管理员控制接口 - 修改关系数据"""
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': '无效请求'}), 400
        
        # 验证管理员密码
        password = data.get('password', '')
        if password != '1314':  # 根据前端代码，密码是1314
            return jsonify({'status': 'error', 'message': '密码错误'}), 403
        
        # 获取要修改的数据
        affection = int(data.get('affection', 50))
        intimacy = int(data.get('intimacy', 50))  
        level = int(data.get('level', 1))
        
        # 验证数据范围
        affection = max(0, min(100, affection))
        intimacy = max(0, min(100, intimacy))
        level = max(1, min(100, level))
        
        # 更新数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE relationship_stats 
            SET affection = ?, intimacy = ?, level = ?, last_updated = ?
            WHERE id = 1
        ''', (affection, intimacy, level, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # 获取更新后的完整数据
        updated_stats = relationship_manager.get_stats()
        
        return jsonify({
            'status': 'success',
            'stats': updated_stats,
            'message': '数据更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/chat_history', methods=['GET'])
def get_chat_history():
    """获取聊天历史记录"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, unicorn_reply, emotion, affection_change, 
                   intimacy_change, timestamp, has_voice, voice_file_path
            FROM chat_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'user_message': row[0],
                'unicorn_reply': row[1],
                'emotion': row[2],
                'affection_change': row[3],
                'intimacy_change': row[4],
                'timestamp': row[5],
                'has_voice': row[6],
                'voice_file_path': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/export_data', methods=['GET'])
def export_data():
    """导出所有数据（聊天记录和关系数据）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取关系数据
        cursor.execute('SELECT * FROM relationship_stats WHERE id = 1')
        relationship = cursor.fetchone()
        
        # 获取聊天历史
        cursor.execute('SELECT * FROM chat_history ORDER BY timestamp')
        chat_history = cursor.fetchall()
        
        conn.close()
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'relationship_stats': {
                'affection': relationship[1] if relationship else 50,
                'intimacy': relationship[2] if relationship else 50,
                'level': relationship[3] if relationship else 1,
                'total_messages': relationship[4] if relationship else 0
            },
            'chat_history': [
                {
                    'id': row[0],
                    'user_message': row[1],
                    'unicorn_reply': row[2],
                    'emotion': row[3],
                    'affection_change': row[4],
                    'intimacy_change': row[5],
                    'timestamp': row[6],
                    'has_voice': row[7],
                    'voice_file_path': row[8] if len(row) > 8 else None,
                    'voice_backend': row[9] if len(row) > 9 else None
                }
                for row in chat_history
            ]
        }
        
        return jsonify({
            'status': 'success',
            'data': export_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ======================
# 微信机器人 API 接口
# ======================
@app.route('/api/synthesize', methods=['POST'])
def api_synthesize():
    """为微信机器人提供语音合成服务"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice_enabled = data.get('voice_enabled', True)

        if not text:
            return jsonify({'error': '文本不能为空'}), 400

        if not voice_enabled or not voice_manager or not voice_manager.is_voice_enabled:
            return jsonify({'error': '语音功能未启用'}), 503

        # 生成语音
        audio_data = voice_manager.synthesize(text)

        if audio_data is None:
            return jsonify({'error': '语音生成失败'}), 500

        # 返回音频文件
        return send_file(
            io.BytesIO(audio_data),
            mimetype='audio/wav',
            as_attachment=True,
            download_name='voice.wav'
        )

    except Exception as e:
        print(f"API 语音合成错误: {e}")
        return jsonify({'error': str(e)}), 500

# ======================
# 应用启动
# ======================
if __name__ == '__main__':
    print("=" * 70)
    print("      碧蓝航线 - 独角兽语音聊天系统 v5.0 (VITS增强版)")
    print(f"      基础目录: {BASE_DIR}")
    print("=" * 70)
    
    # 系统状态检查
    print(f"数据库: {'✅ 正常' if DB_PATH.exists() else '⚠️ 将自动创建'}")
    
    if voice_manager:
        voice_status = voice_manager.get_voice_status()
        print(f"语音功能: {'✅ 启用' if voice_status['voice_enabled'] else '❌ 禁用'}")
        print(f"TTS后端: {voice_status['backend'] or '无'}")
        print(f"当前模型: {voice_status['current_model'] or '无'}")
        print(f"可用模型: {', '.join(voice_status['available_models']) or '无'}")
        print(f"音频缓存: {voice_status['audio_cache_size']} 个文件")
    else:
        print("语音功能: ❌ 依赖库未安装")
    
    print("\n功能特性:")
    print("✅ 1. 基础聊天对话")
    print("✅ 2. 关系数据系统")
    print("✅ 3. VITS语音合成")
    print("✅ 4. 语音转文本 (STT)")
    print("✅ 5. 情感语音效果")
    print("✅ 6. 自定义VITS模型导入")
    print("✅ 7. 音频缓存管理")
    
    print(f"\n服务端点:")
    print("前端界面: http://localhost:5000")
    print("系统状态: http://localhost:5000/test")
    print("语音状态: http://localhost:5000/voice_status")
    print("模型导入: http://localhost:5000/import_voice_model")
    print("缓存清理: http://localhost:5000/clear_audio_cache")
    
    print("\nVITS模型导入说明:")
    print("1. 准备.pth模型文件和.json配置文件")
    print("2. 通过/import_voice_model接口上传")
    print("3. 模型将自动加载并启用")
    
    print("=" * 70)
    
    app.run(debug=True, port=5000, host='0.0.0.0')