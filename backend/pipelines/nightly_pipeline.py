"""
夜间离线整理 Pipeline
晚上 12 点自动跑，或者手动触发
把白天攒的片段整理成完整手帐
"""
import uuid
from datetime import datetime
from backend.database import db
from backend.agents.writer import write_journal, generate_quote
from backend.agents.rule_nlp import rule_based_classify
from backend.agents.diarization import diarize_speakers
from backend.agents.tts import generate_journal_audio
from backend.agents.self_evolution import evaluate_journal
from backend.traces import new_trace_id


def nightly_organize_pipeline(journey_id: str, date: str = None, trace_id: str = None):
    """
    夜间离线整理 pipeline
    读取白天攒的所有片段，整理成完整手帐
    """
    if trace_id is None:
        trace_id = new_trace_id()
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"[夜间整理] trace_id={trace_id}，旅程={journey_id}，日期={date}")

    # Step 1: 读取今天所有的音频片段
    print("[Step 1/7] 读取今天的音频片段...")
    # Demo 阶段先 mock 几个片段
    clips = [
        {
            "transcript": "早上吃了一家三十年的米线，汤底特别鲜",
            "time": "08:30",
            "tags": ["美食"],
            "score": 0.9,
            "location": "大理古城",
            "emotion": "开心",
        },
        {
            "transcript": "爬玉龙雪山，高反了但是看到雪山那一刻值了",
            "time": "10:30",
            "tags": ["景点", "感受"],
            "score": 0.85,
            "location": "玉龙雪山",
            "emotion": "感动",
        },
        {
            "transcript": "在束河古镇吃的腊排骨火锅，太香了",
            "time": "12:30",
            "tags": ["美食"],
            "score": 0.8,
            "location": "束河古镇",
            "emotion": "开心",
        },
        {
            "transcript": "下午在咖啡馆坐了一下午，窗外就是苍山",
            "time": "15:00",
            "tags": ["感受", "景点"],
            "score": 0.9,
            "location": "大理",
            "emotion": "平静",
        },
        {
            "transcript": "傍晚去了蓝月谷，水蓝得像宝石一样",
            "time": "18:00",
            "tags": ["景点"],
            "score": 0.85,
            "location": "蓝月谷",
            "emotion": "惊喜",
        },
        {
            "transcript": "晚上在古城酒吧街听了首民谣，氛围不错",
            "time": "20:00",
            "tags": ["感受"],
            "score": 0.75,
            "location": "大理古城",
            "emotion": "平静",
        },
    ]

    print(f"   找到 {len(clips)} 个片段")

    # Step 2: 按时间排序
    print("[Step 2/7] 按时间排序...")
    clips.sort(key=lambda x: x["time"])

    # Step 3: 深度理解（串联上下文）
    print("[Step 3/7] 深度理解中...")
    # 产品化这里调大模型做深度理解，Demo 先跳过

    # Step 4: 写手帐
    print("[Step 4/7] 写手帐中...")
    journal = write_journal(clips, mode="deep", trace_id=trace_id)

    # Step 5: 自我评估
    print("[Step 5/7] 自我评估中...")
    evaluation = evaluate_journal(
        content=journal["content"],
        title=journal["title"],
        clips=clips,
        trace_id=trace_id,
    )

    # 低于 7 分自动重写
    if evaluation.get("overall_score", 10) < 7:
        print(f"   自评 {evaluation.get('overall_score', 0)} 分，重写一次...")
        journal = write_journal(clips, mode="deep", trace_id=trace_id)
        evaluation = evaluate_journal(
            content=journal["content"],
            title=journal["title"],
            clips=clips,
            trace_id=trace_id,
        )

    # Step 6: 生成金句
    print("[Step 6/7] 生成今日金句...")
    quote_result = generate_quote(journal["content"], clips, trace_id=trace_id)

    # Step 7: 生成语音版
    print("[Step 7/7] 生成语音版手帐...")
    journal_text = f"{journal['title']}。{journal['content']}"
    audio_result = generate_journal_audio(trace_id, journal_text)

    result = {
        "trace_id": trace_id,
        "journey_id": journey_id,
        "date": date,
        "title": journal["title"],
        "content": journal["content"],
        "quote": quote_result["quote"],
        "clips_count": len(clips),
        "evaluation": evaluation,
        "audio_url": f"/static/audio/journal_{trace_id}.mp3",
        "mode": "nightly",
        "created_at": datetime.now().isoformat(),
    }

    print(f"[夜间整理] 完成！自评 {evaluation.get('overall_score', 0)}/10")
    print(f"[金句] {quote_result['quote']}")
    return result


if __name__ == "__main__":
    # 测试
    result = nightly_organize_pipeline("test_journey")
    print("\n=== 结果 ===")
    print(f"标题: {result['title']}")
    print(f"金句: {result['quote']}")
    print(f"片段数: {result['clips_count']}")
