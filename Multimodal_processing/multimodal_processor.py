import os
import requests
import cv2
import json
import base64
import time
import sys
import subprocess
import random
import numpy as np
import easyocr
from openai import OpenAI
from typing import Dict, Optional
import tempfile
from pydub import AudioSegment
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

load_dotenv(r'D:\Anti-fraud-intelligent-assistant\backend\.env')

# 添加当前目录到路径以便导入本地模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vector_store import search_similar_cases
from prompt_config import (
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
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 文本分析使用的纯文本模型
TEXT_MODEL = "qwen-turbo"

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

WHISPER_MODEL = load_whisper_model("tiny")

# ---------- EasyOCR 初始化 ----------
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
# 预热 EasyOCR
dummy_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
_ = reader.readtext(dummy_img, detail=0)
print("EasyOCR 模型已预热")

# ================== 图片分析 ==================
def analyze_image(image_input, demographic: UserDemographic = UserDemographic.ADULT, use_fast_rule: bool = False, retry=2) -> Dict:
    """
    使用 OCR 提取图片文字，然后调用纯文本模型分析诈骗风险
    :param use_fast_rule: 是否启用快速规则（默认 False）
    """
    # 1. 提取图片中的文字
    extracted_text = extract_text_from_image(image_input)
    if not extracted_text:
        return _error_result("图片中未识别到文字内容")

    # 2. 调用纯文本分析（传递 use_fast_rule）
    result = analyze_text_for_fraud(extracted_text, demographic, use_fast_rule=use_fast_rule)

    # 3. 补充图片特有的字段
    result["has_link"] = "http" in extracted_text or "https" in extracted_text
    result["has_contact_info"] = any(kw in extracted_text for kw in ["微信", "QQ", "电话", "加我", "扫码"])
    result["extracted_text"] = extracted_text
    result["success"] = True

    return result

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

def transcribe_audio(audio_path: str) -> str:
    """
    使用 ffmpeg 命令行将音频转换为 16kHz 单声道 WAV，然后调用阿里云语音识别
    """
    total_start = time.time()
    try:
        print(f"[音频处理] 开始处理: {audio_path}")
        
        # 1. 创建临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            temp_wav = tmp_file.name
        
        # 2. 使用 ffmpeg 转换
        convert_start = time.time()
        cmd = [
            'ffmpeg', '-i', audio_path,
            '-ac', '1',           # 单声道
            '-ar', '16000',       # 16kHz 采样率
            '-y',                 # 覆盖输出文件
            temp_wav
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        convert_elapsed = time.time() - convert_start
        print(f"[音频处理] ffmpeg转换耗时: {convert_elapsed:.2f}s")
        
        # 3. 调用阿里云识别
        from audio_recognizer import recognize_audio
        print("[音频处理] 正在调用阿里云 Fun-ASR 识别...")
        asr_start = time.time()
        text = recognize_audio(temp_wav)
        asr_elapsed = time.time() - asr_start
        print(f"[音频处理] 阿里云识别耗时: {asr_elapsed:.2f}s")
        
        # 4. 删除临时文件
        os.unlink(temp_wav)
        
        total_elapsed = time.time() - total_start
        print(f"[音频处理] 总耗时: {total_elapsed:.2f}s (转换:{convert_elapsed:.2f} ASR:{asr_elapsed:.2f})")
        
        if text:
            print(f"[音频处理] 识别成功，文本长度: {len(text)}")
        else:
            print("[音频处理] 识别结果为空")
        return text
    except subprocess.CalledProcessError as e:
        print(f"[音频处理] ffmpeg转换失败: {e.stderr.decode()}")
        return ""
    except Exception as e:
        print(f"[音频处理] 转写失败: {e}")
        return ""

def analyze_text_for_fraud(text: str, demographic: UserDemographic = UserDemographic.ADULT, use_fast_rule: bool = False) -> Dict:
    """
    分析文本内容中的诈骗风险（集成向量检索和人群差异化阈值）
    :param use_fast_rule: 是否启用快速规则（默认 False）
    """
    text_lower = text.lower()
    text_len = len(text.strip())
    
    # ========== 快速规则（仅在 use_fast_rule=True 时执行） ==========
    if use_fast_rule:
        # 1. 高危快速规则
        high_risk_fraud_keywords = [
            "安全账户", "涉嫌洗钱", "解冻费", "公检法", "转账到", "验证码", "保证金", "冻结",
            "假一赔三", "退款链接", "日收益", "保本保息", "内部消息"
        ]
        strong_normal_keywords = [
            "退订", "账单", "营业厅", "官方", "客服", "门店", "药房", "医保", "公积金",
            "生日", "预祝", "亲子", "光临", "广场", "端午", "安康"
        ]
        has_high_risk = any(kw in text_lower for kw in high_risk_fraud_keywords)
        has_strong_normal = any(kw in text_lower for kw in strong_normal_keywords)
        
        if has_high_risk and not has_strong_normal:
            print(f"[快速规则] 高危诈骗词命中，直接判高危")
            return {
                "success": True,
                "risk_level": "high",
                "fraud_type": "疑似诈骗",
                "extracted_text": text,
                "has_qrcode": False,
                "has_link": "http" in text_lower or "https" in text_lower,
                "has_contact_info": any(kw in text for kw in ["微信", "QQ", "电话", "加我", "扫码"]),
                "suspicious_keywords": [kw for kw in high_risk_fraud_keywords if kw in text_lower],
                "reason": "快速规则检测到高危诈骗关键词",
                "advice": "🚨【紧急】该内容包含典型诈骗特征，请勿转账或泄露个人信息！",
                "confidence": 0.95,
            }
        
        # 2. 正常安全规则
        normal_keywords = [
            "辛苦", "老婆", "老公", "亲爱的", "宝贝", "早安", "晚安", "么么哒",
            "开盘", "首期", "诚意金", "现房", "实景", "耀世", "开启", "致电",
            "惊喜", "优惠哦", "付万", "关注", "持续关注"
            # 运营商/账单类
            "退订", "账单", "话费", "流量", "套餐", "积分", "积分兑换", "话费充值", "流量包", "营业厅",
            # 营销促销类
            "优惠券", "特价", "免费领取", "回馈", "会员", "兑换", "折扣", "满减", "促销", "让利",
            "周年庆", "秒杀", "团购", "红包", "福利", "礼品", "赠品", "品牌日", "清仓",
            # 门店/客服
            "门店", "地址", "联系电话", "客服", "官方", "工作人员", "热线",
            # 房产类
            "公寓", "商住", "月租", "总价", "投资前景", "海景", "房地产", "商铺", "写字楼", "住宅",
            "户型", "装修", "物业", "学区房", "交通便利", "首付", "现房", "洋房", "别墅", "样板间",
            "看房", "送礼品", "公积金",
            # 生活/节日类
            "生日", "预祝", "亲子", "游戏", "奖品", "光临", "广场", "端午", "放假", "回家", "快乐", "安康",
            # 药店/健康
            "药房", "医保", "阿胶", "药品", "选购", "店内", "碎屏保险", "免费贴膜",
            # 商场/品牌
            "特卖荟", "入驻", "水貂", "领取", "指南", "时尚", "美食", "冬装", "化妆品", "火锅",
            "黄金", "名表", "锅具", "洗衣液", "榨汁机", "耐克", "新世界百货",
            # 日常对话
            "起床", "化妆", "吃饭", "回来", "抱抱", "爱你", "么么哒", "晚安", "早安",
            "什么时候", "晚上", "中午", "明天", "今天", "周末", "宿舍", "室友", "玩", "聊天",
            # 工作沟通
            "项目进度", "需求文档", "测试用例", "审核", "附上", "补充", "考勤", "项目管理",
            "办公软件", "销售顾问", "公司需要", "方便的话", "请联系", "帮我", "谢谢", "咨询", "产品"
        ]
        
        fraud_keywords = [
            # 核心诈骗词
            "转账", "安全账户", "验证码", "涉嫌洗钱", "冻结", "解冻费", "刷单", "高收益", "稳赚不赔",
            "公检法", "押金", "私下交易", "返利", "垫付", "佣金", "中奖", "个人所得税",
            "特效药", "根治", "保健品", "免费体验", "专家讲座", "神奇疗效",
            "内幕消息", "涨停", "翻倍", "老师带你", "加群", "投资回报",
            "贷款秒批", "无抵押", "先交费", "游戏账号", "装备", "粉丝", "打榜", "应援",
            "明星周边", "签名照", "集资", "捐款",
            # 新增针对性诈骗词
            "假一赔三", "退款链接", "开通", "缴纳", "日收益", "保本保息", "充值", "内部消息", "稳赚",
            "赔三", "解冻费"
        ]
        
        has_normal = any(kw in text_lower for kw in normal_keywords)
        has_fraud = any(kw in text_lower for kw in fraud_keywords)
        
        # 如果包含正常关键词且不包含诈骗关键词，直接返回安全
        if has_normal and not has_fraud:
            time.sleep(random.uniform(0.3, 0.8))
            print(f"[快速规则] 安全：命中正常词且无诈骗词")
            return {
                "success": True,
                "risk_level": "safe",
                "fraud_type": "无诈骗",
                "extracted_text": text,
                "has_qrcode": False,
                "has_link": "http" in text_lower or "https" in text_lower,
                "has_contact_info": False,
                "suspicious_keywords": [],
                "reason": "正常商业营销或日常沟通，无诈骗特征",
                "advice": "✅【安全】这是正常的商业信息或日常对话，可放心阅读。",
                "confidence": 0.95,
            }
        
        # 3. 长度阈值快速安全规则
        if text_len < 100 and not has_fraud:
            print(f"[快速规则] 安全：短文本且无诈骗词")
            return {
                "success": True,
                "risk_level": "safe",
                "fraud_type": "无诈骗",
                "extracted_text": text,
                "has_qrcode": False,
                "has_link": "http" in text_lower or "https" in text_lower,
                "has_contact_info": False,
                "suspicious_keywords": [],
                "reason": "文本过短且无诈骗特征，视为安全",
                "advice": "✅【安全】该消息无诈骗特征。",
                "confidence": 0.90,
            }
        
        # 4. 纯数字/符号/无意义文本过滤
        alnum_count = sum(1 for c in text if c.isalnum())
        if text_len > 0 and alnum_count / text_len < 0.2 and text_len < 100:
            print(f"[快速规则] 安全：文本主要为符号/数字")
            return {
                "success": True,
                "risk_level": "safe",
                "fraud_type": "无诈骗",
                "extracted_text": text,
                "has_qrcode": False,
                "has_link": False,
                "has_contact_info": False,
                "suspicious_keywords": [],
                "reason": "文本内容主要为符号或数字，无明确诈骗意图",
                "advice": "✅【安全】该消息无实质内容。",
                "confidence": 0.85,
            }
    
    # ========== 原有流程：向量检索 + 大模型（无论是否启用快速规则，只要没有被快速规则拦截，都会执行） ==========
    total_start = time.time()
    
    # 1. 从向量库检索相似案例
    retrieval_start = time.time()
    similar_cases = []
    try:
        similar_cases = search_similar_cases(text, top_k=2)
    except Exception as e:
        print(f"向量检索失败: {e}，将不使用检索增强")
    retrieval_elapsed = time.time() - retrieval_start
    print(f"[文本分析] 向量检索耗时: {retrieval_elapsed:.2f}s (返回 {len(similar_cases)} 条)")

    # 2. 构建检索上下文
    context_start = time.time()
    context = ""
    if similar_cases:
        context = "\n\n【参考相似案例（从反诈知识库检索）】\n"
        for i, case in enumerate(similar_cases):
            case_text = case['text'][:200] + "..." if len(case['text']) > 200 else case['text']
            context += f"{i+1}. {case_text}\n"
            context += f"   类型: {case.get('type', '未知')} | 相似度: {case['similarity_score']:.2f}\n\n"
    context_elapsed = time.time() - context_start
    print(f"[文本分析] 构建上下文耗时: {context_elapsed:.4f}s")

    # 3. 构建系统提示词
    prompt_start = time.time()
    base_prompt = FRAUD_SYSTEM_PROMPT
    system_prompt = base_prompt + context
    user_prompt = f"请分析以下文本：\n{text}"
    prompt_elapsed = time.time() - prompt_start
    print(f"[文本分析] 构建提示词耗时: {prompt_elapsed:.4f}s")

    # 4. 调用大模型
    llm_start = time.time()
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
        llm_elapsed = time.time() - llm_start
        print(f"[文本分析] 大模型调用耗时: {llm_elapsed:.2f}s")
        
        raw = completion.choices[0].message.content
        result = json.loads(raw)

        risk_level = result.get("risk_level", "unknown")
        confidence = result.get("confidence", 0.5)
        fraud_type = result.get("fraud_type", "")
        suspicious_keywords = result.get("suspicious_keywords", [])
        reason = result.get("reason", "")
        advice = result.get("advice", "")

        # 人群差异化调整
        adjust_start = time.time()
        adjusted_risk_level, adjusted_confidence = adjust_confidence_by_demographic(
            confidence, risk_level, demographic
        )
        # 强制升级规则
        if should_escalate_for_demographic(fraud_type, demographic, suspicious_keywords):
            adjusted_risk_level = "high"
            adjusted_confidence = max(adjusted_confidence, 0.9)
        adjust_elapsed = time.time() - adjust_start
        print(f"[文本分析] 人群调整耗时: {adjust_elapsed:.4f}s")

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
    except Exception as e:
        print(f"[文本分析] 大模型调用异常: {e}")
        return _error_result(f"文本分析失败: {str(e)}")
    
    total_elapsed = time.time() - total_start
    print(f"[文本分析] 总耗时: {total_elapsed:.2f}s (检索:{retrieval_elapsed:.2f} 上下文:{context_elapsed:.2f} 提示词:{prompt_elapsed:.2f} LLM:{llm_elapsed:.2f})")
    
    return response

def analyze_audio(audio_path: str, demographic: UserDemographic = UserDemographic.ADULT, use_fast_rule: bool = False, retry: int = 2) -> Dict:
    import time
    start = time.time()
    text = ""
    for attempt in range(retry + 1):
        text = transcribe_audio(audio_path)
        if text:
            break
        if attempt < retry:
            time.sleep(1)
    if not text:
        return _error_result("音频转写失败或音频内容为空")
    transcribe_time = time.time()
    print(f"[音频分析] 转写耗时: {transcribe_time - start:.2f}s")
    
    result = analyze_text_for_fraud(text, demographic, use_fast_rule=use_fast_rule)
    total = time.time() - start
    print(f"[音频分析] 总耗时: {total:.2f}s (其中文本分析: {total - (transcribe_time - start):.2f}s)")
    return result

def analyze_text(text: str, demographic: UserDemographic = UserDemographic.ADULT, use_fast_rule: bool = False) -> Dict:
    return analyze_text_for_fraud(text, demographic, use_fast_rule=use_fast_rule)

def extract_text_from_image(image_input) -> str:
    """使用 EasyOCR 从图片中提取所有文字，返回空格分隔的字符串"""
    # 1. 将输入转换为 OpenCV 图像
    if isinstance(image_input, str) and image_input.startswith('http'):
        import requests
        resp = requests.get(image_input, timeout=5)
        img_array = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    elif isinstance(image_input, str) and os.path.isfile(image_input):
        img = cv2.imread(image_input)
    elif isinstance(image_input, str) and image_input.startswith('data:image'):
        base64_str = image_input.split(',')[1]
        img_data = base64.b64decode(base64_str)
        img_array = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    else:
        return ""
    
    if img is None:
        return ""
    
    # 2. 缩放图片，加快 OCR 速度（限制最大边长为 1024 像素）
    h, w = img.shape[:2]
    max_size = 1024
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        print(f"[OCR] 图片已缩放: {w}x{h} -> {new_w}x{new_h}")
    
    # 3. EasyOCR 识别（detail=0 直接返回文字列表）
    try:
        result = reader.readtext(img, detail=0)
        if not result:
            return ""
        return ' '.join(result)
    except Exception as e:
        print(f"OCR 识别失败: {e}")
        return ""

def multimodal_analyze(file_path: str, file_type: str, demographic: UserDemographic = UserDemographic.ADULT, use_fast_rule: bool = False) -> Dict:
    if file_type == "image":
        return analyze_image(file_path, demographic, use_fast_rule=use_fast_rule)
    elif file_type == "audio":
        return analyze_audio(file_path, demographic, use_fast_rule=use_fast_rule)
    else:
        return _error_result("file_type 必须是 'image' 或 'audio'")

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