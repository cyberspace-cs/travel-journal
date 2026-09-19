"""
FastAPI 入口
"""
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from backend.config import HOST, PORT, AUDIO_DIR
from backend.database import init_db, db
from backend.agents.rag import init_knowledge_base
from backend.agents.router import route_request
from backend.pipelines.simple_pipeline import fast_pipeline, enhanced_pipeline
from backend.traces import get_trace_summary

app = FastAPI(title="旅行手帐 AI", version="0.1.0")

# 挂载前端静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.on_event("startup")
def startup():
    """启动时初始化"""
    init_db()
    # init_knowledge_base()  # 先注释，Chroma 模型下载慢，Demo 用 mock 数据
    print("🚀 服务器启动成功！")


# ========== 前端页面 ==========

@app.get("/", response_class=HTMLResponse)
def index():
    """首页"""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()


# ========== API 接口 ==========

@app.post("/api/process-audio")
async def process_audio(
    audio: UploadFile = File(...),
    mode: str = Form("quick"),  # quick / deep
):
    """
    上传音频，处理生成手帐
    """
    # 保存音频文件
    audio_id = f"audio_{uuid.uuid4().hex[:12]}"
    audio_path = AUDIO_DIR / f"{audio_id}.wav"

    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    print(f"收到音频：{audio_path}, 模式：{mode}")

    # 路由判断
    route_result = route_request(user_query="", user_mode=mode)
    path = route_result["path"]

    print(f"路由到：{path}")

    # 跑流水线
    if mode == "deep":
        result = enhanced_pipeline(str(audio_path))
    else:
        result = fast_pipeline(str(audio_path))

    # 加 trace 信息
    trace_summary = get_trace_summary(result["trace_id"])
    result["trace"] = trace_summary

    return result


@app.get("/api/trace/{trace_id}")
def get_trace(trace_id: str):
    """查看某个请求的 trace 详情"""
    summary = get_trace_summary(trace_id)
    if summary is None:
        return {"error": "trace not found"}
    return summary


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# ========== 旅程 CRUD ==========

@app.post("/api/journeys")
def create_journey(title: str = Form(...), start_date: str = Form(...), end_date: str = Form(None)):
    """创建新旅程"""
    journey_id = f"journey_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    db["journeys"].insert({
        "id": journey_id,
        "title": title,
        "start_date": start_date,
        "end_date": end_date or start_date,
        "cover_image": "",
        "created_at": now,
    })

    return {"id": journey_id, "title": title, "start_date": start_date}


@app.get("/api/journeys")
def list_journeys():
    """列出所有旅程"""
    rows = db.execute("SELECT * FROM journeys ORDER BY created_at DESC")
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "start_date": r["start_date"],
            "end_date": r["end_date"],
            "cover_image": r.get("cover_image", ""),
        }
        for r in rows
    ]


@app.get("/api/journeys/{journey_id}")
def get_journey(journey_id: str):
    """获取单个旅程详情 + 所有天"""
    try:
        journey = db["journeys"].get(journey_id)
    except:
        return {"error": "journey not found"}

    days = list(db["days"].rows_where("journey_id = ?", [journey_id], order_by="date"))

    return {
        "id": journey["id"],
        "title": journey["title"],
        "start_date": journey["start_date"],
        "end_date": journey["end_date"],
        "days": days,
    }


# ========== 手帐详情 ==========

@app.get("/api/days/{day_id}")
def get_day_detail(day_id: str):
    """获取某一天的完整手帐"""
    try:
        day = db["days"].get(day_id)
    except:
        return {"error": "day not found"}

    clips = list(db["audio_clips"].rows_where("day_id = ?", [day_id], order_by="start_time"))

    return {
        "id": day["id"],
        "date": day["date"],
        "title": day["title"],
        "weather": day.get("weather", ""),
        "summary": day["summary"],
        "clips": clips,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
