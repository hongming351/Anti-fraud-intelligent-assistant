import os
import time
import dashscope
from dashscope.audio.asr import Recognition
from http import HTTPStatus
from dotenv import load_dotenv

# 加载 backend 目录下的 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', '.env')
load_dotenv(env_path)
print(f"[DEBUG] 尝试加载 .env 文件: {env_path}")

def recognize_audio(audio_file_path: str) -> str:
    print(f"[DEBUG] 开始调用阿里云 Fun-ASR，音频文件: {audio_file_path}")
    start_time = time.time()
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误: 未找到 DASHSCOPE_API_KEY 环境变量")
        return ""
    print(f"[DEBUG] API Key 已加载（长度: {len(api_key)}）")
    
    dashscope.api_key = api_key

    recognition = Recognition(
        model='paraformer-realtime-v2',
        format='wav',
        sample_rate=16000,
        language_hints=['zh'],
        callback=None
    )
    
    print("[DEBUG] 正在发送识别请求...")
    result = recognition.call(audio_file_path)
    
    elapsed = time.time() - start_time
    print(f"[DEBUG] 识别请求完成，耗时: {elapsed:.2f} 秒")
    
    if result.status_code == HTTPStatus.OK:
        sentences = result.get_sentence()
        text = ''.join([s['text'] for s in sentences]) if sentences else ""
        print(f"[DEBUG] 识别成功，文本长度: {len(text)} 字符")
        return text
    else:
        print(f"语音识别失败: {result.message}")
        return ""