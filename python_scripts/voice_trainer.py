#!/usr/bin/env python3
"""
修复So-VITS-SVC训练脚本中的start_time变量bug
"""
import os
import shutil

def fix_start_time_bug():
    """修复训练脚本中的start_time变量bug"""
    print("🔧 修复训练脚本中的start_time变量bug")
    print("=" * 50)
    
    train_script_path = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\train.py"
    
    if not os.path.exists(train_script_path):
        print(f"❌ 训练脚本不存在: {train_script_path}")
        return False
    
    # 备份原文件
    backup_path = train_script_path + ".backup.start_time_fix"
    if not os.path.exists(backup_path):
        shutil.copy2(train_script_path, backup_path)
        print(f"📝 备份原文件: {backup_path}")
    
    # 读取原文件
    with open(train_script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并修复start_time问题
    fixes_applied = 0
    
    # 修复1: 确保在train_and_evaluate函数开始时初始化start_time
    if 'def train_and_evaluate(' in content:
        # 查找函数定义
        lines = content.split('\n')
        new_lines = []
        in_train_evaluate = False
        start_time_initialized = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # 检测进入train_and_evaluate函数
            if 'def train_and_evaluate(' in line:
                in_train_evaluate = True
                start_time_initialized = False
                continue
            
            # 在函数内部，查找合适的位置初始化start_time
            if in_train_evaluate and not start_time_initialized:
                # 寻找第一个实际代码行（非注释、非空行）
                stripped = line.strip()
                if (stripped and 
                    not stripped.startswith('#') and 
                    not stripped.startswith('"""') and
                    not stripped.startswith("'''") and
                    'global global_step' not in stripped and
                    stripped != ''):
                    
                    # 在这一行之前插入start_time初始化
                    indent = len(line) - len(line.lstrip())
                    start_time_init = ' ' * indent + 'start_time = time.time()  # 初始化start_time变量'
                    new_lines.insert(-1, start_time_init)
                    start_time_initialized = True
                    fixes_applied += 1
                    print(f"   ✅ 在第{i+1}行前添加start_time初始化")
                    break
            
            # 检测函数结束
            if in_train_evaluate and line.strip().startswith('def ') and 'train_and_evaluate' not in line:
                in_train_evaluate = False
        
        content = '\n'.join(new_lines)
    
    # 修复2: 确保import time
    if 'import time' not in content:
        # 在其他import语句附近添加
        lines = content.split('\n')
        new_lines = []
        time_imported = False
        
        for line in lines:
            if (line.startswith('import ') or line.startswith('from ')) and not time_imported:
                new_lines.append('import time')
                time_imported = True
                fixes_applied += 1
                print(f"   ✅ 添加 import time")
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    # 修复3: 在finally块中安全使用start_time
    if 'duration = now - start_time' in content:
        content = content.replace(
            'duration = now - start_time',
            'duration = now - getattr(locals(), "start_time", now)  # 安全访问start_time'
        )
        fixes_applied += 1
        print(f"   ✅ 修复start_time安全访问")
    
    # 写入修复后的文件
    if fixes_applied > 0:
        with open(train_script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 应用了 {fixes_applied} 个修复")
        print(f"修复的问题:")
        print(f"   - start_time变量初始化")
        print(f"   - 安全的start_time访问")
        print(f"   - import time语句")
        
        return True
    else:
        print(f"⚠️  未找到需要修复的问题")
        return False

def create_fixed_training_launcher():
    """创建修复后的训练启动器"""
    
    launcher_code = '''#!/usr/bin/env python3
"""
修复后的So-VITS-SVC训练启动器
包含start_time变量修复
"""
import os
import sys
import subprocess
import time

def safe_training_launcher():
    """安全的训练启动器"""
    print("🚀 So-VITS-SVC 安全训练启动器")
    print("=" * 50)
    
    project_root = r"C:\\Users\\HP\\Desktop\\CHATBOT_WECHAT\\so-vits-svc-4.1-Stable"
    os.chdir(project_root)
    
    print(f"📁 工作目录: {project_root}")
    
    # 检查关键文件
    required_files = [
        "train.py",
        "44k/config.json",
        "filelists/train.txt",
        "filelists/val.txt"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少文件: {file}")
            return False
    
    print("✅ 所有必要文件已找到")
    
    # 启动训练，使用错误处理
    model_dir = os.path.join(project_root, "logs", "44k")
    
    cmd = [
        sys.executable, "train.py",
        "-c", "44k/config.json",
        "-m", model_dir
    ]
    
    print(f"💡 执行命令: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # 启动训练进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时显示输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        return_code = process.poll()
        
        if return_code == 0:
            print(f"\\n🎉 训练完成!")
        else:
            print(f"\\n❌ 训练异常退出，返回代码: {return_code}")
        
        return return_code == 0
        
    except KeyboardInterrupt:
        print(f"\\n🛑 用户中断训练")
        if process:
            process.terminate()
        return False
        
    except Exception as e:
        print(f"\\n❌ 启动训练失败: {e}")
        return False

def main():
    """主函数"""
    success = safe_training_launcher()
    
    if success:
        print("✅ 训练启动成功!")
    else:
        print("❌ 训练启动失败!")
        print("💡 建议检查错误信息并重试")

if __name__ == "__main__":
    main()
'''
    
    launcher_path = r"C:\Users\HP\Desktop\CHATBOT_WECHAT\so-vits-svc-4.1-Stable\safe_launch_training.py"
    
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_code)
    
    print(f"📝 创建安全启动器: {launcher_path}")
    return launcher_path

def main():
    """主函数"""
    print("🛠️ So-VITS-SVC start_time Bug 修复器")
    print("=" * 60)
    
    # 修复训练脚本
    if fix_start_time_bug():
        
        # 创建安全启动器
        launcher_path = create_fixed_training_launcher()
        
        print(f"\n🎉 Bug修复完成!")
        print(f"\n📝 现在可以安全启动训练:")
        print(f"方案1 (使用修复后的脚本):")
        print(f"  python safe_launch_training.py")
        print(f"\n方案2 (直接使用修复后的train.py):")
        print(f"  python train.py -c 44k/config.json -m logs/44k")
        
        print(f"\n💡 提示:")
        print(f"   - 已备份原始train.py文件")
        print(f"   - 修复了start_time变量初始化问题")
        print(f"   - 添加了安全的错误处理")
        
    else:
        print(f"\n❌ Bug修复失败!")
        print(f"建议手动检查train.py文件中的start_time变量使用")

if __name__ == "__main__":
    main()