@echo off
chcp 65001
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
pause
