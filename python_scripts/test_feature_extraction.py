import torch
import numpy as np
from fairseq import checkpoint_utils
import parselmouth
import librosa

# 1. 加载HuBERT模型
models, _, _ = checkpoint_utils.load_model_ensemble_and_task(
    ["hubert_base.pt"],
    suffix="",
)
hubert_model = models[0].cuda()

# 2. 提取HuBERT特征
audio, sr = librosa.load("dataset/44k/unicorn/unicorn_battle_25.wav", sr=16000)
audio = torch.FloatTensor(audio).unsqueeze(0).cuda()

with torch.no_grad():
    c = hubert_model(audio, output_layer=12)["last_hidden_state"]
torch.save(c.cpu(), "test.soft.pt")
print("HuBERT特征已保存: test.soft.pt")

# 3. 提取F0特征
sound = parselmouth.Sound("dataset/44k/unicorn/unicorn_battle_25.wav")
pitch = sound.to_pitch()
f0 = pitch.selected_array['frequency']
np.save("test.f0.npy", f0)
print("F0特征已保存: test.f0.npy")