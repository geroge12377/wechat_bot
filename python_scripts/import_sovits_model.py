#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
So-VITS-SVC 模型导入工具
帮助您轻松导入和配置模型
"""

import os
import sys
import json
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

class ModelImporter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("So-VITS-SVC 模型导入工具")
        self.root.geometry("600x500")
        
        # 路径变量
        self.model_path = tk.StringVar()
        self.config_path = tk.StringVar()
        self.cluster_path = tk.StringVar()
        
        self.voice_models_dir = Path("./voice_models")
        self.voice_models_dir.mkdir(exist_ok=True)
        
        self.create_ui()
    
    def create_ui(self):
        """创建用户界面"""
        # 标题
        tk.Label(self.root, text="So-VITS-SVC 模型导入工具", 
                font=("Arial", 16, "bold")).pack(pady=10)
        
        # 说明
        instructions = """
请选择以下文件：
1. 模型文件 (G_*.pth)
2. 配置文件 (config.json)
3. 聚类模型 (可选, kmeans_*.pt)
        """
        tk.Label(self.root, text=instructions, justify=tk.LEFT).pack(pady=10)
        
        # 模型文件选择
        frame1 = tk.Frame(self.root)
        frame1.pack(pady=5, padx=20, fill=tk.X)
        tk.Label(frame1, text="模型文件:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        tk.Entry(frame1, textvariable=self.model_path, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(frame1, text="浏览", command=self.select_model).pack(side=tk.LEFT)
        
        # 配置文件选择
        frame2 = tk.Frame(self.root)
        frame2.pack(pady=5, padx=20, fill=tk.X)
        tk.Label(frame2, text="配置文件:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        tk.Entry(frame2, textvariable=self.config_path, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(frame2, text="浏览", command=self.select_config).pack(side=tk.LEFT)
        
        # 聚类模型选择（可选）
        frame3 = tk.Frame(self.root)
        frame3.pack(pady=5, padx=20, fill=tk.X)
        tk.Label(frame3, text="聚类模型(可选):", width=12, anchor=tk.W).pack(side=tk.LEFT)
        tk.Entry(frame3, textvariable=self.cluster_path, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(frame3, text="浏览", command=self.select_cluster).pack(side=tk.LEFT)
        
        # 导入按钮
        tk.Button(self.root, text="导入模型", command=self.import_model,
                 bg="#4CAF50", fg="white", font=("Arial", 12),
                 width=20, height=2).pack(pady=20)
        
        # 日志区域
        tk.Label(self.root, text="导入日志:").pack(anchor=tk.W, padx=20)
        self.log_text = tk.Text(self.root, height=10, width=70)
        self.log_text.pack(padx=20, pady=5)
        
        # 滚动条
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
    
    def log(self, message):
        """添加日志信息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def select_model(self):
        """选择模型文件"""
        filename = filedialog.askopenfilename(
            title="选择模型文件",
            filetypes=[("PyTorch模型", "*.pth"), ("所有文件", "*.*")]
        )
        if filename:
            self.model_path.set(filename)
            self.log(f"已选择模型: {Path(filename).name}")
    
    def select_config(self):
        """选择配置文件"""
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            self.config_path.set(filename)
            self.log(f"已选择配置: {Path(filename).name}")
    
    def select_cluster(self):
        """选择聚类模型"""
        filename = filedialog.askopenfilename(
            title="选择聚类模型（可选）",
            filetypes=[("PyTorch模型", "*.pt"), ("所有文件", "*.*")]
        )
        if filename:
            self.cluster_path.set(filename)
            self.log(f"已选择聚类模型: {Path(filename).name}")
    
    def import_model(self):
        """执行模型导入"""
        model_file = self.model_path.get()
        config_file = self.config_path.get()
        
        if not model_file or not config_file:
            messagebox.showerror("错误", "请选择模型文件和配置文件！")
            return
        
        try:
            self.log("开始导入模型...")
            
            # 创建目标文件名
            model_name = "unicorn_voice"
            
            # 复制模型文件
            dest_model = self.voice_models_dir / f"{model_name}.pth"
            shutil.copy2(model_file, dest_model)
            self.log(f"✅ 模型文件已复制到: {dest_model}")
            
            # 复制配置文件
            dest_config = self.voice_models_dir / f"{model_name}_config.json"
            shutil.copy2(config_file, dest_config)
            self.log(f"✅ 配置文件已复制到: {dest_config}")
            
            # 复制聚类模型（如果有）
            if self.cluster_path.get():
                dest_cluster = self.voice_models_dir / f"{model_name}_kmeans.pt"
                shutil.copy2(self.cluster_path.get(), dest_cluster)
                self.log(f"✅ 聚类模型已复制到: {dest_cluster}")
            
            # 验证配置文件
            with open(dest_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.log("\n模型信息:")
            self.log(f"  采样率: {config.get('data', {}).get('sampling_rate', 'N/A')}")
            self.log(f"  说话人数量: {config.get('data', {}).get('n_speakers', 'N/A')}")
            
            if 'spk' in config:
                self.log("  说话人列表:")
                for name, idx in config['spk'].items():
                    self.log(f"    - {name}: {idx}")
            
            # 创建模型信息文件
            model_info = {
                "model_name": model_name,
                "model_path": str(dest_model),
                "config_path": str(dest_config),
                "cluster_path": str(dest_cluster) if self.cluster_path.get() else None,
                "import_time": str(Path(model_file).stat().st_mtime),
                "source_files": {
                    "model": model_file,
                    "config": config_file,
                    "cluster": self.cluster_path.get() if self.cluster_path.get() else None
                }
            }
            
            info_file = self.voice_models_dir / f"{model_name}_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, indent=2, ensure_ascii=False)
            
            self.log(f"\n✅ 模型导入成功！")
            self.log(f"模型已保存为: {model_name}")
            self.log("\n您现在可以在独角兽AI中使用此模型了！")
            
            messagebox.showinfo("成功", "模型导入成功！")
            
        except Exception as e:
            self.log(f"\n❌ 导入失败: {str(e)}")
            messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def import_model_cli():
    """命令行导入模式"""
    print("=" * 60)
    print("So-VITS-SVC 模型导入工具（命令行模式）")
    print("=" * 60)
    
    voice_models_dir = Path("./voice_models")
    voice_models_dir.mkdir(exist_ok=True)
    
    # 获取文件路径
    model_path = input("请输入模型文件路径 (G_*.pth): ").strip()
    if not Path(model_path).exists():
        print("❌ 模型文件不存在！")
        return
    
    config_path = input("请输入配置文件路径 (config.json): ").strip()
    if not Path(config_path).exists():
        print("❌ 配置文件不存在！")
        return
    
    cluster_path = input("请输入聚类模型路径 (可选，直接回车跳过): ").strip()
    
    model_name = input("请输入模型名称 (默认: unicorn_voice): ").strip()
    if not model_name:
        model_name = "unicorn_voice"
    
    try:
        # 复制文件
        dest_model = voice_models_dir / f"{model_name}.pth"
        shutil.copy2(model_path, dest_model)
        print(f"✅ 模型文件已复制")
        
        dest_config = voice_models_dir / f"{model_name}_config.json"
        shutil.copy2(config_path, dest_config)
        print(f"✅ 配置文件已复制")
        
        if cluster_path and Path(cluster_path).exists():
            dest_cluster = voice_models_dir / f"{model_name}_kmeans.pt"
            shutil.copy2(cluster_path, dest_cluster)
            print(f"✅ 聚类模型已复制")
        
        print(f"\n✅ 模型 '{model_name}' 导入成功！")
        print(f"文件已保存到: {voice_models_dir}")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")


if __name__ == "__main__":
    print("选择导入模式:")
    print("1. 图形界面模式")
    print("2. 命令行模式")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        try:
            importer = ModelImporter()
            importer.run()
        except Exception as e:
            print(f"GUI模式启动失败: {e}")
            print("切换到命令行模式...")
            import_model_cli()
    else:
        import_model_cli()
    
    input("\n按回车键退出...")