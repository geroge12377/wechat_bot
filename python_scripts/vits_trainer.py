#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VITS语音训练模块
VITS Voice Training Module for Unicorn AI
"""

import os
import json
import time
import torch
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# VITS相关导入
try:
    from vits import commons
    from vits import utils
    from vits.models import SynthesizerTrn
    from vits.text import text_to_sequence, _clean_text
    from vits.mel_processing import spectrogram_torch
    from vits.data_utils import TextAudioLoader, TextAudioCollate, DistributedBucketSampler
    from torch.utils.data import DataLoader
    import torch.nn.functional as F
    print("✅ VITS训练库加载成功")
    VITS_AVAILABLE = True
except ImportError as e:
    print(f"❌ VITS训练库缺失: {e}")
    print("请安装: git clone https://github.com/jaywalnut310/vits.git")
    VITS_AVAILABLE = False

# 音频处理库
try:
    import librosa
    import soundfile as sf
    import scipy.signal
    from scipy.io import wavfile
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 音频处理库缺失: {e}")
    AUDIO_PROCESSING_AVAILABLE = False

# 使用相对路径
BASE_DIR = Path(__file__).parent.resolve()
VITS_CONFIG_DIR = BASE_DIR / "vits_configs"
VITS_TRAINING_DIR = BASE_DIR / "vits_training_data"
VITS_CHECKPOINTS_DIR = BASE_DIR / "vits_checkpoints"

# 创建必要目录
for directory in [VITS_CONFIG_DIR, VITS_TRAINING_DIR, VITS_CHECKPOINTS_DIR]:
    directory.mkdir(exist_ok=True)

# ======================
# VITS训练配置
# ======================
@dataclass
class VITSTrainingConfig:
    """VITS训练配置"""
    # 模型配置
    model_name: str = "unicorn_vits"
    n_speakers: int = 1  # 说话人数量
    
    # 训练参数
    epochs: int = 10000
    batch_size: int = 16
    learning_rate: float = 2e-4
    lr_decay: float = 0.999875
    adam_betas: Tuple[float, float] = (0.8, 0.99)
    eps: float = 1e-9
    
    # 音频参数
    sampling_rate: int = 22050
    filter_length: int = 1024
    hop_length: int = 256
    win_length: int = 1024
    n_mel_channels: int = 80
    mel_fmin: float = 0.0
    mel_fmax: float = None
    
    # 模型参数
    inter_channels: int = 192
    hidden_channels: int = 192
    filter_channels: int = 768
    n_heads: int = 2
    n_layers: int = 6
    kernel_size: int = 3
    p_dropout: float = 0.1
    resblock: str = "1"
    resblock_kernel_sizes: List[int] = None
    resblock_dilation_sizes: List[List[int]] = None
    
    # 训练设置
    fp16_run: bool = True
    eval_interval: int = 1000
    log_interval: int = 100
    save_interval: int = 5000
    warmup_epochs: int = 0
    c_mel: int = 45
    c_kl: float = 1.0
    
    def __post_init__(self):
        if self.resblock_kernel_sizes is None:
            self.resblock_kernel_sizes = [3, 7, 11]
        if self.resblock_dilation_sizes is None:
            self.resblock_dilation_sizes = [[1, 3, 5], [1, 3, 5], [1, 3, 5]]

# ======================
# 数据预处理器
# ======================
class VITSDataPreprocessor:
    """VITS数据预处理器"""
    
    def __init__(self, config: VITSTrainingConfig):
        self.config = config
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger('VITSPreprocessor')
        logger.setLevel(logging.INFO)
        return logger
    
    def prepare_dataset(self, audio_files: List[Path], text_files: List[Path], 
                       output_dir: Path) -> Tuple[bool, str]:
        """准备VITS训练数据集"""
        try:
            output_dir.mkdir(exist_ok=True)
            
            # 创建文件列表
            filelist = []
            processed_count = 0
            
            for audio_path, text_path in zip(audio_files, text_files):
                try:
                    # 读取文本
                    with open(text_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                    
                    # 清理文本
                    text = self._clean_text_for_training(text)
                    
                    # 处理音频
                    processed_audio_path = output_dir / f"{audio_path.stem}_processed.wav"
                    success = self._process_audio(audio_path, processed_audio_path)
                    
                    if success:
                        # 添加到文件列表（格式：音频路径|文本）
                        filelist.append(f"{processed_audio_path}|{text}")
                        processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理文件失败 {audio_path}: {e}")
                    continue
            
            # 保存文件列表
            train_list_path = output_dir / "train_filelist.txt"
            val_list_path = output_dir / "val_filelist.txt"
            
            # 划分训练集和验证集（90:10）
            split_idx = int(len(filelist) * 0.9)
            train_list = filelist[:split_idx]
            val_list = filelist[split_idx:]
            
            with open(train_list_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(train_list))
            
            with open(val_list_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(val_list))
            
            self.logger.info(f"数据预处理完成: {processed_count}个样本")
            self.logger.info(f"训练集: {len(train_list)}, 验证集: {len(val_list)}")
            
            return True, f"成功处理 {processed_count} 个音频样本"
            
        except Exception as e:
            return False, f"数据预处理失败: {str(e)}"
    
    def _clean_text_for_training(self, text: str) -> str:
        """清理训练文本"""
        import re
        
        # 移除括号内容
        text = re.sub(r'[（(].*?[)）]', '', text)
        
        # 移除特殊符号
        text = re.sub(r'[【】\[\]「」『』《》〈〉]', '', text)
        
        # 移除多余的标点
        text = re.sub(r'[。，！？、]+', '，', text)
        text = re.sub(r'[\.。]+', '。', text)
        
        # 移除表情符号
        text = re.sub(r'[^\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\s\w，。！？]', '', text)
        
        # 标准化空格
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _process_audio(self, input_path: Path, output_path: Path) -> bool:
        """处理音频文件"""
        if not AUDIO_PROCESSING_AVAILABLE:
            return False
        
        try:
            # 加载音频
            audio, sr = librosa.load(str(input_path), sr=self.config.sampling_rate)
            
            # 去除静音
            audio = self._trim_silence(audio, sr)
            
            # 标准化音量
            audio = librosa.util.normalize(audio)
            
            # 限制长度（10秒）
            max_length = sr * 10
            if len(audio) > max_length:
                audio = audio[:max_length]
            
            # 添加少量静音边界
            silence_length = int(0.1 * sr)  # 0.1秒
            audio = np.concatenate([
                np.zeros(silence_length),
                audio,
                np.zeros(silence_length)
            ])
            
            # 保存处理后的音频
            sf.write(str(output_path), audio, sr)
            
            return True
            
        except Exception as e:
            self.logger.error(f"音频处理失败: {e}")
            return False
    
    def _trim_silence(self, audio: np.ndarray, sr: int, 
                     top_db: int = 20, frame_length: int = 2048) -> np.ndarray:
        """去除音频静音"""
        try:
            # 使用librosa的trim功能
            trimmed, _ = librosa.effects.trim(
                audio, 
                top_db=top_db,
                frame_length=frame_length,
                hop_length=frame_length//4
            )
            return trimmed
        except:
            return audio

# ======================
# VITS训练器
# ======================
class VITSTrainer:
    """VITS语音训练器"""
    
    def __init__(self, config: VITSTrainingConfig):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger = self._setup_logger()
        
        # 模型组件
        self.model = None
        self.optimizer = None
        self.scheduler = None
        
        # 数据加载器
        self.train_loader = None
        self.eval_loader = None
        
        # 训练状态
        self.global_step = 0
        self.epoch = 0
        
    def _setup_logger(self):
        logger = logging.getLogger(f'VITSTrainer_{self.config.model_name}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 文件处理器
            log_file = BASE_DIR / "logs" / f"vits_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
        
        return logger
    
    def build_model(self) -> bool:
        """构建VITS模型"""
        if not VITS_AVAILABLE:
            return False
        
        try:
            # 创建模型配置
            hps = self._create_hparams()
            
            # 构建生成器（合成器）
            self.model = SynthesizerTrn(
                len(hps.symbols),
                hps.data.filter_length // 2 + 1,
                hps.train.segment_size // hps.data.hop_length,
                n_speakers=hps.data.n_speakers,
                **hps.model
            ).to(self.device)
            
            # 构建优化器
            self.optimizer = torch.optim.AdamW(
                self.model.parameters(),
                lr=self.config.learning_rate,
                betas=self.config.adam_betas,
                eps=self.config.eps
            )
            
            # 学习率调度器
            self.scheduler = torch.optim.lr_scheduler.ExponentialLR(
                self.optimizer,
                gamma=self.config.lr_decay
            )
            
            self.logger.info("VITS模型构建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"模型构建失败: {e}")
            return False
    
    def _create_hparams(self):
        """创建超参数配置"""
        hps = type('HParams', (), {})()
        
        # 数据配置
        hps.data = type('HParams', (), {})()
        hps.data.training_files = str(VITS_TRAINING_DIR / "train_filelist.txt")
        hps.data.validation_files = str(VITS_TRAINING_DIR / "val_filelist.txt")
        hps.data.max_wav_value = 32768.0
        hps.data.sampling_rate = self.config.sampling_rate
        hps.data.filter_length = self.config.filter_length
        hps.data.hop_length = self.config.hop_length
        hps.data.win_length = self.config.win_length
        hps.data.n_mel_channels = self.config.n_mel_channels
        hps.data.mel_fmin = self.config.mel_fmin
        hps.data.mel_fmax = self.config.mel_fmax
        hps.data.add_blank = True
        hps.data.n_speakers = self.config.n_speakers
        hps.data.cleaned_text = True
        
        # 模型配置
        hps.model = type('HParams', (), {})()
        hps.model.inter_channels = self.config.inter_channels
        hps.model.hidden_channels = self.config.hidden_channels
        hps.model.filter_channels = self.config.filter_channels
        hps.model.n_heads = self.config.n_heads
        hps.model.n_layers = self.config.n_layers
        hps.model.kernel_size = self.config.kernel_size
        hps.model.p_dropout = self.config.p_dropout
        hps.model.resblock = self.config.resblock
        hps.model.resblock_kernel_sizes = self.config.resblock_kernel_sizes
        hps.model.resblock_dilation_sizes = self.config.resblock_dilation_sizes
        hps.model.upsample_rates = [8, 8, 2, 2]
        hps.model.upsample_initial_channel = 512
        hps.model.upsample_kernel_sizes = [16, 16, 4, 4]
        hps.model.use_spectral_norm = False
        
        # 训练配置
        hps.train = type('HParams', (), {})()
        hps.train.log_interval = self.config.log_interval
        hps.train.eval_interval = self.config.eval_interval
        hps.train.seed = 1234
        hps.train.epochs = self.config.epochs
        hps.train.learning_rate = self.config.learning_rate
        hps.train.betas = self.config.adam_betas
        hps.train.eps = self.config.eps
        hps.train.batch_size = self.config.batch_size
        hps.train.fp16_run = self.config.fp16_run
        hps.train.lr_decay = self.config.lr_decay
        hps.train.segment_size = 8192
        hps.train.init_lr_ratio = 1
        hps.train.warmup_epochs = self.config.warmup_epochs
        hps.train.c_mel = self.config.c_mel
        hps.train.c_kl = self.config.c_kl
        
        # 符号表
        hps.symbols = self._get_symbols()
        
        return hps
    
    def _get_symbols(self):
        """获取符号表（字符集）"""
        # 中文字符集
        symbols = ['_', ',', '.', '!', '?', '-', '~', '…', 
                  'N', 'Q', 'a', 'b', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                  'ɑ', 'æ', 'ə', 'ɛ', 'ɜ', 'ɡ', 'ɪ', 'ɔ', 'ɹ', 'ʃ', 'ʊ', 'ʒ',
                  'ˈ', 'ˌ', 'ː', ' ']
        
        # 添加中文音素（如果使用音素）
        # 这里可以根据需要添加更多中文相关的符号
        
        return symbols
    
    def prepare_data(self, train_files: str, val_files: str) -> bool:
        """准备数据加载器"""
        try:
            hps = self._create_hparams()
            
            # 创建训练数据集
            train_dataset = TextAudioLoader(train_files, hps.data)
            self.train_loader = DataLoader(
                train_dataset,
                batch_size=self.config.batch_size,
                shuffle=True,
                num_workers=4,
                collate_fn=TextAudioCollate(),
                pin_memory=True
            )
            
            # 创建验证数据集
            eval_dataset = TextAudioLoader(val_files, hps.data)
            self.eval_loader = DataLoader(
                eval_dataset,
                batch_size=1,
                shuffle=False,
                num_workers=1,
                collate_fn=TextAudioCollate(),
                pin_memory=True
            )
            
            self.logger.info(f"数据加载器准备完成: 训练集 {len(train_dataset)} 样本")
            return True
            
        except Exception as e:
            self.logger.error(f"数据准备失败: {e}")
            return False
    
    def train_step(self, batch) -> Dict[str, float]:
        """单步训练"""
        self.model.train()
        
        # 解包数据
        x, x_lengths, spec, spec_lengths, y, y_lengths = batch
        x = x.to(self.device)
        x_lengths = x_lengths.to(self.device)
        spec = spec.to(self.device)
        spec_lengths = spec_lengths.to(self.device)
        y = y.to(self.device)
        y_lengths = y_lengths.to(self.device)
        
        # 前向传播
        outputs = self.model(x, x_lengths, spec, spec_lengths, y, y_lengths)
        
        # 计算损失
        loss_gen, losses_gen = self.model.module.generator_loss(*outputs)
        loss_disc, losses_disc = self.model.module.discriminator_loss(*outputs)
        
        # 生成器优化
        self.optimizer.zero_grad()
        loss_gen.backward()
        self.optimizer.step()
        
        # 判别器优化
        self.optimizer.zero_grad()
        loss_disc.backward()
        self.optimizer.step()
        
        losses = {
            'loss_gen': loss_gen.item(),
            'loss_disc': loss_disc.item(),
            **{f'g_{k}': v.item() for k, v in losses_gen.items()},
            **{f'd_{k}': v.item() for k, v in losses_disc.items()}
        }
        
        return losses
    
    def evaluate(self) -> Dict[str, float]:
        """评估模型"""
        self.model.eval()
        total_eval_loss = 0.0
        
        with torch.no_grad():
            for batch_idx, batch in enumerate(self.eval_loader):
                x, x_lengths, spec, spec_lengths, y, y_lengths = batch
                x = x.to(self.device)
                x_lengths = x_lengths.to(self.device)
                spec = spec.to(self.device)
                spec_lengths = spec_lengths.to(self.device)
                y = y.to(self.device)
                y_lengths = y_lengths.to(self.device)
                
                # 前向传播
                outputs = self.model(x, x_lengths, spec, spec_lengths, y, y_lengths)
                loss_gen, _ = self.model.module.generator_loss(*outputs)
                
                total_eval_loss += loss_gen.item()
        
        avg_eval_loss = total_eval_loss / len(self.eval_loader)
        
        return {'eval_loss': avg_eval_loss}
    
    def save_checkpoint(self, checkpoint_path: Path):
        """保存检查点"""
        try:
            checkpoint = {
                'model': self.model.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'scheduler': self.scheduler.state_dict(),
                'global_step': self.global_step,
                'epoch': self.epoch,
                'config': self.config
            }
            
            torch.save(checkpoint, checkpoint_path)
            self.logger.info(f"检查点已保存: {checkpoint_path}")
            
        except Exception as e:
            self.logger.error(f"保存检查点失败: {e}")
    
    def load_checkpoint(self, checkpoint_path: Path):
        """加载检查点"""
        try:
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            
            self.model.load_state_dict(checkpoint['model'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.scheduler.load_state_dict(checkpoint['scheduler'])
            self.global_step = checkpoint['global_step']
            self.epoch = checkpoint['epoch']
            
            self.logger.info(f"检查点已加载: {checkpoint_path}")
            
        except Exception as e:
            self.logger.error(f"加载检查点失败: {e}")
    
    def export_model(self, export_path: Path):
        """导出模型用于推理"""
        try:
            # 只保存模型权重
            model_dict = {
                'model': self.model.state_dict(),
                'config': self.config,
                'symbols': self._get_symbols()
            }
            
            torch.save(model_dict, export_path.with_suffix('.pth'))
            
            # 保存配置文件
            config_dict = {
                'sampling_rate': self.config.sampling_rate,
                'n_speakers': self.config.n_speakers,
                'symbols': self._get_symbols(),
                'data': {
                    'filter_length': self.config.filter_length,
                    'hop_length': self.config.hop_length,
                    'win_length': self.config.win_length,
                    'n_mel_channels': self.config.n_mel_channels,
                    'mel_fmin': self.config.mel_fmin,
                    'mel_fmax': self.config.mel_fmax,
                    'text_cleaners': ['chinese_cleaners']
                },
                'model': {
                    'inter_channels': self.config.inter_channels,
                    'hidden_channels': self.config.hidden_channels,
                    'filter_channels': self.config.filter_channels,
                    'n_heads': self.config.n_heads,
                    'n_layers': self.config.n_layers,
                    'kernel_size': self.config.kernel_size,
                    'p_dropout': self.config.p_dropout,
                    'resblock': self.config.resblock,
                    'resblock_kernel_sizes': self.config.resblock_kernel_sizes,
                    'resblock_dilation_sizes': self.config.resblock_dilation_sizes
                }
            }
            
            with open(export_path.with_suffix('.json'), 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"模型已导出: {export_path}")
            
        except Exception as e:
            self.logger.error(f"导出模型失败: {e}")

# ======================
# 训练管理器
# ======================
class VITSTrainingManager:
    """VITS训练管理器"""
    
    def __init__(self):
        self.current_trainer = None
        self.training_config = None
        self.is_training = False
        self.training_thread = None
        self.progress_callback = None
    
    def create_training_task(self, audio_files: List[Path], text_files: List[Path],
                           config: Optional[VITSTrainingConfig] = None) -> Tuple[bool, str]:
        """创建训练任务"""
        try:
            if self.is_training:
                return False, "已有训练任务在进行中"
            
            # 使用默认配置或自定义配置
            self.training_config = config or VITSTrainingConfig()
            
            # 预处理数据
            preprocessor = VITSDataPreprocessor(self.training_config)
            success, message = preprocessor.prepare_dataset(
                audio_files, text_files, VITS_TRAINING_DIR
            )
            
            if not success:
                return False, message
            
            # 创建训练器
            self.current_trainer = VITSTrainer(self.training_config)
            
            # 构建模型
            if not self.current_trainer.build_model():
                return False, "模型构建失败"
            
            # 准备数据
            train_files = str(VITS_TRAINING_DIR / "train_filelist.txt")
            val_files = str(VITS_TRAINING_DIR / "val_filelist.txt")
            
            if not self.current_trainer.prepare_data(train_files, val_files):
                return False, "数据加载失败"
            
            return True, "训练任务创建成功"
            
        except Exception as e:
            return False, f"创建任务失败: {str(e)}"
    
    def start_training(self) -> bool:
        """开始训练"""
        if not self.current_trainer or self.is_training:
            return False
        
        self.is_training = True
        
        # 在新线程中运行训练
        import threading
        self.training_thread = threading.Thread(target=self._training_loop)
        self.training_thread.start()
        
        return True
    
    def _training_loop(self):
        """训练循环"""
        try:
            trainer = self.current_trainer
            config = self.training_config
            
            for epoch in range(config.epochs):
                trainer.epoch = epoch
                
                # 训练一个epoch
                for batch_idx, batch in enumerate(trainer.train_loader):
                    if not self.is_training:
                        break
                    
                    # 训练步骤
                    losses = trainer.train_step(batch)
                    trainer.global_step += 1
                    
                    # 记录日志
                    if trainer.global_step % config.log_interval == 0:
                        self._log_training_status(epoch, batch_idx, losses)
                    
                    # 评估
                    if trainer.global_step % config.eval_interval == 0:
                        eval_losses = trainer.evaluate()
                        self._log_evaluation_status(eval_losses)
                    
                    # 保存检查点
                    if trainer.global_step % config.save_interval == 0:
                        checkpoint_path = VITS_CHECKPOINTS_DIR / f"checkpoint_{trainer.global_step}.pth"
                        trainer.save_checkpoint(checkpoint_path)
                
                # 学习率调度
                trainer.scheduler.step()
                
                if not self.is_training:
                    break
            
            # 导出最终模型
            export_path = BASE_DIR / "voice_models" / f"{config.model_name}"
            trainer.export_model(export_path)
            
        except Exception as e:
            print(f"训练失败: {e}")
        finally:
            self.is_training = False
    
    def stop_training(self):
        """停止训练"""
        self.is_training = False
        if self.training_thread:
            self.training_thread.join()
    
    def _log_training_status(self, epoch, batch_idx, losses):
        """记录训练状态"""
        status_msg = f"Epoch {epoch} [{batch_idx}/{len(self.current_trainer.train_loader)}] - "
        status_msg += " - ".join([f"{k}: {v:.4f}" for k, v in losses.items()])
        
        if self.progress_callback:
            self.progress_callback({
                'epoch': epoch,
                'batch': batch_idx,
                'total_batches': len(self.current_trainer.train_loader),
                'losses': losses,
                'global_step': self.current_trainer.global_step
            })
    
    def _log_evaluation_status(self, eval_losses):
        """记录评估状态"""
        status_msg = "Evaluation - "
        status_msg += " - ".join([f"{k}: {v:.4f}" for k, v in eval_losses.items()])
        
        if self.progress_callback:
            self.progress_callback({
                'type': 'evaluation',
                'eval_losses': eval_losses,
                'global_step': self.current_trainer.global_step
            })

# ======================
# 工厂函数
# ======================
def create_vits_trainer(model_name: str = "unicorn_vits", **kwargs) -> Optional[VITSTrainingManager]:
    """创建VITS训练管理器"""
    if not VITS_AVAILABLE:
        print("❌ VITS训练功能不可用，请安装必要的依赖")
        return None
    
    try:
        manager = VITSTrainingManager()
        return manager
    except Exception as e:
        print(f"❌ 创建VITS训练器失败: {e}")
        return None

# ======================
# 命令行接口
# ======================
def main():
    """命令行主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VITS语音训练器")
    parser.add_argument('--data', type=str, required=True, help="训练数据目录")
    parser.add_argument('--model-name', type=str, default="unicorn_vits", help="模型名称")
    parser.add_argument('--epochs', type=int, default=10000, help="训练轮数")
    parser.add_argument('--batch-size', type=int, default=16, help="批次大小")
    parser.add_argument('--learning-rate', type=float, default=2e-4, help="学习率")
    
    args = parser.parse_args()
    
    print("🎙️ VITS语音训练器")
    print("=" * 50)
    
    # 收集训练数据
    data_dir = Path(args.data)
    audio_files = list(data_dir.glob("*.wav"))
    text_files = list(data_dir.glob("*.txt"))
    
    print(f"找到 {len(audio_files)} 个音频文件")
    print(f"找到 {len(text_files)} 个文本文件")
    
    if len(audio_files) != len(text_files):
        print("❌ 音频和文本文件数量不匹配")
        return
    
    # 创建训练管理器
    manager = create_vits_trainer(args.model_name)
    if not manager:
        return
    
    # 创建训练配置
    config = VITSTrainingConfig(
        model_name=args.model_name,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
    
    # 创建训练任务
    success, message = manager.create_training_task(audio_files, text_files, config)
    
    if success:
        print("✅ " + message)
        print("开始训练...")
        manager.start_training()
        
        # 等待训练完成
        while manager.is_training:
            time.sleep(10)
        
        print("🎉 训练完成！")
    else:
        print("❌ " + message)

if __name__ == "__main__":
    main()