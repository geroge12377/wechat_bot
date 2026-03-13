#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独角兽AI聊天机器人 - 一键启动脚本
自动检测环境并选择最佳启动方式
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖项"""
    dependencies = {
        'flask': False,
        'flask_cors': False,
        'requests': False,
        'TTS': False,
        'torch': False,
        'vits': False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"❌ {dep} 未安装")
    
    return dependencies

def setup_directories():
    """设置必要的目录"""
    base_dir = Path(__file__).parent
    dirs_to_create = ['static', 'audio_cache', 'voice_models', 'uploads', 'logs']
    
    for dir_name in dirs_to_create:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"📁 创建目录: {dir_name}")
    
    # 复制 index.html 到 static
    index_source = base_dir / 'index.html'
    index_dest = base_dir / 'static' / 'index.html'
    
    if index_source.exists() and not index_dest.exists():
        import shutil
        shutil.copy2(index_source, index_dest)
        print("📄 已复制 index.html 到 static 目录")
    
    return base_dir

def install_basic_dependencies():
    """安装基础依赖"""
    print("\n正在安装基础依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask', 'flask-cors', 'requests'])
        print("✅ 基础依赖安装完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败")
        return False

def main():
    print("=" * 70)
    print("      独角兽AI聊天机器人 - 智能启动器")
    print("=" * 70)
    
    # 设置目录
    base_dir = setup_directories()
    
    # 检查依赖
    print("\n检查系统依赖...")
    deps = check_dependencies()
    
    # 决定启动哪个版本
    if deps['flask'] and deps['flask_cors'] and deps['requests']:
        if deps['TTS'] or deps['torch'] or deps['vits']:
            # 有语音相关依赖，尝试启动完整版
            print("\n✅ 检测到语音依赖，尝试启动完整版...")
            app_file = base_dir / 'app.py'
            if app_file.exists():
                print("启动 app.py (完整版)")
                os.system(f'"{sys.executable}" "{app_file}"')
            else:
                print("❌ app.py 不存在")
        else:
            # 只有基础依赖，启动简化版
            print("\n⚡ 使用简化版启动（无语音功能）...")
            app_simple = base_dir / 'app_simple.py'
            if app_simple.exists():
                print("启动 app_simple.py (简化版)")
                os.system(f'"{sys.executable}" "{app_simple}"')
            else:
                print("❌ app_simple.py 不存在")
                print("请确保已创建 app_simple.py 文件")
    else:
        # 缺少基础依赖
        print("\n❌ 缺少基础依赖")
        answer = input("是否自动安装基础依赖？(y/n): ")
        if answer.lower() == 'y':
            if install_basic_dependencies():
                print("\n✅ 依赖安装成功，请重新运行此脚本")
            else:
                print("\n❌ 请手动安装: pip install flask flask-cors requests")
        else:
            print("\n请手动安装以下依赖：")
            print("pip install flask flask-cors requests")
    
    print("\n" + "=" * 70)
    input("按回车键退出...")

if __name__ == '__main__':
    main()