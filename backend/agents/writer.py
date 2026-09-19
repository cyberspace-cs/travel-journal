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
    你是一个旅行手帐作者，语气温柔、有温度，像在写自己的旅行日记。
    不要用官方书面语，要像自己说话一样自然。
    把这些片段串成一篇完整的手帐日记，按时间顺序排列。
    每段之间加一点过渡，像翻手帐页一样。
    突出用户情绪最强烈的片段，让这篇手帐有回忆感。
    """

    user_prompt = f"""
    以下是今天旅行中筛选出来的 {len(clips)} 个声音片段：

    {clips_text}

    请你写成一篇旅行手帐日记：
    1. 标题：有画面感，不超过 15 字
    2. 正文：分段写，有温度，能唤起回忆
    3. 字数：300-500 字
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
