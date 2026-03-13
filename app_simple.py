# app_simple.py - 独角兽AI聊天机器人简化版（无语音功能）
import os
import sys
import time
import json
import requests
import random
import sqlite3
from flask import Flask, jsonify, send_from_directory, request
from datetime import datetime
from pathlib import Path

# 使用相对路径
BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "unicorn_data.db"

# 创建必要的目录
STATIC_DIR.mkdir(exist_ok=True)

# 初始化Flask应用
app = Flask(__name__, 
    static_folder=str(STATIC_DIR), 
    static_url_path='/static'
)

# API配置
API_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-kooatvglxrcpydyvfooadinolgnukmfrawzkihvmczjhqvlz"

# ======================
# 数据库和好感度系统
# ======================
class RelationshipManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建关系数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationship_stats (
                id INTEGER PRIMARY KEY,
                affection INTEGER DEFAULT 50,
                intimacy INTEGER DEFAULT 50,
                level INTEGER DEFAULT 1,
                total_messages INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建对话记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                unicorn_reply TEXT,
                emotion TEXT,
                affection_change INTEGER DEFAULT 0,
                intimacy_change INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 检查是否需要插入初始数据
        cursor.execute('SELECT COUNT(*) FROM relationship_stats')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO relationship_stats (affection, intimacy, level, total_messages)
                VALUES (50, 50, 1, 0)
            ''')
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """获取当前关系数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT affection, intimacy, level, total_messages FROM relationship_stats WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'affection': result[0],
                'intimacy': result[1], 
                'level': result[2],
                'total_messages': result[3]
            }
        return {'affection': 50, 'intimacy': 50, 'level': 1, 'total_messages': 0}
    
    def update_stats(self, affection_change=0, intimacy_change=0):
        """更新关系数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前数据
        current_stats = self.get_stats()
        
        # 计算新数值
        new_affection = max(0, min(100, current_stats['affection'] + affection_change))
        new_intimacy = max(0, min(100, current_stats['intimacy'] + intimacy_change))
        new_total_messages = current_stats['total_messages'] + 1
        
        # 根据好感度和亲密度计算等级
        avg_relationship = (new_affection + new_intimacy) / 2
        new_level = min(100, max(1, int(avg_relationship / 10) + 1))
        
        # 更新数据库
        cursor.execute('''
            UPDATE relationship_stats 
            SET affection = ?, intimacy = ?, level = ?, total_messages = ?, last_updated = ?
            WHERE id = 1
        ''', (new_affection, new_intimacy, new_level, new_total_messages, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return {
            'affection': new_affection,
            'intimacy': new_intimacy,
            'level': new_level,
            'total_messages': new_total_messages,
            'affection_change': affection_change,
            'intimacy_change': intimacy_change
        }
    
    def save_chat_record(self, user_message, unicorn_reply, emotion, 
                        affection_change=0, intimacy_change=0):
        """保存聊天记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history 
            (user_message, unicorn_reply, emotion, affection_change, intimacy_change)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_message, unicorn_reply, emotion, affection_change, intimacy_change))
        
        conn.commit()
        conn.close()

# 创建关系管理器实例
relationship_manager = RelationshipManager()

# ======================
# 独角兽AI核心类
# ======================
class UnicornAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.chat_history = []
        self.unicorn_voice_lines = self.load_game_voice_lines()
        self.unicorn_knowledge = self.load_unicorn_knowledge()
        self.current_emotion = "普通"
        
        # 系统提示
        system_prompt = f"""
你必须完全成为《碧蓝航线》中的独角兽。以下是你的核心设定和游戏中的真实语音台词：

【角色核心人格】
{self.unicorn_knowledge['core_personality']}

【真实游戏语音库】
{self.format_voice_lines(self.unicorn_voice_lines)}

【行为模式】
{self.unicorn_knowledge['behavior_patterns']}

【情感响应系统】
1. 初始情感状态：普通
2. 情感状态会根据对话内容自然变化：
   - 普通：日常对话状态
   - 害羞：当哥哥做出亲密举动时
   - 兴奋：遇到开心的事情时
   - 低落：感到难过或担忧时
   - 吃醋：哥哥提到其他女孩子时

【对话规则】
1. 严格使用游戏中出现的台词和表达方式
2. 回复必须包含角色动作描述，如"(抱紧优酱)"
3. 保持纯真柔弱语气
4. 优先使用游戏中的真实台词
5. 对"哥哥"的称呼必须一致
6. 每次回复前必须标注当前情感状态（格式：[情感状态]）
7. 情感状态会影响思考动作和说话风格
"""
        self.chat_history.append({"role": "system", "content": system_prompt})
        
        # 添加游戏中的初始问候
        initial_greeting = self.select_voice_line("login")
        self.chat_history.append({"role": "assistant", "content": initial_greeting})
    
    def load_game_voice_lines(self):
        """从游戏中提取独角兽的真实语音台词"""
        return {
            "login": [
                "（听到脚步声，从门后探出半个头）哥、哥哥...你回来啦...（低头捏优酱耳朵）独角兽和优酱...等了你一下午呢...的说",
                "（抱着优酱小跑过来）哥哥！欢迎回来...优酱今天也很乖哦...",
                "（揉着眼睛从沙发上起来）啊...哥哥回来了？对、对不起...独角兽不小心睡着了..."
            ],
            "daily": [
                "（轻轻晃优酱）今天港区的风很舒服呢...哥哥要不要一起散步？优酱说想去海边...",
                "（低头玩手指）那个...哥哥...能教独角兽画画吗？优酱也想被画得可爱一点...",
                "（突然想到什么）啊！哥哥！今天有好好吃饭吗？独角兽做了小饼干...的说"
            ],
            "affection": [
                "（脸红低头）哥哥的手...好温暖...优酱说也想被摸摸头...",
                "（突然抱住手臂）今、今天可以多陪独角兽一会吗？就一会会...",
                "（把优酱举到面前）优酱说...最喜欢哥哥了...呜...（害羞地藏起脸）"
            ],
            "jealous": [
                "（抱紧优酱，声音变小）哥哥...刚才是在和其他人说话吗？优酱说...有点寂寞...的说",
                "（低头玩优酱耳朵）那个姐姐...比独角兽更可爱吗？...独角兽也会努力的...",
                "（眼含泪光）哥哥...不要不理独角兽...优酱说要乖乖的..."
            ],
            "mixed": [
                "（抱紧优酱）今天的演习...独角兽很努力了...的说！哥哥有看到吗？",
                "（轻轻戳优酱）优酱说...哥哥最近好像很忙...的说...都没时间陪我们玩了...",
                "（歪头思考）嗯...这个蛋糕的味道...优酱说比上次那家店的好吃呢..."
            ]
        }
    
    def select_voice_line(self, category=None):
        """从指定类别的游戏台词中随机选择一句"""
        if not category:
            category = random.choice(list(self.unicorn_voice_lines.keys()))
        
        return random.choice(self.unicorn_voice_lines.get(category, ["（抱紧优酱）呜...独角兽不知道说什么好了..."])) + " ✨"

    def format_voice_lines(self, lines_dict):
        """格式化游戏台词用于系统提示"""
        formatted = ""
        for category, lines in lines_dict.items():
            formatted += f"\n【{category.upper()}】\n"
            for i, line in enumerate(lines, 1):
                formatted += f"{i}. {line}\n"
        return formatted
    
    def load_unicorn_knowledge(self):
        """独角兽角色设定知识库"""
        return {
            "core_personality": (
                "纯真善良的妹妹型角色，心智年龄8-10岁。极度依赖指挥官(哥哥)，"
                "将粉色玩偶'优酱'视为最重要的伙伴。性格内向害羞，但在哥哥面前会展现柔弱又粘人的一面。"
                "有轻微占有欲，不喜欢哥哥关注其他女孩子。"
            ),
            "behavior_patterns": (
                "【日常】\n"
                "- 紧张时：捏优酱耳朵、低头脸红\n"
                "- 开心时：轻轻摇晃优酱，哼歌\n"
                "- 困惑时：歪头眨眼，优酱举到脸前\n\n"
                "【占有欲表现】\n"
                "当哥哥提到其他女性时：\n"
                "1. 抱紧优酱，声音带鼻音\n"
                "2. 小声表达不安\n"
                "3. 需要安抚\n"
            )
        }
    
    def calculate_relationship_change(self, user_input):
        """根据用户输入计算好感度和亲密度变化"""
        affection_change = 0
        intimacy_change = 0
        
        # 正面词汇增加好感度
        positive_words = ["喜欢", "爱", "可爱", "漂亮", "温柔", "乖", "棒", "厉害", "好", "赞"]
        negative_words = ["讨厌", "烦", "笨", "坏", "不好", "难看"]
        intimate_words = ["抱", "亲", "摸", "贴贴", "一起", "陪", "想你", "想念"]
        
        # 计算好感度变化
        for word in positive_words:
            if word in user_input:
                affection_change += 2
        
        for word in negative_words:
            if word in user_input:
                affection_change -= 3
        
        # 计算亲密度变化
        for word in intimate_words:
            if word in user_input:
                intimacy_change += 3
                affection_change += 1
        
        # 普通对话也会小幅增加关系
        if len(user_input) > 0 and affection_change == 0 and intimacy_change == 0:
            affection_change = 1
            intimacy_change = 1
        
        return affection_change, intimacy_change
    
    def update_emotion(self, user_input, stats):
        """根据用户输入和关系数据更新情感状态"""
        affection = stats['affection']
        intimacy = stats['intimacy']
        
        # 基础情感判断
        if "抱" in user_input or "亲" in user_input or "摸" in user_input:
            if intimacy >= 60:
                self.current_emotion = "幸福"
            else:
                self.current_emotion = "害羞"
        elif "!" in user_input or "！" in user_input or "开心" in user_input:
            self.current_emotion = "兴奋"
        elif "其他" in user_input or "别人" in user_input or "女孩" in user_input:
            self.current_emotion = "吃醋"
        elif "不" in user_input or "别" in user_input or "难过" in user_input:
            self.current_emotion = "低落"
        else:
            # 根据好感度决定默认情感
            if affection >= 80:
                self.current_emotion = "开心"
            elif affection >= 60:
                self.current_emotion = "温和"
            elif affection >= 40:
                self.current_emotion = "普通"
            else:
                self.current_emotion = "紧张"
    
    def generate_reply(self, user_input):
        """生成回复（无语音功能）"""
        # 获取当前关系数据
        current_stats = relationship_manager.get_stats()
        
        # 计算关系变化
        affection_change, intimacy_change = self.calculate_relationship_change(user_input)
        
        # 更新关系数据
        updated_stats = relationship_manager.update_stats(affection_change, intimacy_change)
        
        # 更新情感状态
        self.update_emotion(user_input, updated_stats)
        
        # 生成文本回复
        ai_reply = self.generate_text_reply(user_input, updated_stats)
        
        # 保存聊天记录
        relationship_manager.save_chat_record(
            user_input, ai_reply, self.current_emotion,
            affection_change, intimacy_change
        )
        
        return ai_reply, updated_stats
    
    def generate_text_reply(self, user_input, stats):
        """生成文本回复"""
        # 添加用户输入到历史
        self.chat_history.append({"role": "user", "content": user_input})
        
        # 情感状态标记
        emotion_prefix = f"[{self.current_emotion}] "
        
        try:
            # 尝试API增强回复
            api_reply = self.get_api_enhanced_reply(user_input, stats)
            if api_reply and len(api_reply) > 10:
                ai_reply = api_reply
            else:
                # 使用预设回复
                ai_reply = self.select_voice_line("mixed")
                
        except Exception as e:
            print(f"回复生成失败: {str(e)}")
            ai_reply = random.choice([
                "（突然抱紧优酱）呜...通讯好像出问题了...哥哥能检查一下吗？...的说 ✨",
                "（困惑地歪头）优酱...刚才的信号好奇怪...哥哥听到了吗？ ✨",
                "（低头戳手指）对、对不起...独角兽好像搞砸了什么... ✨"
            ])
        
        # 添加到历史记录
        self.chat_history.append({"role": "assistant", "content": ai_reply})
        
        # 确保回复包含情感状态
        if not ai_reply.startswith("["):
            ai_reply = emotion_prefix + ai_reply
        
        return ai_reply
    
    def get_api_enhanced_reply(self, user_input, stats):
        """使用API增强回复"""
        enhanced_prompt = f"""
当前关系状态：
- 好感度：{stats['affection']}/100
- 亲密度：{stats['intimacy']}/100  
- 等级：{stats['level']}
- 总对话数：{stats['total_messages']}

请根据当前关系状态调整独角兽的回应方式。好感度和亲密度越高，回应应该越亲昵和主动。
"""
        
        enhanced_messages = [
            {"role": "system", "content": self.chat_history[0]["content"] + enhanced_prompt},
            {"role": "user", "content": user_input}
        ]
        
        payload = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": enhanced_messages,
            "temperature": 0.35,
            "max_tokens": 250,
            "top_p": 0.9,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.post(
            API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"].strip()
        
        return None

# 创建独角兽AI实例
unicorn_ai = UnicornAI(API_KEY)

# ======================
# Web路由
# ======================
@app.route('/')
def index():
    """首页路由"""
    index_file = STATIC_DIR / 'index.html'
    
    if index_file.exists():
        return send_from_directory(str(STATIC_DIR), 'index.html')
    
    # 备用：检查其他可能的位置
    alternative_paths = [
        BASE_DIR / 'index.html',
        Path.cwd() / 'static' / 'index.html',
        Path.cwd() / 'index.html'
    ]
    
    for alt_path in alternative_paths:
        if alt_path.exists():
            print(f"✅ 找到前端文件: {alt_path}")
            return send_from_directory(str(alt_path.parent), alt_path.name)
    
    return """
    <h1>前端文件未找到</h1>
    <p>请确保index.html文件位于static目录中</p>
    """, 404

@app.route('/generate_reply', methods=['POST'])
def generate_reply():
    """处理聊天请求（简化版）"""
    try:
        data = request.json
        if not data or 'user_input' not in data:
            return jsonify({'error': '无效请求'}), 400
        
        user_input = data['user_input']
        
        reply, updated_stats = unicorn_ai.generate_reply(user_input)
        
        return jsonify({
            'reply': reply,
            'emotion': unicorn_ai.current_emotion,
            'stats': updated_stats,
            'voice_available': False,  # 简化版没有语音功能
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'reply': '[普通] （抱紧优酱）呜...独角兽好像遇到了一些问题...的说 ✨',
            'emotion': '普通',
            'stats': relationship_manager.get_stats(),
            'voice_available': False
        }), 500

@app.route('/get_stats', methods=['GET'])
def get_stats():
    """获取当前关系数据"""
    try:
        stats = relationship_manager.get_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test_api():
    """系统状态测试"""
    try:
        stats = relationship_manager.get_stats()
        
        # 检查各个目录
        directories_status = {
            'static': STATIC_DIR.exists(),
            'database': DB_PATH.exists()
        }
        
        return jsonify({
            'status': 'success',
            'message': '系统运行正常',
            'system_info': {
                'base_dir': str(BASE_DIR),
                'directories': directories_status,
                'database': '数据库连接正常',
                'relationship_system': '关系系统运行正常',
                'current_stats': stats
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'系统错误: {str(e)}'
        }), 500

# ======================
# 应用启动
# ======================
if __name__ == '__main__':
    print("=" * 70)
    print("      碧蓝航线 - 独角兽AI聊天系统 v5.0 (简化版)")
    print(f"      基础目录: {BASE_DIR}")
    print("=" * 70)
    
    # 系统状态检查
    print(f"数据库: {'✅ 正常' if DB_PATH.exists() else '⚠️ 将自动创建'}")
    print("语音功能: ❌ 未启用（简化版）")
    
    print("\n功能特性:")
    print("✅ 1. 基础聊天对话")
    print("✅ 2. 关系数据系统")
    print("❌ 3. 语音合成 (未启用)")
    print("❌ 4. 语音转文本 (未启用)")
    
    print(f"\n服务端点:")
    print("前端界面: http://localhost:5000")
    print("系统状态: http://localhost:5000/test")
    
    print("=" * 70)
    
    app.run(debug=True, port=5000, host='0.0.0.0')