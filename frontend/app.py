"""
多模态反诈智能助手 - 主应用入口
Streamlit多页面应用的主文件
"""

import streamlit as st

try:
    # 在frontend目录中运行时使用相对导入
    from components.theme import init_theme_state, apply_theme
    from utils.session import init_session_state
except ImportError:
    # 在pages目录中或作为模块运行时使用绝对导入
    from frontend.components.theme import init_theme_state, apply_theme
    from frontend.utils.session import init_session_state

# 初始化session状态
init_session_state()
init_theme_state()

# 应用主题
apply_theme(st.session_state.get("theme", "light"))

# 显示欢迎信息
st.title("🛡️ 多模态反诈智能助手")
st.markdown("基于多模态AI的实时反诈防护系统")

st.info("""
这是一个多页面应用。请使用侧边栏导航到不同页面：

- **登录/注册页面**: 用户认证和注册
- **主功能界面**: 多模态诈骗风险分析

如果侧边栏未显示，请点击左上角的箭头图标。
""")

# 检查认证状态
if st.session_state.get("access_token"):
    st.success(f"已登录用户: {st.session_state.get('user_info', {}).get('username', '未知用户')}")
    if st.button("🚪 退出登录"):
        st.session_state["access_token"] = None
        st.session_state["user_info"] = None
        st.rerun()
else:
    st.warning("您尚未登录。请前往登录页面进行认证。")

# 显示当前session状态（调试用，生产环境可移除）
with st.expander("调试信息 - Session状态"):
    st.json({
        "access_token": "***" if st.session_state.get("access_token") else None,
        "user_info": st.session_state.get("user_info"),
        "role": st.session_state.get("role"),
        "gender": st.session_state.get("gender"),
        "risk_sensitivity": st.session_state.get("risk_sensitivity"),
        "theme": st.session_state.get("theme")
    })