# 1. 生成正确格式的文件列表（带speaker标签）
python -c "
import os, random

# 收集所有音频文件
files = []
for root, dirs, files_list in os.walk('dataset/44k/unicorn'):
    for file in files_list:
        if file.endswith('.wav'):
            files.append(os.path.join(root, file).replace('\\\\', '/'))

print(f'找到 {len(files)} 个音频文件')
random.shuffle(files)
split = int(len(files) * 0.9)

# 创建带speaker标签的文件列表 (重要：格式是 path|speaker)
with open('filelists/44k/train_correct.txt', 'w') as f:
    for file in files[:split]:
        f.write(f'{file}|unicorn\\n')

with open('filelists/44k/val_correct.txt', 'w') as f:
    for file in files[split:]:
        f.write(f'{file}|unicorn\\n')

print(f'生成文件列表:')
print(f'  训练文件: {len(files[:split])} 个')
print(f'  验证文件: {len(files[split:])} 个')
print('格式: path|speaker')
"

# 2. 创建正确的配置文件
python -c "
import json

# 读取当前配置
with open('configs/44k/config.json', 'r') as f:
    config = json.load(f)

# 修正关键配置
config['model']['n_speakers'] = 1  # 正确设置为1个speaker
config['data']['training_files'] = 'filelists/44k/train_correct.txt'
config['data']['validation_files'] = 'filelists/44k/val_correct.txt'

# 保存正确配置
with open('configs/44k/config_correct.json', 'w') as f:
    json.dump(config, f, indent=2)

print('创建正确配置文件: config_correct.json')
print('关键修改:')
print('  - n_speakers: 1')
print('  - 文件列表包含speaker标签')
"