import json

try:
    with open('configs/44k/config_clean.json', 'r') as f:
        config = json.load(f)
    
    # 检查关键字段
    assert isinstance(config['model'].get('type', ''), str), "model.type 必须是字符串"
    assert config['model']['type'] == "softvc", "model.type 应为 'softvc'"
    
    print("配置文件验证通过！")
    print("模型类型:", config['model']['type'])
    
except Exception as e:
    print("配置错误:", str(e))