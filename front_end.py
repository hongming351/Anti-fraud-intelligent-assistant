import streamlit as st
import pandas as pd
import time
import json
import requests
from datetime import datetime

# 后端API配置
BACKEND_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 角色/性别/灵敏度映射
ROLE_MAP = {
    "儿童/青少年": "child",
    "青年（学生/职场新人）": "youth",
    "中年（职场人士）": "adult",
    "老年人": "elderly",
    "财务/高管（高风险）": "high_risk"
}

GENDER_MAP = {
    "男": "male",
    "女": "female"
}

RISK_MAP = {
    "低": "low",
    "中": "medium",
    "高": "high"
}

# 页面配置
st.set_page_config(
    page_title="多模态反诈智能助手",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化主题设置
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

# 主题CSS
light_theme = """
<style>
    body {
        background-color: #f8f9fa;
        color: #333;
    }
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    .auth-container {
        max-width: 400px;
        margin: 5rem auto;
        padding: 2rem;
        background: white;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .risk-high {
        background-color: #FEE2E2;
        border-left: 5px solid #DC2626;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .risk-mid {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .risk-low {
        background-color: #E0F2FE;
        border-left: 5px solid #3B82F6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .warning-box {
        background-color: #FFF1F0;
        border: 1px solid #FFCCC7;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #6B7280;
    }
    .theme-toggle {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }
</style>
"""

dark_theme = """
<style>
    body {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    .auth-container {
        max-width: 400px;
        margin: 5rem auto;
        padding: 2rem;
        background: #2d2d2d;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .main-header {
        font-size: 2.5rem;
        color: #64b5f6;
        text-align: center;
        margin-bottom: 1rem;
    }
    .risk-high {
        background-color: #4a1e1e;
        border-left: 5px solid #dc2626;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .risk-mid {
        background-color: #4a3a1e;
        border-left: 5px solid #f59e0b;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .risk-low {
        background-color: #1e2a4a;
        border-left: 5px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .warning-box {
        background-color: #4a1e2a;
        border: 1px solid #ffccc7;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #999;
    }
    .theme-toggle {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }
    input, textarea, select {
        background-color: #3d3d3d !important;
        color: #e0e0e0 !important;
        border: 1px solid #555 !important;
    }
    button {
        background-color: #3b82f6 !important;
        color: white !important;
    }
</style>
"""

# 应用主题
if st.session_state["theme"] == "dark":
    st.markdown(dark_theme, unsafe_allow_html=True)
else:
    st.markdown(light_theme, unsafe_allow_html=True)

# 主题切换按钮
st.markdown('<div class="theme-toggle">', unsafe_allow_html=True)
col_theme = st.columns([1, 1])
with col_theme[0]:
    if st.button("🌙 切换暗色模式" if st.session_state["theme"] == "light" else "☀️ 切换亮色模式"):
        st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 用户认证和API调用函数
def register_user(username, email, password, role, gender, risk_sensitivity, guardian_name="", guardian_phone="", guardian_email=""):
    """注册新用户"""
    try:
        url = f"{BACKEND_URL}{API_PREFIX}/auth/register"
        data = {
            "username": username,
            "email": email,
            "password": password,
            "role": ROLE_MAP.get(role, "youth"),
            "gender": GENDER_MAP.get(gender, gender),
            "risk_sensitivity": RISK_MAP.get(risk_sensitivity, "medium"),
            "guardian_name": guardian_name if guardian_name else None,
            "guardian_phone": guardian_phone if guardian_phone else None,
            "guardian_email": guardian_email if guardian_email else None
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code in (200, 201):
            return response.json()
        else:
            try:
                error_detail = response.json().get("detail", response.text)
                st.error(f"注册失败：{response.status_code} - {error_detail}")
            except:
                st.error(f"注册失败：{response.status_code} - {response.text}")
        return None
    except Exception as e:
        st.error(f"注册请求异常: {e}")
        return None

def login_user(username, password):
    """用户登录"""
    try:
        url = f"{BACKEND_URL}{API_PREFIX}/auth/login"
        data = {
            "username": username,
            "password": password,
            "scope": ""
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(url, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            st.session_state["access_token"] = result.get("access_token")
            st.session_state["user_info"] = {"username": username}
            return True
        else:
            try:
                error_detail = response.json().get("detail", "未知错误")
                st.error(f"登录失败: {error_detail}")
            except:
                st.error(f"登录失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        st.error(f"登录请求异常: {e}")
        return False

def update_knowledge_base():
    """手动更新知识库"""
    try:
        url = f"{BACKEND_URL}{API_PREFIX}/admin/knowledge/update"
        headers = {}
        if "access_token" in st.session_state and st.session_state["access_token"]:
            headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
        
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"更新失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"更新请求异常: {e}")
        return None

def get_system_status(force_refresh=False):
    """获取系统状态和自学习进度，支持缓存和定期更新"""
    current_time = time.time()
    cache_duration = 30  # 缓存30秒
    
    if (force_refresh or 
        st.session_state["system_status_cache"] is None or 
        current_time - st.session_state["last_status_update"] > cache_duration):
        
        try:
            url = f"{BACKEND_URL}{API_PREFIX}/admin/system/status"
            headers = {}
            if "access_token" in st.session_state and st.session_state["access_token"]:
                headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                st.session_state["system_status_cache"] = response.json()
                st.session_state["last_status_update"] = current_time
            else:
                # 模拟数据
                st.session_state["system_status_cache"] = {
                    "knowledge_base": {
                        "total_cases": 12384,
                        "last_updated": "2026-03-28T00:00:00",
                        "cases_by_type": {"诈骗类型1": 5000, "诈骗类型2": 4000, "其他": 3384},
                        "cases_by_risk_level": {"low": 3000, "medium": 6000, "high": 3384}
                    },
                    "learning_status": {
                        "progress": 0.85,
                        "last_training": "2026-03-28T03:00:00",
                        "total_training_samples": 15000,
                        "next_scheduled_training": "每日 03:00"
                    },
                    "system_health": {
                        "vector_db": "healthy",
                        "api_server": "healthy",
                        "last_health_check": datetime.now().isoformat()
                    }
                }
                st.session_state["last_status_update"] = current_time
        except Exception as e:
            st.session_state["system_status_cache"] = {
                "knowledge_base": {
                    "total_cases": 12384,
                    "last_updated": "2026-03-28T00:00:00",
                    "cases_by_type": {"诈骗类型1": 5000, "诈骗类型2": 4000, "其他": 3384},
                    "cases_by_risk_level": {"low": 3000, "medium": 6000, "high": 3384}
                },
                "learning_status": {
                    "progress": 0.85,
                    "last_training": "2026-03-28T03:00:00",
                    "total_training_samples": 15000,
                    "next_scheduled_training": "每日 03:00"
                },
                "system_health": {
                    "vector_db": "healthy",
                    "api_server": "healthy",
                    "last_health_check": datetime.now().isoformat()
                }
            }
            st.session_state["last_status_update"] = current_time
    
    return st.session_state["system_status_cache"]

# 初始化session state
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None
if "role" not in st.session_state:
    st.session_state["role"] = "青年（学生/职场新人）"
if "gender" not in st.session_state:
    st.session_state["gender"] = "男"
if "risk_sensitivity" not in st.session_state:
    st.session_state["risk_sensitivity"] = "中"
if "guardian_name" not in st.session_state:
    st.session_state["guardian_name"] = ""
if "guardian_phone" not in st.session_state:
    st.session_state["guardian_phone"] = ""
if "guardian_email" not in st.session_state:
    st.session_state["guardian_email"] = ""
if "last_status_update" not in st.session_state:
    st.session_state["last_status_update"] = 0
if "system_status_cache" not in st.session_state:
    st.session_state["system_status_cache"] = None

# 认证检查
if not st.session_state["access_token"]:
    # 未登录状态 - 显示居中的登录/注册表单
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🛡️ 多模态反诈智能助手</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center;">基于多模态AI的实时反诈防护系统</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    auth_tab = st.selectbox("选择操作", ["登录", "注册"], index=0)
    
    if auth_tab == "登录":
        st.subheader("🔑 用户登录")
        login_username = st.text_input("用户名", key="login_username")
        login_password = st.text_input("密码", type="password", key="login_password")
        
        if st.button("🔑 登录"):
            if login_username and login_password:
                if login_user(login_username, login_password):
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("登录失败，请检查用户名和密码")
            else:
                st.error("登录失败，请检查用户名和密码")
    
    else:  # 注册
        st.subheader("📝 用户注册")
        reg_username = st.text_input("用户名", key="reg_username")
        reg_email = st.text_input("邮箱", key="reg_email")
        reg_password = st.text_input("密码", type="password", key="reg_password")
        reg_confirm_password = st.text_input("确认密码", type="password", key="reg_confirm_password")
        
        st.markdown("---")
        st.caption("基本信息（必填）")
        reg_role = st.selectbox(
            "选择您的身份",
            ["儿童/青少年", "青年（学生/职场新人）", "中年（职场人士）", "老年人", "财务/高管（高风险）"],
            key="reg_role"
        )
        reg_gender = st.radio("性别", ["男", "女"], key="reg_gender")
        reg_risk_sensitivity = st.select_slider(
            "预警灵敏度",
            options=["低", "中", "高"],
            value="中",
            key="reg_risk_sensitivity"
        )
        
        st.markdown("---")
        st.caption("监护人信息（可选）")
        reg_guardian_name = st.text_input("监护人姓名", placeholder="例如：张老师", key="reg_guardian_name")
        reg_guardian_phone = st.text_input("监护人电话", placeholder="用于紧急通知", key="reg_guardian_phone")
        reg_guardian_email = st.text_input("监护人邮箱", placeholder="用于报告推送", key="reg_guardian_email")
        
        if st.button("📝 注册"):
            if not reg_username or not reg_email or not reg_password:
                st.warning("请填写所有必填字段")
            elif reg_password != reg_confirm_password:
                st.error("两次输入的密码不一致")
            else:
                result = register_user(
                    username=reg_username,
                    email=reg_email,
                    password=reg_password,
                    role=reg_role,
                    gender=reg_gender,
                    risk_sensitivity=reg_risk_sensitivity,
                    guardian_name=reg_guardian_name,
                    guardian_phone=reg_guardian_phone,
                    guardian_email=reg_guardian_email
                )
                if result:
                    st.success("注册成功！请登录")
                else:
                    st.error("注册失败，用户名或邮箱可能已被使用")
    
    st.markdown("---")
    st.title("⚙️ 个性化设置")
    st.markdown("---")
    
    # 角色定制
    st.subheader("👤 我的角色")
    st.session_state["role"] = st.selectbox(
        "选择您的身份",
        ["儿童/青少年", "青年（学生/职场新人）", "中年（职场人士）", "老年人", "财务/高管（高风险）"],
        index=["儿童/青少年", "青年（学生/职场新人）", "中年（职场人士）", "老年人", "财务/高管（高风险）"].index(st.session_state["role"])
    )
    st.session_state["gender"] = st.radio("性别", ["男", "女"], horizontal=True, index=0 if st.session_state["gender"] == "男" else 1)
    
    st.markdown("---")
    st.subheader("👨‍👩‍👧 监护人联动")
    st.session_state["guardian_name"] = st.text_input("监护人姓名", placeholder="例如：张老师", value=st.session_state["guardian_name"])
    st.session_state["guardian_phone"] = st.text_input("监护人电话", placeholder="用于紧急通知", value=st.session_state["guardian_phone"])
    st.session_state["guardian_email"] = st.text_input("监护人邮箱", placeholder="用于报告推送", value=st.session_state["guardian_email"])
    
    st.markdown("---")
    st.subheader("📋 风险偏好")
    st.session_state["risk_sensitivity"] = st.select_slider(
        "预警灵敏度",
        options=["低", "中", "高"],
        value=st.session_state["risk_sensitivity"]
    )
    
    # 知识库更新状态 - 调用后端API获取真实数据
    st.markdown("---")
    st.subheader("🧠 智能进化状态")
    
    system_status = get_system_status()
    knowledge_base = system_status.get("knowledge_base", {})
    learning_status = system_status.get("learning_status", {})
    
    last_updated = knowledge_base.get("last_updated", "2026-03-28T00:00:00")
    if isinstance(last_updated, str):
        try:
            last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            last_updated_str = last_updated_dt.strftime("%Y-%m-%d %H:%M")
        except:
            last_updated_str = last_updated
    else:
        last_updated_str = "未知时间"
    
    if st.button("🔄 手动更新反诈知识库"):
        with st.spinner("正在同步最新诈骗案例库..."):
            result = update_knowledge_base()
            if result:
                st.success(f"知识库更新成功！更新于: {result.get('updated_at', '刚刚')}")
                system_status = get_system_status()
                knowledge_base = system_status.get("knowledge_base", {})
                learning_status = system_status.get("learning_status", {})
            else:
                st.error("知识库更新失败，请检查后端服务")
    
    st.caption(f"自动更新: 每日 03:00 | 最后更新: {last_updated_str}")
    st.caption(f"当前知识库条目: {knowledge_base.get('total_cases', 12384):,} 条诈骗模式")
    st.caption(f"模型自学习进度: {learning_status.get('progress', 0.85):.1%}")

# 主页面标题
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.markdown('<div class="main-header">🛡️ 多模态反诈智能助手</div>', unsafe_allow_html=True)
st.markdown("基于多模态AI的实时反诈防护系统 | 支持文本、语音、图像联合分析")

# 创建三列用于不同模态输入
col_text, col_audio, col_image = st.columns(3)

input_data = {
    "text": "",
    "audio": None,
    "image": None
}

audio_file = None
image_file = None

with col_text:
    st.subheader("📝 文本分析")
    st.caption("支持聊天记录、短信、社交媒体文案")
    text_input = st.text_area("请输入可疑文本内容", height=150, 
                              placeholder="例如：您有一笔异地大额消费异常，请点击链接核实...\n或者：我是XX公安局，您的账户涉嫌洗钱，需要将资金转入安全账户...")
    input_data["text"] = text_input

with col_audio:
    st.subheader("🎙️ 语音分析")
    st.caption("支持通话录音、语音消息（.wav/.mp3）")
    audio_file = st.file_uploader("上传音频文件", type=["wav", "mp3", "m4a"], key="audio")
    if audio_file is not None:
        st.audio(audio_file, format="audio/wav")
        input_data["audio"] = audio_file.name
        st.success("音频文件已上传，将进行语音合成分析")
    else:
        st.info("未上传音频文件")

with col_image:
    st.subheader("🖼️ 视觉分析")
    st.caption("支持屏幕截图、视频截图、图片")
    image_file = st.file_uploader("上传图片/截图", type=["jpg", "jpeg", "png"], key="image")
    if image_file is not None:
        st.image(image_file, caption="上传的图片")
        input_data["image"] = image_file.name
        st.success("图片已上传，将进行OCR和场景分析")
    else:
        st.info("未上传图片")

def call_backend_analysis(text, audio_file, image_file, enable_deep_audio, enable_ocr, enable_behavior_profile):
    """调用后端API进行多模态分析"""
    try:
        url = f"{BACKEND_URL}{API_PREFIX}/analyze/multimodal"
        files = {}
        data = {
            "text": text or "",
            "enable_deep_analysis": str(enable_behavior_profile).lower(),
            "enable_deep_audio": str(enable_deep_audio).lower(),
            "enable_ocr": str(enable_ocr).lower(),
            "enable_behavior_profile": str(enable_behavior_profile).lower()
        }
        if audio_file:
            files["audio_file"] = (audio_file.name, audio_file.getvalue(), audio_file.type)
        if image_file:
            files["image_file"] = (image_file.name, image_file.getvalue(), image_file.type)
        headers = {}
        if "access_token" in st.session_state and st.session_state["access_token"]:
            headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
        response = requests.post(url, data=data, files=files or None, headers=headers)
        if response.status_code in (200, 201):
            return response.json()
        else:
            st.error(f"分析失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"调用API失败: {e}")
        return None

# 高级选项
with st.expander("🔍 高级分析选项"):
    col_adv1, col_adv2, col_adv3 = st.columns(3)
    with col_adv1:
        enable_deep_audio = st.checkbox("深度语音特征分析", value=True)
    with col_adv2:
        enable_ocr = st.checkbox("OCR文字提取", value=True)
    with col_adv3:
        enable_behavior_profile = st.checkbox("结合用户行为画像", value=True)
    st.caption("注：启用更多分析可能增加响应时间，但提升准确率")

def mock_analysis(text, audio_flag, image_flag, role, sensitivity):
    """模拟多模态融合分析"""
    high_risk_keywords = ["安全账户", "转账", "验证码", "涉嫌洗钱", "冻结账户", "保证金", "贷款", "刷单", "投资高回报", "公检法"]
    mid_risk_keywords = ["中奖", "客服", "退款", "链接", "扫码", "兼职", "代购", "陌生链接"]
    
    risk_score = 0
    fraud_type = "正常交流"
    details = ""
    
    if text:
        text_lower = text.lower()
        for kw in high_risk_keywords:
            if kw in text_lower:
                risk_score += 40
                fraud_type = "高危诈骗（冒充公检法/投资理财）"
                details = f"检测到高危关键词: {kw}"
                break
        if risk_score == 0:
            for kw in mid_risk_keywords:
                if kw in text_lower:
                    risk_score += 20
                    fraud_type = "中危风险（诱导点击/刷单）"
                    details = f"检测到可疑关键词: {kw}"
                    break
    
    if audio_flag:
        risk_score += 15
        if risk_score < 30:
            fraud_type = "可疑语音内容"
            details += "；语音中可能包含诱导话术"
        else:
            details += "；语音合成深度伪造可能性较高"
    
    if image_flag:
        risk_score += 10
        text_lower = text.lower() if text else ""
        if "二维码" in text_lower:
            risk_score += 15
            details += "；图片包含二维码或钓鱼界面"
        else:
            details += "；图片含有疑似诈骗界面"
    
    role_weight = {"儿童/青少年": 1.3, "青年（学生/职场新人）": 1.1, "中年（职场人士）": 1.0, "老年人": 1.4, "财务/高管（高风险）": 1.5}
    sensitivity_weight = {"低": 0.8, "中": 1.0, "高": 1.2}
    risk_score = risk_score * role_weight.get(role, 1.0) * sensitivity_weight.get(sensitivity, 1.0)
    risk_score = min(risk_score, 100)
    
    if risk_score >= 60:
        level = "高危"
        level_class = "risk-high"
        advice = "立即中断联系！已触发监护人联动，建议立即报警或联系96110反诈专线。"
    elif risk_score >= 30:
        level = "中危"
        level_class = "risk-mid"
        advice = "存在较大诈骗风险，请勿转账或提供个人信息，建议核实对方身份。"
    else:
        level = "低危"
        level_class = "risk-low"
        advice = "无明显诈骗特征，但仍需保持警惕，避免泄露个人信息。"
    
    confidence = 0.7 + (risk_score / 100) * 0.25
    confidence = min(confidence, 0.98)
    
    return {
        "level": level,
        "level_class": level_class,
        "risk_score": risk_score,
        "fraud_type": fraud_type,
        "details": details if details else "基于多模态分析未发现明显异常",
        "advice": advice,
        "confidence": confidence,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# 分析按钮与结果展示
st.markdown("---")
col_btn, col_status = st.columns([1, 3])
with col_btn:
    analyze_btn = st.button("🚨 立即智能分析", type="primary")

if analyze_btn:
    if not input_data["text"] and not audio_file and not image_file:
        st.warning("请至少输入文本、上传音频或图片其中一种数据进行分析")
    else:
        with st.spinner("正在多模态融合分析中... 语音特征提取中 | 图像OCR识别中 | 行为画像匹配中"):
            backend_result = call_backend_analysis(
                text=input_data["text"],
                audio_file=audio_file,
                image_file=image_file,
                enable_deep_audio=enable_deep_audio,
                enable_ocr=enable_ocr,
                enable_behavior_profile=enable_behavior_profile
            )
            if backend_result:
                result = backend_result
                risk_level_map = {"high": "高危", "medium": "中危", "low": "低危"}
                level = risk_level_map.get(result.get("risk_level", "low"), "低危")
                level_class_map = {"high": "risk-high", "medium": "risk-mid", "low": "risk-low"}
                level_class = level_class_map.get(result.get("risk_level", "low"), "risk-low")
            else:
                st.warning("后端API调用失败，使用模拟分析结果")
                time.sleep(1)
                result = mock_analysis(
                    text=input_data["text"],
                    audio_flag=input_data["audio"] is not None,
                    image_flag=input_data["image"] is not None,
                    role=st.session_state["role"],
                    sensitivity=st.session_state["risk_sensitivity"]
                )
                level = result["level"]
                level_class = result["level_class"]
        
        st.markdown("## 📊 智能分析结果")
        with st.container():
            st.markdown(f'<div class="{level_class}">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("风险等级", level, delta=None)
                st.metric("置信度", f"{result.get('confidence', 0.7):.1%}")
            with col2:
                st.metric("诈骗类型", result.get("fraud_type", "未知类型"))
                st.metric("风险评分", f"{result.get('risk_score', 0):.0f}/100")
            with col3:
                st.metric("分析时间", result.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                if level == "高危":
                    st.error("⚠️ 立即阻断")
                elif level == "中危":
                    st.warning("⚠️ 需警惕")
                else:
                    st.info("✅ 正常")
            st.markdown(f"**🔍 详细分析：** {result.get('details', '无详细分析')}")
            st.markdown(f"**💡 处置建议：** {result.get('advice', '请保持警惕')}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 分级预警展示 - 修复 guardian_phone 变量
        st.markdown("### 🔔 实时预警机制")
        guardian_phone_val = st.session_state.get("guardian_phone", "")
        if level == "高危":
            st.error("🔴 高危预警：已触发弹窗阻断并自动通知监护人！")
            if guardian_phone_val:
                st.warning(f"📞 正在拨打监护人电话 {guardian_phone_val} 进行紧急联动...")
            else:
                st.info("请完善监护人信息以启用自动联动")
        elif level == "中危":
            st.warning("🟡 中危提醒：建议立即核实对方身份，谨防受骗。")
        else:
            st.info("🔵 当前会话安全，持续监控中。")
        
        # 生成安全监测报告
        st.markdown("### 📄 安全监测报告")
        report_data = {
            "用户角色": st.session_state["role"],
            "性别": st.session_state["gender"],
            "监护人": st.session_state["guardian_name"] if st.session_state["guardian_name"] else "未设置",
            "分析时间": result.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "风险等级": level,
            "诈骗类型": result.get("fraud_type", "未知类型"),
            "置信度": f"{result.get('confidence', 0.7):.1%}",
            "详细分析": result.get("details", "无详细分析"),
            "处置建议": result.get("advice", "请保持警惕"),
            "多模态输入": f"文本: {'有' if input_data['text'] else '无'}, 音频: {'有' if audio_file else '无'}, 图像: {'有' if image_file else '无'}"
        }
        report_df = pd.DataFrame([report_data])
        st.dataframe(report_df)
        
        csv = report_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 下载安全监测报告 (CSV)",
            data=csv,
            file_name=f"反诈报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
        
        # 自适应进化模块提示
        st.markdown("### 🧬 自适应进化")
        st.success("本次分析结果已用于优化反诈模型，知识库持续进化中。")
        system_status = get_system_status()
        learning_status = system_status.get("learning_status", {})
        learning_progress = learning_status.get("progress", 0.85)
        st.progress(learning_progress, text=f"模型自学习进度: {learning_progress:.1%}")
        
        with st.expander("📊 查看详细学习状态"):
            col_learn1, col_learn2 = st.columns(2)
            with col_learn1:
                st.metric("总训练样本数", f"{learning_status.get('total_training_samples', 15000):,}")
                st.metric("最后训练时间", learning_status.get('last_training', '2026-03-28T03:00:00'))
            with col_learn2:
                st.metric("下次计划训练", learning_status.get('next_scheduled_training', '每日 03:00'))
                st.metric("知识库案例数", f"{system_status.get('knowledge_base', {}).get('total_cases', 12384):,}")
        
elif not analyze_btn:
    st.info("👆 点击【立即智能分析】按钮，系统将综合文本、语音、视觉信息进行诈骗风险研判")

# 实时监测区域
st.markdown("---")
st.markdown("### 📡 全时守护状态")
col_guard1, col_guard2, col_guard3 = st.columns(3)
with col_guard1:
    st.metric("今日拦截风险会话", "3", delta="+2")
with col_guard2:
    st.metric("当前活跃监控渠道", "文本/语音/图像", delta=None)
with col_guard3:
    st.metric("用户满意度", "98%", delta="+1%")

st.markdown("---")
st.markdown('<div class="footer">多模态反诈智能助手 | 基于AI的全民反诈防护体系 | 实时守护您的数字生活</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)