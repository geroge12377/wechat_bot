#!/usr/bin/env python3
"""
快速修复检查点恢复问题
"""

import os
import glob
import shutil
import torch
import json

def fix_checkpoint_resume():
    """修复检查点恢复问题"""
    
    print("🔧 开始修复检查点恢复问题...")
    
    # 1. 查找所有检查点文件
    all_pth_files = glob.glob("**/*.pth", recursive=True)
    print(f"找到 {len(all_pth_files)} 个.pth文件:")
    for f in all_pth_files:
        print(f"  - {f}")
    
    # 2. 查找config.json
    config_files = glob.glob("**/config.json", recursive=True)
    if not config_files:
        print("❌ 未找到config.json文件")
        return
    
    config_path = config_files[0]
    print(f"📄 使用配置文件: {config_path}")
    
    # 3. 读取配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        model_dir = config.get('model_dir', './logs')
        print(f"📁 配置中的model_dir: {model_dir}")
        
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        return
    
    # 4. 确保model_dir存在
    os.makedirs(model_dir, exist_ok=True)
    
    # 5. 查找现有的检查点文件
    existing_checkpoints = []
    
    # 在model_dir中查找
    model_dir_checkpoints = glob.glob(os.path.join(model_dir, "*.pth"))
    existing_checkpoints.extend(model_dir_checkpoints)
    
    # 在其他位置查找（如44k_final目录）
    other_checkpoints = []
    for pth_file in all_pth_files:
        if model_dir not in pth_file:
            other_checkpoints.append(pth_file)
    
    print(f"\n在model_dir中找到 {len(model_dir_checkpoints)} 个检查点:")
    for ckpt in model_dir_checkpoints:
        print(f"  ✅ {ckpt}")
    
    print(f"\n在其他位置找到 {len(other_checkpoints)} 个检查点:")
    for ckpt in other_checkpoints:
        print(f"  📦 {ckpt}")
    
    # 6. 修复策略
    if not model_dir_checkpoints and other_checkpoints:
        print(f"\n🔄 检测到检查点在错误位置，开始修复...")
        
        # 寻找最新的检查点
        latest_checkpoint = max(other_checkpoints, key=os.path.getmtime)
        print(f"🎯 最新检查点: {latest_checkpoint}")
        
        # 检查检查点内容
        try:
            checkpoint = torch.load(latest_checkpoint, map_location='cpu')
            epoch = checkpoint.get('epoch', 0)
            iteration = checkpoint.get('iteration', 0)
            
            print(f"📊 检查点信息: epoch={epoch}, iteration={iteration}")
            
            # 判断是生成器还是判别器
            if 'module.enc_p' in str(checkpoint.get('model', {})) or 'enc_p' in str(checkpoint.get('model', {})):
                # 生成器
                target_name = f"G_{iteration}.pth"
            elif 'discriminator' in latest_checkpoint.lower() or 'mpd' in str(checkpoint.get('model', {})):
                # 判别器  
                target_name = f"D_{iteration}.pth"
            else:
                # 根据文件名猜测
                if 'G_' in latest_checkpoint or 'generator' in latest_checkpoint.lower():
                    target_name = f"G_{iteration}.pth"
                else:
                    target_name = f"D_{iteration}.pth"
            
            target_path = os.path.join(model_dir, target_name)
            
            # 复制文件
            shutil.copy2(latest_checkpoint, target_path)
            print(f"✅ 已复制到: {target_path}")
            
        except Exception as e:
            print(f"❌ 处理检查点失败: {e}")
    
    # 7. 验证修复结果
    final_checkpoints = glob.glob(os.path.join(model_dir, "*.pth"))
    g_checkpoints = [f for f in final_checkpoints if 'G_' in os.path.basename(f)]
    d_checkpoints = [f for f in final_checkpoints if 'D_' in os.path.basename(f)]
    
    print(f"\n📋 修复后的检查点状态:")
    print(f"  生成器检查点: {len(g_checkpoints)} 个")
    for g in g_checkpoints:
        print(f"    - {g}")
    print(f"  判别器检查点: {len(d_checkpoints)} 个")
    for d in d_checkpoints:
        print(f"    - {d}")
    
    if g_checkpoints and d_checkpoints:
        print(f"\n✅ 检查点修复完成！")
        print(f"下次训练时应该能正确恢复。")
    else:
        print(f"\n⚠️  仍然缺少检查点文件，可能需要手动处理。")
    
    return g_checkpoints, d_checkpoints

def modify_training_script():
    """修改训练脚本以增强检查点加载"""
    
    print(f"\n🔧 训练脚本增强建议:")
    
    enhanced_code = '''
# 在train.py的检查点恢复部分添加更详细的日志
try:
    # 打印检查点搜索路径
    checkpoint_dir = hps.model_dir
    print(f"🔍 在目录中搜索检查点: {checkpoint_dir}")
    
    g_pattern = os.path.join(checkpoint_dir, "G_*.pth")
    d_pattern = os.path.join(checkpoint_dir, "D_*.pth")
    
    g_files = glob.glob(g_pattern)
    d_files = glob.glob(d_pattern)
    
    print(f"找到生成器检查点: {g_files}")
    print(f"找到判别器检查点: {d_files}")
    
    if g_files and d_files:
        latest_g = utils.latest_checkpoint_path(hps.model_dir, "G_*.pth")
        latest_d = utils.latest_checkpoint_path(hps.model_dir, "D_*.pth")
        
        print(f"最新生成器检查点: {latest_g}")
        print(f"最新判别器检查点: {latest_d}")
        
        # 加载检查点
        _, _, _, epoch_str = utils.load_checkpoint(latest_g, net_g, optim_g, skip_optimizer)
        _, _, _, epoch_str = utils.load_checkpoint(latest_d, net_d, optim_d, skip_optimizer)
        
        # 从文件名提取global_step
        if latest_d:
            step_str = os.path.basename(latest_d).split('_')[1].split('.')[0]
            global_step = int(step_str)
            print(f"恢复global_step: {global_step}")
    else:
        print("❌ 未找到匹配的检查点文件")
        
except Exception as e:
    print(f"❌ 检查点加载详细错误: {e}")
    import traceback
    traceback.print_exc()
'''
    
    print("建议在train.py中添加上述代码以获得更详细的调试信息。")

if __name__ == "__main__":
    g_ckpts, d_ckpts = fix_checkpoint_resume()
    modify_training_script()
    
    print(f"\n" + "="*50)
    print("🎯 完成修复！下一步:")
    print("1. 重新运行训练命令")
    print("2. 观察是否出现 '🔁 从检查点恢复' 消息")
    print("3. 检查loss值是否从合理数值开始")
    print("="*50)