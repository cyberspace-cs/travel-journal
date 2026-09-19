"""
TTS 语音合成模块：把手帐文字转成语音
用 edge-tts，免费，不用 API key
"""
import asyncio
import edge_tts
from pathlib import Path
from backend.config import AUDIO_DIR


# 可选的音色
VOICES = {
    "female_warm": "zh-CN-XiaoxiaoNeural",  # 温暖女声
    "male_gentle": "zh-CN-YunxiNeural",     # 温柔男声
    "female_lively": "zh-CN-XiaoyiNeural",  # 活泼女声
}


async def _generate_tts(text: str, output_path: str, voice: str = "female_warm"):
    """内部异步生成 TTS"""
    voice_id = VOICES.get(voice, VOICES["female_warm"])
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_path)


def generate_journal_audio(journal_id: str, content: str, voice: str = "female_warm"):
    """
    把手帐内容转成语音
    :param journal_id: 手帐 ID
    :param content: 手帐文字内容
    :param voice: 音色选择
    :return: 音频文件路径
    """
    output_file = AUDIO_DIR / f"journal_{journal_id}.mp3"

    # 运行异步生成
    asyncio.run(_generate_tts(content, str(output_file), voice))

    return {
        "audio_path": str(output_file),
        "voice": voice,
        "duration_estimate": len(content) / 4,  # 大概每秒 4 个字
    }


if __name__ == "__main__":
    # 测试
    test_text = "今天在大理逛了一天，空气里都是慢悠悠的味道。早上吃了一家很好吃的米线，下午去了洱海，风吹过来特别舒服。"
    result = generate_journal_audio("test", test_text)
    print(f"✅ 生成成功：{result['audio_path']}")
    print(f"   预计时长：{result['duration_estimate']:.1f} 秒")
