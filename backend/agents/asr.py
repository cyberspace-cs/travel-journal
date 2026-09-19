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
