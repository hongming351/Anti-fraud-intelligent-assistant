"""
Session状态管理模块
包含session状态的初始化和管理函数
"""

import streamlit as st

def init_session_state():
    """
    初始化session state
    确保所有需要的状态变量都存在
    """
    # 认证相关状态
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "user_info" not in st.session_state:
        st.session_state["user_info"] = None

    # 用户偏好设置
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

    # 主题状态（由theme模块管理，但这里确保存在）
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"

    # 页面状态（用于页面导航）
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "login"

def clear_auth_state():
    """清除认证状态"""
    st.session_state["access_token"] = None
    st.session_state["user_info"] = None

def is_authenticated() -> bool:
    """检查用户是否已认证"""
    return st.session_state.get("access_token") is not None

def get_user_info() -> dict:
    """获取用户信息"""
    return st.session_state.get("user_info", {})

def update_user_preferences(
    role: str = None,
    gender: str = None,
    risk_sensitivity: str = None,
    guardian_name: str = None,
    guardian_phone: str = None,
    guardian_email: str = None
):
    """更新用户偏好设置"""
    if role is not None:
        st.session_state["role"] = role
    if gender is not None:
        st.session_state["gender"] = gender
    if risk_sensitivity is not None:
        st.session_state["risk_sensitivity"] = risk_sensitivity
    if guardian_name is not None:
        st.session_state["guardian_name"] = guardian_name
    if guardian_phone is not None:
        st.session_state["guardian_phone"] = guardian_phone
    if guardian_email is not None:
        st.session_state["guardian_email"] = guardian_email