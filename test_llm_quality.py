"""
LLM 输出质量测试结果
"""
import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from unicorn_rag import UnicornRAG
import requests

load_dotenv()

from unicorn_scheduler import UNICORN_VOICE_LINES, format_voice_lines

async def test_llm_output(user_input: str):
    rag = UnicornRAG()
    rag.init_static_collection("unicorn.list")
    history_context, _, _ = await rag.query_memory(user_input)

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
  * 禁止使用英文句号(.)，必须使用日文句号（。）或省略号（……）
  * 用「……」表示停顿和呼吸感
  * 语气模仿独角兽：温柔、略带撒娇、偶尔害羞
  * 使用ね、よ、だ、わ等日文语气词
- 只返回JSON，不要其他内容

示例：
用户："你好呀"
{{
  "display": "[普通]（听到脚步声，从门后探出半个头）哥、哥哥...你回来啦...（低头捏优酱耳朵）独角兽和优酱...等了你一下午呢...的说",
  "tts": "お兄ちゃん……帰ってきたの……？ユニコーンとU-ちゃん……ずっと待ってたよ……"
}}"""

    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    api_url = base_url
    if not api_url.endswith('/chat/completions'):
        if api_url.endswith('/v1'):
            api_url = f"{api_url}/chat/completions"
        else:
            api_url = f"{api_url}/v1/chat/completions"

    response = requests.post(
        api_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7
        },
        timeout=30.0
    )
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"]

    import re
    try:
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            return data.get("display", ""), data.get("tts", "")
        else:
            return content, ""
    except Exception as e:
        return content, ""


async def main():
    test_cases = [
        "哥哥回来啦",
        "今天天气真好呀",
        "独角兽真可爱",
        "我刚才和贝尔法斯特聊天了"
    ]

    results = []

    for user_input in test_cases:
        try:
            display_text, tts_text = await test_llm_output(user_input)

            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in tts_text)
            has_japanese = any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in tts_text)
            has_emotion_tag = '[' in display_text and ']' in display_text
            has_action = '（' in display_text and '）' in display_text

            result = {
                "input": user_input,
                "display": display_text,
                "tts": tts_text,
                "quality": {
                    "has_emotion_tag": has_emotion_tag,
                    "has_action": has_action,
                    "tts_has_chinese": has_chinese,
                    "tts_has_japanese": has_japanese,
                    "tts_is_pure_japanese": has_japanese and not has_chinese
                }
            }
            results.append(result)

        except Exception as e:
            results.append({
                "input": user_input,
                "error": str(e)
            })

    # 保存到文件
    output_file = Path("llm_test_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Results saved to: {output_file}")

    # 打印摘要
    print("\n=== Test Summary ===")
    for r in results:
        if "error" not in r:
            q = r["quality"]
            print(f"\nInput: {r['input']}")
            print(f"  Emotion tag: {'YES' if q['has_emotion_tag'] else 'NO'}")
            print(f"  Action desc: {'YES' if q['has_action'] else 'NO'}")
            print(f"  TTS pure JP: {'YES' if q['tts_is_pure_japanese'] else 'NO'}")

if __name__ == "__main__":
    asyncio.run(main())
