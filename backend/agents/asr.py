"""
ASR Agent：语音转文字
"""
import dashscope
from dashscope.audio.asr import Transcription
from backend.config import DASHSCOPE_API_KEY, QWEN_ASR_MODEL
from backend.traces import trace_agent

dashscope.api_key = DASHSCOPE_API_KEY


@trace_agent("asr", QWEN_ASR_MODEL)
def transcribe_audio(audio_url: str):
    """
    把音频文件转成文字
    :param audio_url: 音频文件的 URL 或本地路径
    :return: 转写结果
    """
    # Demo 阶段：如果没有 API key，返回 mock 结果
    if DASHSCOPE_API_KEY == "your-api-key-here":
        return {
            "text": "今天在大理古城逛了逛，人好多啊，但是很有感觉。吃了一家很好吃的米线，老板是本地人，说他们做了三十年了。下午去了洱海，风吹过来特别舒服，看到好多人在拍照。",
            "usage": {"input_tokens": 0, "output_tokens": 100},
        }

    # 真实调用千问 ASR
    task = Transcription.async_call(
        model=QWEN_ASR_MODEL,
        file_urls=[audio_url],
    )
    result = Transcription.wait(task.task_id)

    if result.status_code == 200:
        text = result.output["results"][0]["transcription_url"]
        return {
            "text": text,
            "usage": {"input_tokens": 0, "output_tokens": 500},
        }
    else:
        raise Exception(f"ASR 失败: {result.message}")
