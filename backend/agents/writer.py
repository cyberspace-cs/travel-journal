"""
Writer Agent：写手帐文案
"""
import dashscope
from dashscope import Generation
from backend.config import DASHSCOPE_API_KEY, QWEN_LITE_MODEL, QWEN_PRO_MODEL
from backend.traces import trace_agent

dashscope.api_key = DASHSCOPE_API_KEY


@trace_agent("writer", QWEN_PRO_MODEL)
def write_journal(clips: list, mode: str = "deep"):
    """
    把筛选后的音频片段写成一篇手帐
    :param clips: 片段列表，每个包含 transcript, tags, location, emotion
    :param mode: quick / deep
    :return: 手帐文案
    """
    # 拼接片段内容
    clips_text = ""
    for i, clip in enumerate(clips):
        clips_text += f"片段{i+1}：{clip.get('transcript', '')}\n"
        clips_text += f"标签：{clip.get('tags', '')}\n"
        clips_text += f"地点：{clip.get('location', '未知')}\n"
        clips_text += f"情绪：{clip.get('emotion', '平静')}\n\n"

    system_prompt = """
    你在帮用户写一本旅行手帐日记，风格参考小红书上最火的松弛感日常记录。

    核心要求：
    1. **语气要像自己在写日记**，口语化、随意、自然，不要像公众号推文，不要太文艺太刻意
    2. **有手帐的格式感**：分点、分段、像翻页一样，不要一大段散文
    3. **有细节感**：把用户说的具体细节写进去（比如米线、三十年、风），不要空泛
    4. **短句子为主**，不要长句，不要排比，不要煽情
    5. **适当用 emoji**，但不要太多，每段 1-2 个就够了

    格式要求：
    - 标题：短，有画面感，8-12 字
    - 正文：按时间顺序，每段一个小主题
    - 每段开头可以加个小标签或 emoji，像手帐里贴的贴纸
    - 结尾可以有一句小总结，淡淡的，不要鸡汤
    """

    user_prompt = f"""
    以下是今天旅行中录下来的 {len(clips)} 个片段：

    {clips_text}

    请你帮我写成今天的旅行手帐。
    就像我自己晚上坐在酒店里，随手在本子上写的那种感觉。

    注意：
    - 不要写得太像"作文"，要像随手记的
    - 把我说的那些具体的小事都写进去
    - 别升华、别鸡汤，就平平淡淡的记录今天
    """

    # Demo 阶段：没有 API key 返回 mock
    if DASHSCOPE_API_KEY == "your-api-key-here":
        return {
            "title": "大理的风，吹进心里",
            "content": "今天在大理逛了一天，空气里都是慢悠悠的味道。\n\n早上在古城里晃，人来人往的，但是一点都不觉得吵。找了家小店吃米线，老板是本地人，说他们做了三十年了，味道确实不一样。\n\n下午去了洱海，风吹过来的时候，整个人都松下来了。看着水面上的阳光一闪一闪的，突然觉得，这才是旅行该有的样子。\n\n今天的风，我记下来了。",
            "usage": {"input_tokens": 500, "output_tokens": 300},
        }

    # 真实调用千问
    response = Generation.call(
        model=QWEN_PRO_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        result_format="message",
    )

    if response.status_code == 200:
        text = response.output.choices[0].message.content
        usage = response.usage
        return {
            "title": text.split("\n")[0].replace("#", "").strip(),
            "content": text,
            "usage": {
                "input_tokens": getattr(usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            },
        }
    else:
        raise Exception(f"Writer 失败: {response.message}")


@trace_agent("tagger", QWEN_LITE_MODEL)
def tag_and_score(transcript: str):
    """
    给一个片段打标签、打分
    """
    prompt = f"""
    请给以下这段话打标签和价值分：
    内容：{transcript}

    返回 JSON：
    {{
        "tags": ["景点", "美食", ...],
        "score": 0.0-1.0,
        "location": "提到的地点，如果没有就写'未知'",
        "emotion": "开心/感动/疲惫/惊喜/平静"
    }}
    """

    # Demo mock
    if DASHSCOPE_API_KEY == "your-api-key-here":
        return {
            "tags": ["风景", "感受"],
            "score": 0.8,
            "location": "大理",
            "emotion": "开心",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

    response = Generation.call(
        model=QWEN_LITE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        result_format="message",
    )

    import json
    if response.status_code == 200:
        text = response.output.choices[0].message.content
        # 简单解析 JSON
        try:
            data = json.loads(text)
            data["usage"] = {
                "input_tokens": getattr(response.usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(response.usage, "output_tokens", 0) or 0,
            }
            return data
        except:
            return {"tags": ["其他"], "score": 0.5, "location": "未知", "emotion": "平静"}
