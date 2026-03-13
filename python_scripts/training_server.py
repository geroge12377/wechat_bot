# 快速修补原版train.py的方法
# 
# 1. 注释掉数据集验证行（第61行左右）：
# 把这行：
# validate_and_fix_dataset(hps)
# 改为：
# # validate_and_fix_dataset(hps)  # 临时跳过数据集验证
# print("⚠️ 跳过数据集验证，直接开始训练")

# 2. 移除强制CUDA检查（第58行左右）：
# 把这行：
# assert torch.cuda.is_available(), "CPU训练不被支持"
# 改为：
# if not torch.cuda.is_available():
#     print("⚠️ CUDA不可用，将使用CPU训练")

# 3. 或者直接用这个一键修补脚本：

import sys
import os

def patch_train_py():
    """一键修补train.py"""
    print("🔧 正在修补train.py...")
    
    # 备份原文件
    if os.path.exists("train.py"):
        import shutil
        shutil.copy("train.py", "train.py.backup")
        print("✅ 已备份原文件为 train.py.backup")
    
    # 读取原文件
    with open("train.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 应用修补
    patches = [
        # 跳过数据集验证
        ("validate_and_fix_dataset(hps)", 
         '# validate_and_fix_dataset(hps)  # 临时跳过\n    print("⚠️ 跳过数据集验证，直接开始训练")'),
        
        # 移除强制CUDA检查
        ('assert torch.cuda.is_available(), "CPU训练不被支持"',
         'if not torch.cuda.is_available():\n        print("⚠️ CUDA不可用，将使用CPU训练")'),
    ]
    
    patched_count = 0
    for old_code, new_code in patches:
        if old_code in content:
            content = content.replace(old_code, new_code)
            patched_count += 1
            print(f"✅ 修补: {old_code[:30]}...")
    
    # 写入修补后的文件
    with open("train_patched.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"🎉 修补完成！应用了 {patched_count} 个修补")
    print("📄 修补后的文件保存为: train_patched.py")
    print("\n使用修补版训练:")
    print("python train_patched.py -c 44k/config.json -m logs/44k")

if __name__ == "__main__":
    patch_train_py()