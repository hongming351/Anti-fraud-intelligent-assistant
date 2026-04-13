"""
登录/注册页面
独立认证界面，只包含注册/登录、角色选择和监护人信息
"""

import streamlit as st
import time

try:
    # 尝试绝对导入
    from frontend.components.theme import apply_theme, init_theme_state, render_theme_toggle
    from frontend.utils.api import register_user, login_user
    from frontend.utils.session import init_session_state
except ImportError:
    # 回退到相对导入
    from ..components.theme import apply_theme, init_theme_state, render_theme_toggle
    from ..utils.api import register_user, login_user
    from ..utils.session import init_session_state

# 页面配置 - 隐藏侧边栏，居中布局
st.set_page_config(
    page_title="登录 - 反诈智能助手",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 初始化状态
init_session_state()
init_theme_state()

# 应用主题
apply_theme(st.session_state.get("theme", "light"))

# 主题切换按钮
render_theme_toggle()

# 如果已经登录，跳转到主界面
if st.session_state.get("access_token"):
    st.success("您已登录，正在跳转到主界面...")
    st.switch_page("pages/02_Main.py")

# 认证表单容器
st.markdown('<div class="auth-container">', unsafe_allow_html=True)

st.markdown('<div class="main-header">🛡️ 多模态反诈智能助手</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center;">基于多模态AI的实时反诈防护系统</div>', unsafe_allow_html=True)
st.markdown("---")

auth_tab = st.selectbox("选择操作", ["登录", "注册"], index=0)

if auth_tab == "登录":
    st.subheader("🔑 用户登录")
    login_username = st.text_input("用户名", key="login_username")
    login_password = st.text_input("密码", type="password", key="login_password")

    if st.button("登录", type="primary", use_container_width=True):
        if login_username and login_password:
            with st.spinner("登录中..."):
                if login_user(login_username, login_password):
                    st.success("登录成功！正在跳转到主界面...")
                    time.sleep(1)
                    st.switch_page("pages/02_Main.py")
                else:
                    st.error("登录失败，请检查用户名和密码")
        else:
            st.warning("请输入用户名和密码")
else:  # 注册
    st.subheader("📝 用户注册")
    reg_username = st.text_input("用户名", key="reg_username")
    reg_email = st.text_input("邮箱", key="reg_email")
    reg_password = st.text_input("密码", type="password", key="reg_password")
    reg_confirm_password = st.text_input("确认密码", type="password", key="reg_confirm_password")

    # 注册时也需要角色等信息，添加到注册表单中
    st.markdown("---")
    st.caption("基本信息（必填）")
    reg_role = st.selectbox(
        "选择您的身份",
        ["儿童/青少年", "青年（学生/职场新人）", "中年（职场人士）", "老年人", "财务/高管（高风险）"],
        key="reg_role",
        index=1
    )
    reg_gender = st.radio("性别", ["男", "女"], key="reg_gender", horizontal=True)
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

    if st.button("注册", type="primary", use_container_width=True):
        if not reg_username or not reg_email or not reg_password:
            st.warning("请填写所有必填字段")
        elif reg_password != reg_confirm_password:
            st.error("两次输入的密码不一致")
        else:
            with st.spinner("注册中..."):
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

st.markdown('</div>', unsafe_allow_html=True)

# 隐藏Streamlit自动生成的页面导航
hide_pages_nav = """
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
"""
st.markdown(hide_pages_nav, unsafe_allow_html=True)