"""
简单流水线：快速路径
"""
import uuid
from datetime import datetime
from backend.database import db
from backend.agents.asr import transcribe_audio
from backend.agents.writer import tag_and_score, write_journal
from backend.agents.rag import retrieve_context
from backend.agents.self_evolution import evaluate_journal
from backend.traces import new_trace_id


def fast_pipeline(audio_file_path: str, journey_id: str = None,
                  trace_id: str = None):
    """
    极速流水线（快速模式 + 简单任务）：
    ASR → 分段 → 打标签 → 筛选 Top N → 写手帐
    目标：10-20 秒出结果
    """
    if trace_id is None:
        trace_id = new_trace_id()

    print(f"[Fast Pipeline] trace_id={trace_id} 开始处理 {audio_file_path}")

    # Step 1: ASR 转写
    print("[Step 1/5] ASR 转写中...")
    asr_result = transcribe_audio(audio_file_path, trace_id=trace_id)
    transcript = asr_result["text"]

    # Step 2: 简单分段（按句号分）
    print("[Step 2/5] 语义分段中...")
    segments = [s.strip() for s in transcript.split("。") if len(s.strip()) > 10]

    # Step 3: 打标签+打分（并行模拟）
    print("[Step 3/5] 打标签打分中...")
    clips = []
    for seg in segments:
        tag_result = tag_and_score(seg, trace_id=trace_id)
        clips.append({
            "transcript": seg,
            "tags": tag_result.get("tags", []),
            "score": tag_result.get("score", 0.5),
            "location": tag_result.get("location", "未知"),
            "emotion": tag_result.get("emotion", "平静"),
        })

    # Step 4: 筛选 Top N（按分数排序）
    print("[Step 4/5] 筛选优质片段...")
    clips.sort(key=lambda x: x["score"], reverse=True)
    top_clips = clips[:5]  # 取前 5 个

    # Step 5: 写手帐
    print("[Step 5/6] 写手帐中...")
    journal = write_journal(top_clips, mode="quick", trace_id=trace_id)

    # Step 6: 自我评估（自进化）
    print("[Step 6/6] 自我评估中...")
    evaluation = evaluate_journal(
        content=journal["content"],
        title=journal["title"],
        clips=top_clips,
        trace_id=trace_id,
    )

    result = {
        "trace_id": trace_id,
        "title": journal["title"],
        "content": journal["content"],
        "clips": top_clips,
        "mode": "fast",
        "evaluation": evaluation,
    }

    print(f"[Fast Pipeline] 完成！自评得分 {evaluation.get('overall_score', 0)}/10")
    return result


def enhanced_pipeline(audio_file_path: str, journey_id: str = None,
                      trace_id: str = None):
    """
    增强流水线（深度模式 + 简单任务）：
    Fast Pipeline + RAG 知识库召回
    目标：30 秒左右
    """
    if trace_id is None:
        trace_id = new_trace_id()

    print(f"[Enhanced Pipeline] trace_id={trace_id}")

    # 先跑 fast pipeline 拿到基础结果
    base_result = fast_pipeline(audio_file_path, journey_id, trace_id)

    # 加 RAG：根据提到的地名召回攻略
    print("[Enhanced] 加 RAG 知识库...")
    locations = [c.get("location", "") for c in base_result["clips"]]
    locations = [l for l in locations if l and l != "未知"]

    rag_contexts = []
    for loc in locations[:2]:  # 只查前 2 个地点
        rag_result = retrieve_context(loc, trace_id=trace_id)
        rag_contexts.extend(rag_result["contexts"])

    # 把 RAG 结果加到 AI 补充里
    if rag_contexts:
        base_result["ai_enhanced"] = rag_contexts

    return base_result
