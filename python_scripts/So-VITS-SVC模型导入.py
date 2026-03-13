#!/usr/bin/env python3
"""
完整修复so-vits-svc检查点和配置问题
"""

import os
import json
import shutil
from pathlib import Path

def complete_fix():
    """完整修复方案"""
    print("🔧 开始完整修复so-vits-svc问题...")
    print("=" * 60)
    
    # 1. 确定项目根目录
    project_root = Path("so-vits-svc-4.1-Stable")
    if not project_root.exists():
        print("❌ 项目目录不存在，请确认当前路径")
        return False
    
    os.chdir(project_root)
    print(f"📁 进入项目目录: {project_root.absolute()}")
    
    # 2. 找到配置文件
    config_paths = [
        Path("44k/config.json"),
        Path("configs/44k/config.json"),
        Path("44k_config.json")
    ]
    
    config_path = None
    for path in config_paths:
        if path.exists():
            config_path = path
            break
    
    if not config_path:
        print("❌ 未找到配置文件")
        print("请检查以下位置:")
        for path in config_paths:
            print(f"  - {path}")
        return False
    
    print(f"📄 找到配置文件: {config_path}")
    
    # 3. 检查检查点文件
    checkpoint_files = {
        "G_25": Path("logs/44k/G_25.pth"),
        "D_25": Path("logs/44k/D_25.pth")
    }
    
    missing_files = []
    for name, path in checkpoint_files.items():
        if path.exists():
            print(f"✅ 找到检查点: {path}")
        else:
            missing_files.append(name)
            print(f"❌ 缺少检查点: {path}")
    
    if missing_files:
        print(f"❌ 缺少关键检查点文件，无法继续")
        return False
    
    # 4. 修复配置文件
    if not fix_config_file(config_path):
        return False
    
    # 5. 确保检查点在正确位置
    if not ensure_checkpoints_in_correct_location():
        return False
    
    # 6. 创建目录结构
    create_directory_structure()
    
    # 7. 提供正确的训练命令
    provide_training_commands(config_path)
    
    return True

def fix_config_file(config_path):
    """修复配置文件"""
    print(f"\n🔧 修复配置文件: {config_path}")
    
    # 备份原文件
    backup_path = str(config_path) + ".backup"
    shutil.copy2(config_path, backup_path)
    print(f"✅ 已备份到: {backup_path}")
    
    try:
        # 读取配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 确保有model_dir字段
        if 'model_dir' not in config:
            config['model_dir'] = './logs/44k'
            print("✅ 添加了model_dir字段")
        else:
            config['model_dir'] = './logs/44k'
            print("✅ 更新了model_dir字段")
        
        # 更新train部分的路径
        if 'train' in config:
            config['train']['save_dir'] = 'logs/44k'
            config['train']['checkpoint_dir'] = 'logs/44k'
            print("✅ 更新了train配置中的路径")
        
        # 保存修改后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ 配置文件修复完成")
        return True
        
    except Exception as e:
        print(f"❌ 修复配置文件失败: {e}")
        # 恢复备份
        shutil.copy2(backup_path, config_path)
        return False

def ensure_checkpoints_in_correct_location():
    """确保检查点在正确位置"""
    print(f"\n🔧 确保检查点位置正确...")
    
    source_dir = Path("logs/44k")
    target_dir = Path("logs")
    
    # 确保目标目录存在
    target_dir.mkdir(exist_ok=True)
    
    # 复制检查点文件
    files_to_copy = [
        ("G_25.pth", "生成器"),
        ("D_25.pth", "判别器")
    ]
    
    try:
        for filename, desc in files_to_copy:
            source = source_dir / filename
            target = target_dir / filename
            
            if source.exists():
                shutil.copy2(source, target)
                print(f"✅ 已复制{desc}检查点: {source} -> {target}")
            else:
                print(f"❌ 源文件不存在: {source}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 复制检查点失败: {e}")
        return False

def create_directory_structure():
    """创建必要的目录结构"""
    print(f"\n🛠️ 创建目录结构...")
    
    directories = [
        "logs",
        "logs/44k", 
        "lightning_logs",
        "lightning_logs/version_0",
        "lightning_logs/version_0/checkpoints"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")

def provide_training_commands(config_path):
    """提供正确的训练命令"""
    print(f"\n🚀 正确的训练命令:")
    
    # 方法1：使用Python直接调用
    print(f"方法1 (推荐):")
    if "44k" in str(config_path):
        print(f"cd 44k")
        print(f"python ../train.py -c config.json")
    else:
        print(f"python train.py -c {config_path}")
    
    # 方法2：使用svc命令（如果可用）
    print(f"\n方法2 (如果svc命令可用):")
    print(f"svc train -c {config_path} -m logs/44k")
    
    # 方法3：完整路径
    print(f"\n方法3 (完整路径):")
    abs_config = Path(config_path).absolute()
    print(f"python train.py -c \"{abs_config}\"")

def verify_fix():
    """验证修复结果"""
    print(f"\n🔍 验证修复结果:")
    
    # 检查配置文件
    config_files = ["44k/config.json", "configs/44k/config.json"]
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                model_dir = config.get('model_dir', '未设置')
                print(f"✅ {path}: model_dir = {model_dir}")
            except:
                print(f"❌ {path}: 读取失败")
    
    # 检查检查点文件
    checkpoint_locations = [
        ("logs/G_25.pth", "主位置生成器"),
        ("logs/D_25.pth", "主位置判别器"),
        ("logs/44k/G_25.pth", "备份位置生成器"),
        ("logs/44k/D_25.pth", "备份位置判别器")
    ]
    
    for path, desc in checkpoint_locations:
        if Path(path).exists():
            size = Path(path).stat().st_size / (1024*1024)
            print(f"✅ {desc}: {path} ({size:.1f} MB)")
        else:
            print(f"❌ {desc}: {path} 不存在")

if __name__ == "__main__":
    try:
        if complete_fix():
            print(f"\n" + "="*60)
            print("🎉 修复完成！")
            print("="*60)
            verify_fix()
            print(f"\n现在可以重新启动训练了！")
        else:
            print(f"\n❌ 修复失败，请检查上述错误信息")
    except Exception as e:
        print(f"❌ 修复过程出错: {e}")
        import traceback
        traceback.print_exc()