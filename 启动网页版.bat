@echo off
cd /d "%~dp0"
echo ==========================================
echo   AI Assistant - Web (Streamlit)
echo ==========================================
echo Starting... your browser will open soon.
echo Press Ctrl + C in this window to STOP.
echo.
py -m streamlit run app.py
echo.
echo Server stopped.
pause
