"""
Agent Trace 可观测性：记录每次调用的耗时、token、成本
"""
import time
import uuid
from datetime import datetime
from functools import wraps
from backend.database import db
from backend.config import MODEL_PRICE


def new_trace_id():
    """生成新的 trace_id"""
    return f"trace_{uuid.uuid4().hex[:12]}"


def trace_agent(agent_name: str, model_name: str = ""):
    """
    装饰器：自动记录 Agent 调用的 trace 数据
    用法：
        @trace_agent("asr", "paraformer-realtime-v2")
        def call_asr(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, trace_id: str = None, user_id: str = "default",
                    journey_id: str = None, **kwargs):
            if trace_id is None:
                trace_id = new_trace_id()

            trace_record_id = f"trace_{uuid.uuid4().hex[:16]}"
            start_time = datetime.now().isoformat()
            start_ms = time.time()

            status = "success"
            error_msg = ""
            input_tokens = 0
            output_tokens = 0

            try:
                result = func(*args, **kwargs)

                # 如果返回结果里有 usage 信息，提取出来
                if isinstance(result, dict) and "usage" in result:
                    usage = result["usage"]
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                elif hasattr(result, "usage"):
                    usage = result.usage
                    input_tokens = getattr(usage, "input_tokens", 0) or 0
                    output_tokens = getattr(usage, "output_tokens", 0) or 0

                return result

            except Exception as e:
                status = "error"
                error_msg = str(e)
                raise

            finally:
                end_ms = time.time()
                duration_ms = int((end_ms - start_ms) * 1000)
                end_time = datetime.now().isoformat()

                # 计算成本
                cost_cny = 0.0
                if model_name in MODEL_PRICE:
                    price = MODEL_PRICE[model_name]
                    cost_cny = (input_tokens / 1000) * price["input"] + \
                               (output_tokens / 1000) * price["output"]

                # 写进数据库
                db["agent_traces"].insert({
                    "id": trace_record_id,
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "journey_id": journey_id or "",
                    "agent_name": agent_name,
                    "model_name": model_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_ms": duration_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_cny": round(cost_cny, 6),
                    "status": status,
                    "error_msg": error_msg,
                })

        return wrapper
    return decorator


def get_trace_summary(trace_id: str):
    """获取一次请求的 trace 汇总"""
    rows = db["agent_traces"].rows_where("trace_id = ?", [trace_id])
    traces = list(rows)

    if not traces:
        return None

    total_duration = sum(r["duration_ms"] for r in traces)
    total_input = sum(r["input_tokens"] for r in traces)
    total_output = sum(r["output_tokens"] for r in traces)
    total_cost = sum(r["cost_cny"] for r in traces)

    # 找最慢的步骤
    slowest = max(traces, key=lambda x: x["duration_ms"])

    return {
        "trace_id": trace_id,
        "total_duration_ms": total_duration,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_cny": round(total_cost, 4),
        "call_count": len(traces),
        "slowest_agent": slowest["agent_name"],
        "slowest_duration_ms": slowest["duration_ms"],
        "steps": [
            {
                "agent": r["agent_name"],
                "model": r["model_name"],
                "duration_ms": r["duration_ms"],
                "tokens": r["input_tokens"] + r["output_tokens"],
                "cost": r["cost_cny"],
            }
            for r in traces
        ],
    }
