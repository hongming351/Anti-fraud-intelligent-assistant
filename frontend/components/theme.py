"""
主题管理模块
包含亮色和暗色主题的CSS样式，以及主题切换功能
"""

# 亮色主题CSS
LIGHT_THEME_CSS = """
<style>
    body {
        background-color: #f8f9fa;
        color: #333;
        font-size: 14px;
    }
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 1.5rem;
        background: white;
        border-radius: 0.8rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header {
        font-size: 1.8rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.8rem;
    }
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
    /* 调整Streamlit默认元素大小 */
    .stTextInput > div > div > input {
        font-size: 14px;
        padding: 8px;
    }
    .stSelectbox > div > div > select {
        font-size: 14px;
        padding: 8px;
    }
    .stRadio > div {
        font-size: 14px;
    }
    .stSlider > div {
        font-size: 14px;
    }
    .stButton > button {
        font-size: 14px;
        padding: 8px 16px;
    }
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stSubheader {
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
</style>
"""

# 暗色主题CSS
DARK_THEME_CSS = """
<style>
    body {
        background-color: #1e1e1e;
        color: #e0e0e0;
        font-size: 14px;
    }
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 1.5rem;
        background: #2d2d2d;
        border-radius: 0.8rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .main-header {
        font-size: 1.8rem;
        color: #64b5f6;
        text-align: center;
        margin-bottom: 0.8rem;
    }
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
        color: #999;
        font-size: 12px;
    }
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
    input, textarea, select {
        background-color: #3d3d3d !important;
        color: #e0e0e0 !important;
        border: 1px solid #555 !important;
        font-size: 14px !important;
        padding: 8px !important;
    }
    button {
        background-color: #3b82f6 !important;
        color: white !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
    }
    /* 调整Streamlit默认元素大小 */
    .stTextInput > div > div > input {
        font-size: 14px;
        padding: 8px;
    }
    .stSelectbox > div > div > select {
        font-size: 14px;
        padding: 8px;
    }
    .stRadio > div {
        font-size: 14px;
    }
    .stSlider > div {
        font-size: 14px;
    }
    .stButton > button {
        font-size: 14px;
        padding: 8px 16px;
    }
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stSubheader {
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
</style>
"""

def apply_theme(theme: str = "light"):
    """
    应用主题CSS到页面

    Args:
        theme: 主题名称，"light" 或 "dark"
    """
    import streamlit as st

    if theme == "dark":
        st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)

def render_theme_toggle():
    """
    渲染主题切换按钮
    """
    import streamlit as st

    st.markdown('<div class="theme-toggle">', unsafe_allow_html=True)
    col_theme = st.columns([1, 1])
    with col_theme[0]:
        if st.button("🌙 切换暗色模式" if st.session_state.get("theme", "light") == "light" else "☀️ 切换亮色模式"):
            st.session_state["theme"] = "dark" if st.session_state.get("theme", "light") == "light" else "light"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def init_theme_state():
    """
    初始化主题状态
    """
    import streamlit as st

    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"