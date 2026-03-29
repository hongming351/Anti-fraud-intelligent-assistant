import streamlit as st

st.set_page_config(page_title="测试应用", page_icon="✅")
st.title("Streamlit测试应用")
st.write("这是一个简单的测试应用，用于检查Streamlit是否能正常运行。")

name = st.text_input("请输入您的名字")
if name:
    st.success(f"您好，{name}！Streamlit运行正常。")