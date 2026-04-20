@echo off
echo 启动反诈智能助手后端...
cd /d D:\Anti-fraud-intelligent-assistant\backend
call .venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause