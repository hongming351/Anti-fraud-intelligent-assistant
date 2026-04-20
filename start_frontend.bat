@echo off
echo 启动反诈智能助手前端...
cd /d D:\Anti-fraud-intelligent-assistant
call .venv\Scripts\activate
streamlit run front_end.py
pause