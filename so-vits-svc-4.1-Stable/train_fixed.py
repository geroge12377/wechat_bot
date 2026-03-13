import logging
import multiprocessing
import os
import time
import re  # 添加正则表达式模块用于文件名解析

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.cuda.amp import GradScaler, autocast
from torch.nn import functional as F
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

import modules.commons as commons
import utils
from data_utils import TextAudioCollate, TextAudioSpeakerLoader
from models import (
    MultiPeriodDiscriminator,
    SynthesizerTrn,
)
from modules.losses import discriminator_loss, feature_loss, generator_loss, kl_loss
from modules.mel_processing import mel_spectrogram_torch, spec_to_mel_torch

logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('numba').setLevel(logging.WARNING)

torch.backends.cudnn.benchmark = True
global_step = 0
start_time = time.time()

def find_latest_checkpoint(model_dir, pattern):
    """查找最新检查点并返回文件名和步数"""
    checkpoint_files = []
    for file in os.listdir(model_dir):
        if file.startswith(pattern.split('*')[0]) and file.endswith('.pth'):
            match = re.search(r'_(\d+)\.pth$', file)
            if match:
                step = int(match.group(1))
                checkpoint_files.append((file, step))
    
    if not checkpoint_files:
        return None, 0
    
    # 按步数排序并返回最新的
    checkpoint_files.sort(key=lambda x: x[1], reverse=True)
    return checkpoint_files[0][0], checkpoint_files[0][1]

def main():
    """Assume Single Node Multi GPUs Training Only"""
    assert torch.cuda.is_available(), "CPU training is not allowed."
    hps = utils.get_hparams()

    n_gpus = torch.cuda.device_count()
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = hps.train.port

    mp.spawn(run, nprocs=n_gpus, args=(n_gpus, hps,))

def run(rank, n_gpus, hps):
    global global_step
    if rank == 0:
        logger = utils.get_logger(hps.model_dir)
        logger.info(hps)
        utils.check_git_hash(hps.model_dir)
        writer = SummaryWriter(log_dir=hps.model_dir)
        writer_eval = SummaryWriter(log_dir=os.path.join(hps.model_dir, "eval"))
    
    # for pytorch on win, backend use gloo    
    dist.init_process_group(backend='gloo' if os.name == 'nt' else 'nccl', init_method='env://', world_size=n_gpus, rank=rank)
    torch.manual_seed(hps.train.seed)
    torch.cuda.set_device(rank)
    collate_fn = TextAudioCollate()
    all_in_mem = hps.train.all_in_mem
    train_dataset = TextAudioSpeakerLoader(hps.data.training_files, hps, all_in_mem=all_in_mem)
    
    # 创建分布式采样器
    train_sampler = torch.utils.data.distributed.DistributedSampler(
        train_dataset,
        num_replicas=n_gpus,
        rank=rank,
        shuffle=True
    )
    
    # 添加诊断信息
    if rank == 0:
        logger.info(f"训练集样本数: {len(train_dataset)}")
        logger.info(f"批大小: {hps.train.batch_size}")
        logger.info(f"GPU数量: {n_gpus}")
    
    num_workers = 5 if multiprocessing.cpu_count() > 4 else multiprocessing.cpu_count()
    if all_in_mem:
        num_workers = 0
    
    # 使用分布式采样器
    train_loader = DataLoader(
        train_dataset, 
        num_workers=num_workers, 
        shuffle=False,  # 使用sampler时必须设置为False
        pin_memory=True,
        batch_size=hps.train.batch_size, 
        collate_fn=collate_fn,
        sampler=train_sampler,
        drop_last=True  # 避免最后一批数据大小不一致
    )
    
    # 计算每个epoch的步数
    steps_per_epoch = len(train_loader)
    if rank == 0:
        logger.info(f"每个epoch的步数: {steps_per_epoch}")
    
    if rank == 0:
        eval_dataset = TextAudioSpeakerLoader(hps.data.validation_files, hps, all_in_mem=all_in_mem, vol_aug=False)
        eval_loader = DataLoader(eval_dataset, num_workers=1, shuffle=False,
                                 batch_size=1, pin_memory=False,
                                 drop_last=False, collate_fn=collate_fn)

    net_g = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        **hps.model).cuda(rank)
    net_d = MultiPeriodDiscriminator(hps.model.use_spectral_norm).cuda(rank)
    optim_g = torch.optim.AdamW(
        net_g.parameters(),
        hps.train.learning_rate,
        betas=hps.train.betas,
        eps=hps.train.eps)
    optim_d = torch.optim.AdamW(
        net_d.parameters(),
        hps.train.learning_rate,
        betas=hps.train.betas,
        eps=hps.train.eps)
    net_g = DDP(net_g, device_ids=[rank])
    net_d = DDP(net_d, device_ids=[rank])

    skip_optimizer = False
    epoch_str = 1
    loaded_global_step = 0
    
    try:
        # 改进的检查点加载逻辑
        g_file, g_step = find_latest_checkpoint(hps.model_dir, "G_*.pth")
        d_file, d_step = find_latest_checkpoint(hps.model_dir, "D_*.pth")
        
        if g_file and d_file:
            # 使用最新的步数
            loaded_global_step = max(g_step, d_step)
            
            # 加载生成器
            g_path = os.path.join(hps.model_dir, g_file)
            _, _, _, epoch_str = utils.load_checkpoint(g_path, net_g, optim_g, skip_optimizer)
            
            # 加载判别器
            d_path = os.path.join(hps.model_dir, d_file)
            _, _, _, _ = utils.load_checkpoint(d_path, net_d, optim_d, skip_optimizer)
            
            epoch_str = max(epoch_str, 1)
            
            # 设置全局步数
            global_step = loaded_global_step
            
            if rank == 0:
                logger.info(f"从检查点恢复: G={g_file}, D={d_file}, global_step={global_step}, epoch={epoch_str}")
        else:
            global_step = 0
            if rank == 0:
                logger.info("未找到检查点，从头开始训练")
                
    except Exception as e:
        if rank == 0:
            logger.error(f"加载检查点失败: {str(e)}")
        print(f"加载旧检查点失败...{str(e)}")
        epoch_str = 1
        global_step = 0
    
    if skip_optimizer:
        epoch_str = 1
        global_step = 0

    warmup_epoch = hps.train.warmup_epochs
    scheduler_g = torch.optim.lr_scheduler.ExponentialLR(optim_g, gamma=hps.train.lr_decay, last_epoch=epoch_str - 2)
    scheduler_d = torch.optim.lr_scheduler.ExponentialLR(optim_d, gamma=hps.train.lr_decay, last_epoch=epoch_str - 2)

    scaler = GradScaler(enabled=hps.train.fp16_run)

    # 添加保存间隔配置（带默认值）
    save_every_epoch = getattr(hps.train, 'save_every_epoch', 50)
    min_epochs_to_save = getattr(hps.train, 'min_epochs_to_save', 10)
    
    if rank == 0:
        logger.info(f"保存配置: 每{save_every_epoch}个epoch保存一次, 从第{min_epochs_to_save}个epoch开始")

    for epoch in range(epoch_str, hps.train.epochs + 1):
        # 设置epoch以确保每个epoch的数据打乱不同
        train_sampler.set_epoch(epoch)
        
        # set up warm-up learning rate
        if epoch <= warmup_epoch:
            for param_group in optim_g.param_groups:
                param_group['lr'] = hps.train.learning_rate / warmup_epoch * epoch
            for param_group in optim_d.param_groups:
                param_group['lr'] = hps.train.learning_rate / warmup_epoch * epoch
        
        # training
        if rank == 0:
            train_and_evaluate(rank, epoch, hps, [net_g, net_d], [optim_g, optim_d], [scheduler_g, scheduler_d], scaler,
                               [train_loader, eval_loader], logger, [writer, writer_eval], steps_per_epoch)
        else:
            train_and_evaluate(rank, epoch, hps, [net_g, net_d], [optim_g, optim_d], [scheduler_g, scheduler_d], scaler,
                               [train_loader, None], None, None, steps_per_epoch)
        
        # 在每个epoch结束时保存检查点
        if rank == 0:
            if epoch >= min_epochs_to_save and epoch % save_every_epoch == 0:
                logger.info(f"=== 保存Epoch {epoch}的检查点 ===")
                utils.save_checkpoint(net_g, optim_g, hps.train.learning_rate, epoch,
                                     os.path.join(hps.model_dir, f"G_epoch_{epoch}.pth"))
                utils.save_checkpoint(net_d, optim_d, hps.train.learning_rate, epoch,
                                     os.path.join(hps.model_dir, f"D_epoch_{epoch}.pth"))
        
        # update learning rate
        scheduler_g.step()
        scheduler_d.step()


def train_and_evaluate(rank, epoch, hps, nets, optims, schedulers, scaler, loaders, logger, writers, steps_per_epoch):
    net_g, net_d = nets
    optim_g, optim_d = optims
    scheduler_g, scheduler_d = schedulers
    train_loader, eval_loader = loaders
    if writers is not None:
        writer, writer_eval = writers
    
    half_type = torch.bfloat16 if hps.train.half_type=="bf16" else torch.float16

    global global_step

    net_g.train()
    net_d.train()
    
    epoch_start_time = time.time()
    epoch_loss_g = 0
    epoch_loss_d = 0
    batch_count = 0
    
    for batch_idx, items in enumerate(train_loader):
        # 检查数据是否为空
        if items is None or len(items) == 0:
            if rank == 0:
                logger.warning(f"批次 {batch_idx} 数据为空，跳过")
            continue
            
        try:
            c, f0, spec, y, spk, lengths, uv, volume = items
            
            # 检查数据维度
            if y.size(0) == 0:
                if rank == 0:
                    logger.warning(f"批次 {batch_idx} 样本数为0，跳过")
                continue
                
            g = spk.cuda(rank, non_blocking=True)
            spec, y = spec.cuda(rank, non_blocking=True), y.cuda(rank, non_blocking=True)
            c = c.cuda(rank, non_blocking=True)
            f0 = f0.cuda(rank, non_blocking=True)
            uv = uv.cuda(rank, non_blocking=True)
            lengths = lengths.cuda(rank, non_blocking=True)
            
            mel = spec_to_mel_torch(
                spec,
                hps.data.filter_length,
                hps.data.n_mel_channels,
                hps.data.sampling_rate,
                hps.data.mel_fmin,
                hps.data.mel_fmax)
            
            with autocast(enabled=hps.train.fp16_run, dtype=half_type):
                y_hat, ids_slice, z_mask, \
                (z, z_p, m_p, logs_p, m_q, logs_q), pred_lf0, norm_lf0, lf0 = net_g(c, f0, uv, spec, g=g, c_lengths=lengths,
                                                                                    spec_lengths=lengths, vol=volume)

                y_mel = commons.slice_segments(mel, ids_slice, hps.train.segment_size // hps.data.hop_length)
                y_hat_mel = mel_spectrogram_torch(
                    y_hat.squeeze(1),
                    hps.data.filter_length,
                    hps.data.n_mel_channels,
                    hps.data.sampling_rate,
                    hps.data.hop_length,
                    hps.data.win_length,
                    hps.data.mel_fmin,
                    hps.data.mel_fmax
                )
                y = commons.slice_segments(y, ids_slice * hps.data.hop_length, hps.train.segment_size)  # slice

                # Discriminator
                y_d_hat_r, y_d_hat_g, _, _ = net_d(y, y_hat.detach())

                with autocast(enabled=False, dtype=half_type):
                    loss_disc, losses_disc_r, losses_disc_g = discriminator_loss(y_d_hat_r, y_d_hat_g)
                    loss_disc_all = loss_disc
            
            optim_d.zero_grad()
            scaler.scale(loss_disc_all).backward()
            scaler.unscale_(optim_d)
            grad_norm_d = commons.clip_grad_value_(net_d.parameters(), None)
            scaler.step(optim_d)
            
            with autocast(enabled=hps.train.fp16_run, dtype=half_type):
                # Generator
                y_d_hat_r, y_d_hat_g, fmap_r, fmap_g = net_d(y, y_hat)
                with autocast(enabled=False, dtype=half_type):
                    loss_mel = F.l1_loss(y_mel, y_hat_mel) * hps.train.c_mel
                    loss_kl = kl_loss(z_p, logs_q, m_p, logs_p, z_mask) * hps.train.c_kl
                    loss_fm = feature_loss(fmap_r, fmap_g)
                    loss_gen, losses_gen = generator_loss(y_d_hat_g)
                    loss_lf0 = F.mse_loss(pred_lf0, lf0) if net_g.module.use_automatic_f0_prediction else 0
                    loss_gen_all = loss_gen + loss_fm + loss_mel + loss_kl + loss_lf0
                    
            optim_g.zero_grad()
            scaler.scale(loss_gen_all).backward()
            scaler.unscale_(optim_g)
            grad_norm_g = commons.clip_grad_value_(net_g.parameters(), None)
            scaler.step(optim_g)
            scaler.update()

            epoch_loss_g += loss_gen_all.item()
            epoch_loss_d += loss_disc_all.item()
            batch_count += 1

            if rank == 0:
                if global_step % hps.train.log_interval == 0:
                    lr = optim_g.param_groups[0]['lr']
                    losses = [loss_disc, loss_gen, loss_fm, loss_mel, loss_kl]
                    reference_loss = 0
                    for i in losses:
                        reference_loss += i
                    
                    # 添加训练进度信息
                    epoch_progress = (batch_idx + 1) / len(train_loader) * 100
                    elapsed = time.time() - epoch_start_time
                    avg_time_per_batch = elapsed / (batch_idx + 1)
                    remaining_batches = len(train_loader) - batch_idx - 1
                    eta_seconds = avg_time_per_batch * remaining_batches
                    eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
                    
                    logger.info(f"Epoch: {epoch} [{epoch_progress:.1f}%] ETA: {eta_str}")
                    logger.info(f"Losses: {[x.item() for x in losses]}, step: {global_step}, lr: {lr}, reference_loss: {reference_loss}")

                    scalar_dict = {"loss/g/total": loss_gen_all, "loss/d/total": loss_disc_all, "learning_rate": lr,
                                   "grad_norm_d": grad_norm_d, "grad_norm_g": grad_norm_g}
                    scalar_dict.update({"loss/g/fm": loss_fm, "loss/g/mel": loss_mel, "loss/g/kl": loss_kl,
                                        "loss/g/lf0": loss_lf0})

                    image_dict = {
                        "slice/mel_org": utils.plot_spectrogram_to_numpy(y_mel[0].data.cpu().numpy()),
                        "slice/mel_gen": utils.plot_spectrogram_to_numpy(y_hat_mel[0].data.cpu().numpy()),
                        "all/mel": utils.plot_spectrogram_to_numpy(mel[0].data.cpu().numpy())
                    }

                    if net_g.module.use_automatic_f0_prediction:
                        image_dict.update({
                            "all/lf0": utils.plot_data_to_numpy(lf0[0, 0, :].cpu().numpy(),
                                                                  pred_lf0[0, 0, :].detach().cpu().numpy()),
                            "all/norm_lf0": utils.plot_data_to_numpy(lf0[0, 0, :].cpu().numpy(),
                                                                       norm_lf0[0, 0, :].detach().cpu().numpy())
                        })

                    utils.summarize(
                        writer=writer,
                        global_step=global_step,
                        images=image_dict,
                        scalars=scalar_dict
                    )

                if global_step % hps.train.eval_interval == 0:
                    evaluate(hps, net_g, eval_loader, writer_eval)
                    utils.save_checkpoint(net_g, optim_g, hps.train.learning_rate, epoch,
                                          os.path.join(hps.model_dir, "G_{}.pth".format(global_step)))
                    utils.save_checkpoint(net_d, optim_d, hps.train.learning_rate, epoch,
                                          os.path.join(hps.model_dir, "D_{}.pth".format(global_step)))
                    keep_ckpts = getattr(hps.train, 'keep_ckpts', 3)
                    if keep_ckpts > 0:
                        utils.clean_checkpoints(path_to_models=hps.model_dir, n_ckpts_to_keep=keep_ckpts, sort_by_time=True)

            global_step += 1
            
        except Exception as e:
            if rank == 0:
                logger.error(f"批次 {batch_idx} 处理失败: {str(e)}")
            continue

    if rank == 0:
        epoch_time = time.time() - epoch_start_time
        avg_loss_g = epoch_loss_g / batch_count if batch_count > 0 else 0
        avg_loss_d = epoch_loss_d / batch_count if batch_count > 0 else 0
        logger.info(f'====> Epoch: {epoch}, 耗时 {epoch_time:.2f} 秒, 步数: {global_step}, 平均损失 G: {avg_loss_g:.4f}, D: {avg_loss_d:.4f}')


def evaluate(hps, generator, eval_loader, writer_eval):
    generator.eval()
    image_dict = {}
    audio_dict = {}
    with torch.no_grad():
        for batch_idx, items in enumerate(eval_loader):
            c, f0, spec, y, spk, _, uv, volume = items
            g = spk[:1].cuda(0)
            spec, y = spec[:1].cuda(0), y[:1].cuda(0)
            c = c[:1].cuda(0)
            f0 = f0[:1].cuda(0)
            uv = uv[:1].cuda(0)
            if volume is not None:
                volume = volume[:1].cuda(0)
            mel = spec_to_mel_torch(
                spec,
                hps.data.filter_length,
                hps.data.n_mel_channels,
                hps.data.sampling_rate,
                hps.data.mel_fmin,
                hps.data.mel_fmax)
            y_hat, _ = generator.module.infer(c, f0, uv, g=g, vol=volume)

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

            audio_dict.update({
                f"gen/audio_{batch_idx}": y_hat[0],
                f"gt/audio_{batch_idx}": y[0]
            })
        image_dict.update({
            "gen/mel": utils.plot_spectrogram_to_numpy(y_hat_mel[0].cpu().numpy()),
            "gt/mel": utils.plot_spectrogram_to_numpy(mel[0].cpu().numpy())
        })
    utils.summarize(
        writer=writer_eval,
        global_step=global_step,
        images=image_dict,
        audios=audio_dict,
        audio_sampling_rate=hps.data.sampling_rate
    )
    generator.train()


if __name__ == "__main__":
    main()