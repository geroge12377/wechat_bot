@echo off
echo 🦄 独角兽语音训练 - 安装依赖包
echo ================================

echo 📦 安装基础依赖...
pip install loguru
pip install librosa
pip install torch torchvision torchaudio
pip install numpy
pip install scipy
pip install tensorboard
pip install matplotlib
pip install tqdm
pip install scikit-learn

echo 📦 安装音频处理依赖...
pip install soundfile
pip install resampy
pip install pyworld
pip install parselmouth
pip install faiss-cpu

echo 📦 安装深度学习依赖...
pip install transformers
pip install fairseq
pip install omegaconf

echo 📦 安装其他工具...
pip install gradio
pip install flask
pip install requests

echo ✅ 依赖安装完成！
echo 🎯 现在可以运行训练了
pause