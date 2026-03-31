import os
import json
import base64
import time
from openai import OpenAI
from typing import Dict, Optional

# 导入 Whisper（需要已安装 openai-whisper）
import whisper

# ---------- 初始化大模型客户端 ----------
client = OpenAI(
    api_key="sk-5a37562a35fb4f8e9cfa79007314b2ce",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 图片分析使用的多模态模型
IMAGE_MODEL = "qwen2.5-vl-32b-instruct"
# 文本分析使用的纯文本模型
TEXT_MODEL = "qwen-max"

# ---------- 初始化 Whisper 音频转文字模型 ----------
# 可选模型: "tiny", "base", "small", "medium", "large"
# 平衡速度和准确率推荐 "base" 或 "small"
WHISPER_MODEL = whisper.load_model("base")

# ================== 图片分析部分（已有） ==================

def analyze_image(image_input, retry=2) -> Dict:
    """
    分析图片中的诈骗风险，返回结构化结果
    
    Args:
        image_input: 本地图片路径、图片URL或base64字符串
        retry: 失败重试次数
    
    Returns:
        Dict: 包含 success, risk_level, fraud_type, extracted_text,
              has_qrcode, has_link, has_contact_info, suspicious_keywords, reason
    """
    image_url = _prepare_image_url(image_input)
    if not image_url:
        return _error_result("无法识别图片格式，请提供路径/URL/base64")

    system_prompt = """你是一个反诈专家。请分析用户提供的图片，判断是否涉及诈骗风险。
严格按照JSON格式输出，不要添加任何其他内容。示例：
{
    "risk_level": "high",
    "fraud_type": "刷单诈骗",
    "extracted_text": "图片中的所有文字内容",
    "has_qrcode": true,
    "has_link": true,
    "has_contact_info": true,
    "suspicious_keywords": ["垫付", "佣金", "日赚"],
    "reason": "图片中包含垫付返利等典型刷单诈骗关键词"
}
风险等级说明：
- high: 明显诈骗（如转账二维码、刷单、投资陷阱）
- medium: 可疑（如不明链接、诱导加好友）
- low: 轻微可疑但不确定
- safe: 完全正常
诈骗类型可选：刷单诈骗、杀猪盘、冒充公检法、虚假贷款、投资理财诈骗、游戏交易诈骗、追星诈骗、养生保健品诈骗、AI换脸诈骗、其他
"""

    user_prompt = """请分析这张图片，输出JSON。重点关注：
- 是否有二维码/链接/联系方式
- 是否包含诱导转账、高额回报、紧急处理等话术
- 提取所有可见文字"""

    for attempt in range(retry + 1):
        try:
            completion = client.chat.completions.create(
                model=IMAGE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_url}},
                            {"type": "text", "text": user_prompt},
                        ],
                    },
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw = completion.choices[0].message.content
            result = json.loads(raw)
            result["success"] = True
            result["raw_response"] = raw
            return result
        except Exception as e:
            if attempt == retry:
                return _error_result(f"调用失败: {str(e)}")
            time.sleep(1)

def _prepare_image_url(image_input) -> Optional[str]:
    """将各种输入转为图片URL或base64 data URL"""
    if isinstance(image_input, str) and (image_input.startswith("http://") or image_input.startswith("https://")):
        return image_input
    if isinstance(image_input, str) and os.path.isfile(image_input):
        with open(image_input, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
            mime = "image/jpeg" if image_input.lower().endswith((".jpg", ".jpeg")) else "image/png"
            return f"data:{mime};base64,{img_data}"
    if isinstance(image_input, str) and image_input.startswith("data:image/"):
        return image_input
    return None

# ================== 音频处理模块（新增） ==================

def transcribe_audio(audio_path: str) -> str:
    """
    将音频文件转成文字（使用 Whisper）
    
    Args:
        audio_path: 音频文件路径（支持 mp3, wav, m4a, flac 等）
    
    Returns:
        转写出的文字内容，失败返回空字符串
    """
    try:
        result = WHISPER_MODEL.transcribe(
            audio_path,
            language="zh",      # 指定中文，提高准确率
            task="transcribe",  # 直接转写，不翻译
            temperature=0.0     # 越低结果越确定
        )
        return result["text"]
    except Exception as e:
        print(f"音频转写失败: {e}")
        return ""

def analyze_text_for_fraud(text: str) -> Dict:
    """
    分析文本内容中的诈骗风险（供音频模块复用）
    
    Args:
        text: 待分析的文本内容
    
    Returns:
        与 analyze_image 相同格式的字典
    """
    system_prompt = """你是一个反诈专家。分析以下文本是否涉及诈骗，严格按照JSON格式输出。
诈骗类型可选：["刷单诈骗","冒充客服退款诈骗","杀猪盘", "冒充公检法", "虚假贷款", "投资理财诈骗", "游戏交易诈骗", "追星诈骗", "养生保健品诈骗", "AI换脸诈骗", "虚假中奖诈骗", "无诈骗"]

输出格式：
{
    "risk_level": "high/medium/low/safe",
    "fraud_type": "从上面枚举中选择",
    "suspicious_keywords": ["关键词1", "关键词2"],
    "reason": "判断理由"
}
"""
    user_prompt = f"请分析以下文本：{text}"
    
    try:
        completion = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        raw = completion.choices[0].message.content
        result = json.loads(raw)
        
        # 补充字段以保持与 analyze_image 格式一致
        return {
            "success": True,
            "risk_level": result.get("risk_level", "unknown"),
            "fraud_type": result.get("fraud_type", ""),
            "extracted_text": text,  # 原始转写文本
            "has_qrcode": False,      # 音频没有二维码
            "has_link": False,        # 音频没有链接
            "has_contact_info": any(kw in text for kw in ["微信", "QQ", "电话", "加我", "扫码"]),
            "suspicious_keywords": result.get("suspicious_keywords", []),
            "reason": result.get("reason", ""),
            "raw_response": raw
        }
    except Exception as e:
        return _error_result(f"文本分析失败: {str(e)}")

def analyze_audio(audio_path: str, retry: int = 2) -> Dict:
    """
    分析音频文件中的诈骗风险（完整流程：转文字 → 文本分析）
    
    Args:
        audio_path: 音频文件路径
        retry: 重试次数（目前仅用于转文字，文本分析内部已带重试）
    
    Returns:
        与 analyze_image 相同格式的字典
    """
    # 1. 音频转文字（可加重试）
    text = ""
    for attempt in range(retry + 1):
        text = transcribe_audio(audio_path)
        if text:
            break
        if attempt < retry:
            time.sleep(1)
    
    if not text:
        return _error_result("音频转写失败或音频内容为空")
    
    # 2. 调用文本分析
    return analyze_text_for_fraud(text)

# ================== 纯文本分析入口（补全致命漏洞！） ==================
def analyze_text(text: str) -> Dict:
    """
    纯文本反诈分析统一入口
    供后端文本接口调用，完全复用大模型分析逻辑
    Args:
        text: 前端输入的纯文本内容
    Returns:
        统一格式的分析结果字典
    """
    return analyze_text_for_fraud(text)

# ================== 统一入口（供后端调用） ==================

def multimodal_analyze(file_path: str, file_type: str) -> Dict:
    """
    统一的多模态分析入口
    
    Args:
        file_path: 文件路径（本地文件）
        file_type: "image" 或 "audio"
    
    Returns:
        统一格式的分析结果
    """
    if file_type == "image":
        return analyze_image(file_path)
    elif file_type == "audio":
        return analyze_audio(file_path)
    else:
        return _error_result("file_type 必须是 'image' 或 'audio'")

# ================== 辅助函数 ==================

def _error_result(error_msg: str) -> Dict:
    """生成错误结果字典"""
    return {
        "success": False,
        "error": error_msg,
        "risk_level": "unknown",
        "fraud_type": "",
        "extracted_text": "",
        "has_qrcode": False,
        "has_link": False,
        "has_contact_info": False,
        "suspicious_keywords": [],
        "reason": error_msg,
    }

# ================== 测试入口 ==================
if __name__ == "__main__":
    # 测试图片
    local_path = "test_images/游戏交易诈骗.jpeg"
    result = analyze_image(local_path)
    print("图片测试结果：")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 测试音频
    audio_path = "test_audio/冒充客服退款诈骗.mp3"
    if os.path.exists(audio_path):
        result = analyze_audio(audio_path)
        print("音频测试结果：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("请准备一个测试音频文件，并修改 audio_path 变量")
    
    # 新增：测试纯文本分析
    test_text = "我们是人性化执法,考虑到你这个年龄,所以没有传唤你到海南这边来"
    text_result = analyze_text(test_text)
    print("\n纯文本测试结果：")
    print(json.dumps(text_result, indent=2, ensure_ascii=False))