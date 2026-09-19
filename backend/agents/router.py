"""
Router：路由层，判断走哪条路径
"""
import dashscope
from dashscope import Generation
from backend.config import DASHSCOPE_API_KEY, QWEN_LITE_MODEL
from backend.traces import trace_agent

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
