import os
import json
import base64
import time
import sys
from openai import OpenAI
from typing import Dict, Optional

# 添加当前目录到路径以便导入本地模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from .vector_store import search_similar_cases
from .prompt_config import (
    UserDemographic,
    FRAUD_SYSTEM_PROMPT,
    adjust_confidence_by_demographic,
    should_escalate_for_demographic,
)

# 设置 HuggingFace 国内镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

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

# ---------- Whisper 模型下载配置 ----------
WHISPER_MODEL_URLS = {
    "tiny": "https://hf-mirror.com/openai/whisper-tiny/resolve/main/tiny.pt",
    "base": "https://hf-mirror.com/openai/whisper-base/resolve/main/base.pt",
    "small": "https://hf-mirror.com/openai/whisper-small/resolve/main/small.pt",
    "medium": "https://hf-mirror.com/openai/whisper-medium/resolve/main/medium.pt",
    "large": "https://hf-mirror.com/openai/whisper-large-v3/resolve/main/large-v3.pt",
}

def _download_whisper_model(model_name: str = "base", download_root: str = None) -> str:
    import urllib.request
    if download_root is None:
        download_root = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
    os.makedirs(download_root, exist_ok=True)
    model_url = WHISPER_MODEL_URLS.get(model_name)
    if not model_url:
        model_url = f"https://openaipublic.azureedge.net/main/whisper/models/{model_name}.pt"
    model_path = os.path.join(download_root, f"{model_name}.pt")
    if os.path.exists(model_path):
        return model_path
    print(f"正在从国内镜像下载 Whisper {model_name} 模型...")
    try:
        urllib.request.urlretrieve(model_url, model_path)
        print(f"模型下载完成: {model_path}")
        return model_path
    except Exception as e:
        print(f"下载失败: {e}")
        return None

def load_whisper_model(model_name: str = "base"):
    model_path = _download_whisper_model(model_name)
    if model_path and os.path.exists(model_path):
        return whisper.load_model(model_path, download_root=None)
    else:
        print("使用默认方式加载模型...")
        return whisper.load_model(model_name)

WHISPER_MODEL = load_whisper_model("base")

# ================== 图片分析 ==================
def analyze_image(image_input, demographic: UserDemographic = UserDemographic.ADULT, retry=2) -> Dict:
    """
    分析图片中的诈骗风险，返回结构化结果，支持人群差异化阈值
    """
    image_url = _prepare_image_url(image_input)
    if not image_url:
        return _error_result("无法识别图片格式，请提供路径/URL/base64")

    # 使用统一的系统提示词（可附加检索案例，但图片分析暂不强制检索）
    system_prompt = FRAUD_SYSTEM_PROMPT

    user_prompt = """请分析这张图片中的诈骗风险，严格按照JSON格式输出结果。重点关注：
1. 是否有二维码、转账二维码、收款码
2. 是否包含"立即转账"、"扫码支付"、"垫付"等明确支付指令
3. 是否宣传"高收益"、"保本保收益"、"日赚"等虚假承诺
4. 是否存在虚假身份冒充（如冒充官方、警方、客服等）
5. 提取所有可见文字并识别诈骗关键词
"""

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
            # 确保结果包含必要字段
            risk_level = result.get("risk_level", "unknown")
            confidence = result.get("confidence", 0.5)
            fraud_type = result.get("fraud_type", "")
            suspicious_keywords = result.get("suspicious_keywords", [])
            reason = result.get("reason", "")
            advice = result.get("advice", "")

            # 人群差异化调整
            adjusted_risk_level, adjusted_confidence = adjust_confidence_by_demographic(
                confidence, risk_level, demographic
            )
            # 检查是否需要强制升级
            if should_escalate_for_demographic(fraud_type, demographic, suspicious_keywords):
                adjusted_risk_level = "high"
                adjusted_confidence = max(adjusted_confidence, 0.9)

            response = {
                "success": True,
                "risk_level": adjusted_risk_level,
                "fraud_type": fraud_type,
                "extracted_text": result.get("extracted_text", ""),
                "has_qrcode": result.get("has_qrcode", False),
                "has_link": result.get("has_link", False),
                "has_contact_info": result.get("has_contact_info", False),
                "suspicious_keywords": suspicious_keywords,
                "reason": reason,
                "advice": advice,
                "confidence": adjusted_confidence,
                "raw_response": raw,
            }
            return response
        except Exception as e:
            if attempt == retry:
                return _error_result(f"调用失败: {str(e)}")
            time.sleep(1)

def _prepare_image_url(image_input) -> Optional[str]:
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

# ================== 音频处理 ==================
def transcribe_audio(audio_path: str) -> str:
    try:
        result = WHISPER_MODEL.transcribe(audio_path, language="zh", task="transcribe", temperature=0.0)
        return result["text"]
    except Exception as e:
        print(f"音频转写失败: {e}")
        return ""

# ================== 核心：带向量检索和人群差异化的文本分析 ==================
def analyze_text_for_fraud(text: str, demographic: UserDemographic = UserDemographic.ADULT) -> Dict:
    """
    分析文本内容中的诈骗风险（集成向量检索和人群差异化阈值）
    """
    # 1. 从向量库检索相似案例
    similar_cases = []
    try:
        similar_cases = search_similar_cases(text, top_k=3)
    except Exception as e:
        print(f"向量检索失败: {e}，将不使用检索增强")

    # 2. 构建检索上下文
    context = ""
    if similar_cases:
        context = "\n\n【参考相似案例（从反诈知识库检索）】\n"
        for i, case in enumerate(similar_cases):
            case_text = case['text'][:200] + "..." if len(case['text']) > 200 else case['text']
            context += f"{i+1}. {case_text}\n"
            context += f"   类型: {case.get('type', '未知')} | 相似度: {case['similarity_score']:.2f}\n\n"

    # 3. 使用统一的系统提示词，并附加检索上下文
    base_prompt = FRAUD_SYSTEM_PROMPT
    system_prompt = base_prompt + context

    user_prompt = f"请分析以下文本：\n{text}"

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

        risk_level = result.get("risk_level", "unknown")
        confidence = result.get("confidence", 0.5)
        fraud_type = result.get("fraud_type", "")
        suspicious_keywords = result.get("suspicious_keywords", [])
        reason = result.get("reason", "")
        advice = result.get("advice", "")

        # 人群差异化调整
        adjusted_risk_level, adjusted_confidence = adjust_confidence_by_demographic(
            confidence, risk_level, demographic
        )
        # 强制升级规则
        if should_escalate_for_demographic(fraud_type, demographic, suspicious_keywords):
            adjusted_risk_level = "high"
            adjusted_confidence = max(adjusted_confidence, 0.9)

        response = {
            "success": True,
            "risk_level": adjusted_risk_level,
            "fraud_type": fraud_type,
            "extracted_text": text,
            "has_qrcode": False,
            "has_link": False,
            "has_contact_info": any(kw in text for kw in ["微信", "QQ", "电话", "加我", "扫码"]),
            "suspicious_keywords": suspicious_keywords,
            "reason": reason,
            "advice": advice,
            "confidence": adjusted_confidence,
            "raw_response": raw,
        }
        if similar_cases:
            response["retrieved_cases"] = similar_cases
        return response
    except Exception as e:
        return _error_result(f"文本分析失败: {str(e)}")

def analyze_audio(audio_path: str, demographic: UserDemographic = UserDemographic.ADULT, retry: int = 2) -> Dict:
    text = ""
    for attempt in range(retry + 1):
        text = transcribe_audio(audio_path)
        if text:
            break
        if attempt < retry:
            time.sleep(1)
    if not text:
        return _error_result("音频转写失败或音频内容为空")
    return analyze_text_for_fraud(text, demographic)

def analyze_text(text: str, demographic: UserDemographic = UserDemographic.ADULT) -> Dict:
    return analyze_text_for_fraud(text, demographic)

# ================== 统一入口 ==================
def multimodal_analyze(file_path: str, file_type: str, demographic: UserDemographic = UserDemographic.ADULT) -> Dict:
    if file_type == "image":
        return analyze_image(file_path, demographic)
    elif file_type == "audio":
        return analyze_audio(file_path, demographic)
    else:
        return _error_result("file_type 必须是 'image' 或 'audio'")

# ================== 辅助函数 ==================
def _error_result(error_msg: str) -> Dict:
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
        "advice": "",
        "confidence": 0.0,
    }

# ================== 测试入口 ==================
if __name__ == "__main__":
    # 测试图片（默认成年人）
    local_path = "test_images/游戏交易诈骗.jpeg"
    if os.path.exists(local_path):
        result = analyze_image(local_path, demographic=UserDemographic.ADULT)
        print("图片测试结果：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"图片文件不存在: {local_path}")

    # 测试音频（老年人）
    audio_path = "test_audio/冒充客服退款诈骗.mp3"
    if os.path.exists(audio_path):
        result = analyze_audio(audio_path, demographic=UserDemographic.ELDERLY)
        print("音频测试结果：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"音频文件不存在: {audio_path}")

    # 测试纯文本（儿童）
    test_text = "我们是人性化执法,考虑到你这个年龄,所以没有传唤你到海南这边来"
    text_result = analyze_text(test_text, demographic=UserDemographic.CHILDREN)
    print("\n纯文本测试结果：")
    print(json.dumps(text_result, indent=2, ensure_ascii=False))