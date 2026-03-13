
# So-VITS-SVC 训练指南

## 准备数据
1. 创建 `dataset_raw/speaker_name/` 目录
2. 放入 5-15 秒的 .wav 音频文件（44100Hz单声道）
3. 至少需要 10 分钟的音频数据

## 训练步骤
```bash
# 1. 重采样音频
python resample.py

# 2. 自动切分长音频
python preprocess_flist_config.py

# 3. 生成HuBERT特征
python preprocess_hubert_f0.py

# 4. 开始训练
python train.py -c configs/config.json -m 44k
```

## 监控训练
```bash
# 启动TensorBoard
tensorboard --logdir=logs/44k --port=6006
```

在浏览器打开: http://localhost:6006

## 推理测试
```bash
python inference_main.py -m logs/44k/G_latest.pth -c configs/config.json -n input.wav -t 0 -s 0
```

## 参数说明
- `-m`: 模型路径
- `-c`: 配置文件路径
- `-n`: 输入音频
- `-t`: 音高调整（半音）
- `-s`: 说话人ID
