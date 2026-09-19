"""
说话人分离模块
Demo 阶段先 mock，产品化接 pyannote 或阿里云 API
"""
import uuid
from typing import List, Dict


def diarize_speakers(audio_path: str, num_speakers: int = 2) -> List[Dict]:
    """
    说话人分离：把音频按说话人分段
    :param audio_path: 音频文件路径
    :param num_speakers: 预计说话人数
    :return: [{speaker: "spk0", start: 0.0, end: 5.2, text: "..."}]
    """
    # Demo 阶段先 mock 一个示例
    # 产品化接 pyannote.audio 或阿里云智能语音交互 API
    print(f"[说话人分离] 处理 {audio_path}，预计 {num_speakers} 个说话人")

    # 假设有两个说话人：用户自己 + 朋友
    mock_result = [
        {
            "speaker": "spk_you",
            "start_time": 0.0,
            "end_time": 8.5,
            "text": "今天的风好舒服啊，你看那边的山",
        },
        {
            "speaker": "spk_friend",
            "start_time": 8.5,
            "end_time": 12.0,
            "text": "是啊，好久没出来玩了",
        },
        {
            "speaker": "spk_you",
            "start_time": 12.0,
            "end_time": 20.3,
            "text": "对啊，出来走走感觉整个人都放松了",
        },
    ]

    return mock_result


def identify_speaker_voice(voice_embedding):
    """
    声纹识别：判断这个声音是谁
    Demo 阶段先不做，产品化做
    """
    return "unknown"


if __name__ == "__main__":
    result = diarize_speakers("test.wav")
    for r in result:
        print(f"[{r['speaker']}] {r['start_time']:.1f}s - {r['end_time']:.1f}s: {r['text']}")
