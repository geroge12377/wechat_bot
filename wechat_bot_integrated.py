"""
WeChat Bot 集成 Unicorn Scheduler
支持情感化语音回复的微信机器人
"""

import asyncio
import os
import concurrent.futures
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from unicorn_scheduler import UnicornScheduler

# 加载环境变量
load_dotenv()

# 配置
BASE_DIR = Path(__file__).parent.resolve()
AUDIO_OUTPUT_DIR = BASE_DIR / "audio_cache"
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)

# API 配置（从 .env 读取）
DEEPSEEK_API_KEY = os.getenv("AI_API_KEY", "sk-cjeKQXbJvi1cLQ7O7a0L43nvJGZvcJnNvQve8T0urA4FdjrA")
DEEPSEEK_BASE_URL = os.getenv("AI_BASE_URL", "https://api.vectorengine.ai/v1")


class WeChatUnicornBot:
    """集成 Unicorn Scheduler 的微信机器人"""

    def __init__(self):
        self.scheduler = UnicornScheduler(
            deepseek_api_key=DEEPSEEK_API_KEY,
            deepseek_base_url=DEEPSEEK_BASE_URL,
            gpt_model="GPT_weights_v2Pro/xxx-e50.ckpt",
            sovits_model=""
        )
        self.initialized = False
        # 消息队列（串行处理）
        self.message_queue = asyncio.Queue()
        self.queue_processor_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """初始化语料库和模型"""
        if self.initialized:
            return

        try:
            list_file = BASE_DIR / "unicorn.list"
            if not list_file.exists():
                print("[WARNING] unicorn.list 不存在，将使用空语料库")
            else:
                self.scheduler.rag.init_static_collection(str(list_file))
                print(f"[INFO] 语料库初始化完成")

            # 初始化时切换模型
            print("[INFO] 正在初始化模型...")
            await self.scheduler._change_models()
            print("[INFO] 模型初始化完成")

            self.initialized = True
        except Exception as e:
            print(f"[ERROR] 初始化失败: {e}")
            raise

    async def start_queue_processor(self):
        """启动消息队列处理器"""
        if self.queue_processor_task is None or self.queue_processor_task.done():
            self.queue_processor_task = asyncio.create_task(self._process_queue())
            print("[INFO] 消息队列处理器已启动")

    async def _process_queue(self):
        """处理消息队列（串行）"""
        while True:
            try:
                # 从队列获取消息
                message_data = await self.message_queue.get()
                user_input = message_data["input"]
                user_id = message_data["user_id"]
                result_future = message_data["future"]

                try:
                    # 处理消息
                    result = await self._process_message_internal(user_input, user_id)
                    result_future.set_result(result)
                except Exception as e:
                    result_future.set_exception(e)
                finally:
                    self.message_queue.task_done()
                    # 每条消息处理后等待 2 秒
                    await asyncio.sleep(2)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ERROR] 队列处理器异常: {e}")

    async def process_message(self, user_input: str, user_id: str = "default") -> dict:
        """
        处理用户消息（通过队列串行处理）
        """
        # 确保队列处理器正在运行
        await self.start_queue_processor()

        # 创建 Future 用于接收结果
        result_future = asyncio.Future()

        # 将消息放入队列
        await self.message_queue.put({
            "input": user_input,
            "user_id": user_id,
            "future": result_future
        })

        # 等待结果
        return await result_future

    async def _process_message_internal(self, user_input: str, user_id: str) -> dict:
        """
        内部消息处理逻辑
        """
        try:
            # 运行调度器（带120秒超时保护）
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.scheduler.run(user_input))
                try:
                    text_response, audio_bytes = future.result(timeout=120)
                except concurrent.futures.TimeoutError:
                    print(f"[ERROR] 推理超时（120秒）")
                    return {
                        "text": "抱歉，处理超时了...",
                        "audio_path": None,
                        "emotion": "default",
                        "success": False,
                        "error": "推理超时"
                    }

            # 保存音频文件
            import hashlib
            import time
            audio_hash = hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()[:8]
            audio_filename = f"unicorn_{audio_hash}.wav"
            audio_path = AUDIO_OUTPUT_DIR / audio_filename

            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            # 转换为 SILK 格式（微信语音格式）
            silk_filename = f"unicorn_{audio_hash}.silk"
            silk_path = AUDIO_OUTPUT_DIR / silk_filename

            try:
                import pilk
                pilk.encode(str(audio_path), str(silk_path), pcm_rate=24000, tencent=True)
                print(f"[INFO] SILK 转码成功: {silk_path}")
            except Exception as e:
                print(f"[WARNING] SILK 转码失败: {e}，将使用 WAV 格式")
                silk_path = audio_path
                silk_filename = audio_filename

            # 检测情感标签
            emotion = "default"
            for tag in ["[撒娇]", "[温柔]", "[害羞]", "[开心]", "[担心]"]:
                if tag in user_input:
                    emotion = tag.strip("[]")
                    break

            return {
                "text": text_response,
                "audio_path": str(silk_path),  # 返回 SILK 路径
                "audio_filename": silk_filename,
                "audio_url": f"http://localhost:5000/audio/{silk_filename}",
                "emotion": emotion,
                "success": True
            }

        except Exception as e:
            print(f"[ERROR] 处理消息失败: {e}")
            import traceback
            traceback.print_exc()

            return {
                "text": "抱歉，我遇到了一些问题...",
                "audio_path": None,
                "emotion": "default",
                "success": False,
                "error": str(e)
            }


# ==================
# Flask 集成示例
# ==================
def create_flask_app():
    """创建 Flask 应用（可选）"""
    from flask import Flask, request, jsonify, send_file

    app = Flask(__name__)
    bot = WeChatUnicornBot()

    # Flask 启动时初始化（同步包装异步初始化）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot.initialize())
    loop.close()
    print("[INFO] Flask 应用初始化完成，模型已加载")

    @app.route('/chat', methods=['POST'])
    def chat():
        """聊天接口（完整模式：LLM + TTS）"""
        print("=" * 60, flush=True)
        print("收到 /chat 请求！", flush=True)
        print("=" * 60, flush=True)

        data = request.json
        print(f"请求数据: {data}", flush=True)

        user_input = data.get('message', '')
        user_id = data.get('user_id', 'default')
        is_group = data.get('is_group', False)
        mentioned = data.get('mentioned', False)

        print(f"用户ID: {user_id}", flush=True)
        print(f"消息内容: {user_input}", flush=True)
        print(f"群聊: {is_group}, 被@: {mentioned}", flush=True)

        if not user_input:
            print("错误: 消息为空", flush=True)
            return jsonify({"error": "消息不能为空"}), 400

        print("开始处理消息（完整模式：LLM + TTS）...", flush=True)

        # 运行异步任务（LLM + TTS）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot.process_message(user_input, user_id))
        loop.close()

        print(f"处理完成，返回结果: {result.get('success')}", flush=True)
        print("=" * 60, flush=True)

        return jsonify(result)

    @app.route('/audio/<filename>')
    def get_audio(filename):
        """获取音频文件"""
        audio_path = AUDIO_OUTPUT_DIR / filename
        if audio_path.exists():
            # 根据文件扩展名设置 MIME 类型
            if filename.endswith('.silk'):
                return send_file(audio_path, mimetype='audio/silk')
            else:
                return send_file(audio_path, mimetype='audio/wav')
        return jsonify({"error": "文件不存在"}), 404

    @app.route('/health')
    def health():
        """健康检查"""
        return jsonify({
            "status": "ok",
            "initialized": bot.initialized,
            "sovits_url": "http://localhost:9872"
        })

    return app


# ==================
# 命令行测试
# ==================
async def test_bot():
    """命令行测试"""
    print("=== WeChat Unicorn Bot 测试 ===\n")

    bot = WeChatUnicornBot()
    bot.initialize()

    test_messages = [
        "你好呀[撒娇]",
        "今天天气真好[开心]",
        "我有点担心明天的考试[担心]"
    ]

    for msg in test_messages:
        print(f"\n用户: {msg}")
        result = await bot.process_message(msg, "test_user")

        if result["success"]:
            # 使用 encode/decode 处理 Unicode 字符
            try:
                text = result['text']
                print(f"回复: {text}")
            except UnicodeEncodeError:
                # 移除无法编码的字符
                text = result['text'].encode('gbk', errors='ignore').decode('gbk')
                print(f"回复: {text}")

            print(f"情感: {result['emotion']}")
            print(f"音频: {result['audio_path']}")
        else:
            print(f"错误: {result['error']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # 启动 Flask 服务器
        print("=" * 60, flush=True)
        print("启动 Flask 服务器...", flush=True)
        print("监听地址: 0.0.0.0:5000", flush=True)
        print("访问地址: http://localhost:5000", flush=True)
        print("=" * 60, flush=True)
        app = create_flask_app()
        print("Flask app 已创建，开始运行...", flush=True)
        app.run(host='0.0.0.0', port=5000, debug=False)  # 关闭 debug 模式
    else:
        # 命令行测试
        asyncio.run(test_bot())
