#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VITS训练服务器集成模块
VITS Training Server Integration for Training Server
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# 导入VITS训练器
try:
    from vits_trainer import (
        VITSTrainingManager, 
        VITSTrainingConfig,
        create_vits_trainer,
        VITS_AVAILABLE
    )
except ImportError:
    print("⚠️ VITS训练模块未找到")
    VITS_AVAILABLE = False
    VITSTrainingManager = None
    VITSTrainingConfig = None

# 创建Blueprint
vits_bp = Blueprint('vits_training', __name__, url_prefix='/api/vits')

# 全局VITS训练管理器
vits_manager = None

# ======================
# VITS训练状态管理
# ======================
class VITSTrainingStatus:
    """VITS训练状态管理"""
    
    def __init__(self):
        self.current_task = None
        self.training_history = []
        self.progress = {}
        
    def create_task(self, task_info: Dict) -> str:
        """创建新任务"""
        task_id = f"vits_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_task = {
            'task_id': task_id,
            'status': 'created',
            'progress': 0.0,
            'config': task_info.get('config', {}),
            'created_at': datetime.now().isoformat(),
            'message': '任务已创建'
        }
        
        self.training_history.append(self.current_task.copy())
        return task_id
    
    def update_progress(self, progress_data: Dict):
        """更新训练进度"""
        if self.current_task:
            if 'epoch' in progress_data:
                total_epochs = self.current_task['config'].get('epochs', 10000)
                self.current_task['progress'] = (progress_data['epoch'] / total_epochs) * 100
            
            self.current_task['current_epoch'] = progress_data.get('epoch', 0)
            self.current_task['global_step'] = progress_data.get('global_step', 0)
            self.current_task['losses'] = progress_data.get('losses', {})
            self.current_task['message'] = self._format_progress_message(progress_data)
    
    def _format_progress_message(self, progress_data: Dict) -> str:
        """格式化进度消息"""
        if progress_data.get('type') == 'evaluation':
            return f"评估中 - 损失: {progress_data.get('eval_losses', {}).get('eval_loss', 0):.4f}"
        else:
            epoch = progress_data.get('epoch', 0)
            batch = progress_data.get('batch', 0)
            total_batches = progress_data.get('total_batches', 0)
            return f"训练中 - Epoch {epoch} [{batch}/{total_batches}]"
    
    def get_current_status(self) -> Optional[Dict]:
        """获取当前状态"""
        return self.current_task
    
    def complete_task(self, success: bool, message: str):
        """完成任务"""
        if self.current_task:
            self.current_task['status'] = 'completed' if success else 'failed'
            self.current_task['message'] = message
            self.current_task['completed_at'] = datetime.now().isoformat()

# 创建状态管理器
vits_status = VITSTrainingStatus()

# ======================
# 初始化函数
# ======================
def init_vits_training():
    """初始化VITS训练系统"""
    global vits_manager
    
    if not VITS_AVAILABLE:
        return False
    
    try:
        vits_manager = create_vits_trainer()
        
        if vits_manager:
            # 设置进度回调
            vits_manager.progress_callback = vits_status.update_progress
            print("✅ VITS训练系统初始化成功")
            return True
        else:
            print("❌ VITS训练系统初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ VITS初始化错误: {e}")
        return False

# ======================
# API路由
# ======================

@vits_bp.route('/status', methods=['GET'])
def get_vits_status():
    """获取VITS训练系统状态"""
    try:
        return jsonify({
            'status': 'success',
            'vits_available': VITS_AVAILABLE,
            'vits_initialized': vits_manager is not None,
            'current_task': vits_status.get_current_status(),
            'is_training': vits_manager.is_training if vits_manager else False
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@vits_bp.route('/create_task', methods=['POST'])
def create_vits_training_task():
    """创建VITS训练任务"""
    try:
        if not vits_manager:
            return jsonify({'error': 'VITS系统未初始化'}), 500
        
        if vits_manager.is_training:
            return jsonify({'error': '已有训练任务在进行中'}), 400
        
        data = request.json
        
        # 验证必需参数
        if 'uploaded_files' not in data:
            return jsonify({'error': '缺少训练文件'}), 400
        
        uploaded_files = data['uploaded_files']
        
        # 分离音频和文本文件
        audio_files = []
        text_files = []
        
        for file_info in uploaded_files:
            file_path = Path(file_info['path'])
            if file_info['type'] == 'audio':
                audio_files.append(file_path)
            elif file_info['type'] == 'text':
                text_files.append(file_path)
        
        if len(audio_files) != len(text_files):
            return jsonify({'error': '音频和文本文件数量不匹配'}), 400
        
        # 创建训练配置
        config_params = data.get('config', {})
        config = VITSTrainingConfig(
            model_name=data.get('model_name', 'unicorn_vits'),
            epochs=config_params.get('epochs', 10000),
            batch_size=config_params.get('batch_size', 16),
            learning_rate=config_params.get('learning_rate', 2e-4),
            n_speakers=config_params.get('n_speakers', 1),
            sampling_rate=config_params.get('sampling_rate', 22050)
        )
        
        # 创建任务
        task_id = vits_status.create_task({
            'config': config.__dict__,
            'audio_files': len(audio_files),
            'text_files': len(text_files)
        })
        
        # 创建训练任务
        success, message = vits_manager.create_training_task(
            audio_files, text_files, config
        )
        
        if success:
            # 启动训练
            vits_manager.start_training()
            
            return jsonify({
                'status': 'success',
                'task_id': task_id,
                'message': '训练任务已启动'
            })
        else:
            vits_status.complete_task(False, message)
            return jsonify({'error': message}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vits_bp.route('/stop', methods=['POST'])
def stop_vits_training():
    """停止VITS训练"""
    try:
        if not vits_manager:
            return jsonify({'error': 'VITS系统未初始化'}), 500
        
        if not vits_manager.is_training:
            return jsonify({'error': '没有正在进行的训练'}), 400
        
        vits_manager.stop_training()
        vits_status.complete_task(False, '训练被用户中断')
        
        return jsonify({
            'status': 'success',
            'message': '训练已停止'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vits_bp.route('/models', methods=['GET'])
def get_vits_models():
    """获取可用的VITS模型"""
    try:
        models_dir = Path(__file__).parent / "voice_models"
        models = []
        
        # 扫描VITS模型
        for model_file in models_dir.glob("*.pth"):
            config_file = model_file.with_suffix(".json")
            
            model_info = {
                'name': model_file.stem,
                'model_file': str(model_file),
                'config_file': str(config_file) if config_file.exists() else None,
                'size': model_file.stat().st_size,
                'created': datetime.fromtimestamp(model_file.stat().st_mtime).isoformat()
            }
            
            # 尝试读取配置信息
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    model_info['config'] = {
                        'sampling_rate': config_data.get('sampling_rate', 22050),
                        'n_speakers': config_data.get('n_speakers', 1)
                    }
                except:
                    pass
            
            models.append(model_info)
        
        return jsonify({
            'status': 'success',
            'models': models,
            'count': len(models)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vits_bp.route('/export/<model_name>', methods=['GET'])
def export_vits_model(model_name):
    """导出VITS模型用于推理"""
    try:
        models_dir = Path(__file__).parent / "voice_models"
        model_path = models_dir / f"{model_name}.pth"
        config_path = models_dir / f"{model_name}.json"
        
        if not model_path.exists():
            return jsonify({'error': '模型不存在'}), 404
        
        # 返回模型文件路径，前端可以下载
        return jsonify({
            'status': 'success',
            'model_name': model_name,
            'files': {
                'model': str(model_path),
                'config': str(config_path) if config_path.exists() else None
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vits_bp.route('/config/presets', methods=['GET'])
def get_config_presets():
    """获取预设配置"""
    try:
        presets = {
            'fast': {
                'name': '快速训练',
                'description': '适合快速测试，质量较低',
                'config': {
                    'epochs': 1000,
                    'batch_size': 32,
                    'learning_rate': 3e-4,
                    'eval_interval': 500,
                    'save_interval': 1000
                }
            },
            'balanced': {
                'name': '平衡训练',
                'description': '质量和速度平衡',
                'config': {
                    'epochs': 5000,
                    'batch_size': 16,
                    'learning_rate': 2e-4,
                    'eval_interval': 1000,
                    'save_interval': 2500
                }
            },
            'quality': {
                'name': '高质量训练',
                'description': '最佳质量，训练时间较长',
                'config': {
                    'epochs': 10000,
                    'batch_size': 8,
                    'learning_rate': 1e-4,
                    'eval_interval': 1000,
                    'save_interval': 5000
                }
            }
        }
        
        return jsonify({
            'status': 'success',
            'presets': presets
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ======================
# 辅助函数
# ======================
def validate_audio_files(file_paths: List[Path]) -> tuple:
    """验证音频文件"""
    valid_files = []
    errors = []
    
    for file_path in file_paths:
        try:
            # 检查文件存在
            if not file_path.exists():
                errors.append(f"{file_path.name}: 文件不存在")
                continue
            
            # 检查文件大小
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:
                errors.append(f"{file_path.name}: 文件过大 (>50MB)")
                continue
            
            if file_size_mb < 0.01:
                errors.append(f"{file_path.name}: 文件过小 (<10KB)")
                continue
            
            valid_files.append(file_path)
            
        except Exception as e:
            errors.append(f"{file_path.name}: {str(e)}")
    
    return valid_files, errors

def validate_text_files(file_paths: List[Path]) -> tuple:
    """验证文本文件"""
    valid_files = []
    errors = []
    
    for file_path in file_paths:
        try:
            # 检查文件存在
            if not file_path.exists():
                errors.append(f"{file_path.name}: 文件不存在")
                continue
            
            # 读取并验证内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                errors.append(f"{file_path.name}: 文件为空")
                continue
            
            if len(content) > 1000:
                errors.append(f"{file_path.name}: 文本过长 (>1000字符)")
                continue
            
            valid_files.append(file_path)
            
        except Exception as e:
            errors.append(f"{file_path.name}: {str(e)}")
    
    return valid_files, errors

# ======================
# 集成到训练服务器
# ======================
def integrate_vits_to_training_server(app):
    """将VITS功能集成到训练服务器"""
    
    # 注册Blueprint
    app.register_blueprint(vits_bp)
    
    # 初始化VITS系统
    init_vits_training()
    
    # 添加到训练服务器的路由列表
    print("✅ VITS训练路由已注册:")
    print("   - /api/vits/status")
    print("   - /api/vits/create_task")
    print("   - /api/vits/stop")
    print("   - /api/vits/models")
    print("   - /api/vits/export/<model_name>")
    print("   - /api/vits/config/presets")

# 如果作为模块导入，自动初始化
if __name__ != '__main__':
    init_vits_training()