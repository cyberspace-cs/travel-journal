"""
ASR Agent：语音转文字
"""
import requests
import dashscope
from dashscope.audio.asr import Transcription
from backend.config import DASHSCOPE_API_KEY, QWEN_ASR_MODEL
from backend.traces import trace_agent

dashscope.api_key = DASHSCOPE_API_KEY


@trace_agent("asr", QWEN_ASR_MODEL)
def transcribe_audio(audio_url: str):
    """
    把音频文件转成文字
    :param audio_url: 音频文件的 URL
    :return: 转写结果
    """
    # 如果是本地文件路径，用 mock 模式
    if audio_url.startswith("/") or audio_url.startswith("./"):
        print("[ASR] 本地文件，使用 mock 转写结果")
        mock_text = """
        今天在大理古城逛了逛，吃了碗米线，三十年的老店，味道特别好。
        下午去了洱海，风特别大，但是很舒服，水很蓝，像镜子一样。
        晚上在古城里找了家小酒馆，喝了点酒，听人唱歌，感觉很放松。
        今天走了很多路，但是心情特别好，好久没这么放松了。
        """
        return {
            "text": mock_text.strip(),
            "usage": {"input_tokens": 0, "output_tokens": len(mock_text)},
        }

    task = Transcription.async_call(
        model=QWEN_ASR_MODEL,
        file_urls=[audio_url],
    )
    task_id = task.output["task_id"]

    result = Transcription.wait(task_id)

    if result.output["task_status"] == "SUCCEEDED":
        transcription_url = result.output["results"][0]["transcription_url"]
        resp = requests.get(transcription_url)
        data = resp.json()
        text = data["transcripts"][0]["text"]
        return {
            "text": text,
            "usage": {"input_tokens": 0, "output_tokens": len(text)},
        }
    else:
        raise Exception(f"ASR 失败: {result.output}")
