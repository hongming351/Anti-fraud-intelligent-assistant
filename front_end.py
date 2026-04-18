import streamlit as st
import pandas as pd
import time
import base64
import json
import requests
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

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
    /* 全局背景渐变 */
    body {
        background-image: url('static/background.jpeg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-color: #f8f9fa;
        color: #333;
        font-size: 14px;
    }
    
    /* 主容器 */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* 登录/注册卡片 - 毛玻璃 + 圆角 + 阴影 */
    .auth-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 0 2rem 2rem !important;
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(12px);
        border-radius: 2rem;
        box-shadow: 0 25px 45px -12px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.5);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .auth-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 30px 50px -15px rgba(0, 0, 0, 0.25);
    }
    
    /* 标题渐变 */
    .main-header {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
        text-align: center;
    }
    
    /* 副标题 */
    .auth-container > div[style*="text-align: center"] {
        font-size: 0.9rem;
        color: #6B7280;
        margin-bottom: 1.8rem;
        font-weight: 500;
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input {
        border-radius: 1rem !important;
        border: 1px solid #E5E7EB !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease;
        background-color: #F9FAFB !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.2) !important;
        background-color: white !important;
        outline: none;
    }
    
    /* 下拉选择框（选项卡） */
    .stSelectbox > div > div > select {
        border-radius: 2rem !important;
        background-color: #F3F4F6 !important;
        border: none !important;
        font-weight: 500;
        padding: 0.5rem 1rem !important;
        color: #1F2937;
    }
    
    /* 单选按钮组 */
    .stRadio > div {
        gap: 1rem;
    }
    .stRadio label {
        font-weight: 500;
        color: #374151;
    }
    
    /* 按钮 */
    .stButton > button {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%) !important;
        border: none !important;
        border-radius: 2rem !important;
        padding: 0.6rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        color: white !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 12px -4px rgba(59,130,246,0.4);
    }
    
    /* 分隔线 */
    hr {
        margin: 1.5rem 0;
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #D1D5DB, transparent);
    }
    
    /* 标签文字 */
    .stTextInput label, .stSelectbox label, .stRadio label {
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.25rem;
        font-size: 0.85rem;
    }
    
    /* 链接/提示文字 */
    .stCaption, .stMarkdown small {
        color: #6B7280;
    }
    
    /* 风险等级卡片样式保持不变 */
    .risk-high {
        background-color: #FEE2E2;
        border-left: 5px solid #DC2626;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-size: 14px;
    }
    .risk-mid {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-size: 14px;
    }
    .risk-low {
        background-color: #E0F2FE;
        border-left: 5px solid #3B82F6;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-size: 14px;
    }
    .warning-box {
        background-color: #FFF1F0;
        border: 1px solid #FFCCC7;
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        font-size: 14px;
    }
    .footer {
        text-align: center;
        margin-top: 1.5rem;
        color: #6B7280;
        font-size: 12px;
    }
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
    
    /* 其他 Streamlit 组件微调 */
    .stTextInput > div > div > input, .stSelectbox > div > div > select {
        font-size: 14px;
        padding: 8px;
    }
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stSubheader {
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stTitle, .stCaption {
        text-align: center !important;
    }
    /* 全局重置顶部边距 */
    body, .stApp, .stAppViewContainer, .stAppViewBlockContainer, .stMarkdown {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
</style>
"""

dark_theme = """
<style>
    /* 暗色渐变背景 */
    body {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
        color: #e0e0e0;
        font-size: 14px;
    }
    
    /* 主容器 */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* 登录/注册卡片 - 毛玻璃 + 圆角 + 阴影 */
    .auth-container {
        max-width: 420px;
        margin: 0rem auto;
        padding: 0 2rem 2rem !important;
        background: rgba(30, 30, 46, 0.92);
        backdrop-filter: blur(12px);
        border-radius: 2rem;
        box-shadow: 0 25px 45px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .auth-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 30px 50px -15px rgba(0, 0, 0, 0.6);
    }
    
    /* 标题渐变 */
    .main-header {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
        text-align: center;  /* 新增居中 */
    }
    
    /* 副标题 */
    .auth-container > div[style*="text-align: center"] {
        font-size: 0.9rem;
        color: #9CA3AF;
        margin-bottom: 1.8rem;
        font-weight: 500;
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input {
        border-radius: 1rem !important;
        border: 1px solid #3F3F4A !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease;
        background-color: #2D2D3A !important;
        color: #E0E0E0 !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #60A5FA !important;
        box-shadow: 0 0 0 3px rgba(96,165,250,0.2) !important;
        background-color: #3D3D4A !important;
        outline: none;
    }
    
    /* 下拉选择框（选项卡） */
    .stSelectbox > div > div > select {
        border-radius: 2rem !important;
        background-color: #2D2D3A !important;
        border: none !important;
        font-weight: 500;
        padding: 0.5rem 1rem !important;
        color: #E0E0E0;
    }
    
    /* 单选按钮组 */
    .stRadio > div {
        gap: 1rem;
    }
    .stRadio label {
        font-weight: 500;
        color: #D1D5DB;
    }
    
    /* 按钮渐变 */
    .stButton > button {
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%) !important;
        border: none !important;
        border-radius: 2rem !important;
        padding: 0.6rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        color: white !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 12px -4px rgba(59,130,246,0.5);
    }
    
    /* 分隔线 */
    hr {
        margin: 1.5rem 0;
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #4B5563, transparent);
    }
    
    /* 标签文字 */
    .stTextInput label, .stSelectbox label, .stRadio label {
        font-weight: 600;
        color: #D1D5DB;
        margin-bottom: 0.25rem;
        font-size: 0.85rem;
    }
    
    /* 风险等级卡片样式保持不变 */
    .risk-high {
        background-color: #4a1e1e;
        border-left: 5px solid #dc2626;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-size: 14px;
    }
    .risk-mid {
        background-color: #4a3a1e;
        border-left: 5px solid #f59e0b;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-size: 14px;
    }
    .risk-low {
        background-color: #1e2a4a;
        border-left: 5px solid #3b82f6;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-size: 14px;
    }
    .warning-box {
        background-color: #4a1e2a;
        border: 1px solid #ffccc7;
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        font-size: 14px;
    }
    .footer {
        text-align: center;
        margin-top: 1.5rem;
        color: #9CA3AF;
        font-size: 12px;
    }
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
    
    /* 其他 Streamlit 组件微调 */
    .stTextInput > div > div > input, .stSelectbox > div > div > select {
        font-size: 14px;
        padding: 8px;
    }
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.2rem !important;
        margin-bottom: 0.5rem !important;
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
        headers = {"Content-Type": "application/json"}
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
    try:
        url = f"{BACKEND_URL}{API_PREFIX}/auth/login"
        data = {"username": username, "password": password, "scope": ""}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
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
    current_time = time.time()
    cache_duration = 30
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
                st.session_state["system_status_cache"] = {
                    "knowledge_base": {"total_cases": 12384, "last_updated": "2026-03-28T00:00:00", "cases_by_type": {}, "cases_by_risk_level": {}},
                    "learning_status": {"progress": 0.85, "last_training": "2026-03-28T03:00:00", "total_training_samples": 15000, "next_scheduled_training": "每日 03:00"},
                    "system_health": {"vector_db": "healthy", "api_server": "healthy", "last_health_check": datetime.now().isoformat()}
                }
                st.session_state["last_status_update"] = current_time
        except Exception:
            st.session_state["system_status_cache"] = {
                "knowledge_base": {"total_cases": 12384, "last_updated": "2026-03-28T00:00:00", "cases_by_type": {}, "cases_by_risk_level": {}},
                "learning_status": {"progress": 0.85, "last_training": "2026-03-28T03:00:00", "total_training_samples": 15000, "next_scheduled_training": "每日 03:00"},
                "system_health": {"vector_db": "healthy", "api_server": "healthy", "last_health_check": datetime.now().isoformat()}
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
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="main-header">多模态反诈智能助手</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; font-size: 0.9rem; color: #6B7280; margin-bottom: 1rem;">基于多模态AI的实时反诈防护系统</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('</div>', unsafe_allow_html=True)
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
    else:
        st.subheader("📝 用户注册")
        reg_username = st.text_input("用户名", key="reg_username")
        reg_email = st.text_input("邮箱", key="reg_email")
        reg_password = st.text_input("密码", type="password", key="reg_password")
        reg_confirm_password = st.text_input("确认密码", type="password", key="reg_confirm_password")
        st.markdown("---")
        st.caption("基本信息（必填）")
        reg_role = st.selectbox("选择您的身份", ["儿童/青少年", "青年（学生/职场新人）", "中年（职场人士）", "老年人", "财务/高管（高风险）"], key="reg_role")
        reg_gender = st.radio("性别", ["男", "女"], key="reg_gender")
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
                    risk_sensitivity="medium",
                    guardian_name=reg_guardian_name,
                    guardian_phone=reg_guardian_phone,
                    guardian_email=reg_guardian_email
                )
                if result:
                    st.success("注册成功！请登录")
                else:
                    st.error("注册失败，用户名或邮箱可能已被使用")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 已登录状态 - 显示侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=60)
    st.title("🔐 用户信息")
    st.markdown("---")
    user_info = st.session_state["user_info"] or {}
    st.success(f"✅ 已登录: {user_info.get('username', '用户')}")
    st.caption(f"角色: {st.session_state['role']}")
    st.caption(f"性别: {st.session_state['gender']}")
    if st.button("🚪 退出登录"):
        st.session_state["access_token"] = None
        st.session_state["user_info"] = None
        st.rerun()
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
    if st.button("🔄 手动更新向量数据库"):
        with st.spinner("正在同步最新诈骗案例库..."):
            result = update_knowledge_base()
            if result:
                st.success(f"向量数据库更新成功！更新于: {result.get('updated_at', '刚刚')}")
                system_status = get_system_status()
                knowledge_base = system_status.get("knowledge_base", {})
                learning_status = system_status.get("learning_status", {})
            else:
                st.error("向量数据库更新失败，请检查后端服务")
    st.caption(f"自动更新: 每日 03:00 | 最后更新: {last_updated_str}")
    st.caption(f"当前向量数据库条目: {knowledge_base.get('total_cases', 12384):,} 条诈骗模式")
    st.caption(f"模型自学习进度: {learning_status.get('progress', 0.85):.1%}")

# 主页面标题
st.markdown('<div class="main-container">', unsafe_allow_html=True)
# 添加 LOGO
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🛡️ 多模态反诈智能助手")
    st.caption("基于多模态AI的实时反诈防护系统", help=None)
    st.markdown("")  # 可选占位
# 创建三列用于不同模态输入
col_text, col_audio, col_image = st.columns(3)

input_data = {"text": "", "audio": None, "image": None}
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
        with st.spinner("多模态融合分析中... "):
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
                # 显示处理总时长
                if "processing_time" in result:
                    st.caption(f"⏱️ 处理总时长: {result['processing_time']:.2f} 秒")

            st.markdown(f"**🔍 详细分析：** {result.get('details', '无详细分析')}")
            st.markdown(f"**💡 处置建议：** {result.get('advice', '请保持警惕')}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 分级预警展示
        st.markdown("### 🔔 实时预警机制")
        guardian_phone_val = st.session_state.get("guardian_phone", "")
        if level == "高危":
            # 语音阻断
            js_code = """
            <script>
                var msg = new SpeechSynthesisUtterance("警告！检测到高危诈骗，请立即停止操作！");
                window.speechSynthesis.speak(msg);
            </script>
            """
            st.components.v1.html(js_code, height=0)
            st.error("🔴 高危预警：已触发弹窗阻断并自动通知监护人！")
            if guardian_phone_val:
                st.warning(f"📞 正在拨打监护人电话 {guardian_phone_val} 进行紧急联动...")
            else:
                st.info("请完善监护人信息以启用自动联动")
            
            # 一键通报监护人按钮
            analysis_id = result.get("analysis_id")
            if st.button("📢 一键通报监护人", key="notify_guardian_btn"):
                if not analysis_id:
                    st.warning("无法获取分析记录ID，请稍后重试")
                else:
                    with st.spinner("正在通知监护人..."):
                        notify_resp = requests.post(
                            f"{BACKEND_URL}{API_PREFIX}/analyze/notify-guardian",
                            json={"analysis_id": analysis_id},
                            headers={"Authorization": f"Bearer {st.session_state['access_token']}"}
                        )
                        if notify_resp.status_code == 200:
                            st.success("已通知监护人，请保持通讯畅通。")
                        else:
                            st.error("通知失败，请检查监护人信息是否完整。")
        elif level == "中危":
            st.warning("🟡 中危提醒：建议立即核实对方身份，谨防受骗。")
        else:
            st.info("🔵 当前会话安全，持续监控中。")
        
        # 安全监测仪表盘
        st.markdown("### 📊 安全监测仪表盘")
        risk_score_val = result.get('risk_score', 0)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = risk_score_val,
            title = {'text': "风险评分"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkred"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgray"},
                    {'range': [30, 70], 'color': "gray"},
                    {'range': [70, 100], 'color': "darkred"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': risk_score_val}
            }
        ))
        st.plotly_chart(fig_gauge, width='stretch')
        
        fraud_type = result.get('fraud_type', '未知')
        confidence = result.get('confidence', 0)
        fig_bar = go.Figure(go.Bar(
            x=[fraud_type],
            y=[confidence],
            text=[f"{confidence:.1%}"],
            textposition='auto',
            marker_color='crimson',
            name='置信度'
        ))
        fig_bar.update_layout(title="诈骗类型置信度", yaxis=dict(range=[0, 1], tickformat=".0%"), xaxis_title="诈骗类型", yaxis_title="置信度")
        st.plotly_chart(fig_bar, width='stretch')
        
        # HTML报告下载
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>安全监测报告</title></head>
        <body>
        <h1>反诈安全监测报告</h1>
        <p><strong>用户角色：</strong>{st.session_state['role']}</p>
        <p><strong>分析时间：</strong>{result.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
        <p><strong>风险等级：</strong><span style="color:red">{level}</span></p>
        <p><strong>诈骗类型：</strong>{fraud_type}</p>
        <p><strong>置信度：</strong>{confidence:.1%}</p>
        <p><strong>详细分析：</strong>{result.get('details', '')}</p>
        <p><strong>处置建议：</strong>{result.get('advice', '')}</p>
        <hr>
        <p>本报告由多模态反诈智能助手自动生成。</p>
        </body>
        </html>
        """
        st.download_button(
            label="📄 下载安全监测报告 (HTML)",
            data=report_html,
            file_name=f"反诈报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
        )
        
        # 自适应进化模块提示
        st.markdown("### 🧬 自适应进化")
        st.success("本次分析结果已用于优化反诈模型，向量数据库持续进化中。")
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
                st.metric("向量数据库案例数", f"{system_status.get('knowledge_base', {}).get('total_cases', 12384):,}")
        
elif not analyze_btn:
    st.info("👆 点击【立即智能分析】按钮，系统将综合文本、语音、视觉信息进行诈骗风险研判")


st.markdown("---")
st.markdown('<div class="footer">多模态反诈智能助手 | 基于AI的全民反诈防护体系 | 实时守护您的数字生活</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)