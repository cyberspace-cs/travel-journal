"""
Router：路由层，判断走哪条路径
"""
import dashscope
from dashscope import Generation
from backend.config import DASHSCOPE_API_KEY, QWEN_LITE_MODEL
from backend.traces import trace_agent
from backend.agents.content_classifier import classify_content
from backend.agents.rule_nlp import rule_based_classify
from backend.agents.quote_library import get_quote

dashscope.api_key = DASHSCOPE_API_KEY


@trace_agent("router", QWEN_LITE_MODEL)
def route_request(user_query: str = "", user_mode: str = "quick"):
    """
    路由决策：两个维度
    1. 用户选的模式：quick / deep
    2. 任务复杂度：simple / complex
    :return: 走哪条路径
    """
    # 如果用户明确选了模式，就直接用
    # Demo 阶段：简单点，就按用户选的模式走
    # 产品化阶段：加 LLM 判断复杂度

    path_map = {
        ("quick", "simple"): "fast_pipeline",
        ("quick", "complex"): "fast_orchestrator",
        ("deep", "simple"): "enhanced_pipeline",
        ("deep", "complex"): "full_orchestrator",
    }

    # 简单判断：有没有提到具体地名/要求
    is_complex = any(kw in user_query for kw in [
        "查一下", "告诉我", "更多", "详细", "配图", "分享", "帮我找",
        "玉龙", "洱海", "大理", "丽江", "成都", "重庆",  # 具体地名
    ])

    complexity = "complex" if is_complex else "simple"
    path = path_map.get((user_mode, complexity), "fast_pipeline")

    return {
        "path": path,
        "mode": user_mode,
        "complexity": complexity,
        "usage": {"input_tokens": len(user_query), "output_tokens": 10},
    }


def route_by_content(transcript: str, user_mode: str = "auto"):
    """
    按内容类型路由：旅行/工作/日常，走不同的 pipeline
    不是什么都走到 Writer 那里去
    :param transcript: 转写文本
    :param user_mode: 用户指定的模式：auto/travel/daily/work/summary
    :return: {
        "route": str,  # 走哪个 pipeline
        "options": list,  # 给用户的可选模式
        "classification": dict,  # 分类结果
    }
    """
    # 如果用户指定了模式，就走指定的
    if user_mode != "auto":
        return {
            "route": user_mode,
            "options": [user_mode],
            "classification": classify_content(transcript),
        }

    # 自动模式：先分类
    classification = classify_content(transcript)
    content_type = classification["content_type"]

    # 根据分类路由
    if content_type == "travel":
        route = "travel_journal"
        options = ["travel_journal", "daily_diary", "just_summary"]
    elif content_type == "work":
        route = "work_summary"
        options = ["work_summary", "travel_journal", "just_transcript"]
    else:
        route = "daily_diary"
        options = ["daily_diary", "travel_journal", "just_summary"]

    return {
        "route": route,
        "options": options,
        "classification": classification,
    }


def generate_summary_only(transcript: str):
    """
    只生成摘要和标签，不写手帐
    适合工作内容、或者用户不想写手帐的时候
    """
    # 规则化打标签
    rule_result = rule_based_classify(transcript)

    # 简单分段
    segments = [s.strip() for s in transcript.split("。") if len(s.strip()) > 20]

    # 选金句
    quote = get_quote("daily", rule_result["tags"])

    return {
        "mode": "summary_only",
        "title": "内容摘要",
        "content": transcript,
        "quote": quote,
        "clips": [{"transcript": s, "tags": [], "score": 0.5} for s in segments[:5]],
        "tags": rule_result["tags"],
        "location": rule_result["location"],
        "emotion": rule_result["emotion"],
    }


if __name__ == "__main__":
    # 测试
    test_texts = [
        "今天在大理古城逛了逛，吃了米线，下午去洱海吹风",
        "基层治理涉及多个层级多个领域，各主体各置其位，信息梗阻",
        "今天早上起来做了个早饭，然后去上班，开了三个会",
    ]

    for text in test_texts:
        result = route_by_content(text)
        print(f"原文: {text[:30]}...")
        print(f"  路由: {result['route']}")
        print(f"  可选: {result['options']}")
        print()
