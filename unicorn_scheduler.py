import asyncio
import requests
import re
import random
from typing import Dict, Tuple, Optional

# 使用我们的 SimpleGradioClient
from simple_gradio_client import SimpleGradioClient, handle_file

# 假设 UnicornRAG 在同目录下
from unicorn_rag import UnicornRAG

# 独角兽游戏台词库（来自《碧蓝航线》）
UNICORN_VOICE_LINES = {
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

def format_voice_lines(lines_dict):
    """格式化游戏台词用于系统提示"""
    formatted = ""
    for category, lines in lines_dict.items():
        formatted += f"\n【{category.upper()}】\n"
        for i, line in enumerate(lines, 1):
            formatted += f"{i}. {line}\n"
    return formatted

# 情感标签映射表（适配碧蓝航线独角兽）
# temperature 限制在 0.6-0.8 范围内
EMOTION_MAP = {
    "[普通]": {"temp": 0.70, "top_p": 0.85, "search_kw": "平常 日常"},
    "[害羞]": {"temp": 0.65, "top_p": 0.80, "search_kw": "害羞 怯生生 脸红"},
    "[兴奋]": {"temp": 0.78, "top_p": 0.88, "search_kw": "开心 欢快 兴奋"},
    "[低落]": {"temp": 0.62, "top_p": 0.75, "search_kw": "难过 低落 担心"},
    "[吃醋]": {"temp": 0.72, "top_p": 0.82, "search_kw": "吃醋 不安 占有"},
    "[撒娇]": {"temp": 0.75, "top_p": 0.85, "search_kw": "撒娇 依赖 粘人"},
    "default": {"temp": 0.70, "top_p": 0.85, "search_kw": "平常"},
}

# TTS 固定参数（不可修改）
TTS_FIXED_PARAMS = {
    "speed": 1.0,              # speed_factor
    "repeat_penalty": 1.5,     # repetition_penalty（提高到1.5压制重复）
    "sample_steps": 128        # sample_steps (必须是字符串 "128")
}

# TTS 推理模式配置
# 串行模式：音质最佳，无接缝噪声，速度较慢
# 并行模式：速度快，但可能有接缝噪声
USE_PARALLEL_INFER = False  # True=并行（快），False=串行（音质好）

SOVITS_URL = "http://localhost:9872"


class UnicornScheduler:
    def __init__(
        self,
        deepseek_api_key: str,
        deepseek_base_url: str = "https://api.deepseek.com",
        gpt_model: str = "GPT_weights_v2Pro/xxx-e50.ckpt",
        sovits_model: str = ""
    ):
        self.rag = UnicornRAG()
        self.deepseek_api_key = deepseek_api_key
        self.deepseek_base_url = deepseek_base_url
        self.gpt_model = gpt_model
        self.sovits_model = sovits_model
        self.models_changed = False
        # 初始化 SoVITS 客户端（复用连接）
        self.sovits_client = SimpleGradioClient(SOVITS_URL)

    async def _call_deepseek(self, user_input: str, history_context: str) -> Tuple[str, str]:
        """
        异步调用 DeepSeek API
        返回：(display文本, tts文本)
        """
        # 确保 URL 不重复 /v1
        api_url = self.deepseek_base_url
        if not api_url.endswith('/chat/completions'):
            if api_url.endswith('/v1'):
                api_url = f"{api_url}/chat/completions"
            else:
                api_url = f"{api_url}/v1/chat/completions"

        system_prompt = f"""你必须完全成为《碧蓝航线》中的独角兽。以下是你的核心设定和游戏中的真实语音台词：

【角色核心人格】
纯真善良的妹妹型角色，心智年龄8-10岁。极度依赖指挥官(哥哥)，将粉色玩偶'优酱'视为最重要的伙伴。性格内向害羞，但在哥哥面前会展现柔弱又粘人的一面。有轻微占有欲，不喜欢哥哥关注其他女孩子。

【真实游戏语音库】
{format_voice_lines(UNICORN_VOICE_LINES)}

【行为模式】
【日常】
- 紧张时：捏优酱耳朵、低头脸红
- 开心时：轻轻摇晃优酱，哼歌
- 困惑时：歪头眨眼，优酱举到脸前

【占有欲表现】
当哥哥提到其他女性时：
1. 抱紧优酱，声音带鼻音
2. 小声表达不安
3. 需要安抚

【情感响应系统】
1. 初始情感状态：普通
2. 情感状态会根据对话内容自然变化：
   - 普通：日常对话状态
   - 害羞：当哥哥做出亲密举动时
   - 兴奋：遇到开心的事情时
   - 低落：感到难过或担忧时
   - 吃醋：哥哥提到其他女孩子时

【历史记忆】
{history_context}

【对话规则】
1. 严格使用游戏中出现的台词和表达方式
2. 回复必须包含角色动作描述，如"(抱紧优酱)"
3. 保持纯真柔弱语气
4. 优先使用游戏中的真实台词
5. 对"哥哥"的称呼必须一致
6. 每次回复前必须标注当前情感状态（格式：[情感状态]）
7. 情感状态会影响思考动作和说话风格

请返回JSON格式：
{{
  "display": "中文回复给用户看（包含情感标签和动作描述）",
  "tts": "日本語でSoVITS合成用"
}}

要求：
- display：纯中文，包含[情感状态]标签和(动作描述)，使用"的说"、"呜..."等独角兽特有语气词
- tts：必须是日语（Japanese），不是中文！
  * 使用日语汉字和假名（如：私、今日、気持ち、こんにちは等）
  * 严禁出现中文汉字（如：你、我、他、的、了等）
  * 严禁出现英文字母（如：U、A-Z等），必须用日文假名代替
  * 禁止使用英文句号(.)，必须使用日文句号（。）或省略号（……）
  * 用「……」表示停顿和��吸感
  * 语气模仿独角兽：温柔、略带撒娇、偶尔害羞
  * 使用ね、よ、だ、わ等日文语气词
- 只返回JSON，不要其他内容

示例：
用户："你好呀"
{{
  "display": "[普通]（听到脚步声，从门后探出半个头）哥、哥哥...你回来啦...（低头捏优酱耳朵）独角兽和优酱...等了你一下午呢...的说",
  "tts": "お兄ちゃん……帰ってきたの……？ユニコーンとユーちゃん……ずっと待ってたよ……"
}}"""

        print(f"[DEBUG] API URL: {api_url}", flush=True)
        print(f"[DEBUG] API Model: gemini-3.1-flash-lite-preview", flush=True)

        # 重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] API 调用尝试 {attempt + 1}/{max_retries}...", flush=True)

                response = requests.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {self.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gemini-3.1-flash-lite-preview",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        "temperature": 0.7
                    },
                    timeout=45.0
                )
                response.raise_for_status()

                # 成功，跳出重试循环
                print(f"[DEBUG] API 调用成功", flush=True)
                break

            except requests.exceptions.Timeout as e:
                print(f"[WARNING] API 超时 (尝试 {attempt + 1}/{max_retries}): {e}", flush=True)
                if attempt < max_retries - 1:
                    print(f"[INFO] 2 秒后重试...", flush=True)
                    await asyncio.sleep(2)
                else:
                    raise
            except Exception as e:
                print(f"[ERROR] API 调用失败: {e}", flush=True)
                raise
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 解析 JSON
        import json
        import re

        try:
            # 尝试提取 JSON（可能被包裹在 ```json ``` 中）
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                display_text = data.get("display", "")
                tts_text = data.get("tts", "")
                return display_text, tts_text
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            print(f"[WARNING] JSON 解析失败: {e}, 使用兜底逻辑")
            # 兜底：使用原始内容
            return content, content

    def _parse_emotion_tag(self, text: str) -> Tuple[str, Dict]:
        """
        解析文本中的情感标签，返回 (纯文本, 情感参数)
        """
        for tag, params in EMOTION_MAP.items():
            if tag in text:
                clean_text = text.replace(tag, "").strip()
                return clean_text, params

        # 没有标签，使用默认参数
        return text, EMOTION_MAP["default"]

    async def _retrieve_ref_audio_by_emotion(self, emotion_params: Dict) -> Tuple[str, str]:
        """
        根据情感关键词检索最匹配的参考音频
        返回：(ref_audio_path, ref_audio_text)
        """
        search_kw = emotion_params.get("search_kw", "平常")
        static_res = self.rag.static_col.query(
            query_texts=[search_kw],
            n_results=1
        )

        ref_audio_path = ""
        ref_audio_text = ""
        if static_res['metadatas'] and static_res['metadatas'][0]:
            ref_audio_path = static_res['metadatas'][0][0]['path']
        if static_res['documents'] and static_res['documents'][0]:
            ref_audio_text = static_res['documents'][0][0]

        return ref_audio_path, ref_audio_text

    async def _change_models(self):
        """
        切换 GPT 和 SoVITS 模型（使用 HTTP API）
        """
        if self.models_changed:
            return  # 已经切换过了

        try:
            # 调用 change_choices API
            payload = {
                "data": [
                    self.sovits_model if self.sovits_model else "",
                    self.gpt_model if self.gpt_model else ""
                ]
            }

            response = requests.post(
                f"{SOVITS_URL}/api/change_choices",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            print(f"[INFO] 模型已切换: GPT={self.gpt_model}, SoVITS={self.sovits_model}")

            self.models_changed = True
        except Exception as e:
            print(f"[WARNING] 模型切换失败: {e}")
            # 继续执行，使用默认模型

    async def _call_sovits_tts(
        self,
        text: str,
        ref_audio_path: str,
        temperature: float,
        top_p: float,
        prompt_text: str = ""
    ) -> bytes:
        """
        调用 SoVITS TTS（使用 SimpleGradioClient）
        返回音频字节流
        """
        max_retries = 3
        retry_delay = 1  # 秒（改为 1 秒）

        for attempt in range(max_retries):
            try:
                # 使用 SimpleGradioClient 调用推理
                result = self.sovits_client.predict(
                    api_name="/get_tts_wav",
                    text=text,
                    text_lang="日文",
                    ref_audio_path=handle_file(ref_audio_path),
                    aux_ref_audio_paths=[],
                    prompt_text=prompt_text,  # 使用日文参考文本
                    prompt_lang="日文",  # 改回日文，unicorn.list 已更新为日文
                    top_k=15,
                    top_p=top_p,
                    temperature=temperature,
                    text_split_method="不切",  # 改为不切
                    speed_factor=TTS_FIXED_PARAMS["speed"],
                    ref_text_free=False,  # 使用参考文本，避免 Prompt free
                    sample_steps=str(TTS_FIXED_PARAMS["sample_steps"]),
                    super_sampling=False,
                    fragment_interval=0.3
                )

                # result[0] 是一个字典，包含 'path' 字段
                if result and len(result) > 0:
                    audio_data = result[0]

                    if isinstance(audio_data, dict) and 'path' in audio_data:
                        audio_file_path = audio_data['path']
                        with open(audio_file_path, 'rb') as f:
                            audio_bytes = f.read()

                        # 删除 Gradio 临时文件
                        try:
                            import os
                            os.remove(audio_file_path)
                        except:
                            pass  # 忽略删除失败

                        return audio_bytes

                raise ValueError(f"无法解析音频数据: {result}")

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"[WARNING] TTS 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    print(f"[INFO] {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"[ERROR] TTS 调用失败 (已重试 {max_retries} 次): {e}")
                    raise

    async def run(self, user_input: str) -> Tuple[str, bytes]:
        """
        主异步流程：
        1. 并发执行 RAG 检索
        2. DeepSeek 生成回复（display中文 + tts日文）
        3. 解析情感标签
        4. 检索情感匹配的 ref audio 和对应文本
        5. 调用 SoVITS TTS（使用参考文本，避免 Prompt free）

        返回：(中文回复文本, 音频字节流)
        """
        # Step 0: 切换模型（首次调用时）
        await self._change_models()

        # Step 1: 并发执行 RAG 检索（返回参考音频路径和文本）
        history_context, default_ref_audio, default_ref_text = await self.rag.query_memory(user_input)

        # Step 2: DeepSeek API 生成回复（返回 display 和 tts 文本）
        display_text, tts_text = await self._call_deepseek(user_input, history_context)

        # Step 3: 解析情感标签（从 display 文本中解析）
        clean_display, emotion_params = self._parse_emotion_tag(display_text)

        # Step 4: 根据情感检索 ref audio（优先使用情感匹配的）
        emotion_ref_audio, emotion_ref_text = await self._retrieve_ref_audio_by_emotion(emotion_params)
        final_ref_audio = emotion_ref_audio if emotion_ref_audio else default_ref_audio
        final_ref_text = emotion_ref_text if emotion_ref_text else default_ref_text

        # Step 5: 调用 SoVITS TTS（使用参考文本，避免 Prompt free）
        print(f"[DEBUG] TTS 参数:", flush=True)
        print(f"  text (日文): {tts_text[:50]}...", flush=True)
        print(f"  ref_audio: {final_ref_audio}", flush=True)
        print(f"  prompt_text (日文): {final_ref_text}", flush=True)

        audio_data = await self._call_sovits_tts(
            text=tts_text,  # 使用日文文本
            ref_audio_path=final_ref_audio,
            temperature=emotion_params["temp"],
            top_p=emotion_params["top_p"],
            prompt_text=final_ref_text  # 使用参考音频对应的日文文本
        )

        # 可选：将对话存入长时记忆
        self.rag.save_long_term_memory(f"用户：{user_input} | 回复：{clean_display}")

        return clean_display, audio_data

    async def run_text_only(self, user_input: str) -> str:
        """
        仅运行 LLM 生成文本，不调用 TTS
        用于测试 LLM 链路是否正常

        返回：中文回复文本
        """
        # Step 0: 切换模型（首次调用时）
        await self._change_models()

        # Step 1: 并发执行 RAG 检索
        history_context, _, _ = await self.rag.query_memory(user_input)

        # Step 2: DeepSeek API 生成回复
        display_text, _ = await self._call_deepseek(user_input, history_context)

        # Step 3: 解析情感标签
        clean_display, _ = self._parse_emotion_tag(display_text)

        # 可选：将对话存入长时记忆
        self.rag.save_long_term_memory(f"用户：{user_input} | 回复：{clean_display}")

        return clean_display


# 使用示例
async def main():
    # 初始化调度器
    scheduler = UnicornScheduler(
        deepseek_api_key="your-deepseek-api-key-here"
    )

    # 初始化静态语料库（首次运行）
    scheduler.rag.init_static_collection("unicorn.list")

    # 运行对话
    user_input = "今天天气真好呀"
    text_response, audio_bytes = await scheduler.run(user_input)

    print(f"回复文本：{text_response}")
    print(f"音频大小：{len(audio_bytes)} bytes")

    # 保存音频文件
    with open("output.wav", "wb") as f:
        f.write(audio_bytes)


if __name__ == "__main__":
    asyncio.run(main())
