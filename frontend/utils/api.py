"""
API客户端模块
包含与后端API通信的函数和配置
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any

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

# 反向映射（用于显示）
ROLE_REVERSE_MAP = {v: k for k, v in ROLE_MAP.items()}
GENDER_REVERSE_MAP = {v: k for k, v in GENDER_MAP.items()}
RISK_REVERSE_MAP = {v: k for k, v in RISK_MAP.items()}

def get_auth_headers() -> Dict[str, str]:
    """
    获取认证头部信息

    Returns:
        包含Authorization头的字典
    """
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def register_user(
    username: str,
    email: str,
    password: str,
    role: str,
    gender: str,
    risk_sensitivity: str,
    guardian_name: str = "",
    guardian_phone: str = "",
    guardian_email: str = ""
) -> Optional[Dict[str, Any]]:
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

def login_user(username: str, password: str) -> bool:
    """用户登录"""
    try:
        url = f"{BACKEND_URL}{API_PREFIX}/auth/login"
        # OAuth2PasswordRequestForm 需要表单格式数据
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
            # 获取用户信息
            st.session_state["user_info"] = {"username": username}
            return True
        else:
            # 显示后端返回的错误信息
            try:
                error_detail = response.json().get("detail", "未知错误")
                st.error(f"登录失败: {error_detail}")
            except:
                st.error(f"登录失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        st.error(f"登录请求异常: {e}")
        return False

def call_backend_analysis(
    text: str,
    audio_file: Any,
    image_file: Any,
    enable_deep_audio: bool = False,
    enable_ocr: bool = False,
    enable_behavior_profile: bool = False
) -> Optional[Dict[str, Any]]:
    """
    调用后端分析API

    Args:
        text: 文本内容
        audio_file: 音频文件对象
        image_file: 图像文件对象
        enable_deep_audio: 是否启用深度语音特征分析
        enable_ocr: 是否启用OCR文字提取
        enable_behavior_profile: 是否启用行为画像

    Returns:
        分析结果字典或None
    """
    try:
        url = f"{BACKEND_URL}{API_PREFIX}/analyze/multimodal"
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"

        # 准备请求数据
        data = {
            "text": text,
            "enable_deep_audio": enable_deep_audio,
            "enable_ocr": enable_ocr,
            "enable_behavior_profile": enable_behavior_profile
        }

        # 准备文件上传
        files = {}

        if audio_file is not None:
            files["audio"] = ("audio.wav", audio_file.read(), "audio/wav")
            audio_file.seek(0)  # 重置文件指针

        if image_file is not None:
            files["image"] = ("image.jpg", image_file.read(), "image/jpeg")
            image_file.seek(0)  # 重置文件指针

        # 如果有文件，使用multipart/form-data
        if files:
            # 移除JSON头，让requests自动设置
            headers.pop("Content-Type", None)
            # 构建multipart数据
            multipart_data = {}
            for key, value in data.items():
                multipart_data[key] = (None, str(value))

            response = requests.post(
                url,
                files={**files, **multipart_data},
                headers=headers
            )
        else:
            # 没有文件，使用JSON
            response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"分析请求失败: HTTP {response.status_code}")
            try:
                error_detail = response.json().get("detail", response.text)
                st.error(f"错误详情: {error_detail}")
            except:
                pass
            return None
    except Exception as e:
        st.error(f"分析请求异常: {e}")
        return None

def mock_analysis(
    text: str,
    audio_flag: bool,
    image_flag: bool,
    role: str,
    sensitivity: str
) -> Dict[str, Any]:
    """
    模拟分析结果（当后端不可用时使用）

    Args:
        text: 文本内容
        audio_flag: 是否有音频
        image_flag: 是否有图片
        role: 用户角色
        sensitivity: 风险灵敏度

    Returns:
        模拟分析结果
    """
    import time
    import random

    # 模拟处理时间
    time.sleep(1.5)

    # 根据输入内容生成模拟结果
    risk_levels = ["low", "medium", "high"]
    fraud_types = ["投资诈骗", "刷单诈骗", "冒充公检法", "网络购物诈骗", "虚假贷款", "杀猪盘"]

    # 简单的风险判断逻辑
    risk_keywords = {
        "high": ["转账", "密码", "验证码", "汇款", "投资", "高回报", "保证金"],
        "medium": ["优惠", "中奖", "免费", "领取", "活动", "抽奖"],
        "low": ["你好", "谢谢", "请问", "帮忙", "咨询"]
    }

    detected_risk = "low"
    for level, keywords in risk_keywords.items():
        if any(keyword in text for keyword in keywords):
            detected_risk = level
            break

    # 根据用户角色和灵敏度调整风险
    risk_adjustments = {
        "child": 0.3,
        "youth": 0.1,
        "adult": 0.0,
        "elderly": 0.4,
        "high_risk": -0.2
    }

    sensitivity_adjustments = {
        "low": -0.2,
        "medium": 0.0,
        "high": 0.3
    }

    # 模拟置信度
    confidence = random.uniform(0.6, 0.95)

    return {
        "risk_level": detected_risk,
        "confidence": round(confidence, 2),
        "fraud_type": random.choice(fraud_types),
        "analysis": "这是一条模拟分析结果。实际使用时请连接后端服务。",
        "suggestions": [
            "不要轻易转账汇款",
            "核实对方身份信息",
            "保护个人隐私信息",
            "及时报警处理"
        ],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def logout():
    """退出登录"""
    st.session_state["access_token"] = None
    st.session_state["user_info"] = None
    st.rerun()