"""
数据库初始化和连接
"""
import sqlite3
import sqlite_utils
from backend.config import DB_PATH

# 先创建 sqlite3 连接，允许跨线程使用
_conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
db = sqlite_utils.Database(_conn)


def init_db():
    """初始化数据库表"""
    # 旅程表
    if "journeys" not in db.table_names():
        db["journeys"].create({
            "id": str,
            "title": str,
            "start_date": str,
            "end_date": str,
            "cover_image": str,
            "created_at": str,
        }, pk="id")

    # 天数表
    if "days" not in db.table_names():
        db["days"].create({
            "id": str,
            "journey_id": str,
            "date": str,
            "title": str,
            "weather": str,
            "summary": str,
        }, pk="id", foreign_keys=[("journey_id", "journeys")])

    # 音频片段表
    if "audio_clips" not in db.table_names():
        db["audio_clips"].create({
            "id": str,
            "day_id": str,
            "audio_file": str,
            "start_time": str,
            "end_time": str,
            "transcript": str,
            "user_quote": str,
            "ai_enhanced": str,
            "tags": str,  # JSON 数组
            "score": float,
            "location": str,
            "emotion": str,
            "created_at": str,
        }, pk="id", foreign_keys=[("day_id", "days")])

    # 知识库片段表
    if "knowledge_chunks" not in db.table_names():
        db["knowledge_chunks"].create({
            "id": str,
            "content": str,
            "city": str,
            "category": str,
            "source": str,
            "embedding_id": str,
            "created_at": str,
        }, pk="id")

    # 用户偏好表
    if "user_preferences" not in db.table_names():
        db["user_preferences"].create({
            "id": str,
            "user_id": str,
            "pref_type": str,
            "pref_value": float,
            "updated_at": str,
        }, pk="id")

    # Agent Trace 表
    if "agent_traces" not in db.table_names():
        db["agent_traces"].create({
            "id": str,
            "trace_id": str,
            "user_id": str,
            "journey_id": str,
            "agent_name": str,
            "model_name": str,
            "start_time": str,
            "end_time": str,
            "duration_ms": int,
            "input_tokens": int,
            "output_tokens": int,
            "cost_cny": float,
            "status": str,
            "error_msg": str,
        }, pk="id")

    print("✅ 数据库初始化完成")


if __name__ == "__main__":
    init_db()
