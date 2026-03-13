#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版训练启动器 - 跳过可能导致卡住的代码
"""

import sys
import os
import json
import time
import shutil
import glob
import warnings
import multiprocessing
from datetime import datetime

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.cuda.amp import GradScaler, autocast
from torch.nn import functional as F
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

# 添加当前路径
sys.path.insert(0, os.getcwd())

try:
    import modules.commons as commons
    import utils
    from data_utils import TextAudioCollate, TextAudioSpeakerLoader
    from models import (
        MultiPeriodDiscriminator,
        SynthesizerTrn,
    )
    from modules.losses import discriminator_loss, feature_loss, generator_loss, kl_loss
    from modules.mel_processing import mel_spectrogram_torch, spec_to_mel_torch
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在so-vits-svc目录中运行此脚本")
    sys.exit(1)

# 过滤警告
warnings.filterwarnings("ignore")

def setup_basic_directories(model_dir):
    """基础目录设置（简化版）"""
    print("🛠️ 设置基础目录...")
    
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 基础TensorBoard目录
    tb_dir = os.path.join("logs", "tensorboard")
    os.makedirs(tb_dir, exist_ok=True)
    
    print(f"✅ 目录设置完成: {model_dir}, {tb_dir}")
    return tb_dir

def quick_dataset_check(hps):
    """快速数据集检查（跳过修复）"""
    print("🔍 快速数据集检查...")
    
    try:
        # 检查训练文件列表
        with open(hps.data.training_files, 'r', encoding='utf-8') as f:
            train_lines = f.readlines()
        
        print(f"✅ 训练文件列表: {len(train_lines)} 个文件")
        
        # 检查前几个文件是否存在
        for i, line in enumerate(train_lines[:3]):
            wav_path = line.split('|')[0].strip()
            if os.path.exists(wav_path):
                print(f"  ✅ 文件{i+1}存在: {os.path.basename(wav_path)}")
            else:
                print(f"  ❌ 文件{i+1}缺失: {wav_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据集检查失败: {e}")
        return False

def train_single_gpu(hps, tb_dir, force_cpu=False):
    """单GPU训练（避免多进程问题）"""
    print("🚀 启动单GPU训练...")
    
    # 设备选择
    if force_cpu or not torch.cuda.is_available():
        device = torch.device("cpu")
        print("✅ 使用CPU训练")
    else:
        device = torch.device("cuda:0")
        print(f"✅ 使用GPU训练: {torch.cuda.get_device_name(0)}")
    
    # 设置随机种子
    torch.manual_seed(hps.train.seed)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(hps.train.seed)
    
    # 初始化日志
    logger = utils.get_logger(hps.model_dir)
    logger.info("开始训练...")
    
    # TensorBoard
    writer = SummaryWriter(log_dir=tb_dir)
    writer_eval = SummaryWriter(log_dir=os.path.join(tb_dir, "eval"))
    
    try:
        # 数据加载器
        print("📊 初始化数据加载器...")
        collate_fn = TextAudioCollate()
        
        # 训练数据集
        train_dataset = TextAudioSpeakerLoader(
            hps.data.training_files, 
            hps, 
            all_in_mem=False  # 避免内存问题
        )
        
        train_loader = DataLoader(
            train_dataset,
            num_workers=0,  # 单线程避免问题
            shuffle=True,
            pin_memory=False,
            batch_size=min(hps.train.batch_size, 4),  # 限制batch size
            collate_fn=collate_fn
        )
        
        # 验证数据集
        eval_dataset = TextAudioSpeakerLoader(
            hps.data.validation_files, 
            hps, 
            all_in_mem=False,
            vol_aug=False
        )
        
        eval_loader = DataLoader(
            eval_dataset,
            num_workers=0,
            shuffle=False,
            batch_size=1,
            pin_memory=False,
            collate_fn=collate_fn
        )
        
        print(f"✅ 数据加载器初始化完成")
        print(f"  训练样本: {len(train_dataset)}")
        print(f"  验证样本: {len(eval_dataset)}")
        
        # 模型初始化
        print("🤖 初始化模型...")
        
        net_g = SynthesizerTrn(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            **hps.model
        ).to(device)
        
        net_d = MultiPeriodDiscriminator(
            hps.model.use_spectral_norm
        ).to(device)
        
        print("✅ 模型初始化完成")
        
        # 优化器
        optim_g = torch.optim.AdamW(
            net_g.parameters(),
            hps.train.learning_rate,
            betas=hps.train.betas,
            eps=hps.train.eps
        )
        
        optim_d = torch.optim.AdamW(
            net_d.parameters(),
            hps.train.learning_rate,
            betas=hps.train.betas,
            eps=hps.train.eps
        )
        
        # 检查点加载
        print("🔍 检查现有检查点...")
        epoch_str = 1
        global_step = 0
        
        try:
            g_checkpoint = utils.latest_checkpoint_path(hps.model_dir, "G_*.pth")
            if g_checkpoint:
                print(f"🔁 加载生成器检查点: {g_checkpoint}")
                _, _, _, epoch_str = utils.load_checkpoint(
                    g_checkpoint, net_g, optim_g, False
                )
                global_step = int(os.path.basename(g_checkpoint).split('_')[1].split('.')[0])
                
            d_checkpoint = utils.latest_checkpoint_path(hps.model_dir, "D_*.pth")
            if d_checkpoint:
                print(f"🔁 加载判别器检查点: {d_checkpoint}")
                utils.load_checkpoint(d_checkpoint, net_d, optim_d, False)
                
        except Exception as e:
            print(f"⚠️ 检查点加载失败，从头开始: {e}")
            epoch_str = 1
            global_step = 0
        
        # 学习率调度器
        scheduler_g = torch.optim.lr_scheduler.ExponentialLR(
            optim_g, gamma=hps.train.lr_decay, last_epoch=epoch_str-2
        )
        scheduler_d = torch.optim.lr_scheduler.ExponentialLR(
            optim_d, gamma=hps.train.lr_decay, last_epoch=epoch_str-2
        )
        
        # 混合精度训练
        scaler = GradScaler(enabled=hps.train.fp16_run and device.type == 'cuda')
        
        print(f"🎯 开始训练循环 (从epoch {epoch_str}开始)...")
        
        # 简化的训练循环
        for epoch in range(epoch_str, min(epoch_str + 5, hps.train.epochs + 1)):  # 先只训练5个epoch测试
            print(f"\n📅 Epoch {epoch}/{hps.train.epochs}")
            
            net_g.train()
            net_d.train()
            
            epoch_start_time = time.time()
            
            for batch_idx, batch in enumerate(train_loader):
                if batch_idx >= 10:  # 每个epoch只训练10个batch做测试
                    break
                    
                try:
                    # 数据准备
                    (spec, spec_lengths, y, y_lengths, spk, _, f0, uv) = batch
                    spec = spec.to(device)
                    spec_lengths = spec_lengths.to(device)
                    y = y.to(device)
                    y_lengths = y_lengths.to(device)
                    spk = spk.to(device)
                    f0 = f0.to(device)
                    uv = uv.to(device)
                    
                    # 生成器前向传播
                    with autocast(enabled=hps.train.fp16_run and device.type == 'cuda'):
                        (y_hat, ids_slice, x_mask, z_mask, 
                         (z, z_p, m_p, logs_p, m_q, logs_q), pred_lf0, norm_lf0, lf0) = net_g(
                            spec, spec_lengths, spk, f0=f0, uv=uv
                        )
                        
                        mel = spec_to_mel_torch(
                            spec, 
                            hps.data.filter_length, 
                            hps.data.n_mel_channels, 
                            hps.data.sampling_rate,
                            hps.data.mel_fmin, 
                            hps.data.mel_fmax
                        )
                        
                        y_mel = commons.slice_segments(
                            mel, ids_slice, hps.train.segment_size // hps.data.hop_length
                        )
                        
                        with torch.no_grad():
                            y_hat_mel = mel_spectrogram_torch(
                                y_hat.squeeze(1).float(),
                                hps.data.filter_length,
                                hps.data.n_mel_channels,
                                hps.data.sampling_rate,
                                hps.data.hop_length,
                                hps.data.win_length,
                                hps.data.mel_fmin,
                                hps.data.mel_fmax
                            )
                        
                        y = commons.slice_segments(
                            y, ids_slice * hps.data.hop_length, hps.train.segment_size
                        )
                        
                        # 判别器前向传播
                        y_d_hat_r, y_d_hat_g, _, _ = net_d(y, y_hat.detach())
                        
                        # 计算损失
                        loss_disc, losses_disc_r, losses_disc_g = discriminator_loss(
                            y_d_hat_r, y_d_hat_g
                        )
                    
                    # 判别器反向传播
                    optim_d.zero_grad()
                    scaler.scale(loss_disc).backward()
                    scaler.step(optim_d)
                    
                    # 生成器损失
                    with autocast(enabled=hps.train.fp16_run and device.type == 'cuda'):
                        y_d_hat_r, y_d_hat_g, fmap_r, fmap_g = net_d(y, y_hat)
                        loss_gen, losses_gen = generator_loss(y_d_hat_g)
                        loss_fm = feature_loss(fmap_r, fmap_g)
                        loss_mel = F.l1_loss(y_mel, y_hat_mel) * 45
                        loss_lf0 = F.mse_loss(pred_lf0, lf0)
                        loss_kl = kl_loss(z_p, logs_q, m_p, logs_p, z_mask) * 1.0
                        
                        loss_gen_all = loss_gen + loss_fm + loss_mel + loss_kl + loss_lf0
                    
                    # 生成器反向传播
                    optim_g.zero_grad()
                    scaler.scale(loss_gen_all).backward()
                    scaler.step(optim_g)
                    
                    scaler.update()
                    
                    global_step += 1
                    
                    # 打印进度
                    if batch_idx % 5 == 0:
                        print(f"  Batch {batch_idx}/10 - "
                              f"Loss_G: {loss_gen_all.item():.3f}, "
                              f"Loss_D: {loss_disc.item():.3f}")
                        
                        # 记录到TensorBoard
                        if writer:
                            writer.add_scalar("Loss/Generator", loss_gen_all.item(), global_step)
                            writer.add_scalar("Loss/Discriminator", loss_disc.item(), global_step)
                
                except Exception as e:
                    print(f"❌ Batch {batch_idx} 训练失败: {e}")
                    continue
            
            epoch_time = time.time() - epoch_start_time
            print(f"✅ Epoch {epoch} 完成 ({epoch_time:.1f}秒)")
            
            # 保存检查点
            if epoch % 2 == 0:  # 每2个epoch保存一次
                print(f"💾 保存检查点...")
                utils.save_checkpoint(
                    net_g, optim_g, hps.train.learning_rate, epoch,
                    os.path.join(hps.model_dir, f"G_{global_step}.pth")
                )
                utils.save_checkpoint(
                    net_d, optim_d, hps.train.learning_rate, epoch,
                    os.path.join(hps.model_dir, f"D_{global_step}.pth")
                )
                print("✅ 检查点保存完成")
            
            # 更新学习率
            scheduler_g.step()
            scheduler_d.step()
        
        print("🎉 训练测试完成！")
        
    except Exception as e:
        print(f"❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if writer:
            writer.close()
        if writer_eval:
            writer_eval.close()
    
    return True

def main():
    """主函数"""
    print("=" * 70)
    print("🔧 修复版训练启动器")
    print("=" * 70)
    
    # 检查参数
    if len(sys.argv) < 5:
        print("❌ 参数不足")
        print("用法: python fixed_trainer.py -c config.json -m model_dir")
        return
    
    config_path = sys.argv[2]
    model_dir = sys.argv[4]
    
    print(f"📄 配置文件: {config_path}")
    print(f"📁 模型目录: {model_dir}")
    
    # 加载配置
    try:
        hps = utils.get_hparams_from_file(config_path)
        hps.model_dir = model_dir
        print("✅ 配置加载成功")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return
    
    # 设置目录
    tb_dir = setup_basic_directories(model_dir)
    
    # 快速数据集检查
    if not quick_dataset_check(hps):
        print("❌ 数据集检查失败")
        return
    
    # 选择训练模式
    print("\n选择训练模式:")
    print("1. GPU训练 (推荐)")
    print("2. CPU训练 (慢但稳定)")
    print("3. 自动选择")
    
    choice = input("请选择 (1-3): ").strip()
    
    force_cpu = False
    if choice == "2":
        force_cpu = True
    elif choice == "3":
        force_cpu = not torch.cuda.is_available()
    
    # 开始训练
    success = train_single_gpu(hps, tb_dir, force_cpu)
    
    if success:
        print("\n🎉 训练启动成功！")
        print("📊 查看训练进度:")
        print(f"  tensorboard --logdir {tb_dir}")
    else:
        print("\n❌ 训练启动失败")

if __name__ == "__main__":
    main()