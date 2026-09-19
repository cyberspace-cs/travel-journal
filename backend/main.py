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
from backend.database import init_db
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
    init_knowledge_base()
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
