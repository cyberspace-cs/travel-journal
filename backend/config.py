"""
配置文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
CHROMA_DIR = DATA_DIR / "chroma_db"
DB_PATH = DATA_DIR / "app.db"

# 确保目录存在
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# 千问 API
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "your-api-key-here")
QWEN_ASR_MODEL = "paraformer-realtime-v2"
QWEN_LITE_MODEL = "qwen-turbo"  # 轻量模型，快
QWEN_PRO_MODEL = "qwen-plus"    # 质量高模型

# 模型价格（每 1k tokens，人民币）
MODEL_PRICE = {
    "qwen-turbo": {"input": 0.0003, "output": 0.0006},
    "qwen-plus": {"input": 0.0008, "output": 0.002},
}

# 服务器配置
HOST = "0.0.0.0"
PORT = 8000
