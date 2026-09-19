"""
简单流水线：快速路径
"""
import uuid
from datetime import datetime
from backend.database import db
from backend.agents.asr import transcribe_audio
from backend.agents.writer import tag_and_score, write_journal, generate_quote
from backend.agents.rule_nlp import rule_based_classify
from backend.agents.tts import generate_journal_audio
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

    # Step 3: 打标签+打分（用规则化NLP，不调大模型，省成本）
    print("[Step 3/7] 打标签打分中（规则化，不调大模型）...")
    clips = []
    for seg in segments:
        # 先用规则化跑，快且免费
        rule_result = rule_based_classify(seg)
        clips.append({
            "transcript": seg,
            "tags": rule_result["tags"],
            "score": rule_result["score"],
            "location": rule_result["location"],
            "emotion": rule_result["emotion"],
        })

    # Step 4: 筛选 Top N（按分数排序）
    print("[Step 4/5] 筛选优质片段...")
    clips.sort(key=lambda x: x["score"], reverse=True)
    top_clips = clips[:5]  # 取前 5 个

    # Step 5: 写手帐
    print("[Step 5/7] 写手帐中...")
    journal = write_journal(top_clips, mode="quick", trace_id=trace_id)

    # Step 6: 自我评估（自进化）
    print("[Step 6/7] 自我评估中...")
    evaluation = evaluate_journal(
        content=journal["content"],
        title=journal["title"],
        clips=top_clips,
        trace_id=trace_id,
    )

    # 自评低于 7 分，自动重新生成一次
    if evaluation.get("overall_score", 10) < 7:
        print(f"[自进化] 自评 {evaluation.get('overall_score', 0)} 分，低于 7 分，重新生成...")
        print(f"[自进化] 改进建议：{evaluation.get('improvement_suggestion', '')}")
        # 重新生成一次（第二次会自动参考改进建议）
        journal = write_journal(top_clips, mode="quick", trace_id=trace_id)
        evaluation = evaluate_journal(
            content=journal["content"],
            title=journal["title"],
            clips=top_clips,
            trace_id=trace_id,
        )

    # Step 7: 生成今日金句
    print("[Step 7/8] 生成今日金句...")
    quote_result = generate_quote(journal["content"], top_clips, trace_id=trace_id)

    # Step 8: 生成语音版手帐（免费，不用大模型）
    print("[Step 8/8] 生成语音版手帐...")
    journal_text = f"{journal['title']}。{journal['content']}"
    audio_result = generate_journal_audio(trace_id, journal_text)

    result = {
        "trace_id": trace_id,
        "title": journal["title"],
        "content": journal["content"],
        "quote": quote_result["quote"],
        "clips": top_clips,
        "mode": "fast",
        "evaluation": evaluation,
        "audio_url": f"/static/audio/journal_{trace_id}.mp3",
    }

    print(f"[Fast Pipeline] 完成！自评 {evaluation.get('overall_score', 0)}/10")
    print(f"[金句] {quote_result['quote']}")
    print(f"[语音] {audio_result['audio_path']}")
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
