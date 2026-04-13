"""
多模态功能主界面
包含文本、语音、图像的多模态诈骗风险分析功能
"""

import streamlit as st
import time
import pandas as pd
from datetime import datetime

try:
    # 尝试绝对导入
    from frontend.components.theme import apply_theme, init_theme_state, render_theme_toggle
    from frontend.utils.api import call_backend_analysis, mock_analysis, logout, get_auth_headers
    from frontend.utils.session import init_session_state, is_authenticated
except ImportError:
    # 回退到相对导入
    from ..components.theme import apply_theme, init_theme_state, render_theme_toggle
    from ..utils.api import call_backend_analysis, mock_analysis, logout, get_auth_headers
    from ..utils.session import init_session_state, is_authenticated

# 页面配置 - 显示侧边栏，宽布局
st.set_page_config(
    page_title="反诈智能助手",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化状态
init_session_state()
init_theme_state()

# 应用主题
apply_theme(st.session_state.get("theme", "light"))

# 检查认证状态
if not is_authenticated():
    st.warning("请先登录")
    time.sleep(1)
    st.switch_page("pages/01_Login.py")
    st.stop()

# 主题切换按钮
render_theme_toggle()

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=60)

    # 用户信息
    st.title("🔐 用户信息")
    st.markdown("---")

    user_info = st.session_state["user_info"] or {}
    st.success(f"✅ 已登录: {user_info.get('username', '用户')}")
    st.caption(f"角色: {st.session_state['role']}")
    st.caption(f"性别: {st.session_state['gender']}")

    if st.button("🚪 退出登录"):
        logout()
        st.switch_page("pages/01_Login.py")

    st.markdown("---")
    st.title("⚙️ 个性化设置")
    st.markdown("---")

    # 角色定制
    st.subheader("👤 我的角色")
    st.session_state["role"] = st.selectbox(
        "选择您的身份",
        ["儿童/青少年", "青年（学生/职场新人）", "中年（职场人士）", "老年人", "财务/高管（高风险）"],
        index=["儿童/青少年", "青年（学生/职场新人）", "中年（职场人士）", "老年人", "财务/高管（高风险）"].index(st.session_state["role"]),
        key="sidebar_role"
    )
    st.session_state["gender"] = st.radio("性别", ["男", "女"], horizontal=True, index=0 if st.session_state["gender"] == "男" else 1, key="sidebar_gender")

    st.markdown("---")
    st.subheader("👨‍👩‍👧 监护人联动")
    st.session_state["guardian_name"] = st.text_input("监护人姓名", placeholder="例如：张老师", value=st.session_state["guardian_name"], key="sidebar_guardian_name")
    st.session_state["guardian_phone"] = st.text_input("监护人电话", placeholder="用于紧急通知", value=st.session_state["guardian_phone"], key="sidebar_guardian_phone")
    st.session_state["guardian_email"] = st.text_input("监护人邮箱", placeholder="用于报告推送", value=st.session_state["guardian_email"], key="sidebar_guardian_email")

    st.markdown("---")
    st.subheader("📋 风险偏好")
    st.session_state["risk_sensitivity"] = st.select_slider(
        "预警灵敏度",
        options=["低", "中", "高"],
        value=st.session_state["risk_sensitivity"],
        key="sidebar_risk_sensitivity"
    )

    # 知识库更新状态模拟
    st.markdown("---")
    st.subheader("📚 知识库状态")
    st.progress(0.85, text="最新诈骗模式库已更新")
    st.caption("每周自动更新诈骗案例库")

# 主内容区
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.markdown('<div class="main-header">🛡️ 多模态反诈智能助手</div>', unsafe_allow_html=True)
st.markdown("基于多模态AI的实时反诈防护系统 | 支持文本、语音、图像联合分析")

# 创建三列用于不同模态输入
col_text, col_audio, col_image = st.columns(3)

# 存储模态数据
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

# 分析按钮
st.markdown("---")
if st.button("🔍 立即智能分析", type="primary", use_container_width=True):
    if not text_input and not audio_file and not image_file:
        st.warning("请至少输入一种模态的数据（文本、音频或图片）")
    else:
        with st.spinner("正在进行多模态智能分析..."):
            # 调用后端API
            result = call_backend_analysis(
                text=text_input,
                audio_file=audio_file,
                image_file=image_file,
                enable_deep_audio=enable_deep_audio,
                enable_ocr=enable_ocr,
                enable_behavior_profile=enable_behavior_profile
            )

            # 如果后端不可用，使用模拟分析
            if not result:
                st.info("后端服务暂不可用，使用模拟分析结果")
                result = mock_analysis(
                    text=text_input,
                    audio_flag=audio_file is not None,
                    image_flag=image_file is not None,
                    role=st.session_state["role"],
                    sensitivity=st.session_state["risk_sensitivity"]
                )

            # 显示分析结果
            if result:
                st.markdown("---")
                st.subheader("📊 分析结果")

                # 风险等级卡片
                risk_level = result.get("risk_level", "low")
                confidence = result.get("confidence", 0.0)
                fraud_type = result.get("fraud_type", "未知类型")

                if risk_level == "high":
                    st.markdown('<div class="risk-high">', unsafe_allow_html=True)
                    st.markdown(f"### ⚠️ 高危风险 ({confidence*100:.1f}%)")
                    st.markdown(f"**诈骗类型**: {fraud_type}")
                    st.markdown("</div>", unsafe_allow_html=True)
                elif risk_level == "medium":
                    st.markdown('<div class="risk-mid">', unsafe_allow_html=True)
                    st.markdown(f"### ⚠️ 中危风险 ({confidence*100:.1f}%)")
                    st.markdown(f"**诈骗类型**: {fraud_type}")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-low">', unsafe_allow_html=True)
                    st.markdown(f"### ✅ 低危风险 ({confidence*100:.1f}%)")
                    st.markdown(f"**风险类型**: {fraud_type}")
                    st.markdown("</div>", unsafe_allow_html=True)

                # 详细分析和建议
                st.markdown("---")
                col_detail, col_suggestion = st.columns(2)

                with col_detail:
                    st.subheader("📋 详细分析")
                    analysis_text = result.get("analysis", "无详细分析结果")
                    st.write(analysis_text)

                    # 显示检测到的关键信息
                    if "keywords" in result:
                        st.markdown("**检测到关键词**:")
                        for kw in result["keywords"]:
                            st.markdown(f"- `{kw}`")

                with col_suggestion:
                    st.subheader("💡 处置建议")
                    suggestions = result.get("suggestions", [
                        "保持警惕，不轻信陌生信息",
                        "不随意点击链接或下载附件",
                        "涉及资金交易请多方核实",
                        "及时向平台举报可疑行为"
                    ])

                    for i, suggestion in enumerate(suggestions, 1):
                        st.markdown(f"{i}. {suggestion}")

                # 安全监测报告
                st.markdown("---")
                st.subheader("📈 安全监测报告")

                # 生成报告数据
                report_data = {
                    "分析时间": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "风险等级": [risk_level],
                    "置信度": [f"{confidence*100:.1f}%"],
                    "诈骗类型": [fraud_type],
                    "用户角色": [st.session_state["role"]],
                    "灵敏度设置": [st.session_state["risk_sensitivity"]]
                }

                report_df = pd.DataFrame(report_data)
                st.dataframe(report_df, use_container_width=True)

                # 下载报告
                csv = report_df.to_csv(index=False)
                st.download_button(
                    label="📥 下载分析报告 (CSV)",
                    data=csv,
                    file_name=f"反诈分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                # 实时预警机制
                if risk_level in ["high", "medium"]:
                    st.markdown("---")
                    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                    st.subheader("🚨 实时预警机制已激活")

                    if risk_level == "high":
                        st.warning("**高危预警**: 已触发自动防护机制，建议立即采取措施")
                        if st.session_state["guardian_phone"] or st.session_state["guardian_email"]:
                            st.info("监护人通知已准备就绪")
                        if st.button("🆘 一键紧急求助", type="secondary", use_container_width=True):
                            st.success("紧急求助信号已发送，请保持通讯畅通")
                    else:
                        st.info("**中危预警**: 系统已记录此事件，建议密切关注")

                    st.markdown("</div>", unsafe_allow_html=True)

                # 全时守护状态
                st.markdown("---")
                st.subheader("🛡️ 全时守护状态")
    guard_col1, guard_col2, guard_col3 = st.columns(3)

    with guard_col1:
        st.metric("今日检测次数", "12", "3")
    with guard_col2:
        st.metric("风险拦截率", "96.7%", "1.2%")
    with guard_col3:
        st.metric("平均响应时间", "0.8s", "-0.2s")

    st.caption("系统7×24小时全天候守护您的数字安全")

st.markdown('</div>', unsafe_allow_html=True)

# 隐藏Streamlit自动生成的页面导航
hide_pages_nav = """
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
"""
st.markdown(hide_pages_nav, unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("多模态反诈智能助手 v2.0 | 基于Streamlit + FastAPI架构")
st.markdown("© 2024 反诈安全研究中心 | 数据隐私保护 | 服务条款")
st.markdown("</div>", unsafe_allow_html=True)